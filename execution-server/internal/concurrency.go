package internal

import (
	"context"
	"sync"
	"time"
)

// QuoteResult holds the result of a quote request, including any error.
type QuoteResult struct {
	Carrier string
	Quote   *QuoteResponse
	Err     error
}

// RunParallelQuotes runs multiple quote functions in parallel, respecting context timeout and fail-fast.
// Each quoteFunc should be a function that takes a context and returns a QuoteResponse and error.
func RunParallelQuotes(ctx context.Context, quoteFuncs map[string]func(context.Context) (*QuoteResponse, error)) map[string]QuoteResult {
	var (
		wg      sync.WaitGroup
		mu      sync.Mutex
		results = make(map[string]QuoteResult)
		done    = make(chan struct{})
	)

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	for carrier, fn := range quoteFuncs {
		wg.Add(1)
		go func(carrier string, fn func(context.Context) (*QuoteResponse, error)) {
			defer wg.Done()
			select {
			case <-ctx.Done():
				return
			default:
			}
			quote, err := fn(ctx)
			mu.Lock()
			results[carrier] = QuoteResult{Carrier: carrier, Quote: quote, Err: err}
			// Fail fast if critical error
			if err != nil && ctx.Err() == nil {
				cancel()
			}
			mu.Unlock()
		}(carrier, fn)
	}

	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
	case <-ctx.Done():
	}

	return results
}

// WithTimeout runs a function with a timeout, returning context.DeadlineExceeded if it times out.
func WithTimeout(ctx context.Context, timeout time.Duration, fn func(context.Context) error) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	ch := make(chan error, 1)
	go func() {
		ch <- fn(ctx)
	}()
	select {
	case err := <-ch:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
} // Goroutine management for parallel API calls
