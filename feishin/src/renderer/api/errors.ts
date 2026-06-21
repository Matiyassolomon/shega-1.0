import axios, { AxiosError } from 'axios';

import { logFn, LogCategory } from '/@/renderer/utils/logger';

export enum ApiErrorCode {
    UNAUTHORIZED = 'UNAUTHORIZED',
    FORBIDDEN = 'FORBIDDEN',
    NOT_FOUND = 'NOT_FOUND',
    RATE_LIMITED = 'RATE_LIMITED',
    SERVER_ERROR = 'SERVER_ERROR',
    NETWORK_ERROR = 'NETWORK_ERROR',
    UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

export interface ApiError {
    code: ApiErrorCode;
    message: string;
    originalError?: unknown;
    status?: number;
    retryable: boolean;
}

const ERROR_MESSAGES: Record<ApiErrorCode, string> = {
    [ApiErrorCode.UNAUTHORIZED]: 'Please log in to access this feature',
    [ApiErrorCode.FORBIDDEN]: 'You do not have permission to access this resource',
    [ApiErrorCode.NOT_FOUND]: 'The requested resource was not found',
    [ApiErrorCode.RATE_LIMITED]: 'Too many requests. Please try again later',
    [ApiErrorCode.SERVER_ERROR]: 'Server error. Please try again later',
    [ApiErrorCode.NETWORK_ERROR]: 'Network error. Please check your connection',
    [ApiErrorCode.UNKNOWN_ERROR]: 'An unexpected error occurred',
};

export const isAxiosError = (error: unknown): error is AxiosError => {
    return axios.isAxiosError(error);
};

export const classifyError = (error: unknown): ApiError => {
    if (isAxiosError(error)) {
        const status = error.response?.status;
        const url = error.config?.url;
        
        if (status === 401) {
            logFn.error('Unauthorized access attempt', {
                category: LogCategory.BACKEND,
                meta: { url, status },
            });
            return {
                code: ApiErrorCode.UNAUTHORIZED,
                message: ERROR_MESSAGES[ApiErrorCode.UNAUTHORIZED],
                originalError: error,
                status,
                retryable: false,
            };
        }
        
        if (status === 403) {
            logFn.error('Forbidden resource access', {
                category: LogCategory.BACKEND,
                meta: { url, status },
            });
            return {
                code: ApiErrorCode.FORBIDDEN,
                message: ERROR_MESSAGES[ApiErrorCode.FORBIDDEN],
                originalError: error,
                status,
                retryable: false,
            };
        }
        
        if (status === 404) {
            logFn.warn('Resource not found', {
                category: LogCategory.BACKEND,
                meta: { url, status },
            });
            return {
                code: ApiErrorCode.NOT_FOUND,
                message: ERROR_MESSAGES[ApiErrorCode.NOT_FOUND],
                originalError: error,
                status,
                retryable: false,
            };
        }
        
        if (status === 429) {
            logFn.warn('Rate limit exceeded', {
                category: LogCategory.BACKEND,
                meta: { url, status },
            });
            return {
                code: ApiErrorCode.RATE_LIMITED,
                message: ERROR_MESSAGES[ApiErrorCode.RATE_LIMITED],
                originalError: error,
                status,
                retryable: true,
            };
        }
        
        if (status && status >= 500) {
            logFn.error('Server error', {
                category: LogCategory.BACKEND,
                meta: { url, status },
            });
            return {
                code: ApiErrorCode.SERVER_ERROR,
                message: ERROR_MESSAGES[ApiErrorCode.SERVER_ERROR],
                originalError: error,
                status,
                retryable: true,
            };
        }
    }
    
    if (error instanceof Error) {
        if (error.message.includes('Network Error') || error.message.includes('ECONNREFUSED')) {
            logFn.error('Network error', {
                category: LogCategory.BACKEND,
                meta: { message: error.message },
            });
            return {
                code: ApiErrorCode.NETWORK_ERROR,
                message: ERROR_MESSAGES[ApiErrorCode.NETWORK_ERROR],
                originalError: error,
                retryable: true,
            };
        }
    }
    
    logFn.error('Unknown error', {
        category: LogCategory.BACKEND,
        meta: { error },
    });
    
    return {
        code: ApiErrorCode.UNKNOWN_ERROR,
        message: ERROR_MESSAGES[ApiErrorCode.UNKNOWN_ERROR],
        originalError: error,
        retryable: false,
    };
};

export const getErrorMessage = (error: ApiError): string => {
    return error.message;
};

export const isRetryable = (error: ApiError): boolean => {
    return error.retryable;
};

export const shouldRedirectToLogin = (error: ApiError): boolean => {
    return error.code === ApiErrorCode.UNAUTHORIZED;
};
