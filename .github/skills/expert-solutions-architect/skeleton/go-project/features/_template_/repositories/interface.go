package _template_

import "context"

// IEntityRepository defines the data access interface.
type IEntityRepository interface {
	// Create creates a new entity.
	Create(ctx context.Context, entity *Entity) error

	// FindByID retrieves an entity by ID.
	FindByID(ctx context.Context, id string) (*Entity, error)

	// FindAll retrieves entities with filtering and pagination.
	FindAll(ctx context.Context, filter EntityFilter) ([]*Entity, int64, error)

	// Update updates an existing entity.
	Update(ctx context.Context, id string, entity *Entity) error

	// Delete soft-deletes an entity.
	Delete(ctx context.Context, id string) error

	// ExistsByName checks if an entity with the given name exists.
	ExistsByName(ctx context.Context, tenantID, name string) (bool, error)
}
