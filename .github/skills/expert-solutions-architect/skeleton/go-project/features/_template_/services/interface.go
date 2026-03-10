package _template_

import "context"

// IEntityService defines the business logic interface.
type IEntityService interface {
	// Create creates a new entity.
	Create(ctx context.Context, req CreateEntityRequest) (*Entity, error)

	// GetByID retrieves an entity by ID.
	GetByID(ctx context.Context, id string) (*Entity, error)

	// List retrieves entities with filtering and pagination.
	List(ctx context.Context, filter EntityFilter) ([]*Entity, int64, error)

	// Update updates an existing entity.
	Update(ctx context.Context, id string, req UpdateEntityRequest) (*Entity, error)

	// Delete soft-deletes an entity.
	Delete(ctx context.Context, id string) error
}
