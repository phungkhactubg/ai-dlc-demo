#!/usr/bin/env python3
"""
React Feature Scaffolder
========================
Scaffold a complete feature module with all layers following the Senior React Frontend Developer skill guidelines.

Usage:
    python scaffold_feature.py <feature_name>
    python scaffold_feature.py my_dashboard --path apps/frontend/src
"""

import argparse
import os
from pathlib import Path


def to_pascal_case(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))


def to_camel_case(name: str) -> str:
    """Convert snake_case or kebab-case to camelCase."""
    words = name.replace('-', '_').split('_')
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])


# File templates
TEMPLATES = {
    # Core Layer
    "core/models/{feature}.model.ts": '''import {{ z }} from 'zod';

// Zod Schema Definition
export const {PascalName}Schema = z.object({{
  id: z.string().uuid(),
  name: z.string().min(1, 'Name is required'),
  status: z.enum(['active', 'inactive', 'pending']),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
}});

// TypeScript Type Inference (Zero duplication)
export type {PascalName} = z.infer<typeof {PascalName}Schema>;

// DTOs
export const Create{PascalName}Schema = {PascalName}Schema.omit({{ id: true, createdAt: true, updatedAt: true }});
export type Create{PascalName}Request = z.infer<typeof Create{PascalName}Schema>;

export const Update{PascalName}Schema = Create{PascalName}Schema.partial();
export type Update{PascalName}Request = z.infer<typeof Update{PascalName}Schema>;
''',

    "core/interfaces/{feature}.service.interface.ts": '''import {{ {PascalName}, Create{PascalName}Request, Update{PascalName}Request }} from '../models/{feature}.model';

/**
 * I{PascalName}Service - Contract for {PascalName} business logic.
 * UI components should NOT depend on this directly; use Hooks instead.
 */
export interface I{PascalName}Service {{
  getById(id: string): Promise<{PascalName}>;
  getAll(): Promise<{PascalName}[]>;
  create(data: Create{PascalName}Request): Promise<{PascalName}>;
  update(id: string, data: Update{PascalName}Request): Promise<{PascalName}>;
  delete(id: string): Promise<void>;
}}
''',

    "core/constants/{feature}.constants.ts": '''export const {UPPER_NAME}_CONSTANTS = {{
  DEFAULT_STATUS: 'pending',
  MAX_RETRIES: 3,
  CACHE_TTL_MS: 60_000, // 1 minute
}} as const;

export const {UPPER_NAME}_API = {{
  BASE: '/{kebab_name}s',
  BY_ID: (id: string) => `/{kebab_name}s/${{id}}`,
}} as const;

export const {UPPER_NAME}_EVENTS = {{
  CREATED: '{feature}:created',
  UPDATED: '{feature}:updated',
  DELETED: '{feature}:deleted',
}} as const;
''',

    # Infrastructure Layer
    "infrastructure/api/{feature}.api.ts": '''import axios, {{ AxiosInstance }} from 'axios';
import {{ {PascalName}, Create{PascalName}Request, Update{PascalName}Request }} from '../../core/models/{feature}.model';
import {{ {UPPER_NAME}_API }} from '../../core/constants/{feature}.constants';

// In a real app, this instance would come from a shared 'infrastructure/api' module with interceptors
const apiClient: AxiosInstance = axios.create({{
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 10000,
}});

export const {camelName}Api = {{
  getById: (id: string) => apiClient.get<{PascalName}>({UPPER_NAME}_API.BY_ID(id)),
  getAll: () => apiClient.get<{PascalName}[]>({UPPER_NAME}_API.BASE),
  create: (data: Create{PascalName}Request) => apiClient.post<{PascalName}>({UPPER_NAME}_API.BASE, data),
  update: (id: string, data: Update{PascalName}Request) => apiClient.put<{PascalName}>({UPPER_NAME}_API.BY_ID(id), data),
  delete: (id: string) => apiClient.delete<void>({UPPER_NAME}_API.BY_ID(id)),
}};
''',

    "infrastructure/services/{feature}.service.ts": '''import {{ I{PascalName}Service }} from '../../core/interfaces/{feature}.service.interface';
import {{ {PascalName}, {PascalName}Schema, Create{PascalName}Request, Update{PascalName}Request }} from '../../core/models/{feature}.model';
import {{ {camelName}Api }} from '../api/{feature}.api';

/**
 * {PascalName}Service - Concrete implementation of I{PascalName}Service.
 * Handles API calls, data mapping, and runtime validation.
 */
export class {PascalName}Service implements I{PascalName}Service {{
  async getById(id: string): Promise<{PascalName}> {{
    const response = await {camelName}Api.getById(id);
    // Runtime Validation: Ensure API response matches our Zod Schema
    return {PascalName}Schema.parse(response.data);
  }}

  async getAll(): Promise<{PascalName}[]> {{
    const response = await {camelName}Api.getAll();
    return response.data.map((item) => {PascalName}Schema.parse(item));
  }}

  async create(data: Create{PascalName}Request): Promise<{PascalName}> {{
    const response = await {camelName}Api.create(data);
    return {PascalName}Schema.parse(response.data);
  }}

  async update(id: string, data: Update{PascalName}Request): Promise<{PascalName}> {{
    const response = await {camelName}Api.update(id, data);
    return {PascalName}Schema.parse(response.data);
  }}

  async delete(id: string): Promise<void> {{
    await {camelName}Api.delete(id);
  }}
}}

// Singleton export
export const {camelName}Service = new {PascalName}Service();
''',

    "infrastructure/stores/{feature}.store.ts": '''import {{ create }} from 'zustand';
import {{ immer }} from 'zustand/middleware/immer';
import {{ devtools }} from 'zustand/middleware';
import {{ {PascalName} }} from '../../core/models/{feature}.model';
import {{ {camelName}Service }} from '../services/{feature}.service';

interface {PascalName}State {{
  items: Record<string, {PascalName}>;
  currentItemId: string | null;
  isLoading: boolean;
  error: string | null;
}}

interface {PascalName}Actions {{
  fetchById: (id: string) => Promise<void>;
  fetchAll: () => Promise<void>;
  createItem: (data: any) => Promise<{PascalName} | null>;
  updateItem: (id: string, data: any) => Promise<{PascalName} | null>;
  deleteItem: (id: string) => Promise<boolean>;
  resetError: () => void;
  setCurrentItem: (id: string | null) => void;
}}

type {PascalName}Store = {PascalName}State & {PascalName}Actions;

// Zustand Store with Immer for mutability and Devtools for debugging
export const use{PascalName}Store = create<{PascalName}Store>()(
  devtools(
    immer((set, get) => ({{
      // State
      items: {{}},
      currentItemId: null,
      isLoading: false,
      error: null,

      // Actions
      fetchById: async (id: string) => {{
        set((state) => {{ state.isLoading = true; state.error = null; }});
        try {{
          const data = await {camelName}Service.getById(id);
          set((state) => {{
            state.items[data.id] = data;
            state.currentItemId = data.id;
            state.isLoading = false;
          }});
        }} catch (err) {{
          set((state) => {{
            state.isLoading = false;
            state.error = (err as Error).message;
          }});
        }}
      }},

      fetchAll: async () => {{
        set((state) => {{ state.isLoading = true; state.error = null; }});
        try {{
          const data = await {camelName}Service.getAll();
          set((state) => {{
            state.items = data.reduce((acc, item) => {{ acc[item.id] = item; return acc; }}, {{}} as Record<string, {PascalName}>);
            state.isLoading = false;
          }});
        }} catch (err) {{
          set((state) => {{
            state.isLoading = false;
            state.error = (err as Error).message;
          }});
        }}
      }},

      createItem: async (data) => {{
        set((state) => {{ state.isLoading = true; }});
        try {{
          const newItem = await {camelName}Service.create(data);
          set((state) => {{
            state.items[newItem.id] = newItem;
            state.isLoading = false;
          }});
          return newItem;
        }} catch (err) {{
          set((state) => {{
            state.isLoading = false;
            state.error = (err as Error).message;
          }});
          return null;
        }}
      }},

      updateItem: async (id, data) => {{
        set((state) => {{ state.isLoading = true; }});
        try {{
          const updated = await {camelName}Service.update(id, data);
          set((state) => {{
            state.items[updated.id] = updated;
            state.isLoading = false;
          }});
          return updated;
        }} catch (err) {{
          set((state) => {{
            state.isLoading = false;
            state.error = (err as Error).message;
          }});
          return null;
        }}
      }},

      deleteItem: async (id) => {{
        set((state) => {{ state.isLoading = true; }});
        try {{
          await {camelName}Service.delete(id);
          set((state) => {{
            delete state.items[id];
            if (state.currentItemId === id) state.currentItemId = null;
            state.isLoading = false;
          }});
          return true;
        }} catch (err) {{
          set((state) => {{
            state.isLoading = false;
            state.error = (err as Error).message;
          }});
          return false;
        }}
      }},

      resetError: () => set((state) => {{ state.error = null; }}),
      setCurrentItem: (id) => set((state) => {{ state.currentItemId = id; }}),
    }})),
    {{ name: '{PascalName}Store' }}
  )
);

// Memoized Selectors (Best Practice to prevent re-renders)
export const selectIsLoading = (state: {PascalName}State) => state.isLoading;
export const selectError = (state: {PascalName}State) => state.error;
export const selectAllItems = (state: {PascalName}State) => Object.values(state.items);
export const selectCurrentItem = (state: {PascalName}State) =>
  state.currentItemId ? state.items[state.currentItemId] : null;
export const selectItemById = (id: string) => (state: {PascalName}State) => state.items[id] ?? null;
''',

    # Shared Layer
    "shared/hooks/use{PascalName}.ts": '''import {{ useEffect, useCallback }} from 'react';
import {{
  use{PascalName}Store,
  selectCurrentItem,
  selectAllItems,
  selectIsLoading,
  selectError,
}} from '../../infrastructure/stores/{feature}.store';

/**
 * use{PascalName} - Custom Hook to encapsulate {PascalName} state and logic.
 * This is the bridge between the Store and UI Components.
 */
export const use{PascalName} = (id?: string) => {{
  const item = use{PascalName}Store(selectCurrentItem);
  const isLoading = use{PascalName}Store(selectIsLoading);
  const error = use{PascalName}Store(selectError);
  const fetchById = use{PascalName}Store((state) => state.fetchById);

  useEffect(() => {{
    if (id && (!item || item.id !== id)) {{
      fetchById(id);
    }}
  }}, [id, fetchById]);

  return {{
    item,
    isLoading,
    error,
  }};
}};

/**
 * use{PascalName}List - Hook for list views.
 */
export const use{PascalName}List = () => {{
  const items = use{PascalName}Store(selectAllItems);
  const isLoading = use{PascalName}Store(selectIsLoading);
  const error = use{PascalName}Store(selectError);
  const fetchAll = use{PascalName}Store((state) => state.fetchAll);

  const refresh = useCallback(() => {{
    fetchAll();
  }}, [fetchAll]);

  useEffect(() => {{
    if (items.length === 0) {{
      fetchAll();
    }}
  }}, []);

  return {{
    items,
    isLoading,
    error,
    refresh,
  }};
}};
''',

    "shared/components/{PascalName}Card.tsx": '''import React, {{ memo }} from 'react';
import {{ Card, CardContent, Typography, Skeleton, Chip, Box }} from '@mui/material';
import {{ {PascalName} }} from '../../core/models/{feature}.model';

interface {PascalName}CardProps {{
  data: {PascalName};
  isLoading?: boolean;
  onClick?: () => void;
}}

/**
 * {PascalName}Card - Presentational Component.
 * Pure, no side effects, memoized for performance.
 */
export const {PascalName}Card: React.FC<{PascalName}CardProps> = memo(({{ data, isLoading, onClick }}) => {{
  if (isLoading) {{
    return <Skeleton variant="rectangular" height={{120}} sx={{{{ borderRadius: 2 }}}} />;
  }}

  const statusColor = data.status === 'active' ? 'success' : data.status === 'pending' ? 'warning' : 'default';

  return (
    <Card
      elevation={{2}}
      sx={{{{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'box-shadow 0.2s',
        '&:hover': onClick ? {{ boxShadow: 6 }} : {{}},
      }}}}
      onClick={{onClick}}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={{1}}>
          <Typography variant="h6" component="div">
            {{data.name}}
          </Typography>
          <Chip label={{data.status}} color={{statusColor}} size="small" />
        </Box>
        <Typography variant="body2" color="text.secondary">
          ID: {{data.id}}
        </Typography>
        <Typography variant="caption" display="block" mt={{1}}>
          Created: {{new Date(data.createdAt).toLocaleDateString()}}
        </Typography>
      </CardContent>
    </Card>
  );
}});

{PascalName}Card.displayName = '{PascalName}Card';
''',

    # App Layer
    "app/{PascalName}Layout.tsx": '''import React, {{ Suspense }} from 'react';
import {{ Outlet }} from 'react-router-dom';
import {{ Box, CircularProgress, Alert, Button }} from '@mui/material';
import {{ ErrorBoundary }} from 'react-error-boundary';

interface ErrorFallbackProps {{
  error: Error;
  resetErrorBoundary: () => void;
}}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({{ error, resetErrorBoundary }}) => {{
  return (
    <Box p={{3}}>
      <Alert
        severity="error"
        action={{
          <Button color="inherit" size="small" onClick={{resetErrorBoundary}}>
            Retry
          </Button>
        }}
      >
        <strong>Something went wrong in {PascalName} module:</strong>
        <pre style={{{{ fontSize: '0.75rem', marginTop: 8 }}}}>{{error.message}}</pre>
      </Alert>
    </Box>
  );
}};

const LoadingFallback: React.FC = () => (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight={{200}}>
    <CircularProgress />
  </Box>
);

/**
 * {PascalName}Layout - Feature Layout with ErrorBoundary and Suspense.
 * All {PascalName} routes are wrapped by this component.
 */
const {PascalName}Layout: React.FC = () => {{
  return (
    <ErrorBoundary FallbackComponent={{ErrorFallback}}>
      <Box sx={{{{ p: 3, height: '100%' }}}}>
        <Suspense fallback={{<LoadingFallback />}}>
          <Outlet />
        </Suspense>
      </Box>
    </ErrorBoundary>
  );
}};

export default {PascalName}Layout;
''',

    # Index exports
    "index.ts": '''// {PascalName} Feature Barrel Export
// Core
export * from './core/models/{feature}.model';
export * from './core/interfaces/{feature}.service.interface';
export * from './core/constants/{feature}.constants';

// Infrastructure
export {{ {camelName}Service }} from './infrastructure/services/{feature}.service';
export {{ use{PascalName}Store }} from './infrastructure/stores/{feature}.store';

// Shared
export {{ use{PascalName}, use{PascalName}List }} from './shared/hooks/use{PascalName}';
export {{ {PascalName}Card }} from './shared/components/{PascalName}Card';

// App
export {{ default as {PascalName}Layout }} from './app/{PascalName}Layout';
''',
}


