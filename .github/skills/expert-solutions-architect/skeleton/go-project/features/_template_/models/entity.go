package _template_

import (
	"time"
)

// Entity represents the core domain entity.
// Replace "_template_" with your actual feature name.
type Entity struct {
	ID          string    `json:"id" bson:"_id"`
	TenantID    string    `json:"tenant_id" bson:"tenant_id"`
	Name        string    `json:"name" bson:"name"`
	Description string    `json:"description,omitempty" bson:"description,omitempty"`
	Status      string    `json:"status" bson:"status"`
	Metadata    Metadata  `json:"metadata,omitempty" bson:"metadata,omitempty"`
	CreatedBy   string    `json:"created_by" bson:"created_by"`
	UpdatedBy   string    `json:"updated_by,omitempty" bson:"updated_by,omitempty"`
	CreatedAt   time.Time `json:"created_at" bson:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" bson:"updated_at"`
}

// Metadata holds extensible key-value data.
type Metadata map[string]any

// EntityStatus constants.
const (
	StatusActive   = "active"
	StatusInactive = "inactive"
	StatusDeleted  = "deleted"
)

// NewEntity creates a new entity with default values.
func NewEntity(tenantID, name, createdBy string) *Entity {
	now := time.Now()
	return &Entity{
		TenantID:  tenantID,
		Name:      name,
		Status:    StatusActive,
		CreatedBy: createdBy,
		CreatedAt: now,
		UpdatedAt: now,
	}
}
