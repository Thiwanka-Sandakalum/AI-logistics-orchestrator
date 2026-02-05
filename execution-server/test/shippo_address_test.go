package test

import (
	"context"
	"os"
	"testing"
	"time"

	. "github.com/thiwa/execution-server/tools/shippo"
	// removed invalid import
)

func TestCreateAddress_RealAPI(t *testing.T) {
	apiKey := os.Getenv("SHIPPO_API_KEY")

	if apiKey == "" {
		t.Skip("SHIPPO_API_KEY not set; skipping real API test")
	}
	cfg := LoadShippoTestConfig(t)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	resp, err := CreateAddress(ctx, cfg.AddressFrom.ToShippoAddressRequest())
	if err != nil {
		t.Fatalf("CreateAddress real API failed: %v", err)
	}
	if resp.ObjectID == "" {
		t.Error("Expected non-empty ObjectID in response")
	}
}

func TestValidateAddress_MissingAPIKey(t *testing.T) {
	os.Unsetenv("SHIPPO_API_KEY")
	_, err := ValidateAddress(context.Background(), ShippoAddressRequest{})
	if err == nil || err.Error() != "SHIPPO_API_KEY not set in environment" {
		t.Errorf("expected missing API key error, got: %v", err)
	}
}

func TestValidateAddress_RealAPI(t *testing.T) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		t.Skip("SHIPPO_API_KEY not set; skipping real API test")
	}
	cfg := LoadShippoTestConfig(t)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	resp, err := ValidateAddress(ctx, cfg.AddressTo.ToShippoAddressRequest())
	if err != nil {
		t.Fatalf("ValidateAddress real API failed: %v", err)
	}
	if resp.ObjectID == "" {
		t.Error("Expected non-empty ObjectID in response")
	}
}

// Add more tests for real API integration with a valid SHIPPO_API_KEY in CI or local .env
