# Install run dependencies
apt-get update
apt-get install -y \
    software-properties-common \
    build-essential \
    git \
    sudo \
    wget \
    curl \
    jq

# Python environment dependencies
apt-get install -y \
    libssl-dev \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    python3-wheel

# Build tools
apt-get install -y \
    ninja-build \
    cmake
apt-get clean

# Remove externally-managed marker (Ubuntu 24.04+) and upgrade to latest pip
rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED
pip install --upgrade pip --ignore-installed

# Install Python dependencies
uv pip install --no-cache-dir --extra-index-url https://test.pypi.org/simple/ -r requirements.txt
uv pip install --no-cache-dir -r dev-requirements.txt
uv pip install --no-cache-dir -r test_requirements.txt
uv pip install --no-cache-dir wheel build setuptools
uv pip cache purge
