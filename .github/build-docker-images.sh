#!/bin/bash
# SPDX-FileCopyrightText: (c) 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

set -e

REPO=tenstorrent/tt-exalens

# Compute the hash of the Dockerfile
DOCKER_TAG=$(./.github/get-docker-tag.sh)
echo "Docker tag: $DOCKER_TAG"

build_and_push() {
    local ubuntu_version=$1 # Ubuntu version (22.04 or 24.04)

    local ci_image_name=ghcr.io/$REPO/tt-exalens-ci-ubuntu-$ubuntu_version
    local ird_image_name=ghcr.io/$REPO/tt-exalens-ird-ubuntu-$ubuntu_version

    echo "Building images for Ubuntu $ubuntu_version"

    # Build CI image
    if docker manifest inspect $ci_image_name:$DOCKER_TAG > /dev/null 2>&1; then
        echo "Image $ci_image_name:$DOCKER_TAG already exists"
    else
        echo "Building CI image $ci_image_name:$DOCKER_TAG"
        docker build \
            --progress=plain \
            --build-arg FROM_TAG=$DOCKER_TAG \
            --build-arg UBUNTU_VERSION=$ubuntu_version \
            -t $ci_image_name:$DOCKER_TAG \
            -f .github/Dockerfile.ci .

        echo "Pushing image $ci_image_name:$DOCKER_TAG"
        docker push $ci_image_name:$DOCKER_TAG
    fi

    # Build IRD image
    if docker manifest inspect $ird_image_name:$DOCKER_TAG > /dev/null 2>&1; then
        echo "Image $ird_image_name:$DOCKER_TAG already exists"
    else
        echo "Building IRD image $ird_image_name:$DOCKER_TAG"
        docker build \
            --progress=plain \
            --build-arg FROM_TAG=$DOCKER_TAG \
            --build-arg UBUNTU_VERSION=$ubuntu_version \
            --build-arg FROM_IMAGE=$ci_image_name \
            -t $ird_image_name:$DOCKER_TAG \
            -f .github/Dockerfile.ird .

        echo "Pushing image $ird_image_name:$DOCKER_TAG"
        docker push $ird_image_name:$DOCKER_TAG
    fi

    echo "Ubuntu $ubuntu_version images:"
    echo "  CI: $ci_image_name:$DOCKER_TAG"
    echo "  IRD: $ird_image_name:$DOCKER_TAG"
}

# Build for Ubuntu 22.04 and 24.04
build_and_push "22.04"
build_and_push "24.04"

echo ""
echo "All images built and pushed successfully"
