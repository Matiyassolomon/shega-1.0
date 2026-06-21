import { useQuery } from '@tanstack/react-query';

import {
    getAdminDashboard,
    getAdminUsers,
    getAdminArtists,
    getAdminPayments,
    type AdminDashboard,
    type AdminUsersResponse,
    type AdminArtistsResponse,
    type AdminPaymentsResponse,
} from '../client';

export const useAdminDashboard = () => {
    return useQuery({
        queryKey: ['admin-dashboard'],
        queryFn: async (): Promise<AdminDashboard> => {
            return await getAdminDashboard();
        },
        staleTime: 2 * 60 * 1000, // 2 minutes
        gcTime: 5 * 60 * 1000, // 5 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};

export const useAdminUsers = (limit: number = 20, offset: number = 0) => {
    return useQuery({
        queryKey: ['admin-users', limit, offset],
        queryFn: async (): Promise<AdminUsersResponse> => {
            return await getAdminUsers(limit, offset);
        },
        staleTime: 1 * 60 * 1000, // 1 minute
        gcTime: 5 * 60 * 1000, // 5 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};

export const useAdminArtists = (limit: number = 20, offset: number = 0) => {
    return useQuery({
        queryKey: ['admin-artists', limit, offset],
        queryFn: async (): Promise<AdminArtistsResponse> => {
            return await getAdminArtists(limit, offset);
        },
        staleTime: 1 * 60 * 1000, // 1 minute
        gcTime: 5 * 60 * 1000, // 5 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};

export const useAdminPayments = (
    limit: number = 20,
    offset: number = 0,
    status?: string,
) => {
    return useQuery({
        queryKey: ['admin-payments', limit, offset, status],
        queryFn: async (): Promise<AdminPaymentsResponse> => {
            return await getAdminPayments(limit, offset, status);
        },
        staleTime: 1 * 60 * 1000, // 1 minute
        gcTime: 5 * 60 * 1000, // 5 minutes
        retry: 1,
        refetchOnWindowFocus: false,
    });
};
