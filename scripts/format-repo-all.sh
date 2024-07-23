THIS_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

./$THIS_SCRIPT_DIR/clang-format-repo.sh
python -m check_copyright --dry-run --verbose --config infra/copyright-config.yaml .