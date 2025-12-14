#!/bin/bash 

echo "Building fabric orderer"
cd $FABRIC_ROOT/orderer \
    && CGO_CFLAGS=" " go install -ldflags "$LD_FLAGS -linkmode external -extldflags '-static -lpthread'" \
    && go clean
