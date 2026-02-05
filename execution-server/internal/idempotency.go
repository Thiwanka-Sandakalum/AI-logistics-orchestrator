package internal

import (
	"context"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// IdempotencyRecord stores the result and audit info for an idempotent operation.
type IdempotencyRecord struct {
	Key         string      `bson:"key"`
	Result      interface{} `bson:"result"`
	CreatedAt   time.Time   `bson:"created_at"`
	RequestData interface{} `bson:"request_data"`
	Audit       AuditInfo   `bson:"audit"`
}

type AuditInfo struct {
	ClientIP  string    `bson:"client_ip"`
	UserAgent string    `bson:"user_agent"`
	Timestamp time.Time `bson:"timestamp"`
}

// IdempotencyStore manages idempotency records in MongoDB.
type IdempotencyStore struct {
	coll *mongo.Collection
}

func NewIdempotencyStore(mongoURL, dbName, collName string) (*IdempotencyStore, error) {
	client, err := mongo.Connect(context.Background(), options.Client().ApplyURI(mongoURL))
	if err != nil {
		return nil, err
	}
	coll := client.Database(dbName).Collection(collName)
	return &IdempotencyStore{coll: coll}, nil
}

// GetOrCreate checks for an existing record by key, or creates one if not present.
func (s *IdempotencyStore) GetOrCreate(ctx context.Context, key string, reqData interface{}, resultFunc func() (interface{}, error), audit AuditInfo) (interface{}, bool, error) {
	var rec IdempotencyRecord
	err := s.coll.FindOne(ctx, bson.M{"key": key}).Decode(&rec)
	if err == nil {
		return rec.Result, true, nil // Found existing
	}
	if err != mongo.ErrNoDocuments {
		return nil, false, err
	}
	// Not found, create new
	result, err := resultFunc()
	if err != nil {
		return nil, false, err
	}
	rec = IdempotencyRecord{
		Key:         key,
		Result:      result,
		CreatedAt:   time.Now(),
		RequestData: reqData,
		Audit:       audit,
	}
	_, err = s.coll.InsertOne(ctx, rec)
	if err != nil {
		return nil, false, err
	}
	return result, false, nil
}
