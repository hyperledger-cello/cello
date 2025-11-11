 package main

import (
    "bytes"
    "context"
    "crypto/x509"
    "encoding/json"
    "fmt"
    "os"
    "path"
    "path/filepath"
    "strings"
    "time"

    "github.com/hyperledger/fabric-gateway/pkg/client"
    "github.com/hyperledger/fabric-gateway/pkg/hash"
    "github.com/hyperledger/fabric-gateway/pkg/identity"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials"
)

var (
    mspID        string
    certPath     string
    keyPath      string
    tlsCertPath  string
    peerEndpoint string
    gatewayPeer  string
)

func main() {
    /* Check and get the environment variables */
    env := checkEnvVars()
    mspID = env["CORE_PEER_LOCALMSPID"]
    mspConfigPath := env["CORE_PEER_MSPCONFIGPATH"]
    address := env["CORE_PEER_ADDRESS"]
    chaincodeName := env["CHAINCODE_NAME"]
    channelName := env["CHANNEL_NAME"]

    certPath = filepath.Join(mspConfigPath, "signcerts")
    keyPath = filepath.Join(mspConfigPath, "keystore")
    tlsCertPath = filepath.Join(mspConfigPath, "../tls/ca.crt")

    peerEndpoint = "dns:///" + address
    gatewayPeer = strings.Split(address, ":")[0]

    /* Check if the action and function are given */
    if len(os.Args) < 3 {
        panic(fmt.Printf("Error: expected at lease 2 arguments but only %s is given.", len(os.Args) - 1))
    }

    /* submit/evaluate */
    action := strings.ToLower(os.Args[1])
    /* chaincode function name */
    function := os.Args[2]
    /* other arguments */
    args := os.Args[3:]

    // create a Gateway client
    clientConnection := newGrpcConnection()
    defer clientConnection.Close()

    id := newIdentity()
    sign := newSign()

    gw, err := client.Connect(
        id,
        client.WithSign(sign),
        client.WithHash(hash.SHA256),
        client.WithClientConnection(clientConnection),
        client.WithEvaluateTimeout(5*time.Second),
        client.WithEndorseTimeout(15*time.Second),
        client.WithSubmitTimeout(5*time.Second),
        client.WithCommitStatusTimeout(1*time.Minute),
    )
    if err != nil {
        panic(err)
    }
    defer gw.Close()

    // get chaincode
    network := gw.GetNetwork(channelName)
    contract := network.GetContract(chaincodeName)

    // execute
    switch action {
        case "submit":
            result, err := contract.SubmitTransaction(function, args...)
            if err != nil {
                panic(fmt.Errorf("Error: %w", err))
            }
            printJSON(result)

        case "evaluate":
            result, err := contract.EvaluateTransaction(function, args...)
            if err != nil {
                panic(fmt.Errorf("Error: %w", err))
            }
            printJSON(result)
        default:
            panic(fmt.Printf("Error: invalid action %s (should be 'submit' or 'evaluate').", action))
    }
}

func checkEnvVars() map[string]string {
    requiredVars := []string{
        "CORE_PEER_LOCALMSPID",
        "CORE_PEER_MSPCONFIGPATH",
        "CORE_PEER_ADDRESS",
        "CHAINCODE_NAME",
        "CHANNEL_NAME",
    }

    missing := []string{}
    values := make(map[string]string)

    for _, key := range requiredVars {
        val := os.Getenv(key)
        if val == "" {
            missing = append(missing, key)
        } else {
            values[key] = val
        }
    }

    if len(missing) > 0 {
        if len(missing) == 1 {
            panic(fmt.Sprintf("Missing an environment variable: %s", missing[0]))
        }
        panic(fmt.Sprintf("Missing environment variables: %s", strings.Join(missing, ", ")))
    }

    return values
}

func newGrpcConnection() *grpc.ClientConn {
    certificatePEM, err := os.ReadFile(tlsCertPath)
    if err != nil {
        panic(fmt.Errorf("failed to read TLS certificate file: %w", err))
    }

    certificate, err := identity.CertificateFromPEM(certificatePEM)
    if err != nil {
        panic(err)
    }

    certPool := x509.NewCertPool()
    certPool.AddCert(certificate)
    transportCredentials := credentials.NewClientTLSFromCert(certPool, gatewayPeer)

    connection, err := grpc.NewClient(peerEndpoint, grpc.WithTransportCredentials(transportCredentials))
    if err != nil {
        panic(fmt.Errorf("failed to create gRPC connection: %w", err))
    }

    return connection
}

func newIdentity() *identity.X509Identity {
    certificatePEM, err := readFirstFile(certPath)
    if err != nil {
        panic(fmt.Errorf("failed to read certificate file: %w", err))
    }

    certificate, err := identity.CertificateFromPEM(certificatePEM)
    if err != nil {
        panic(err)
    }

    id, err := identity.NewX509Identity(mspID, certificate)
    if err != nil {
        panic(err)
    }

    return id
}

func newSign() identity.Sign {
    privateKeyPEM, err := readFirstFile(keyPath)
    if err != nil {
        panic(fmt.Errorf("failed to read private key file: %w", err))
    }

    privateKey, err := identity.PrivateKeyFromPEM(privateKeyPEM)
    if err != nil {
        panic(err)
    }

    sign, err := identity.NewPrivateKeySign(privateKey)
    if err != nil {
        panic(err)
    }

    return sign
}

func readFirstFile(dirPath string) ([]byte, error) {
    dir, err := os.Open(dirPath)
    if err != nil {
        return nil, err
    }
    fileNames, err := dir.Readdirnames(1)
    if err != nil {
        return nil, err
    }
    return os.ReadFile(path.Join(dirPath, fileNames[0]))
}

func printJSON(data []byte) {
    if len(data) == 0 {
        return
    }
    var pretty bytes.Buffer
    if err := json.Indent(&pretty, data, "", "  "); err != nil {
        /* returned data is not in json */
        fmt.Println(string(data))
        return
    }
    fmt.Println(string(pretty.Bytes()))
}
