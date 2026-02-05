package test

import (
	"context"

	. "github.com/thiwa/execution-server/tools/shippo"

	// removed invalid import
	"os"
	"testing"
	"time"
)

func TestCreateShipment_MissingAPIKey(t *testing.T) {
	os.Unsetenv("SHIPPO_API_KEY")
	_, err := CreateShipment(context.Background(), ShippoShipmentRequest{})
	if err == nil || err.Error() != "SHIPPO_API_KEY not set in environment" {
		t.Errorf("expected missing API key error, got: %v", err)
	}
}

func TestCreateShipment_RealAPI(t *testing.T) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		t.Skip("SHIPPO_API_KEY not set; skipping real API test")
	}
	cfg := LoadShippoTestConfig(t)
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	// Create sender address
	fromAddr, err := CreateAddress(ctx, cfg.AddressFrom.ToShippoAddressRequest())
	if err != nil {
		t.Fatalf("CreateAddress (from) failed: %v", err)
	}
	// Create recipient address
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
	resp, err := CreateShipment(ctx, shipment)
	if err != nil {
		t.Fatalf("CreateShipment real API failed: %v", err)
	}
	if resp.ObjectID == "" {
		t.Error("Expected non-empty ObjectID in response")
	}
	if len(resp.Rates) == 0 {
		t.Error("Expected at least one rate in response")
	}
}

func TestGetShipmentRates_MissingAPIKey(t *testing.T) {
	os.Unsetenv("SHIPPO_API_KEY")
	_, err := GetShipmentRates(context.Background(), "fake-id")
	if err == nil || err.Error() != "SHIPPO_API_KEY not set in environment" {
		t.Errorf("expected missing API key error, got: %v", err)
	}
}

func TestGetShipmentRates_RealAPI(t *testing.T) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		t.Skip("SHIPPO_API_KEY not set; skipping real API test")
	}
	cfg := LoadShippoTestConfig(t)
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
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
		t.Fatalf("CreateShipment for rates failed: %v", err)
	}
	rates, err := GetShipmentRates(ctx, shipmentResp.ObjectID)
	if err != nil {
		t.Fatalf("GetShipmentRates real API failed: %v", err)
	}
	if len(rates) == 0 {
		t.Error("Expected at least one rate in response")
	}
}

// Add more tests for real API integration with a valid SHIPPO_API_KEY in CI or local .env
