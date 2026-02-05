package tools

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

// ShippoShipmentRequest represents the request to create a shipment.
type ShippoShipmentRequest struct {
	AddressFrom     string        `json:"address_from"` // Shippo address object_id or full address object
	AddressTo       string        `json:"address_to"`   // Shippo address object_id or full address object
	Parcels         []interface{} `json:"parcels"`      // Shippo parcel object(s) or IDs
	CarrierAccounts []string      `json:"carrier_accounts,omitempty"`
	Async           bool          `json:"async"`
	IdempotencyKey  string        `json:"idempotency_key,omitempty"`
}

// ShippoShipmentResponse represents the response from Shippo for shipment creation.
type ShippoShipmentResponse struct {
	ObjectID string       `json:"object_id"`
	Rates    []ShippoRate `json:"rates"`
	Status   string       `json:"status"`
}

type ShippoRate struct {
	ObjectID      string `json:"object_id"`
	Amount        string `json:"amount"`
	Currency      string `json:"currency"`
	Provider      string `json:"provider"`
	EstimatedDays int    `json:"estimated_days"`
	ServiceLevel  string `json:"servicelevel_token"`
}

// CreateShipment creates a new shipment in Shippo.
func CreateShipment(ctx context.Context, req ShippoShipmentRequest) (*ShippoShipmentResponse, error) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("SHIPPO_API_KEY not set in environment")
	}
	url := shippoAPIBase + "/shipments"
	body, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}
	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Authorization", "ShippoToken "+apiKey)
	httpReq.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	respBody, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 300 {
		return nil, fmt.Errorf("Shippo API error: %s", string(respBody))
	}
	var shipmentResp ShippoShipmentResponse
	if err := json.Unmarshal(respBody, &shipmentResp); err != nil {
		return nil, err
	}
	return &shipmentResp, nil
}

// GetShipmentRates fetches rates for a shipment by ID.
func GetShipmentRates(ctx context.Context, shipmentID string) ([]ShippoRate, error) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("SHIPPO_API_KEY not set in environment")
	}
	url := fmt.Sprintf("%s/shipments/%s/rates", shippoAPIBase, shipmentID)
	httpReq, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Authorization", "ShippoToken "+apiKey)
	httpReq.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	respBody, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 300 {
		return nil, fmt.Errorf("Shippo API error: %s", string(respBody))
	}
	var ratesResp struct {
		Results []ShippoRate `json:"results"`
	}
	if err := json.Unmarshal(respBody, &ratesResp); err != nil {
		return nil, err
	}
	return ratesResp.Results, nil
}
