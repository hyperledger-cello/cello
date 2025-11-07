#!/bin/bash

echo "Building configtxgen"
CGO_CFLAGS=" " go install -tags "nopkcs11" -ldflags "$LD_FLAGS" github.com/hyperledger/fabric/common/configtx/tool/configtxgen

echo "Building cryptogen"
CGO_CFLAGS=" " go install -tags "" -ldflags "$LD_FLAGS" github.com/hyperledger/fabric/common/tools/cryptogen

echo "Building configtxlator"
CGO_CFLAGS=" " go install -tags "" -ldflags "$LD_FLAGS" github.com/hyperledger/fabric/common/tools/configtxlator


echo "Install configtxgen, cryptogen and configtxlator"
cd $FABRIC_ROOT/ \
    && CGO_CFLAGS=" " go install -tags "nopkcs11" -ldflags "-X github.com/hyperledger/fabric/common/tools/configtxgen/metadata.Version=${PROJECT_VERSION}" github.com/hyperledger/fabric/common/tools/configtxgen \
    && CGO_CFLAGS=" " go install -tags "" -ldflags "-X github.com/hyperledger/fabric/common/tools/cryptogen/metadata.Version=${PROJECT_VERSION}" github.com/hyperledger/fabric/common/tools/cryptogen \
    && CGO_CFLAGS=" " go install -tags "" -ldflags "-X github.com/hyperledger/fabric/common/tools/configtxlator/metadata.Version=${PROJECT_VERSION}" github.com/hyperledger/fabric/common/tools/configtxlator

echo "Install block-listener"
RUN cd $FABRIC_ROOT/examples/events/block-listener \
        && go install
