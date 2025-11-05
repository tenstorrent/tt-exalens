# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# Unit test for ttexalens/util.py:search.
import unittest
from ttexalens.util import search


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.data = [
            "42",
            "<thing>",
            "BLACKHOLE",
            "O_RDWR",
            "Tensix",
            "Tenstorrent",
            "[/string,]",
            "_3",
            "__builtin_unreachable",
            "read",
            "reset",
            "status",
            "step",
            "team",
            "tech",
            "technology",
            "tender",
            "terminal emulator",
            "test",
            "tested",
            "testing",
            "text",
        ]

    def test_default(self):
        result = search(self.data, "*")
        self.assertEqual(self.data, result)

    def test_max(self):
        result = search(self.data, "te*", "all")
        self.assertEqual(
            result,
            [
                "Tensix",
                "Tenstorrent",
                "team",
                "tech",
                "technology",
                "tender",
                "terminal emulator",
                "test",
                "tested",
                "testing",
                "text",
            ],
        )

    def test_exact_match(self):
        result = search(["idk", "man"], "idk")
        self.assertEqual(result, ["idk"])
        result = search(self.data, "42")
        self.assertEqual(result, ["42"])

    def test_zero_results(self):
        result = search(["idk"], "man")
        self.assertEqual(result, [])

    def test_partial(self):
        result = search(self.data, "*re*", "2")  # 4 matches in total, limited to 2
        self.assertEqual(len(result), 2)

    def test_special_chars(self):
        result = search(self.data, "<*", "all")
        self.assertEqual(result, ["<thing>"])
        result = search(self.data, "*,]", "all")
        self.assertEqual(result, ["[/string,]"])
        result = search(self.data, "*_*", "all")
        self.assertEqual(result, ["O_RDWR", "_3", "__builtin_unreachable"])

    def test_invalid_max(self):
        with self.assertRaises(ValueError):
            search([], "", "-1")
        with self.assertRaises(ValueError):
            search([], "", "0")
        with self.assertRaises(ValueError):
            search([], "", "huh")


if __name__ == "__main__":
    unittest.main()
