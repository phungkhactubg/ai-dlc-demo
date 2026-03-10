package _template_

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
)

type entityServiceImpl struct {
	repo IEntityRepository
}

// NewEntityService creates a new entity service.
func NewEntityService(repo IEntityRepository) IEntityService {
	return &entityServiceImpl{repo: repo}
}

// Create creates a new entity.
func (s *entityServiceImpl) Create(ctx context.Context, req CreateEntityRequest) (*Entity, error) {
	// Get tenant ID from context
	tenantID, ok := ctx.Value("tenant_id").(string)
	if !ok || tenantID == "" {
		return nil, fmt.Errorf("missing tenant_id: %w", ErrUnauthorized)
	}

	// Get user ID from context
	userID, _ := ctx.Value("user_id").(string)

	// Check for duplicate name
	exists, err := s.repo.ExistsByName(ctx, tenantID, req.Name)
	if err != nil {
		return nil, fmt.Errorf("check duplicate: %w", err)
	}
	if exists {
		return nil, ErrDuplicateName
	}

	// Create entity
	now := time.Now()
	entity := &Entity{
		ID:          uuid.New().String(),
		TenantID:    tenantID,
		Name:        req.Name,
		Description: req.Description,
		Status:      StatusActive,
		Metadata:    req.Metadata,
		CreatedBy:   userID,
		CreatedAt:   now,
		UpdatedAt:   now,
	}

	if err := s.repo.Create(ctx, entity); err != nil {
		return nil, fmt.Errorf("create entity: %w", err)
	}

	return entity, nil
}

// GetByID retrieves an entity by ID.
func (s *entityServiceImpl) GetByID(ctx context.Context, id string) (*Entity, error) {
	entity, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("find entity: %w", err)
	}
	return entity, nil
}

// List retrieves entities with filtering and pagination.
func (s *entityServiceImpl) List(ctx context.Context, filter EntityFilter) ([]*Entity, int64, error) {
	// Get tenant ID from context if not set
	if filter.TenantID == "" {
		tenantID, _ := ctx.Value("tenant_id").(string)
		filter.TenantID = tenantID
	}

	entities, total, err := s.repo.FindAll(ctx, filter)
	if err != nil {
		return nil, 0, fmt.Errorf("list entities: %w", err)
	}

	return entities, total, nil
}

// Update updates an existing entity.
func (s *entityServiceImpl) Update(ctx context.Context, id string, req UpdateEntityRequest) (*Entity, error) {
	// Get existing entity
	entity, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}

	// Get user ID from context
	userID, _ := ctx.Value("user_id").(string)

	// Apply updates
	if req.Name != nil {
		// Check for duplicate name
		if *req.Name != entity.Name {
			exists, err := s.repo.ExistsByName(ctx, entity.TenantID, *req.Name)
			if err != nil {
				return nil, fmt.Errorf("check duplicate: %w", err)
			}
			if exists {
				return nil, ErrDuplicateName
			}
		}
		entity.Name = *req.Name
	}
	if req.Description != nil {
		entity.Description = *req.Description
	}
	if req.Status != nil {
		entity.Status = *req.Status
	}
	if req.Metadata != nil {
		entity.Metadata = req.Metadata
	}

	entity.UpdatedBy = userID
	entity.UpdatedAt = time.Now()

	if err := s.repo.Update(ctx, id, entity); err != nil {
		return nil, fmt.Errorf("update entity: %w", err)
	}

	return entity, nil
}

// Delete soft-deletes an entity.
func (s *entityServiceImpl) Delete(ctx context.Context, id string) error {
	if err := s.repo.Delete(ctx, id); err != nil {
		return fmt.Errorf("delete entity: %w", err)
	}
	return nil
}
