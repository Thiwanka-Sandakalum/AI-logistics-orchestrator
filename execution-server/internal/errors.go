package internal

import (
	"encoding/json"
	"fmt"
)

// ValidationError is returned when input validation fails.
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("validation error: %s: %s", e.Field, e.Message)
}

func (e *ValidationError) MarshalJSON() ([]byte, error) {
	type Alias ValidationError
	return json.Marshal(&struct {
		Type string `json:"type"`
		*Alias
	}{
		Type:  "ValidationError",
		Alias: (*Alias)(e),
	})
}

// ExternalServiceError is returned when an external API call fails.
type ExternalServiceError struct {
	Service string `json:"service"`
	Message string `json:"message"`
}

func (e *ExternalServiceError) Error() string {
	return fmt.Sprintf("external service error: %s: %s", e.Service, e.Message)
}

func (e *ExternalServiceError) MarshalJSON() ([]byte, error) {
	type Alias ExternalServiceError
	return json.Marshal(&struct {
		Type string `json:"type"`
		*Alias
	}{
		Type:  "ExternalServiceError",
		Alias: (*Alias)(e),
	})
}

// CircuitOpenError is returned when a circuit breaker is open.
type CircuitOpenError struct {
	Service string `json:"service"`
	Message string `json:"message"`
}

func (e *CircuitOpenError) Error() string {
	return fmt.Sprintf("circuit open: %s: %s", e.Service, e.Message)
}

func (e *CircuitOpenError) MarshalJSON() ([]byte, error) {
	type Alias CircuitOpenError
	return json.Marshal(&struct {
		Type string `json:"type"`
		*Alias
	}{
		Type:  "CircuitOpenError",
		Alias: (*Alias)(e),
	})
}
