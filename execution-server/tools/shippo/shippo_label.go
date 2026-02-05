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

// ShippoLabelPurchaseRequest represents the request to purchase a label (transaction).
type ShippoLabelPurchaseRequest struct {
	Rate           string `json:"rate"` // Shippo rate object_id
	LabelFileType  string `json:"label_file_type,omitempty"`
	Async          bool   `json:"async"`
	IdempotencyKey string `json:"idempotency_key,omitempty"`
}

// ShippoLabelPurchaseResponse represents the response from Shippo for label purchase.
type ShippoLabelPurchaseResponse struct {
	ObjectID       string      `json:"object_id"`
	Status         string      `json:"status"`
	LabelURL       string      `json:"label_url"`
	TrackingNumber string      `json:"tracking_number"`
	TrackingStatus interface{} `json:"tracking_status"`
	// ... add more fields as needed
}

// PurchaseLabel purchases a shipping label from Shippo.
func PurchaseLabel(ctx context.Context, req ShippoLabelPurchaseRequest) (*ShippoLabelPurchaseResponse, error) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("SHIPPO_API_KEY not set in environment")
	}
	url := shippoAPIBase + "/transactions"
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
	var labelResp ShippoLabelPurchaseResponse
	if err := json.Unmarshal(respBody, &labelResp); err != nil {
		return nil, err
	}
	return &labelResp, nil
}
