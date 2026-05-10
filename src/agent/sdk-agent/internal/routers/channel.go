package routers

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func GetChannels(c *gin.Context) {
	id := c.Query("channel_id")
	if id == "" {
		channels := []string{"Channel 1", "Channel 2", "Channel 3"}
		c.JSON(http.StatusOK, gin.H{
			"channels": channels,
		})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"message": "Channel ID: " + id,
	})
}

func CreateChannel(c *gin.Context) {
	c.IndentedJSON(http.StatusOK, nil)
}

func UpdateChannel(c *gin.Context) {
	c.IndentedJSON(http.StatusOK, nil)
}

func SignConfigTx(c *gin.Context) {
	c.IndentedJSON(http.StatusOK, nil)
}
