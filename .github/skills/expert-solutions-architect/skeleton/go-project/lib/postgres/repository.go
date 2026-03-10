package postgres

import (
	"context"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v5"
)

// Repository provides generic database operations.
type Repository struct {
	pool *Pool
}

// NewRepository creates a new repository.
func NewRepository(pool *Pool) *Repository {
	return &Repository{pool: pool}
}

// Insert inserts a row and returns the generated ID.
func (r *Repository) Insert(ctx context.Context, table string, columns []string, values []interface{}, returningColumn string) (interface{}, error) {
	placeholders := make([]string, len(values))
	for i := range values {
		placeholders[i] = fmt.Sprintf("$%d", i+1)
	}

	sql := fmt.Sprintf(
		"INSERT INTO %s (%s) VALUES (%s) RETURNING %s",
		table,
		strings.Join(columns, ", "),
		strings.Join(placeholders, ", "),
		returningColumn,
	)

	var id interface{}
	err := r.pool.QueryRow(ctx, sql, values...).Scan(&id)
	if err != nil {
		return nil, fmt.Errorf("insert failed: %w", err)
	}
	return id, nil
}

// InsertReturning inserts and returns multiple columns.
func (r *Repository) InsertReturning(ctx context.Context, table string, columns []string, values []interface{}, returning []string, dest ...interface{}) error {
	placeholders := make([]string, len(values))
	for i := range values {
		placeholders[i] = fmt.Sprintf("$%d", i+1)
	}

	sql := fmt.Sprintf(
		"INSERT INTO %s (%s) VALUES (%s) RETURNING %s",
		table,
		strings.Join(columns, ", "),
		strings.Join(placeholders, ", "),
		strings.Join(returning, ", "),
	)

	return r.pool.QueryRow(ctx, sql, values...).Scan(dest...)
}

// Update updates rows matching the condition.
func (r *Repository) Update(ctx context.Context, table string, setColumns []string, values []interface{}, whereCondition string, whereArgs ...interface{}) (int64, error) {
	setClauses := make([]string, len(setColumns))
	for i, col := range setColumns {
		setClauses[i] = fmt.Sprintf("%s = $%d", col, i+1)
	}

	allArgs := append(values, whereArgs...)
	sql := fmt.Sprintf(
		"UPDATE %s SET %s WHERE %s",
		table,
		strings.Join(setClauses, ", "),
		whereCondition,
	)

	return r.pool.Exec(ctx, sql, allArgs...)
}

// Delete deletes rows matching the condition.
func (r *Repository) Delete(ctx context.Context, table string, whereCondition string, args ...interface{}) (int64, error) {
	sql := fmt.Sprintf("DELETE FROM %s WHERE %s", table, whereCondition)
	return r.pool.Exec(ctx, sql, args...)
}

// FindByID finds a row by ID.
func (r *Repository) FindByID(ctx context.Context, table, idColumn string, id interface{}, columns []string, dest ...interface{}) error {
	sql := fmt.Sprintf(
		"SELECT %s FROM %s WHERE %s = $1",
		strings.Join(columns, ", "),
		table,
		idColumn,
	)

	err := r.pool.QueryRow(ctx, sql, id).Scan(dest...)
	if err != nil {
		if err == pgx.ErrNoRows {
			return ErrNotFound
		}
		return fmt.Errorf("find by id failed: %w", err)
	}
	return nil
}

// FindOne finds a single row.
func (r *Repository) FindOne(ctx context.Context, table string, columns []string, whereCondition string, args []interface{}, dest ...interface{}) error {
	sql := fmt.Sprintf(
		"SELECT %s FROM %s WHERE %s LIMIT 1",
		strings.Join(columns, ", "),
		table,
		whereCondition,
	)

	err := r.pool.QueryRow(ctx, sql, args...).Scan(dest...)
	if err != nil {
		if err == pgx.ErrNoRows {
			return ErrNotFound
		}
		return fmt.Errorf("find one failed: %w", err)
	}
	return nil
}

// Count counts rows matching the condition.
func (r *Repository) Count(ctx context.Context, table, whereCondition string, args ...interface{}) (int64, error) {
	sql := fmt.Sprintf("SELECT COUNT(*) FROM %s", table)
	if whereCondition != "" {
		sql += " WHERE " + whereCondition
	}

	var count int64
	err := r.pool.QueryRow(ctx, sql, args...).Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("count failed: %w", err)
	}
	return count, nil
}

// Exists checks if a row exists.
func (r *Repository) Exists(ctx context.Context, table, whereCondition string, args ...interface{}) (bool, error) {
	sql := fmt.Sprintf("SELECT EXISTS(SELECT 1 FROM %s WHERE %s)", table, whereCondition)

	var exists bool
	err := r.pool.QueryRow(ctx, sql, args...).Scan(&exists)
	if err != nil {
		return false, fmt.Errorf("exists check failed: %w", err)
	}
	return exists, nil
}

// Upsert performs an upsert (INSERT ... ON CONFLICT).
func (r *Repository) Upsert(ctx context.Context, table string, columns []string, values []interface{}, conflictColumns []string, updateColumns []string) (int64, error) {
	placeholders := make([]string, len(values))
	for i := range values {
		placeholders[i] = fmt.Sprintf("$%d", i+1)
	}

	updateClauses := make([]string, len(updateColumns))
	for i, col := range updateColumns {
		updateClauses[i] = fmt.Sprintf("%s = EXCLUDED.%s", col, col)
	}

	sql := fmt.Sprintf(
		"INSERT INTO %s (%s) VALUES (%s) ON CONFLICT (%s) DO UPDATE SET %s",
		table,
		strings.Join(columns, ", "),
		strings.Join(placeholders, ", "),
		strings.Join(conflictColumns, ", "),
		strings.Join(updateClauses, ", "),
	)

	return r.pool.Exec(ctx, sql, values...)
}
