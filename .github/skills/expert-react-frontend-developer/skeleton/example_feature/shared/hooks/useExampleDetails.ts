import { useEffect } from 'react';
import { useExampleStore, selectCurrentItem, selectIsLoading, selectError } from '../../infrastructure/stores/example.store';
import { useShallow } from 'zustand/react/shallow';

// Custom Hook to encapsulate State and Logic
export const useExampleDetails = (id?: string) => {
    // Use shallow comparison for object selection if needed, or specific selectors
    const item = useExampleStore(selectCurrentItem);
    const isLoading = useExampleStore(selectIsLoading);
    const error = useExampleStore(selectError);
    const fetchById = useExampleStore((state) => state.fetchById);

    useEffect(() => {
        if (id && (!item || item.id !== id)) {
            fetchById(id);
        }
    }, [id, fetchById]); // 'item' excluded to avoid infinite loop if reference changes

    return {
        item,
        isLoading,
        error,
    };
};
