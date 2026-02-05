package internal

import (
	"context"
	"strings"
)

// ValidateAddress checks if the address is complete and valid.
func ValidateAddress(ctx context.Context, addr Address) error {
	if strings.TrimSpace(addr.Name) == "" {
		return &ValidationError{Field: "name", Message: "Name is required"}
	}
	if strings.TrimSpace(addr.Street1) == "" {
		return &ValidationError{Field: "street1", Message: "Street1 is required"}
	}
	if strings.TrimSpace(addr.City) == "" {
		return &ValidationError{Field: "city", Message: "City is required"}
	}
	if strings.TrimSpace(addr.PostalCode) == "" {
		return &ValidationError{Field: "postal_code", Message: "Postal code is required"}
	}
	if strings.TrimSpace(addr.CountryCode) == "" {
		return &ValidationError{Field: "country_code", Message: "Country code is required"}
	}
	return nil
}

// ValidatePackage checks if the package has sane dimensions and weight.
func ValidatePackage(ctx context.Context, pkg Package) error {
	if pkg.WeightKg <= 0 {
		return &ValidationError{Field: "weight_kg", Message: "Weight must be positive"}
	}
	if pkg.LengthCm <= 0 || pkg.WidthCm <= 0 || pkg.HeightCm <= 0 {
		return &ValidationError{Field: "dimensions", Message: "All dimensions must be positive"}
	}
	return nil
}

// ValidateQuoteRequest checks if the quote request is valid.
func ValidateQuoteRequest(ctx context.Context, req QuoteRequest) error {
	if err := ValidateAddress(ctx, req.Sender); err != nil {
		return err
	}
	if err := ValidateAddress(ctx, req.Recipient); err != nil {
		return err
	}
	if len(req.Packages) == 0 {
		return &ValidationError{Field: "packages", Message: "At least one package required"}
	}
	for i, pkg := range req.Packages {
		if err := ValidatePackage(ctx, pkg); err != nil {
			return &ValidationError{Field: "packages[" + string(i) + "]", Message: err.Error()}
		}
	}
	return nil
}

// ValidateShipmentRequest checks if the shipment request is valid.
func ValidateShipmentRequest(ctx context.Context, req ShipmentRequest) error {
	if err := ValidateAddress(ctx, req.Sender); err != nil {
		return err
	}
	if err := ValidateAddress(ctx, req.Recipient); err != nil {
		return err
	}
	if len(req.Packages) == 0 {
		return &ValidationError{Field: "packages", Message: "At least one package required"}
	}
	for i, pkg := range req.Packages {
		if err := ValidatePackage(ctx, pkg); err != nil {
			return &ValidationError{Field: "packages[" + string(i) + "]", Message: err.Error()}
		}
	}
	if strings.TrimSpace(req.Carrier) == "" {
		return &ValidationError{Field: "carrier", Message: "Carrier is required"}
	}
	if strings.TrimSpace(req.Service) == "" {
		return &ValidationError{Field: "service", Message: "Service is required"}
	}
	return nil
} // Input validation & rules
