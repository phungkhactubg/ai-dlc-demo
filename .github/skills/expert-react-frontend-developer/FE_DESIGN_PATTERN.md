# Workflow Frontend Design Patterns

## I. Architecture Overview

This document describes the architecture and design patterns used in the refactored Workflow Frontend module.

---

## 1. Feature-Based Architecture

The codebase follows a **Feature-Based Architecture** with **Clean Architecture** principles.

### Directory Structure

```
apps/frontend/src/workflow/
├── core/                    # Domain layer (business rules)
│   ├── models/              # Domain entities
│   ├── interfaces/          # Contracts/ports
│   └── constants/           # Business constants
│
├── infrastructure/          # Technical implementation
│   ├── api/                 # HTTP clients
│   ├── stores/              # State management
│   ├── services/            # Service implementations
│   └── workers/             # Web Workers
│
├── shared/                  # Reusable code
│   ├── components/          # UI components (Atomic Design)
│   ├── hooks/               # Custom React hooks
│   └── utils/               # Utility functions
│
├── features/                # Feature modules
│   ├── canvas/              # Canvas feature
│   ├── nodes/               # Node system
│   ├── properties/          # Properties panel
│   ├── execution/           # Execution system
│   ├── collaboration/       # Real-time collaboration
│   └── ai-assistant/        # AI features
│
└── app/                     # Application layer
    └── WorkflowDesignerNew  # Main component
```

---

## 2. Design Patterns Used

### 2.1 Clean Architecture (Dependency Inversion)

Interfaces are defined in `core/interfaces/`, implementations in `infrastructure/services/`.

```typescript
// core/interfaces/workflow-service.interface.ts
export interface IWorkflowService {
  getById(id: string): Promise<Workflow>;
  save(id: string, data: unknown): Promise<void>;
}

// infrastructure/services/workflow.service.ts
export class WorkflowService implements IWorkflowService {
  async getById(id: string): Promise<Workflow> { ... }
  async save(id: string, data: unknown): Promise<void> { ... }
}
```

### 2.2 Atomic Design (UI Components)

Components organized by complexity:
- **Atoms**: Basic building blocks (Button, Input)
- **Molecules**: Combinations of atoms
- **Organisms**: Complex UI sections
- **Templates**: Page layouts
- **Pages**: Route components

### 2.3 Container/Presentational Pattern

```typescript
// Container (business logic)
export function WorkflowCanvas({ workflowId }: Props) {
  const { nodes, edges } = useWorkflow();
  return <CanvasView nodes={nodes} edges={edges} />;
}

// Presentational (UI only)
export function CanvasView({ nodes, edges }: ViewProps) {
  return <ReactFlow nodes={nodes} edges={edges} />;
}
```

### 2.4 Command Pattern (Undo/Redo)

```typescript
interface Command {
  id: string;
  execute(): void;
  undo(): void;
}

// Usage
const command = createNodeMoveCommand(nodeId, oldPos, newPos);
undoRedoStore.pushCommand(command);
```

### 2.5 Factory Pattern (Node Creation)

```typescript
// Node Registry Service
nodeRegistryService.register({
  type: 'trigger.webhook',
  label: 'Webhook',
  factory: (id) => createWebhookNode(id),
});

const node = nodeRegistryService.create('trigger.webhook');
```

### 2.6 Observer Pattern (Event System)

```typescript
// Execution service events
executionService.on('execution:progress', (event) => {
  updateUI(event.data);
});

executionService.on('execution:completed', (event) => {
  showNotification('Workflow completed!');
});
```

---

## 3. State Management

### 3.1 Zustand Store Structure

```typescript
// Root store with slices
const useRootStore = create<RootState>()(
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        canvas: { viewport, mode, showGrid },
        workflow: { nodes, edges, currentWorkflowId },
        selection: { selectedNodeIds, selectedEdgeIds },
        execution: { isExecuting, executionState },
        ui: { isPaletteOpen, isPropertiesOpen },
        // Actions...
      }))
    )
  )
);
```

### 3.2 Selectors

```typescript
// Memoized selectors
export const selectCanvas = (state: RootState) => state.canvas;
export const selectSelectedNodes = (state: RootState) => 
  state.selection.selectedNodeIds.map(id => state.workflow.nodes.get(id));
```

---

## 4. Hooks API

### Core Hooks

| Hook | Purpose |
|------|---------|
| `useWorkflow` | Workflow data access |
| `useSelection` | Selection management |
| `useCanvas` | Canvas viewport/mode |
| `useExecution` | Execution control |
| `useCollaboration` | Real-time collab |
| `useKeyboardShortcuts` | Keyboard handling |

### Example Usage

```typescript
function MyComponent() {
  const { nodes, addNode, updateNode } = useWorkflow();
  const { selectedNodeIds, selectNodes } = useSelection();
  const { execute, isExecuting, progress } = useExecution();
  
  // ...
}
```

---

## 5. Performance Optimization

### 5.1 Code Splitting

```typescript
// Lazy load features
const LazyPropertiesPanel = lazy(
  () => import('./features/properties/components/PropertiesPanel')
);

// With Suspense
<Suspense fallback={<Loading />}>
  <LazyPropertiesPanel />
</Suspense>
```

### 5.2 Virtual Scrolling

```typescript
// For large lists
const { items, totalHeight, handleScroll } = useVirtualScroll(data, {
  itemCount: 1000,
  itemHeight: 40,
  containerHeight: 400,
});
```

### 5.3 Memoization

```typescript
// Deep comparison memo
const memoizedValue = useDeepMemo(() => computeExpensive(data), [data]);

// Debounced callbacks
const debouncedSearch = useDebouncedCallback(handleSearch, 300);

// Throttled callbacks  
const throttledScroll = useThrottledCallback(handleScroll, 16);
```

### 5.4 Web Workers

Heavy computations offloaded to workers:
- Auto-layout algorithm
- Graph validation
- Cycle detection
- Diff computation

# II. Quy tắc trong quá trình code Frontend:
- Repo của tôi đang được phát triển theo chuẩn Component Based Architecture.
- Source FE đang được phát triển bằng React 18+, TypeScript.
- Không tự ý tạo tài liệu nếu tôi không yêu cầu.
- Không tự ý add, commit, push code nếu tôi không yêu cầu.
- Hãy tuyệt đối tuân thủ thực hiện những công việc mà tôi yêu cầu bạn làm (trong quá trình thực hiện bạn vẫn có thể lên plan nhỏ chi tiết cho từng yêu cầu của tôi).
- Bạn có thể sử dụng Context7 và Internet để tham khảo tài liệu mới nhất về các công nghệ, framework, thư viện, best practices mà tôi yêu cầu bạn sử dụng hoặc tham khảo các best practices mới nhất hoặc sử dụng nó trong quá trình xây dựng giải pháp, kiến trúc.
- Không tạo Unit Test, Integration Test, E2E Test,... nếu tôi không yêu cầu.
- Bạn được quyền sử dụng các lệnh trên Terminal mà không cần phải hỏi ý kiến tôi hoặc chờ tôi xác nhận.
- Tôi muốn mọi thư viện được sử dụng trong repo phải luôn là latest version và không bị deprecated, luôn sử dụng các thư viện chính thức của các công nghệ, framework ở phiên bản stable nhất (không sử dụng các phiên bản alpha, beta, test,...).