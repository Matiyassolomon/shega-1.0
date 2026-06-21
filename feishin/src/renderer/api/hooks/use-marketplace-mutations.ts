import { useMutation, useQueryClient } from '@tanstack/react-query';

import {
    purchasePlaylist,
    purchaseSong,
    savePlaylist,
    getSecurePlaylistAccess,
    getSecureSongAccess,
} from '../client';
import { getBackendUserId } from '../client';

export const usePurchasePlaylist = () => {
    const queryClient = useQueryClient();
    const userId = getBackendUserId();

    return useMutation({
        mutationFn: async (playlistId: string) => {
            if (!userId) {
                throw new Error('User not authenticated');
            }
            return await purchasePlaylist(userId, playlistId);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['marketplace-playlists'] });
            queryClient.invalidateQueries({ queryKey: ['user-profile'] });
        },
    });
};

export const usePurchaseSong = () => {
    const queryClient = useQueryClient();
    const userId = getBackendUserId();

    return useMutation({
        mutationFn: async (songId: string) => {
            if (!userId) {
                throw new Error('User not authenticated');
            }
            return await purchaseSong(userId, songId);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['marketplace-songs'] });
            queryClient.invalidateQueries({ queryKey: ['user-profile'] });
        },
    });
};

export const useSavePlaylist = () => {
    const queryClient = useQueryClient();
    const userId = getBackendUserId();

    return useMutation({
        mutationFn: async (playlistId: string) => {
            if (!userId) {
                throw new Error('User not authenticated');
            }
            return await savePlaylist(userId, playlistId);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['marketplace-playlists'] });
        },
    });
};

export const useSecurePlaylistAccess = () => {
    const userId = getBackendUserId();

    return useMutation({
        mutationFn: async (playlistId: string) => {
            if (!userId) {
                throw new Error('User not authenticated');
            }
            return await getSecurePlaylistAccess(userId, playlistId);
        },
    });
};

export const useSecureSongAccess = () => {
    const userId = getBackendUserId();

    return useMutation({
        mutationFn: async (songId: string) => {
            if (!userId) {
                throw new Error('User not authenticated');
            }
            return await getSecureSongAccess(userId, songId);
        },
    });
};
