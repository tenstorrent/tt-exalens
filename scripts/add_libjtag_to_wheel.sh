#!/bin/sh

REPO_DIR="$(dirname "$(realpath "$0")")/.."

if [ ! -d "$REPO_DIR/third_party/jtag-access-library/" ]; then
	echo "Missing third-party/jtag-access-library."
	echo "Use './script/get_jtag_access-library.sh' to get libjtag (only for internal use)."
	exit 1
fi

if [ ! -f "$REPO_DIR/build/lib/libjtag.so" ] || [ ! -f "$REPO_DIR/build/lib/libjlinkarm.so" ]; then
	echo "Missing libjtag.so & libjlinkarm.so"
	echo "Running 'make' will create these files."
	echo "If you got jtag-access-library after first 'make' command, you will need to run 'make clean', and then 'make'."
	exit 1
fi

if ! command -v pip > /dev/null 2>&1; then
	echo "You do not have 'pip' installed."
fi

if ! pip show ttlens > /dev/null 2>&1; then
	echo "You need to install python wheel first."
	echo "Use 'pip install .' in root of the git repository to install wheel."
	exit 1
fi

PYTHON_SITE_PACKAGES=$(pip show ttlens | grep Location | awk '{print $2}')
cp -f "$REPO_DIR/build/lib/libjtag.so" "$PYTHON_SITE_PACKAGES/build/lib/"
cp -f "$REPO_DIR/build/lib/libjlinkarm.so" "$PYTHON_SITE_PACKAGES/build/lib/"

echo "Successfully added libjtag to tt-lens python wheel!"
