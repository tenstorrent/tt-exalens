#!/usr/bin/env python3
# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""Fill out and submit a Google Form from the command line.

Two modes:
  1. --inspect  : fetch the form and print every question with its entry.<id>
                  and the available choices. Use this first to learn the IDs.
  2. (default)  : submit answers you pass as entry.<id>=value pairs.

No browser required — it just talks HTTP to Google's formResponse endpoint.

Examples:
    # 1. Discover the fields
    python google_form_submit.py --inspect "https://docs.google.com/forms/d/e/FORM_ID/viewform"

    # 2. Submit answers (entry IDs come from the inspect step)
    python google_form_submit.py "https://docs.google.com/forms/d/e/FORM_ID/viewform" \
        entry.123456789="Ada Lovelace" \
        entry.987654321="Yes" \
        entry.555000111="Option A"

Dependencies:
    pip install requests
"""

import argparse
import json
import re
import sys

import requests


def _to_form_response_url(url: str) -> str:
    """Turn a .../viewform URL into the .../formResponse submit URL."""
    url = url.split("?")[0].rstrip("/")
    if url.endswith("/viewform"):
        url = url[: -len("/viewform")]
    if not url.endswith("/formResponse"):
        url = url + "/formResponse"
    return url


def fetch_form_structure(viewform_url: str):
    """Return the list of questions parsed out of the form's embedded JSON.

    Google embeds the whole form definition in a global `FB_PUBLIC_LOAD_DATA_`
    variable. Parsing that is far more reliable than scraping the rendered DOM.
    """
    resp = requests.get(viewform_url, timeout=30)
    resp.raise_for_status()

    match = re.search(r"FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);", resp.text, re.DOTALL)
    if not match:
        raise RuntimeError("Could not find form data. Is the URL a public Google Form viewform link?")

    data = json.loads(match.group(1))
    # data[1][1] is the list of form items.
    items = data[1][1]

    questions = []
    for item in items:
        title = item[1]
        # item[4] holds the answer fields for this question (None for text/section headers).
        field_list = item[4]
        if not field_list:
            continue
        for field in field_list:
            entry_id = field[0]
            # field[1] is the list of choices for multiple-choice/checkbox/dropdown.
            choices = [c[0] for c in field[1]] if field[1] else None
            required = bool(field[2]) if len(field) > 2 else False
            questions.append(
                {
                    "title": title,
                    "entry_id": f"entry.{entry_id}",
                    "choices": choices,
                    "required": required,
                }
            )
    return questions


def inspect(viewform_url: str):
    questions = fetch_form_structure(viewform_url)
    if not questions:
        print("No answerable questions found.")
        return
    for q in questions:
        req = " (required)" if q["required"] else ""
        print(f"\n{q['title']}{req}")
        print(f"  field: {q['entry_id']}")
        if q["choices"]:
            print("  choices:")
            for c in q["choices"]:
                print(f"    - {c}")


def resolve_index_answers(viewform_url: str, answers: dict) -> dict:
    """Replace any '#N' values with the Nth choice (1-based) of that question.

    Only fetches the form structure if at least one answer uses #N syntax.
    """

    def is_index(v):
        return isinstance(v, str) and v.startswith("#") and v[1:].isdigit()

    needs_lookup = any(is_index(v) or (isinstance(v, list) and any(is_index(x) for x in v)) for v in answers.values())
    if not needs_lookup:
        return answers

    questions = fetch_form_structure(viewform_url)
    choices_by_entry = {q["entry_id"]: q["choices"] for q in questions}

    def resolve_one(entry_id, value):
        if not is_index(value):
            return value
        choices = choices_by_entry.get(entry_id)
        if not choices:
            raise ValueError(f"{entry_id} has no choices to index into")
        idx = int(value[1:])
        if not (1 <= idx <= len(choices)):
            raise ValueError(f"{entry_id}: index {idx} out of range (1..{len(choices)})")
        chosen = choices[idx - 1]
        print(f"{entry_id}: #{idx} -> {chosen!r}")
        return chosen

    resolved = {}
    for entry_id, value in answers.items():
        if isinstance(value, list):
            resolved[entry_id] = [resolve_one(entry_id, v) for v in value]
        else:
            resolved[entry_id] = resolve_one(entry_id, value)
    return resolved


def submit(viewform_url: str, answers: dict):
    answers = resolve_index_answers(viewform_url, answers)
    submit_url = _to_form_response_url(viewform_url)

    # requests encodes a list value as repeated keys — needed for checkbox
    # questions where you select multiple options.
    payload = {}
    for key, value in answers.items():
        payload[key] = value

    for _ in range(100):
        resp = requests.post(
            submit_url,
            data=payload,
            headers={"Referer": viewform_url},
            timeout=30,
        )

        if resp.status_code != 200:
            print(f"Submission returned HTTP {resp.status_code} — not submitted.", file=sys.stderr)
            sys.exit(1)

        body = resp.text

        # A genuinely-recorded response lands on the confirmation page.
        confirmation_markers = (
            "freebirdFormviewerViewResponseConfirmationMessage",  # CSS class on the confirm page
            "Your response has been recorded",
            "Ваш одговор је забележен",  # Serbian
        )
        # A rejected submit re-renders the same form (questions present again).
        rerendered_form = "FB_PUBLIC_LOAD_DATA_" in body

        if any(marker in body for marker in confirmation_markers):
            print("Form submitted successfully — confirmation page received.")
        elif rerendered_form:
            print(
                "NOT submitted: Google re-rendered the form (HTTP 200 but no confirmation).\n"
                "Likely a required question was left blank, an entry ID is wrong, or a "
                "choice value doesn't match exactly.",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            # 200 but neither signal — report it honestly rather than claiming success.
            print(
                "Submitted (HTTP 200) but no confirmation marker was found. "
                "Verify manually in the form's responses.",
                file=sys.stderr,
            )


def parse_answer_args(pairs):
    """Parse 'entry.123=value' strings into a dict.

    Repeating the same key builds a list (for multi-select checkbox questions):
        entry.123=A entry.123=B  ->  {'entry.123': ['A', 'B']}
    """
    answers = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Bad answer (expected entry.ID=value): {pair!r}")
        key, value = pair.split("=", 1)
        if key in answers:
            existing = answers[key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                answers[key] = [existing, value]
        else:
            answers[key] = value
    return answers


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url", help="Google Form viewform URL")
    parser.add_argument(
        "answers",
        nargs="*",
        help="Answers as entry.ID=value pairs. Use entry.ID=#N to pick the "
        "Nth choice (1-based). Repeat a key for multi-select.",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Print the form's questions and entry IDs instead of submitting",
    )
    args = parser.parse_args()

    if args.inspect:
        inspect(args.url)
        return

    if not args.answers:
        parser.error("No answers given. Use --inspect first to find the entry IDs.")

    answers = parse_answer_args(args.answers)
    submit(args.url, answers)


if __name__ == "__main__":
    main()
