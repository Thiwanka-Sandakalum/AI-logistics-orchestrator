// MCP Server entrypoint

package main

import (
	"log"
	"net/http"

	"github.com/thiwa/execution-server/internal"
)

func main() {
	// Production-ready logging
	log.Println("Starting Execution Server...")

	// Initialize server
	srv := internal.NewServer()

	// Register tools (Shippo only)

	// Address validation tool
	srv.RegisterTool("address.validate", nil) // No state needed, handled in server

	// Tracking simulation tool
	srv.RegisterTool("shipment.track", nil) // No state needed, handled in server

	// Start HTTP server
	log.Println("Listening on :8080")
	if err := http.ListenAndServe(":8080", srv); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
