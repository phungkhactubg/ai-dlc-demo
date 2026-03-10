package _template_

// CreateEntityRequest represents the DTO for creating an entity.
type CreateEntityRequest struct {
	Name        string   `json:"name" validate:"required,min=1,max=100"`
	Description string   `json:"description,omitempty" validate:"max=500"`
	Metadata    Metadata `json:"metadata,omitempty"`
}

// UpdateEntityRequest represents the DTO for updating an entity.
type UpdateEntityRequest struct {
	Name        *string  `json:"name,omitempty" validate:"omitempty,min=1,max=100"`
	Description *string  `json:"description,omitempty" validate:"omitempty,max=500"`
	Status      *string  `json:"status,omitempty" validate:"omitempty,oneof=active inactive"`
	Metadata    Metadata `json:"metadata,omitempty"`
}

// EntityFilter represents query parameters for listing entities.
type EntityFilter struct {
	TenantID string
	Status   string
	Search   string
	Page     int
	Limit    int
}

// DefaultFilter returns a filter with default values.
func DefaultFilter(tenantID string) EntityFilter {
	return EntityFilter{
		TenantID: tenantID,
		Status:   StatusActive,
		Page:     1,
		Limit:    20,
	}
}
