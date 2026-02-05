package test

import (
	"encoding/json"
	"os"
	"testing"

	shippo "github.com/thiwa/execution-server/tools/shippo"
)

// ToShippoAddressRequest converts Address to tools.ShippoAddressRequest
func (a Address) ToShippoAddressRequest() shippo.ShippoAddressRequest {
	return shippo.ShippoAddressRequest{
		Name:    a.Name,
		Street1: a.Street1,
		City:    a.City,
		State:   a.State,
		Zip:     a.Zip,
		Country: a.Country,
		Phone:   a.Phone,
		Email:   a.Email,
	}
}

type Address struct {
	Name    string `json:"name"`
	Street1 string `json:"street1"`
	City    string `json:"city"`
	State   string `json:"state"`
	Zip     string `json:"zip"`
	Country string `json:"country"`
	Phone   string `json:"phone"`
	Email   string `json:"email"`
}

type Parcel struct {
	Length       string `json:"length"`
	Width        string `json:"width"`
	Height       string `json:"height"`
	DistanceUnit string `json:"distance_unit"`
	Weight       string `json:"weight"`
	MassUnit     string `json:"mass_unit"`
}

type ShippoTestConfig struct {
	AddressFrom Address `json:"AddressFrom"`
	AddressTo   Address `json:"AddressTo"`
	Parcel      Parcel  `json:"Parcel"`
	Carrier     string  `json:"Carrier"`
}

func LoadShippoTestConfig(t *testing.T) ShippoTestConfig {
	f, err := os.Open("./testdata/shippo_test_config.json")
	if err != nil {
		t.Fatalf("Failed to open config: %v", err)
	}
	defer f.Close()
	var cfg ShippoTestConfig
	if err := json.NewDecoder(f).Decode(&cfg); err != nil {
		t.Fatalf("Failed to decode config: %v", err)
	}
	return cfg
}
