package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

// ShippoCarrierAccount represents a carrier account in Shippo.
type ShippoCarrierAccount struct {
	ObjectID string `json:"object_id"`
	Carrier  string `json:"carrier"`
	Active   bool   `json:"active"`
	// ... add more fields as needed
}

// ListCarrierAccounts fetches all carrier accounts from Shippo.
func ListCarrierAccounts(ctx context.Context) ([]ShippoCarrierAccount, error) {
	apiKey := os.Getenv("SHIPPO_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("SHIPPO_API_KEY not set in environment")
	}
	url := shippoAPIBase + "/carrier_accounts"
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
	var accountsResp struct {
		Results []ShippoCarrierAccount `json:"results"`
	}
	if err := json.Unmarshal(respBody, &accountsResp); err != nil {
		return nil, err
	}
	return accountsResp.Results, nil
}
