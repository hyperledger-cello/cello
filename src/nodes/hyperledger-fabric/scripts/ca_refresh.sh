#!/bin/bash 

echo "Restarting fabric-ca"
killall fabric-ca-server
go install -ldflags " -linkmode external -extldflags '-static -lpthread'" github.com/hyperledger/fabric-ca/cmd/...

fabric-ca-server start \
    --ca.certfile $FABRIC_CA_HOME/ca-cert.pem \
    --ca.keyfile $FABRIC_CA_HOME/ca-key.pem \
    -c $FABRIC_CA_HOME/fabric-ca-server-config.yaml \
    -b admin:adminpw \
    -n test_ca
