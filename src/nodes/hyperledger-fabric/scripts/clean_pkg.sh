# Old version pkgs may pollute the build env
echo "Clean up old version pkgs under $GOPATH"
rm -rf $GOPATH/pkg/linux_amd64/github.com/hyperledger/fabric
rm -rf $GOPATH/pkg/linux_amd64/github.com/hyperledger/fabric-ca
