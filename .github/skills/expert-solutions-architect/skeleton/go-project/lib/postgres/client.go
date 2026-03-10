package postgres

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Pool wraps PostgreSQL connection pool.
type Pool struct {
	pool *pgxpool.Pool
}

// Config holds PostgreSQL connection settings.
type Config struct {
	DSN               string        `mapstructure:"dsn"`
	MaxConns          int32         `mapstructure:"max_conns"`
	MinConns          int32         `mapstructure:"min_conns"`
	MaxConnLifetime   time.Duration `mapstructure:"max_conn_lifetime"`
	MaxConnIdleTime   time.Duration `mapstructure:"max_conn_idle_time"`
	HealthCheckPeriod time.Duration `mapstructure:"health_check_period"`
}

// DefaultConfig returns sensible defaults.
func DefaultConfig() Config {
	return Config{
		DSN:               "postgres://user:password@localhost:5432/dbname?sslmode=disable",
		MaxConns:          25,
		MinConns:          5,
		MaxConnLifetime:   1 * time.Hour,
		MaxConnIdleTime:   30 * time.Minute,
		HealthCheckPeriod: 1 * time.Minute,
	}
}

// NewPool creates a new PostgreSQL connection pool.
func NewPool(ctx context.Context, cfg Config) (*Pool, error) {
	poolConfig, err := pgxpool.ParseConfig(cfg.DSN)
	if err != nil {
		return nil, fmt.Errorf("parse config failed: %w", err)
	}

	poolConfig.MaxConns = cfg.MaxConns
	poolConfig.MinConns = cfg.MinConns
	poolConfig.MaxConnLifetime = cfg.MaxConnLifetime
	poolConfig.MaxConnIdleTime = cfg.MaxConnIdleTime
	poolConfig.HealthCheckPeriod = cfg.HealthCheckPeriod

	pool, err := pgxpool.NewWithConfig(ctx, poolConfig)
	if err != nil {
		return nil, fmt.Errorf("pool creation failed: %w", err)
	}

	// Verify connection
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("ping failed: %w", err)
	}

	return &Pool{pool: pool}, nil
}

// Close closes the connection pool.
func (p *Pool) Close() {
	if p.pool != nil {
		p.pool.Close()
	}
}

// Pool returns the underlying pool.
func (p *Pool) Pool() *pgxpool.Pool {
	return p.pool
}

// Health checks if the connection is alive.
func (p *Pool) Health(ctx context.Context) error {
	return p.pool.Ping(ctx)
}

// Stats returns pool statistics.
func (p *Pool) Stats() *pgxpool.Stat {
	return p.pool.Stat()
}

// Exec executes a query without returning rows.
func (p *Pool) Exec(ctx context.Context, sql string, args ...interface{}) (int64, error) {
	result, err := p.pool.Exec(ctx, sql, args...)
	if err != nil {
		return 0, fmt.Errorf("exec failed: %w", err)
	}
	return result.RowsAffected(), nil
}

// QueryRow executes a query returning a single row.
func (p *Pool) QueryRow(ctx context.Context, sql string, args ...interface{}) pgx.Row {
	return p.pool.QueryRow(ctx, sql, args...)
}

// Query executes a query returning multiple rows.
func (p *Pool) Query(ctx context.Context, sql string, args ...interface{}) (pgx.Rows, error) {
	rows, err := p.pool.Query(ctx, sql, args...)
	if err != nil {
		return nil, fmt.Errorf("query failed: %w", err)
	}
	return rows, nil
}

// WithTransaction executes operations in a transaction.
func (p *Pool) WithTransaction(ctx context.Context, fn func(tx pgx.Tx) error) error {
	tx, err := p.pool.Begin(ctx)
	if err != nil {
		return fmt.Errorf("begin transaction failed: %w", err)
	}

	defer func() {
		if r := recover(); r != nil {
			_ = tx.Rollback(ctx)
			panic(r)
		}
	}()

	if err := fn(tx); err != nil {
		if rbErr := tx.Rollback(ctx); rbErr != nil {
			return fmt.Errorf("rollback failed after error: %w (original: %v)", rbErr, err)
		}
		return err
	}

	if err := tx.Commit(ctx); err != nil {
		return fmt.Errorf("commit failed: %w", err)
	}
	return nil
}

// WithTransactionLevel executes operations in a transaction with isolation level.
func (p *Pool) WithTransactionLevel(ctx context.Context, level pgx.TxIsoLevel, fn func(tx pgx.Tx) error) error {
	tx, err := p.pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: level})
	if err != nil {
		return fmt.Errorf("begin transaction failed: %w", err)
	}

	defer func() {
		if r := recover(); r != nil {
			_ = tx.Rollback(ctx)
			panic(r)
		}
	}()

	if err := fn(tx); err != nil {
		if rbErr := tx.Rollback(ctx); rbErr != nil {
			return fmt.Errorf("rollback failed: %w", rbErr)
		}
		return err
	}

	return tx.Commit(ctx)
}

// CopyFrom efficiently bulk inserts rows.
func (p *Pool) CopyFrom(ctx context.Context, tableName string, columnNames []string, rows [][]interface{}) (int64, error) {
	count, err := p.pool.CopyFrom(
		ctx,
		pgx.Identifier{tableName},
		columnNames,
		pgx.CopyFromRows(rows),
	)
	if err != nil {
		return 0, fmt.Errorf("copy from failed: %w", err)
	}
	return count, nil
}

// Acquire acquires a connection from the pool.
func (p *Pool) Acquire(ctx context.Context) (*pgxpool.Conn, error) {
	return p.pool.Acquire(ctx)
}

// SendBatch sends a batch of queries.
func (p *Pool) SendBatch(ctx context.Context, batch *pgx.Batch) pgx.BatchResults {
	return p.pool.SendBatch(ctx, batch)
}
