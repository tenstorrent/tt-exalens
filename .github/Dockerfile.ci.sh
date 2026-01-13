# Install run dependencies
apt-get update
apt-get install -y \
    git

# Python environment dependencies
apt-get install -y \
    python3 \
    python3-pip

# Build tools
apt-get install -y \
    ninja-build \
    cmake
apt-get clean

# Remove externally-managed marker (Ubuntu 24.04+) and upgrade to latest pip
rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED
pip install --upgrade pip --ignore-installed

# Install Python dependencies
uv pip install --no-cache-dir --system --index-strategy unsafe-best-match --extra-index-url https://test.pypi.org/simple/ -r requirements.txt
uv pip install --no-cache-dir --system -r dev-requirements.txt
uv pip install --no-cache-dir --system -r test_requirements.txt
uv pip install --no-cache-dir --system wheel build setuptools

# Clean up pip cache
pip cache purge
