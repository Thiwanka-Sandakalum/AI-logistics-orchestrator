package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

// ShippoTrackResponse represents the response from Shippo for tracking a package.
type ShippoTrackResponse struct {
	TrackingNumber string      `json:"tracking_number"`
	Carrier        string      `json:"carrier"`
	TrackingStatus interface{} `json:"tracking_status"`
	// ... add more fields as needed
}

// GetTrackingStatus fetches tracking status for a package from Shippo.
func GetTrackingStatus(ctx context.Context, carrier, trackingNumber string) (*ShippoTrackResponse, error) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("SHIPPO_API_KEY not set in environment")
	}
	url := fmt.Sprintf("%s/tracks/%s/%s", shippoAPIBase, carrier, trackingNumber)
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
	var trackResp ShippoTrackResponse
	if err := json.Unmarshal(respBody, &trackResp); err != nil {
		return nil, err
	}
	return &trackResp, nil
}
