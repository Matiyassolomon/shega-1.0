import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
    getArtistDashboard,
    getWallet,
    createPayoutRequest,
    getPayoutRequests,
    type ArtistDashboard,
    type Wallet,
    type PayoutRequest,
    type PayoutRequestCreate,
} from '../client';

export const useArtistDashboard = (userId: string) => {
    return useQuery({
        queryKey: ['artist-dashboard', userId],
        queryFn: async (): Promise<ArtistDashboard> => {
            return await getArtistDashboard(userId);
        },
        enabled: !!userId,
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};

export const useWallet = (userId: string) => {
    return useQuery({
        queryKey: ['wallet', userId],
        queryFn: async (): Promise<Wallet> => {
            return await getWallet(userId);
        },
        enabled: !!userId,
        staleTime: 2 * 60 * 1000, // 2 minutes
        gcTime: 5 * 60 * 1000, // 5 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};

export const usePayoutRequests = (userId: string) => {
    return useQuery({
        queryKey: ['payout-requests', userId],
        queryFn: async (): Promise<PayoutRequest[]> => {
            return await getPayoutRequests(userId);
        },
        enabled: !!userId,
        staleTime: 1 * 60 * 1000, // 1 minute
        gcTime: 5 * 60 * 1000, // 5 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};

export const useCreatePayoutRequest = (userId: string) => {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (request: PayoutRequestCreate): Promise<PayoutRequest> => {
            return await createPayoutRequest(userId, request);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['payout-requests', userId] });
            queryClient.invalidateQueries({ queryKey: ['wallet', userId] });
        },
    });
};
