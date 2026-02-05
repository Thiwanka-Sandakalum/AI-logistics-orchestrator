package internal

import "os"

// GetMongoConfig returns MongoDB connection info from environment variables.
func GetMongoConfig() (url, db, coll string) {
	url = os.Getenv("IDEMPOTENCY_MONGO_URL")
	if url == "" {
		url = "mongodb://localhost:27017" // default for local dev
	}
	db = os.Getenv("IDEMPOTENCY_MONGO_DB")
	if db == "" {
		db = "loomis" // sensible default
	}
	coll = os.Getenv("IDEMPOTENCY_MONGO_COLL")
	if coll == "" {
		coll = "idempotency" // sensible default
	}
	return
}
