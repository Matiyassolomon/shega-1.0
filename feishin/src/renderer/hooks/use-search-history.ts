import { useEffect, useState } from 'react';

const SEARCH_HISTORY_KEY = 'search-history';
const MAX_HISTORY_ITEMS = 10;

interface SearchHistoryItem {
    query: string;
    timestamp: number;
}

export function useSearchHistory() {
    const [history, setHistory] = useState<SearchHistoryItem[]>([]);

    useEffect(() => {
        try {
            const stored = localStorage.getItem(SEARCH_HISTORY_KEY);
            if (stored) {
                setHistory(JSON.parse(stored));
            }
        } catch (error) {
            console.error('Failed to load search history:', error);
        }
    }, []);

    const addToHistory = (query: string) => {
        if (!query.trim()) return;

        const newItem: SearchHistoryItem = {
            query: query.trim(),
            timestamp: Date.now(),
        };

        setHistory((prev) => {
            // Remove if already exists
            const filtered = prev.filter((item) => item.query !== newItem.query);
            // Add new item at the beginning
            const updated = [newItem, ...filtered].slice(0, MAX_HISTORY_ITEMS);
            
            try {
                localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(updated));
            } catch (error) {
                console.error('Failed to save search history:', error);
            }
            
            return updated;
        });
    };

    const clearHistory = () => {
        setHistory([]);
        try {
            localStorage.removeItem(SEARCH_HISTORY_KEY);
        } catch (error) {
            console.error('Failed to clear search history:', error);
        }
    };

    const removeFromHistory = (query: string) => {
        setHistory((prev) => {
            const updated = prev.filter((item) => item.query !== query);
            try {
                localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(updated));
            } catch (error) {
                console.error('Failed to update search history:', error);
            }
            return updated;
        });
    };

    return {
        history,
        addToHistory,
        clearHistory,
        removeFromHistory,
    };
}
