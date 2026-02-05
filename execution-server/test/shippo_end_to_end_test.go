package test

import (
	"context"
	"encoding/json"
	"os"
	"testing"
	"time"

	. "github.com/thiwa/execution-server/tools/shippo"
	// removed invalid import
)

func saveJSON(filename string, v interface{}, t *testing.T) {
	f, err := os.Create(filename)
	if err != nil {
		t.Fatalf("Failed to create %s: %v", filename, err)
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	if err := enc.Encode(v); err != nil {
		t.Fatalf("Failed to encode %s: %v", filename, err)
	}
}

func TestShippoEndToEnd(t *testing.T) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		t.Skip("SHIPPO_API_KEY not set; skipping real API test")
	}

	cfg := LoadShippoTestConfig(t)
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// Step 1: Create address_from and address_to
	addrFromReq := cfg.AddressFrom.ToShippoAddressRequest()
	addrFromResp, err := CreateAddress(ctx, addrFromReq)
	if err != nil {
		t.Fatalf("CreateAddress (from) failed: %v", err)
	}
	saveJSON("address_from.json", addrFromResp, t)

	addrToReq := cfg.AddressTo.ToShippoAddressRequest()
	addrToResp, err := CreateAddress(ctx, addrToReq)
	if err != nil {
		t.Fatalf("CreateAddress (to) failed: %v", err)
	}
	saveJSON("address_to.json", addrToResp, t)

	// Step 2: Create shipment using address object_ids
	shipmentReq := ShippoShipmentRequest{
		AddressFrom: addrFromResp.ObjectID,
		AddressTo:   addrToResp.ObjectID,
		Parcels:     []interface{}{cfg.Parcel},
		Async:       false,
	}
	shipmentResp, err := CreateShipment(ctx, shipmentReq)
	if err != nil {
		t.Fatalf("CreateShipment failed: %v", err)
	}
	saveJSON("shipment.json", shipmentResp, t)

	if len(shipmentResp.Rates) == 0 {
		t.Fatalf("No rates returned from shipment; cannot continue")
	}

	// Step 3: Purchase label using a rate object_id
	labelReq := ShippoLabelPurchaseRequest{
		Rate:  shipmentResp.Rates[0].ObjectID,
		Async: false,
	}
	labelResp, err := PurchaseLabel(ctx, labelReq)
	if err != nil {
		t.Fatalf("PurchaseLabel failed: %v", err)
	}
	saveJSON("label.json", labelResp, t)

	if labelResp.TrackingNumber == "" {
		t.Fatalf("No tracking number in label response")
	}

	// Step 4: Track using tracking number
	trackingResp, err := GetTrackingStatus(ctx, cfg.Carrier, labelResp.TrackingNumber)
	if err != nil {
		t.Fatalf("GetTrackingStatus failed: %v", err)
	}
	saveJSON("tracking.json", trackingResp, t)
}
