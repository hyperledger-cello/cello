package main

import (
	server "github.com/hyperledger/cello/src/agent/sdk-agent/internal/server"
)

func main() {
	s := server.NewServer()
	s.Start()
}
