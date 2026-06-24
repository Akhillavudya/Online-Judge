# The sandbox image: a minimal Linux box that can compile C++ and run Python.
#
# This image is NOT the backend. It is the throwaway environment that untrusted
# user code is compiled and executed inside. The judge starts one short-lived
# container from this image per compile and per test-case run, then throws it
# away (`docker run --rm`). The image therefore needs only the compilers/runtimes
# and the `timeout` tool (from coreutils, already in the base image) — nothing
# else, to keep the attack surface small.
#
# Build it once on the deployment host:
#     docker build -t online-judge-sandbox backend/sandbox
#
# (The tag must match SANDBOX_IMAGE in the backend config.)

FROM debian:bookworm-slim

# g++  -> compile + run C++
# python3 -> run Python
# `timeout` (used to bound each run) lives in coreutils, which the base ships.
# --no-install-recommends + cleaning the apt lists keeps the image lean.
RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ python3 \
    && rm -rf /var/lib/apt/lists/*

# Every container runs with /work as its working directory. The judge bind-mounts
# a per-submission host folder here (read-write while compiling, read-only while
# running). We do NOT copy any user code into the image itself.
WORKDIR /work

# The locked-down *run* containers are started with `--user nobody`; `nobody`
# already exists in the base image, so no extra setup is needed here.
