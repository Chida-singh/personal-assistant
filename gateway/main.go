package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"

	"personal-assistant/gateway/auth"
	"personal-assistant/gateway/proxy"
)

// Simple configuration for service URLs
var (
	jwtSecret          = os.Getenv("JWT_SECRET")
	todoServiceURL     = os.Getenv("TODO_SERVICE_URL")
	financeServiceURL  = os.Getenv("FINANCE_SERVICE_URL")
	calendarServiceURL = os.Getenv("CALENDAR_SERVICE_URL")
	vaultServiceURL    = os.Getenv("VAULT_SERVICE_URL")
	llmWorkerURL       = os.Getenv("LLM_WORKER_URL")
	port               = os.Getenv("PORT")
)

func init() {
	if port == "" {
		port = "8000"
	}
	if jwtSecret == "" {
		jwtSecret = "super_secret_key" // Fallback for dev
	}
}

func main() {
	router := gin.Default()

	// CORS Middleware
	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Origin, Authorization, Content-Type")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}
		c.Next()
	})

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "gateway is healthy",
			"time":   time.Now().Format(time.RFC3339),
		})
	})

	// Login Endpoint
	router.POST("/api/auth/login", func(c *gin.Context) {
		token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
			"user_id": "admin",
			"exp":     time.Now().Add(time.Hour * 24).Unix(),
		})

		tokenString, err := token.SignedString([]byte(jwtSecret))
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"token": tokenString,
		})
	})

	// API Routes Group (Protected)
	api := router.Group("/api")
	api.Use(auth.Middleware(jwtSecret))
	{
		// Todo, Notes, and Habits proxying
		if todoServiceURL != "" {
			api.Any("/todos", proxy.Reverse(todoServiceURL))
			api.Any("/todos/*filepath", proxy.Reverse(todoServiceURL))
			api.Any("/notes", proxy.Reverse(todoServiceURL))
			api.Any("/notes/*filepath", proxy.Reverse(todoServiceURL))
			api.Any("/habits", proxy.Reverse(todoServiceURL))
			api.Any("/habits/*filepath", proxy.Reverse(todoServiceURL))
		} else {
			log.Println("Warning: TODO_SERVICE_URL not set")
		}

		// Finance Service proxying
		if financeServiceURL != "" {
			api.Any("/finance", proxy.Reverse(financeServiceURL))
			api.Any("/finance/*filepath", proxy.Reverse(financeServiceURL))
		} else {
			log.Println("Warning: FINANCE_SERVICE_URL not set")
		}

		// Calendar Service proxying
		if calendarServiceURL != "" {
			api.Any("/calendar", proxy.Reverse(calendarServiceURL))
			api.Any("/calendar/*filepath", proxy.Reverse(calendarServiceURL))
		} else {
			log.Println("Warning: CALENDAR_SERVICE_URL not set")
		}

		// Vault Service proxying
		if vaultServiceURL != "" {
			api.Any("/vault", proxy.Reverse(vaultServiceURL))
			api.Any("/vault/*filepath", proxy.Reverse(vaultServiceURL))
		} else {
			log.Println("Warning: VAULT_SERVICE_URL not set")
		}

		// LLM Worker proxying
		if llmWorkerURL != "" {
			api.Any("/chat", proxy.Reverse(llmWorkerURL))
			api.Any("/chat/*filepath", proxy.Reverse(llmWorkerURL))
		} else {
			log.Println("Warning: LLM_WORKER_URL not set")
		}
	}

	addr := fmt.Sprintf(":%s", port)
	log.Printf("API Gateway listening on %s", addr)
	if err := router.Run(addr); err != nil {
		log.Fatalf("Failed to start gateway: %v", err)
	}
}
