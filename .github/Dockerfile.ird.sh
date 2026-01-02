# Create directories for infra
mkdir -p ${TT_EXALENS_INFRA_DIR}

# Install dependencies
apt-get update
apt-get install -y \
    docker.io \
    gh \
    git-lfs \
    libgmp-dev \
    libmpfr-dev \
    rsync \
    ssh \
    vim \
    nano \
    htop

# Install CMake 3.27 from official releases
wget https://github.com/Kitware/CMake/releases/download/v3.27.9/cmake-3.27.9-linux-x86_64.sh
chmod +x cmake-3.27.9-linux-x86_64.sh
./cmake-3.27.9-linux-x86_64.sh --skip-license --prefix=/usr/local
rm cmake-3.27.9-linux-x86_64.sh

# Install clang 17
wget https://apt.llvm.org/llvm.sh
chmod u+x llvm.sh
./llvm.sh 17
apt install -y libc++-17-dev libc++abi-17-dev
ln -s /usr/bin/clang-17 /usr/bin/clang
ln -s /usr/bin/clang++-17 /usr/bin/clang++

# Install clang-format
apt install -y clang-format-17
ln -s /usr/bin/clang-format-17 /usr/bin/clang-format

# Install tt-smi, tt-flash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
pip install --ignore-installed git+https://github.com/tenstorrent/tt-smi.git
pip install --ignore-installed git+https://github.com/tenstorrent/tt-flash.git
