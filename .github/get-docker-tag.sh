#!/bin/bash
# SPDX-FileCopyrightText: (c) 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

# Calculate hash for docker image tag.
DOCKER_TAG=$( (cat .github/Dockerfile.ci .github/Dockerfile.ird ttexalens/requirements.txt test/test_requirements.txt) | sha256sum | cut -d ' ' -f 1)
echo dt-$DOCKER_TAG
