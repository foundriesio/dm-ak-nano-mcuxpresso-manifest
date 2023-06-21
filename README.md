# Build project

    west init https://github.com/foundriesio/dm-ak-nano-mcuxpresso-manifest/ 
    west update
    export ARMGCC_DIR: "/usr/"
    cd ../foundriesio/dm-ak-nano-mcuxpresso/armgcc
    ./build_flexspi_nor_release.sh

# Publish MCUbuild container

Container is built and published
when new release is created in this repository.
The release has to be marked as `latest release`
to allow for proper tagging of the container image.
