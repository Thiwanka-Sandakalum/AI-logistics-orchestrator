package internal

import (
	"context"
	"sync"
	"time"
)

// CircuitBreakerState represents the state of the circuit breaker.
type CircuitBreakerState int

const (
	Closed CircuitBreakerState = iota
	Open
	HalfOpen
)

// CircuitBreakerConfig holds configuration for the circuit breaker.
type CircuitBreakerConfig struct {
	FailureThreshold    int
	ResetTimeout        time.Duration
	HalfOpenMaxRequests int
}

// CircuitBreaker implements a simple thread-safe circuit breaker.
type CircuitBreaker struct {
	mu               sync.Mutex
	state            CircuitBreakerState
	failures         int
	lastFailure      time.Time
	config           CircuitBreakerConfig
	halfOpenRequests int
}

// NewCircuitBreaker creates a new CircuitBreaker with the given config.
func NewCircuitBreaker(cfg CircuitBreakerConfig) *CircuitBreaker {
	return &CircuitBreaker{
		state:  Closed,
		config: cfg,
	}
}

// Allow checks if a request is allowed to proceed.
func (cb *CircuitBreaker) Allow() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	switch cb.state {
	case Closed:
		return true
	case Open:
		if time.Since(cb.lastFailure) > cb.config.ResetTimeout {
			cb.state = HalfOpen
			cb.halfOpenRequests = 0
			return true
		}
		return false
	case HalfOpen:
		if cb.halfOpenRequests < cb.config.HalfOpenMaxRequests {
			cb.halfOpenRequests++
			return true
		}
		return false
	default:
		return false
	}
}

// Success should be called when a request succeeds.
func (cb *CircuitBreaker) Success() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	if cb.state == HalfOpen {
		cb.state = Closed
		cb.failures = 0
		cb.halfOpenRequests = 0
	}
	if cb.state == Closed {
		cb.failures = 0
	}
}

// Failure should be called when a request fails.
func (cb *CircuitBreaker) Failure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	cb.failures++
	cb.lastFailure = time.Now()
	if cb.state == Closed && cb.failures >= cb.config.FailureThreshold {
		cb.state = Open
	}
	if cb.state == HalfOpen {
		cb.state = Open
		cb.halfOpenRequests = 0
	}
}

// State returns the current state of the circuit breaker.
func (cb *CircuitBreaker) State() CircuitBreakerState {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}

// Wrap wraps an external API call with circuit breaker logic.
func (cb *CircuitBreaker) Wrap(ctx context.Context, fn func(context.Context) error) error {
	if !cb.Allow() {
		return &CircuitOpenError{Service: "external", Message: "circuit breaker is open"}
	}
	err := fn(ctx)
	if err != nil {
		cb.Failure()
		return err
	}
	cb.Success()
	return nil
}
