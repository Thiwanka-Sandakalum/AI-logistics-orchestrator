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

const shippoAPIBase = "https://api.goshippo.com"

// ShippoAddressRequest represents the request to create or validate an address.
type ShippoAddressRequest struct {
	Name    string `json:"name,omitempty"`
	Street1 string `json:"street1"`
	Street2 string `json:"street2,omitempty"`
	City    string `json:"city"`
	State   string `json:"state,omitempty"`
	Zip     string `json:"zip"`
	Country string `json:"country"`
	Phone   string `json:"phone,omitempty"`
	Email   string `json:"email,omitempty"`
}

// ShippoAddressResponse represents the response from Shippo for address creation/validation.
type ShippoAddressResponse struct {
	ObjectID          string      `json:"object_id"`
	ValidationResults interface{} `json:"validation_results,omitempty"`
	// ... add more fields as needed
}

// CreateAddress creates a new address in Shippo.
func CreateAddress(ctx context.Context, req ShippoAddressRequest) (*ShippoAddressResponse, error) {
	return callShippoAddressAPI(ctx, req, false)
}

// ValidateAddress creates and validates an address in Shippo.
func ValidateAddress(ctx context.Context, req ShippoAddressRequest) (*ShippoAddressResponse, error) {
	return callShippoAddressAPI(ctx, req, true)
}

func callShippoAddressAPI(ctx context.Context, req ShippoAddressRequest, validate bool) (*ShippoAddressResponse, error) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("SHIPPO_API_KEY not set in environment")
	}
	url := shippoAPIBase + "/addresses"
	if validate {
		url += "/?validate=true"
	}
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
	var addressResp ShippoAddressResponse
	if err := json.Unmarshal(respBody, &addressResp); err != nil {
		return nil, err
	}
	return &addressResp, nil
}
