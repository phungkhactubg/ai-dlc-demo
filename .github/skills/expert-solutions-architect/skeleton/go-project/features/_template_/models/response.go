package _template_

import "time"

// EntityResponse represents the DTO for entity responses.
type EntityResponse struct {
	ID          string    `json:"id"`
	TenantID    string    `json:"tenant_id"`
	Name        string    `json:"name"`
	Description string    `json:"description,omitempty"`
	Status      string    `json:"status"`
	Metadata    Metadata  `json:"metadata,omitempty"`
	CreatedBy   string    `json:"created_by"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// ListResponse represents a paginated list response.
type ListResponse struct {
	Items      []EntityResponse `json:"items"`
	Page       int              `json:"page"`
	Limit      int              `json:"limit"`
	Total      int64            `json:"total"`
	TotalPages int              `json:"total_pages"`
}

// ToResponse converts an Entity to EntityResponse.
func ToResponse(e *Entity) *EntityResponse {
	return &EntityResponse{
		ID:          e.ID,
		TenantID:    e.TenantID,
		Name:        e.Name,
		Description: e.Description,
		Status:      e.Status,
		Metadata:    e.Metadata,
		CreatedBy:   e.CreatedBy,
		CreatedAt:   e.CreatedAt,
		UpdatedAt:   e.UpdatedAt,
	}
}

// ToListResponse converts a slice of entities to ListResponse.
func ToListResponse(entities []*Entity, page, limit int, total int64) *ListResponse {
	items := make([]EntityResponse, len(entities))
	for i, e := range entities {
		items[i] = *ToResponse(e)
	}

	totalPages := int(total) / limit
	if int(total)%limit > 0 {
		totalPages++
	}

	return &ListResponse{
		Items:      items,
		Page:       page,
		Limit:      limit,
		Total:      total,
		TotalPages: totalPages,
	}
}
