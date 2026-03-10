package _template_

import (
	"context"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

const collectionName = "entities" // Replace with actual collection name

type mongoRepository struct {
	collection *mongo.Collection
}

// NewMongoRepository creates a new MongoDB repository.
func NewMongoRepository(db *mongo.Database) IEntityRepository {
	return &mongoRepository{
		collection: db.Collection(collectionName),
	}
}

// Create creates a new entity.
func (r *mongoRepository) Create(ctx context.Context, entity *Entity) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	_, err := r.collection.InsertOne(ctx, entity)
	if err != nil {
		return fmt.Errorf("insert failed: %w", err)
	}
	return nil
}

// FindByID retrieves an entity by ID.
func (r *mongoRepository) FindByID(ctx context.Context, id string) (*Entity, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	var entity Entity
	filter := bson.M{
		"_id":    id,
		"status": bson.M{"$ne": StatusDeleted},
	}

	err := r.collection.FindOne(ctx, filter).Decode(&entity)
	if err != nil {
		if err == mongo.ErrNoDocuments {
			return nil, fmt.Errorf("id %s: %w", id, ErrEntityNotFound)
		}
		return nil, fmt.Errorf("find failed: %w", err)
	}
	return &entity, nil
}

// FindAll retrieves entities with filtering and pagination.
func (r *mongoRepository) FindAll(ctx context.Context, filter EntityFilter) ([]*Entity, int64, error) {
	ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	// Build query
	query := bson.M{
		"tenant_id": filter.TenantID,
		"status":    bson.M{"$ne": StatusDeleted},
	}

	if filter.Status != "" {
		query["status"] = filter.Status
	}

	if filter.Search != "" {
		query["$or"] = []bson.M{
			{"name": bson.M{"$regex": filter.Search, "$options": "i"}},
			{"description": bson.M{"$regex": filter.Search, "$options": "i"}},
		}
	}

	// Count total
	total, err := r.collection.CountDocuments(ctx, query)
	if err != nil {
		return nil, 0, fmt.Errorf("count failed: %w", err)
	}

	// Find with pagination
	opts := options.Find().
		SetSkip(int64((filter.Page - 1) * filter.Limit)).
		SetLimit(int64(filter.Limit)).
		SetSort(bson.D{{Key: "created_at", Value: -1}})

	cursor, err := r.collection.Find(ctx, query, opts)
	if err != nil {
		return nil, 0, fmt.Errorf("find failed: %w", err)
	}
	defer cursor.Close(ctx)

	var entities []*Entity
	if err := cursor.All(ctx, &entities); err != nil {
		return nil, 0, fmt.Errorf("decode failed: %w", err)
	}

	return entities, total, nil
}

// Update updates an existing entity.
func (r *mongoRepository) Update(ctx context.Context, id string, entity *Entity) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	filter := bson.M{"_id": id}
	update := bson.M{"$set": entity}

	result, err := r.collection.UpdateOne(ctx, filter, update)
	if err != nil {
		return fmt.Errorf("update failed: %w", err)
	}
	if result.MatchedCount == 0 {
		return ErrEntityNotFound
	}
	return nil
}

// Delete soft-deletes an entity.
func (r *mongoRepository) Delete(ctx context.Context, id string) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	filter := bson.M{"_id": id}
	update := bson.M{
		"$set": bson.M{
			"status":     StatusDeleted,
			"updated_at": time.Now(),
		},
	}

	result, err := r.collection.UpdateOne(ctx, filter, update)
	if err != nil {
		return fmt.Errorf("delete failed: %w", err)
	}
	if result.MatchedCount == 0 {
		return ErrEntityNotFound
	}
	return nil
}

// ExistsByName checks if an entity with the given name exists.
func (r *mongoRepository) ExistsByName(ctx context.Context, tenantID, name string) (bool, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	filter := bson.M{
		"tenant_id": tenantID,
		"name":      name,
		"status":    bson.M{"$ne": StatusDeleted},
	}

	count, err := r.collection.CountDocuments(ctx, filter)
	if err != nil {
		return false, fmt.Errorf("count failed: %w", err)
	}
	return count > 0, nil
}