def scaffold_feature(feature_name: str, base_path: str = ".") -> None:
    """Create all files for a new feature module."""
    # Normalize names
    name_lower = feature_name.lower().replace('-', '_')
    name_pascal = to_pascal_case(feature_name)
    name_camel = to_camel_case(feature_name)
    name_upper = name_lower.upper()
    name_kebab = name_lower.replace('_', '-')

    feature_dir = Path(base_path) / name_lower

    print(f"\n🚀 Scaffolding React feature: {name_pascal}")
    print(f"   Target directory: {feature_dir.absolute()}\n")

    # Create directories and files
    for template_path, template_content in TEMPLATES.items():
        # Replace placeholders in path
        file_path = template_path.format(
            feature=name_lower,
            PascalName=name_pascal,
        )
        full_path = feature_dir / file_path

        # Replace placeholders in content
        content = template_content.format(
            feature=name_lower,
            PascalName=name_pascal,
            camelName=name_camel,
            UPPER_NAME=name_upper,
            kebab_name=name_kebab,
        )

        # Create directory and file
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        print(f"  ✓ Created: {file_path}")

    print(f"\n✅ Feature '{name_pascal}' scaffolded successfully!")
    print("\nNext steps:")
    print(f"  1. Add routes to your main router (use lazy() for {name_pascal}Layout)")
    print(f"  2. Customize the Zod schema in core/models/{name_lower}.model.ts")
    print(f"  3. Update API endpoints in core/constants/{name_lower}.constants.ts")
    print(f"  4. Run `npx tsc` to verify TypeScript compilation")


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a React feature module following Clean Architecture"
    )
    parser.add_argument("feature_name", help="Name of the feature (snake_case or kebab-case)")
    parser.add_argument("--path", default=".", help="Base path to create feature in (default: current directory)")

    args = parser.parse_args()
    scaffold_feature(args.feature_name, args.path)


if __name__ == "__main__":
    main()
