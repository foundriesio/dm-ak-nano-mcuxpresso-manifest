FROM golang:1.19.0-alpine3.15 AS build

RUN apk add --update --no-cache \
    git \
    g++ \
    make

RUN mkdir /home/fioctl && git clone -b mcu-api https://github.com/foundriesio/fioctl /home/fioctl
RUN cd /home/fioctl && make fioctl-linux-amd64

FROM ubuntu:22.04

LABEL org.opencontainers.image.source="https://github.com/foundriesio/dm-ak-nano-mcuxpresso-manifest"
LABEL org.opencontainers.image.description="MCUbuild container"

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git \
    cmake \
    make \
    python3 \
    python3-pip \
    gcc-arm-none-eabi \
	unzip

RUN python3 -m pip install -U west imgtool requests
COPY root-rsa-2048.pem /home
COPY --from=build /home/fioctl/bin/fioctl-linux-amd64 /usr/local/bin/fioctl
