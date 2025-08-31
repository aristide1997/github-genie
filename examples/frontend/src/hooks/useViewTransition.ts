import { useCallback } from 'react';

// Custom hook for View Transitions API with fallback
export const useViewTransition = () => {
    const startTransition = useCallback(async (callback: () => void): Promise<void> => {
        const supportsVT = typeof document.startViewTransition === 'function' &&
            !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        if (supportsVT) {
            try {
                await document.startViewTransition(callback)?.finished;
                return;
            } catch (e) {
                // Fall back to regular callback
                console.warn('View Transition failed, falling back:', e);
            }
        }

        // Fallback: just execute the callback
        callback();
    }, []);

    return { startTransition };
};
