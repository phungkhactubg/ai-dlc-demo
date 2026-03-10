package mongodb

import (
	"context"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// Filter is a convenience alias for bson.M.
type Filter = bson.M

// Repository provides generic CRUD operations for MongoDB collections.
type Repository[T any] struct {
	collection *mongo.Collection
}

// NewRepository creates a new repository for a collection.
func NewRepository[T any](client *Client, collectionName string) *Repository[T] {
	return &Repository[T]{
		collection: client.Collection(collectionName),
	}
}

// NewRepositoryWithDB creates a repository with a specific database.
func NewRepositoryWithDB[T any](client *Client, database, collection string) *Repository[T] {
	return &Repository[T]{
		collection: client.UseDatabase(database).Collection(collection),
	}
}

// Create inserts a new document.
func (r *Repository[T]) Create(ctx context.Context, entity *T) (string, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	result, err := r.collection.InsertOne(ctx, entity)
	if err != nil {
		return "", fmt.Errorf("insert failed: %w", err)
	}

	if oid, ok := result.InsertedID.(primitive.ObjectID); ok {
		return oid.Hex(), nil
	}
	return fmt.Sprintf("%v", result.InsertedID), nil
}

// FindByID finds a document by its ID.
func (r *Repository[T]) FindByID(ctx context.Context, id string) (*T, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	var entity T
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&entity)
	if err != nil {
		if err == mongo.ErrNoDocuments {
			return nil, fmt.Errorf("id %s: %w", id, ErrNotFound)
		}
		return nil, fmt.Errorf("find by id failed: %w", err)
	}
	return &entity, nil
}

// FindByObjectID finds a document by ObjectID.
func (r *Repository[T]) FindByObjectID(ctx context.Context, id primitive.ObjectID) (*T, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	var entity T
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&entity)
	if err != nil {
		if err == mongo.ErrNoDocuments {
			return nil, ErrNotFound
		}
		return nil, fmt.Errorf("find by object id failed: %w", err)
	}
	return &entity, nil
}

// FindOne finds a single document matching the filter.
func (r *Repository[T]) FindOne(ctx context.Context, filter Filter) (*T, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	var entity T
	err := r.collection.FindOne(ctx, filter).Decode(&entity)
	if err != nil {
		if err == mongo.ErrNoDocuments {
			return nil, ErrNotFound
		}
		return nil, fmt.Errorf("find one failed: %w", err)
	}
	return &entity, nil
}

// FindAll finds all documents matching the filter.
func (r *Repository[T]) FindAll(ctx context.Context, filter Filter) ([]T, error) {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	cursor, err := r.collection.Find(ctx, filter)
	if err != nil {
		return nil, fmt.Errorf("find all failed: %w", err)
	}
	defer cursor.Close(ctx)

	var results []T
	if err := cursor.All(ctx, &results); err != nil {
		return nil, fmt.Errorf("decode results failed: %w", err)
	}
	return results, nil
}

// FindWithPagination finds documents with pagination.
func (r *Repository[T]) FindWithPagination(ctx context.Context, filter Filter, page, limit int64) ([]T, int64, error) {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	// Get total count
	total, err := r.collection.CountDocuments(ctx, filter)
	if err != nil {
		return nil, 0, fmt.Errorf("count failed: %w", err)
	}

	// Calculate skip
	skip := (page - 1) * limit
	opts := options.Find().SetSkip(skip).SetLimit(limit)

	cursor, err := r.collection.Find(ctx, filter, opts)
	if err != nil {
		return nil, 0, fmt.Errorf("find with pagination failed: %w", err)
	}
	defer cursor.Close(ctx)

	var results []T
	if err := cursor.All(ctx, &results); err != nil {
		return nil, 0, fmt.Errorf("decode results failed: %w", err)
	}
	return results, total, nil
}

// Update updates a document by ID.
func (r *Repository[T]) Update(ctx context.Context, id string, update bson.M) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	result, err := r.collection.UpdateOne(ctx, bson.M{"_id": id}, bson.M{"$set": update})
	if err != nil {
		return fmt.Errorf("update failed: %w", err)
	}
	if result.MatchedCount == 0 {
		return ErrNotFound
	}
	return nil
}

// Replace replaces a document entirely.
func (r *Repository[T]) Replace(ctx context.Context, id string, entity *T) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	result, err := r.collection.ReplaceOne(ctx, bson.M{"_id": id}, entity)
	if err != nil {
		return fmt.Errorf("replace failed: %w", err)
	}
	if result.MatchedCount == 0 {
		return ErrNotFound
	}
	return nil
}

// Delete removes a document by ID.
func (r *Repository[T]) Delete(ctx context.Context, id string) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	result, err := r.collection.DeleteOne(ctx, bson.M{"_id": id})
	if err != nil {
		return fmt.Errorf("delete failed: %w", err)
	}
	if result.DeletedCount == 0 {
		return ErrNotFound
	}
	return nil
}

// DeleteMany removes all documents matching the filter.
func (r *Repository[T]) DeleteMany(ctx context.Context, filter Filter) (int64, error) {
	ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	result, err := r.collection.DeleteMany(ctx, filter)
	if err != nil {
		return 0, fmt.Errorf("delete many failed: %w", err)
	}
	return result.DeletedCount, nil
}

// Count returns the number of documents matching the filter.
func (r *Repository[T]) Count(ctx context.Context, filter Filter) (int64, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	count, err := r.collection.CountDocuments(ctx, filter)
	if err != nil {
		return 0, fmt.Errorf("count failed: %w", err)
	}
	return count, nil
}

// Exists checks if a document exists.
func (r *Repository[T]) Exists(ctx context.Context, filter Filter) (bool, error) {
	count, err := r.Count(ctx, filter)
	if err != nil {
		return false, err
	}
	return count > 0, nil
}

// Aggregate performs an aggregation pipeline.
func (r *Repository[T]) Aggregate(ctx context.Context, pipeline mongo.Pipeline) ([]T, error) {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	cursor, err := r.collection.Aggregate(ctx, pipeline)
	if err != nil {
		return nil, fmt.Errorf("aggregate failed: %w", err)
	}
	defer cursor.Close(ctx)

	var results []T
	if err := cursor.All(ctx, &results); err != nil {
		return nil, fmt.Errorf("decode aggregate results failed: %w", err)
	}
	return results, nil
}

// BulkWrite performs bulk write operations.
func (r *Repository[T]) BulkWrite(ctx context.Context, models []mongo.WriteModel) (*mongo.BulkWriteResult, error) {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	result, err := r.collection.BulkWrite(ctx, models)
	if err != nil {
		return nil, fmt.Errorf("bulk write failed: %w", err)
	}
	return result, nil
}
