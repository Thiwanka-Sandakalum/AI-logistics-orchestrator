package test

import (
	"context"
	"os"
	"testing"
	"time"

	. "github.com/thiwa/execution-server/tools/shippo"
)

func TestListCarrierAccounts_MissingAPIKey(t *testing.T) {
	os.Unsetenv("SHIPPO_API_KEY")
	_, err := ListCarrierAccounts(context.Background())
	if err == nil || err.Error() != "SHIPPO_API_KEY not set in environment" {
		t.Errorf("expected missing API key error, got: %v", err)
	}
}

func TestListCarrierAccounts_RealAPI(t *testing.T) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		t.Skip("SHIPPO_API_KEY not set; skipping real API test")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	accounts, err := ListCarrierAccounts(ctx)
	if err != nil {
		t.Fatalf("ListCarrierAccounts real API failed: %v", err)
	}
	if len(accounts) == 0 {
		t.Error("Expected at least one carrier account in response")
	}
}

// Add more tests for real API integration with a valid SHIPPO_API_KEY in CI or local .env
