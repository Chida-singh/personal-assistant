package proxy

import (
	"log"
	"net/http/httputil"
	"net/url"

	"github.com/gin-gonic/gin"
)

// Reverse creates a proxy handler for a target URL.
func Reverse(target string) gin.HandlerFunc {
	targetUrl, err := url.Parse(target)
	if err != nil {
		log.Fatalf("Invalid target URL %s: %v", target, err)
	}

	proxy := httputil.NewSingleHostReverseProxy(targetUrl)

	return func(c *gin.Context) {
		// Update the headers to allow for routing
		c.Request.URL.Host = targetUrl.Host
		c.Request.URL.Scheme = targetUrl.Scheme
		c.Request.Header.Set("X-Forwarded-Host", c.Request.Header.Get("Host"))
		c.Request.Host = targetUrl.Host

		// Pass to the proxy
		proxy.ServeHTTP(c.Writer, c.Request)
	}
}
