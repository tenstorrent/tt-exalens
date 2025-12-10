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

CI_IMAGE_NAME=ghcr.io/$REPO/tt-exalens-ci-ubuntu-$UBUNTU_VERSION
IRD_IMAGE_NAME=ghcr.io/$REPO/tt-exalens-ird-ubuntu-$UBUNTU_VERSION

echo "Building images for Ubuntu $UBUNTU_VERSION"

# Build CI image
if docker manifest inspect $CI_IMAGE_NAME:$DOCKER_TAG > /dev/null 2>&1; then
    echo "Image $CI_IMAGE_NAME:$DOCKER_TAG already exists"
else
    echo "Building CI image $CI_IMAGE_NAME:$DOCKER_TAG"
    docker build \
        --progress=plain \
        --build-arg FROM_TAG=$DOCKER_TAG \
        --build-arg UBUNTU_VERSION=$UBUNTU_VERSION \
        -t $CI_IMAGE_NAME:$DOCKER_TAG \
        -f .github/Dockerfile.ci .

    echo "Pushing image $CI_IMAGE_NAME:$DOCKER_TAG"
    docker push $CI_IMAGE_NAME:$DOCKER_TAG
fi

# Build IRD image
if docker manifest inspect $IRD_IMAGE_NAME:$DOCKER_TAG > /dev/null 2>&1; then
    echo "Image $IRD_IMAGE_NAME:$DOCKER_TAG already exists"
else
    echo "Building IRD image $IRD_IMAGE_NAME:$DOCKER_TAG"
    docker build \
        --progress=plain \
        --build-arg FROM_TAG=$DOCKER_TAG \
        --build-arg UBUNTU_VERSION=$UBUNTU_VERSION \
        --build-arg FROM_IMAGE=$CI_IMAGE_NAME \
        -t $IRD_IMAGE_NAME:$DOCKER_TAG \
        -f .github/Dockerfile.ird .

    echo "Pushing image $IRD_IMAGE_NAME:$DOCKER_TAG"
    docker push $IRD_IMAGE_NAME:$DOCKER_TAG
fi

echo "Ubuntu $UBUNTU_VERSION images:"
echo "$CI_IMAGE_NAME:$DOCKER_TAG"
echo "$IRD_IMAGE_NAME:$DOCKER_TAG"
