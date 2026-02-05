package test

import (
	"context"
	"os"
	"testing"
	"time"

	. "github.com/thiwa/execution-server/tools/shippo"
	// removed invalid import
)

func TestPurchaseLabel_MissingAPIKey(t *testing.T) {
	os.Unsetenv("SHIPPO_API_KEY")
	_, err := PurchaseLabel(context.Background(), ShippoLabelPurchaseRequest{})
	if err == nil || err.Error() != "SHIPPO_API_KEY not set in environment" {
		t.Errorf("expected missing API key error, got: %v", err)
	}
}

func TestPurchaseLabel_RealAPI(t *testing.T) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		t.Skip("SHIPPO_API_KEY not set; skipping real API test")
	}
	cfg := LoadShippoTestConfig(t)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	// Create sender and recipient addresses
	fromAddr, err := CreateAddress(ctx, cfg.AddressFrom.ToShippoAddressRequest())
	if err != nil {
		t.Fatalf("CreateAddress (from) failed: %v", err)
	}
	toAddr, err := CreateAddress(ctx, cfg.AddressTo.ToShippoAddressRequest())
	if err != nil {
		t.Fatalf("CreateAddress (to) failed: %v", err)
	}
	shipment := ShippoShipmentRequest{
		AddressFrom: fromAddr.ObjectID,
		AddressTo:   toAddr.ObjectID,
		Parcels:     []interface{}{cfg.Parcel},
		Async:       false,
	}
	shipmentResp, err := CreateShipment(ctx, shipment)
	if err != nil {
		t.Fatalf("CreateShipment for label failed: %v", err)
	}
	if len(shipmentResp.Rates) == 0 {
		t.Fatalf("No rates returned from shipment; cannot purchase label")
	}
	req := ShippoLabelPurchaseRequest{
		Rate:  shipmentResp.Rates[0].ObjectID,
		Async: false,
	}
	resp, err := PurchaseLabel(ctx, req)
	if err != nil {
		t.Fatalf("PurchaseLabel real API failed: %v", err)
	}
	if resp.ObjectID == "" {
		t.Error("Expected non-empty ObjectID in response")
	}
}

// Add more tests for real API integration with a valid SHIPPO_API_KEY in CI or local .env
