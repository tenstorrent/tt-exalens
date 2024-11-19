#!/bin/sh

# A couple of notes about the command below:
# If we omitted \( and \), the -not filter would've been applied only on -name '*.h', since it has
# higher precedence than -or.
# -print0 will separate each file will null character when printing the result.
# -z in sort tells it to expect null separator between items. Items are sorted just for prettier log.
# -0 in xargs tells it to expect null separator between items, each passed to clang-format.
# -t will print out commands being executed, for prettier log and easier debug.
# -n1 limits the number of items to pass to clang-format to 1. This is also just for easier debugging,
# since clang-format can also accept multiple files.
#
# Note that pybuda docker image has default clang-format at /usr/local/bin, so using explicit location.
echo "Running clang-format version $(clang-format --version) on all files in the repository."
find . \( -name '*.cpp' -or -name '*.h' \) \
    -not -path "./third_party/*" \
    -print0 | \
    sort -z | \
    xargs -0 -t -n1 clang-format -i -style=file