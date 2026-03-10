import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import { Example } from '../../core/models/example.model';
import { exampleService } from '../services/example.service';

interface ExampleState {
    items: Record<string, Example>;
    currentItemId: string | null;
    isLoading: boolean;
    error: string | null;
}

interface ExampleActions {
    fetchById: (id: string) => Promise<void>;
    createItem: (data: any) => Promise<void>;
    resetError: () => void;
}

// Zustand Store with Immer for mutability and Devtools for debugging
export const useExampleStore = create<ExampleState & ExampleActions>()(
    devtools(
        immer((set) => ({
            // State
            items: {},
            currentItemId: null,
            isLoading: false,
            error: null,

            // Actions
            fetchById: async (id: string) => {
                set((state) => { state.isLoading = true; state.error = null; });
                try {
                    const data = await exampleService.getById(id);
                    set((state) => {
                        state.items[data.id] = data; // Normalized state
                        state.currentItemId = data.id;
                        state.isLoading = false;
                    });
                } catch (err) {
                    set((state) => {
                        state.isLoading = false;
                        state.error = (err as Error).message;
                    });
                }
            },

            createItem: async (data) => {
                set((state) => { state.isLoading = true; });
                try {
                    const newItem = await exampleService.create(data);
                    set((state) => {
                        state.items[newItem.id] = newItem;
                        state.isLoading = false;
                    });
                } catch (err) {
                    set((state) => {
                        state.isLoading = false;
                        state.error = (err as Error).message;
                    });
                }
            },

            resetError: () => set((state) => { state.error = null; }),
        }))
    )
);

// Memoized Selectors (Best Practice to prevent re-renders)
export const selectIsLoading = (state: ExampleState) => state.isLoading;
export const selectError = (state: ExampleState) => state.error;
export const selectCurrentItem = (state: ExampleState) =>
    state.currentItemId ? state.items[state.currentItemId] : null;
