package test

import (
	"github.com/joho/godotenv"
)

func init() {
	// Try to load .env from parent directory (project root)
	err := godotenv.Load("../.env")
	if err != nil {
		// Fallback: try current directory
		godotenv.Load(".env")
	}
}
