import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router';

import {
    clearBackendAuth,
    getBackendUserId,
    getBackendAccessToken,
    isBackendAuthenticated,
    setBackendUserId,
    setBackendAccessToken,
} from '/@/renderer/api/client';
import { AppRoute } from '/@/renderer/router/routes';

export interface BackendAuthState {
    userId: string | null;
    accessToken: string | null;
    isAuthenticated: boolean;
}

export const useBackendAuth = () => {
    const navigate = useNavigate();
    const [authState, setAuthState] = useState<BackendAuthState>({
        userId: getBackendUserId(),
        accessToken: getBackendAccessToken(),
        isAuthenticated: isBackendAuthenticated(),
    });

    const login = useCallback((userId: string, accessToken: string) => {
        setBackendUserId(userId);
        setBackendAccessToken(accessToken);
        setAuthState({
            userId,
            accessToken,
            isAuthenticated: true,
        });
    }, []);

    const logout = useCallback(() => {
        clearBackendAuth();
        setAuthState({
            userId: null,
            accessToken: null,
            isAuthenticated: false,
        });
        navigate(AppRoute.LOGIN);
    }, [navigate]);

    const refreshAuthState = useCallback(() => {
        setAuthState({
            userId: getBackendUserId(),
            accessToken: getBackendAccessToken(),
            isAuthenticated: isBackendAuthenticated(),
        });
    }, []);

    useEffect(() => {
        const handleStorageChange = (e: StorageEvent) => {
            if (
                e.key === 'backend-user-id' ||
                e.key === 'backend-access-token'
            ) {
                refreshAuthState();
            }
        };

        window.addEventListener('storage', handleStorageChange);
        return () => {
            window.removeEventListener('storage', handleStorageChange);
        };
    }, [refreshAuthState]);

    return {
        ...authState,
        login,
        logout,
        refreshAuthState,
    };
};

export const requireBackendAuth = () => {
    const auth = useBackendAuth();
    
    useEffect(() => {
        if (!auth.isAuthenticated) {
            auth.logout();
        }
    }, [auth.isAuthenticated, auth.logout]);

    return auth;
};
