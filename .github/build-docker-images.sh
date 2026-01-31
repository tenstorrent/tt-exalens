#!/bin/bash
# SPDX-FileCopyrightText: (c) 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

set -e

REPO=tenstorrent/tt-exalens

# Accept Ubuntu version as argument
if [ -z "$1" ]; then
    echo "Usage: $0 <ubuntu_version>"
    echo "Example: $0 22.04"
    exit 1
fi

UBUNTU_VERSION=$1

# Compute the hash of the Dockerfile
DOCKER_TAG=$(./.github/get-docker-tag.sh)
echo "Docker tag: $DOCKER_TAG"

echo "Building images for Ubuntu $UBUNTU_VERSION"

# Function to build and push a Docker image
build_and_push() {
    local image_name=$1 # Resulting image name
    local dockerfile=$2 # Dockerfile to build
    local from_image=$4 # Base image to build from

    if docker manifest inspect $image_name:$DOCKER_TAG > /dev/null; then
        echo "Image $image_name:$DOCKER_TAG already exists"
    else
        echo "Building image $image_name:$DOCKER_TAG"
        docker build \
            --progress=plain \
            --build-arg FROM_TAG=$DOCKER_TAG \
            --build-arg UBUNTU_VERSION=$UBUNTU_VERSION \
            ${from_image:+--build-arg FROM_IMAGE=$from_image} \
            -t $image_name:$DOCKER_TAG \
            -f $dockerfile .

        echo "Pushing image $image_name:$DOCKER_TAG"
        docker push $image_name:$DOCKER_TAG
    fi
}

CI_IMAGE_NAME=ghcr.io/$REPO/tt-exalens-ci-ubuntu-$UBUNTU_VERSION

build_and_push $CI_IMAGE_NAME .github/Dockerfile.ci

echo "Ubuntu $UBUNTU_VERSION images:"
echo "$CI_IMAGE_NAME:$DOCKER_TAG"
