package internal

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	tools "github.com/thiwa/execution-server/tools/shippo"
)

// JSONRPCRequest represents a JSON-RPC 2.0 request.
type JSONRPCRequest struct {
	JSONRPC string          `json:"jsonrpc"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params"`
	ID      interface{}     `json:"id"`
}

// JSONRPCResponse represents a JSON-RPC 2.0 response.
type JSONRPCResponse struct {
	JSONRPC string      `json:"jsonrpc"`
	Result  interface{} `json:"result,omitempty"`
	Error   *RPCError   `json:"error,omitempty"`
	ID      interface{} `json:"id"`
}

// RPCError represents a JSON-RPC error object.
type RPCError struct {
	Code    int         `json:"code"`
	Message string      `json:"message"`
	Data    interface{} `json:"data,omitempty"`
}

// Server holds the tool registry and handles JSON-RPC requests.
type Server struct {
	mu    sync.RWMutex
	tools map[string]interface{}
}

// NewServer creates a new Server instance.
func NewServer() *Server {
	return &Server{
		tools: make(map[string]interface{}),
	}
}

// RegisterTool registers a tool with a method name.
func (s *Server) RegisterTool(method string, tool interface{}) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.tools[method] = tool
}

// ServeHTTP handles incoming JSON-RPC requests.
func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}
	var req JSONRPCRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, JSONRPCResponse{
			JSONRPC: "2.0",
			Error:   &RPCError{Code: -32700, Message: "Parse error", Data: err.Error()},
			ID:      nil,
		})
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()
	resp := s.handleRequest(ctx, &req)
	writeJSON(w, resp)
}

func (s *Server) handleRequest(ctx context.Context, req *JSONRPCRequest) JSONRPCResponse {
	s.mu.RLock()
	_ = s.tools[req.Method] // keep lock for possible future use
	s.mu.RUnlock()

	// Shippo MCP tools
	switch req.Method {
	case "address.create":
		var params tools.ShippoAddressRequest
		if err := json.Unmarshal(req.Params, &params); err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32602, Message: "Invalid params", Data: err.Error()},
				ID:      req.ID,
			}
		}
		resp, err := tools.CreateAddress(ctx, params)
		if err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32001, Message: "Shippo error", Data: err.Error()},
				ID:      req.ID,
			}
		}
		return JSONRPCResponse{
			JSONRPC: "2.0",
			Result:  resp,
			ID:      req.ID,
		}
	case "address.validate":
		var params tools.ShippoAddressRequest
		if err := json.Unmarshal(req.Params, &params); err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32602, Message: "Invalid params", Data: err.Error()},
				ID:      req.ID,
			}
		}
		resp, err := tools.ValidateAddress(ctx, params)
		if err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32001, Message: "Shippo error", Data: err.Error()},
				ID:      req.ID,
			}
		}
		return JSONRPCResponse{
			JSONRPC: "2.0",
			Result:  resp,
			ID:      req.ID,
		}
	case "shipment.create":
		var params tools.ShippoShipmentRequest
		if err := json.Unmarshal(req.Params, &params); err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32602, Message: "Invalid params", Data: err.Error()},
				ID:      req.ID,
			}
		}
		// Idempotency logic
		mongoURL, mongoDB, mongoColl := GetMongoConfig()
		store, err := NewIdempotencyStore(mongoURL, mongoDB, mongoColl)
		if err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32002, Message: "Idempotency store error", Data: err.Error()},
				ID:      req.ID,
			}
		}
		audit := AuditInfo{
			ClientIP:  "", // Optionally extract from context or headers
			UserAgent: "", // Optionally extract from context or headers
			Timestamp: time.Now(),
		}
		key := params.IdempotencyKey
		if key == "" {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32602, Message: "Missing idempotency_key in params"},
				ID:      req.ID,
			}
		}
		result, _, err := store.GetOrCreate(ctx, key, params, func() (interface{}, error) {
			return tools.CreateShipment(ctx, params)
		}, audit)
		if err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32001, Message: "Shippo error", Data: err.Error()},
				ID:      req.ID,
			}
		}
		return JSONRPCResponse{
			JSONRPC: "2.0",
			Result:  result,
			ID:      req.ID,
		}
	case "shipment.get_rates":
		var params struct {
			ShipmentID string `json:"shipment_id"`
		}
		if err := json.Unmarshal(req.Params, &params); err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32602, Message: "Invalid params", Data: err.Error()},
				ID:      req.ID,
			}
		}
		resp, err := tools.GetShipmentRates(ctx, params.ShipmentID)
		if err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32001, Message: "Shippo error", Data: err.Error()},
				ID:      req.ID,
			}
		}
		return JSONRPCResponse{
			JSONRPC: "2.0",
			Result:  resp,
			ID:      req.ID,
		}
	case "label.purchase":
		var params tools.ShippoLabelPurchaseRequest
		if err := json.Unmarshal(req.Params, &params); err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32602, Message: "Invalid params", Data: err.Error()},
				ID:      req.ID,
			}
		}
		// Idempotency logic
		mongoURL, mongoDB, mongoColl := GetMongoConfig()
		store, err := NewIdempotencyStore(mongoURL, mongoDB, mongoColl)
		if err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32002, Message: "Idempotency store error", Data: err.Error()},
				ID:      req.ID,
			}
		}
		audit := AuditInfo{
			ClientIP:  "", // Optionally extract from context or headers
			UserAgent: "", // Optionally extract from context or headers
			Timestamp: time.Now(),
		}
		key := params.IdempotencyKey
		if key == "" {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32602, Message: "Missing idempotency_key in params"},
				ID:      req.ID,
			}
		}
		result, _, err := store.GetOrCreate(ctx, key, params, func() (interface{}, error) {
			return tools.PurchaseLabel(ctx, params)
		}, audit)
		if err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32001, Message: "Shippo error", Data: err.Error()},
				ID:      req.ID,
			}
		}
		return JSONRPCResponse{
			JSONRPC: "2.0",
			Result:  result,
			ID:      req.ID,
		}
	case "track.get":
		var params struct {
			Carrier        string `json:"carrier"`
			TrackingNumber string `json:"tracking_number"`
		}
		if err := json.Unmarshal(req.Params, &params); err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32602, Message: "Invalid params", Data: err.Error()},
				ID:      req.ID,
			}
		}
		resp, err := tools.GetTrackingStatus(ctx, params.Carrier, params.TrackingNumber)
		if err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32001, Message: "Shippo error", Data: err.Error()},
				ID:      req.ID,
			}
		}
		return JSONRPCResponse{
			JSONRPC: "2.0",
			Result:  resp,
			ID:      req.ID,
		}
	case "carrier_account.list":
		resp, err := tools.ListCarrierAccounts(ctx)
		if err != nil {
			return JSONRPCResponse{
				JSONRPC: "2.0",
				Error:   &RPCError{Code: -32001, Message: "Shippo error", Data: err.Error()},
				ID:      req.ID,
			}
		}
		return JSONRPCResponse{
			JSONRPC: "2.0",
			Result:  resp,
			ID:      req.ID,
		}
	default:
		return JSONRPCResponse{
			JSONRPC: "2.0",
			Error:   &RPCError{Code: -32601, Message: "Method not found"},
			ID:      req.ID,
		}
	}
}

func writeJSON(w http.ResponseWriter, resp JSONRPCResponse) {
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		log.Printf("Failed to write JSON-RPC response: %v", err)
	}
} // JSON-RPC server logic
