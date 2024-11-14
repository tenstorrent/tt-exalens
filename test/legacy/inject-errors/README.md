This directory contains means to inject errors in various places for testing purposes.

Apply a patch by running the following commands from the **root of the git repo**:
```
git apply ttlens/test/inject-errors/sfpu_reciprocal-infinite-spin-grayskull.patch
```
Revert with:
```
git apply -R ttlens/test/inject-errors/sfpu_reciprocal-infinite-spin-grayskull.patch
```
