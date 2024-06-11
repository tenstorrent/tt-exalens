#! /bin/bash

sudo apt-get install -y docker.io
wget -qO act.tar.gz https://github.com/nektos/act/releases/latest/download/act_Linux_x86_64.tar.gz
sudo tar xf act.tar.gz -C /usr/local/bin act
rm -rf act.tar.gz