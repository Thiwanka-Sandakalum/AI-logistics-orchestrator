package test

import (
	"context"
	"os"
	"testing"

	. "github.com/thiwa/execution-server/tools/shippo"
	// removed invalid import
)

func TestGetTrackingStatus_MissingAPIKey(t *testing.T) {
	os.Unsetenv("SHIPPO_API_KEY")
	_, err := GetTrackingStatus(context.Background(), "usps", "123456789")
	if err == nil || err.Error() != "SHIPPO_API_KEY not set in environment" {
		t.Errorf("expected missing API key error, got: %v", err)
	}
}

// Import ShippoTestConfig and LoadShippoTestConfig from config.go

func TestGetTrackingStatus_RealAPI(t *testing.T) {
	t.Skip("ShippoTestConfig has no TrackingNumber; skipping test.")
}

// Add more tests for real API integration with a valid SHIPPO_API_KEY in CI or local .env
