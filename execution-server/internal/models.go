package internal

// Address represents a physical address for shipments.
type Address struct {
	Name        string  `json:"name"`
	Street1     string  `json:"street1"`
	Street2     *string `json:"street2,omitempty"`
	City        string  `json:"city"`
	State       *string `json:"state,omitempty"`
	PostalCode  string  `json:"postal_code"`
	CountryCode string  `json:"country_code"`
	Phone       *string `json:"phone,omitempty"`
	Email       *string `json:"email,omitempty"`
}

// Package represents a single package in a shipment.
type Package struct {
	WeightKg  float64 `json:"weight_kg"`
	LengthCm  float64 `json:"length_cm"`
	WidthCm   float64 `json:"width_cm"`
	HeightCm  float64 `json:"height_cm"`
	Reference *string `json:"reference,omitempty"`
}

// ShipmentRequest represents a request to create a shipment.
type ShipmentRequest struct {
	Sender    Address   `json:"sender"`
	Recipient Address   `json:"recipient"`
	Packages  []Package `json:"packages"`
	Carrier   string    `json:"carrier"`
	Service   string    `json:"service"`
	Reference *string   `json:"reference,omitempty"`
}

// QuoteRequest represents a request for a shipping quote.
type QuoteRequest struct {
	Sender    Address   `json:"sender"`
	Recipient Address   `json:"recipient"`
	Packages  []Package `json:"packages"`
	Carrier   *string   `json:"carrier,omitempty"`
	Service   *string   `json:"service,omitempty"`
}

// QuoteResponse represents a response with a shipping quote.
type QuoteResponse struct {
	Carrier       string  `json:"carrier"`
	Service       string  `json:"service"`
	Price         float64 `json:"price"`
	Currency      string  `json:"currency"`
	EstimatedDays int     `json:"estimated_days"`
	Reference     *string `json:"reference,omitempty"`
}

// TrackingResponse represents the tracking status of a shipment.
type TrackingResponse struct {
	TrackingNumber string          `json:"tracking_number"`
	Status         string          `json:"status"`
	Timestamp      string          `json:"timestamp"`
	Location       *string         `json:"location,omitempty"`
	History        []TrackingEvent `json:"history"`
}

// TrackingEvent represents a single event in the tracking history.
type TrackingEvent struct {
	Status    string  `json:"status"`
	Timestamp string  `json:"timestamp"`
	Location  *string `json:"location,omitempty"`
}
