FROM ubuntu:22.04

LABEL org.opencontainers.image.source="https://github.com/foundriesio/dm-ak-nano-mcuxpresso-manifest"
LABEL org.opencontainers.image.description="MCUbuild container"

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git \
    cmake \
    make \
    python3 \
    python3-pip \
    gcc-arm-none-eabi

#RUN python3 -m pip install -U pyocd
RUN python3 -m pip install -U west imgtool requests
