#!/bin/bash
# This script will read the files from env variables and store them under $FABRIC_CFG_PATH.
# Will run the optional passed command if everything is OK.
#
# It will read the following env variables
# HLF_NODE_MSP: store a base64 encoded zipped "msp" path
# HLF_NODE_TLS: store a base64 encoded zipped "tls" path
# HLF_NODE_BOOTSTRAP_BLOCK: store a base64 encoded zipped bootstrap block
# HLF_NODE_PEER_CONFIG: store a base64 encoded zipped peer configuration file (core.yaml)
# HLF_NODE_ORDERER_CONFIG: store a base64 encoded zipped orderer configuration file (orderer.yaml)


# storeFile will read the variable with given name, and store its data under the given path
# $1: variable-name to decode and then unzip, e.g., HLF_NODE_MSP
# $2: path to put the result under, e.g., $cfg_path
function storeFile {
    name="$1"
    path="$2"
    value="${!name}" # get the data that stored in the env variable
    if [[ -z "${value}" || -z "${path}" ]]; then
        echo "Parameter ${name} or ${path} is empty or undefined"
        return
    else
	echo "Store data in ${name} to ${path}"
        echo "${value}" | base64 -d > /tmp/1.zip
        unzip -o -d ${path} /tmp/1.zip
        rm /tmp/1.zip
        ls ${path}
    fi
}


# The optional cmd to run after storing every file
cmd=$1

# The path to store the files
cfg_path=${FABRIC_CFG_PATH:-/etc/hyperledger/fabric}

# Clean the potential existing msp and tls paths first
if [ ! -z "${HLF_NODE_MSP}" ] && [ -d ${cfg_path}/msp ]; then
    mv ${cfg_path}/msp ${cfg_path}/msp.bak
fi
if [ ! -z "${HLF_NODE_TLS}" ] && [ -d ${cfg_path}/tls ]; then
    mv ${cfg_path}/tls ${cfg_path}/tls.bak
fi

# Read each file from env and store under the ${cfg_path}
for name in HLF_NODE_MSP \
	HLF_NODE_TLS \
	HLF_NODE_BOOTSTRAP_BLOCK \
	HLF_NODE_PEER_CONFIG \
	HLF_NODE_ORDERER_CONFIG
do
    if [ -z "{$name-}"]; then
        storeFile $name $cfg_path
    else
        echo "$name is unset"
done


# Run optional cmd
if [[ ! -z "${cmd}" ]]; then
    echo "Run ${cmd}"
    ${cmd}
fi