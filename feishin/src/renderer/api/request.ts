import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';

import {
    backendClient,
    getBackendAccessToken,
    BACKEND_ACCESS_TOKEN_STORAGE_KEY,
    BACKEND_USER_ID_STORAGE_KEY,
} from './client';
import {
    ApiError,
    classifyError,
    getErrorMessage,
    isRetryable,
    shouldRedirectToLogin,
} from './errors';

export interface RequestConfig extends AxiosRequestConfig {
    skipAuthRedirect?: boolean;
    maxRetries?: number;
    retryDelay?: number;
}

const DEFAULT_MAX_RETRIES = 3;
const DEFAULT_RETRY_DELAY = 1000;

const sleep = (ms: number): Promise<void> => {
    return new Promise((resolve) => setTimeout(resolve, ms));
};

export const executeRequest = async <T = unknown>(
    config: RequestConfig,
): Promise<T> => {
    const {
        skipAuthRedirect = false,
        maxRetries = DEFAULT_MAX_RETRIES,
        retryDelay = DEFAULT_RETRY_DELAY,
        ...axiosConfig
    } = config;

    let lastError: ApiError | null = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const response: AxiosResponse<T> = await backendClient.request<T>(axiosConfig);
            return response.data;
        } catch (error) {
            const apiError = classifyError(error);
            lastError = apiError;

            if (!isRetryable(apiError) || attempt === maxRetries) {
                if (!skipAuthRedirect && shouldRedirectToLogin(apiError)) {
                    handleUnauthorized();
                }
                throw apiError;
            }

            await sleep(retryDelay * (attempt + 1));
        }
    }

    throw lastError;
};

export const executeRequestWithAuth = async <T = unknown>(
    config: RequestConfig,
): Promise<T> => {
    const token = getBackendAccessToken();
    const userId = localStorage.getItem(BACKEND_USER_ID_STORAGE_KEY);

    if (!token || !userId) {
        const error: ApiError = {
            code: 'UNAUTHORIZED' as const,
            message: 'Authentication required',
            retryable: false,
        };
        
        if (!config.skipAuthRedirect) {
            handleUnauthorized();
        }
        
        throw error;
    }

    return executeRequest<T>({
        ...config,
        headers: {
            ...config.headers,
            Authorization: `Bearer ${token}`,
        },
    });
};

const handleUnauthorized = (): void => {
    localStorage.removeItem(BACKEND_USER_ID_STORAGE_KEY);
    localStorage.removeItem(BACKEND_ACCESS_TOKEN_STORAGE_KEY);
    
    if (typeof window !== 'undefined') {
        window.location.href = '/login';
    }
};

export const createApiHook = <T = unknown, P = unknown>(
    queryFn: (params: P) => Promise<T>,
) => {
    return async (params: P): Promise<T> => {
        try {
            return await queryFn(params);
        } catch (error) {
            const apiError = classifyError(error);
            throw apiError;
        }
    };
};

export const wrapApiCall = async <T = unknown>(
    apiCall: () => Promise<T>,
    options?: { skipAuthRedirect?: boolean },
): Promise<T> => {
    try {
        return await apiCall();
    } catch (error) {
        const apiError = classifyError(error);
        
        if (!options?.skipAuthRedirect && shouldRedirectToLogin(apiError)) {
            handleUnauthorized();
        }
        
        throw apiError;
    }
};
