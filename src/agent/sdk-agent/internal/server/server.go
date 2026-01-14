package server

import (
	routers "github.com/hyperledger/cello/src/agent/sdk-agent/internal/routers"

	"github.com/gin-gonic/gin"
)

type server struct {
}

func NewServer() server {
	return server{}
}

func (s *server) Start() {
	grouter := gin.Default()
	grouter.GET("/channels", routers.GetChannels)
	grouter.PUT("/channels", routers.UpdateChannel)
	grouter.POST("/channels", routers.CreateChannel)
	grouter.POST("/channels/:chain_id/signature", routers.SignConfigTx)
	grouter.Run("localhost:8080")
}
