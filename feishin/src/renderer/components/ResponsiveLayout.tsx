// @ts-nocheck
import { useState, useEffect } from 'react';
import { isTelegramMiniApp } from '/@/renderer/utils/telegram';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { Card } from '/@/shared/components/card/card';

interface ResponsiveLayoutProps {
    children: React.ReactNode;
    title?: string;
    showBackButton?: boolean;
    onBackClick?: () => void;
}

export const ResponsiveLayout = ({ 
    children, 
    title, 
    showBackButton = false, 
    onBackClick 
}: ResponsiveLayoutProps) => {
    const [isMobile, setIsMobile] = useState(false);
    const [isTelegram, setIsTelegram] = useState(false);
    const [screenSize, setScreenSize] = useState({ width: 0, height: 0 });

    useEffect(() => {
        const checkDevice = () => {
            const width = window.innerWidth;
            const height = window.innerHeight;
            
            setIsMobile(width <= 768);
            setIsTelegram(isTelegramMiniApp());
            setScreenSize({ width, height });
        };

        checkDevice();
        window.addEventListener('resize', checkDevice);
        return () => window.removeEventListener('resize', checkDevice);
    }, []);

    // Telegram mini-app specific styling
    if (isTelegram) {
        return (
            <div style={{
                minHeight: '100vh',
                backgroundColor: '#ffffff',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                display: 'flex',
                flexDirection: 'column',
                maxWidth: '100vw',
                overflow: 'hidden'
            }}>
                {/* Telegram Header */}
                {(title || showBackButton) && (
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        padding: '12px 16px',
                        backgroundColor: '#ffffff',
                        borderBottom: '1px solid #e1e5e9',
                        position: 'sticky',
                        top: 0,
                        zIndex: 100
                    }}>
                        {showBackButton && (
                            <button
                                onClick={onBackClick}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    fontSize: '24px',
                                    cursor: 'pointer',
                                    marginRight: '12px',
                                    padding: '4px',
                                    borderRadius: '8px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center'
                                }}
                            >
                                ←
                            </button>
                        )}
                        {title && (
                            <Text 
                                size="lg" 
                                weight="bold"
                                style={{ 
                                    color: '#1f2937',
                                    margin: 0,
                                    flex: 1
                                }}
                            >
                                {title}
                            </Text>
                        )}
                    </div>
                )}
                
                {/* Content */}
                <div style={{
                    flex: 1,
                    overflow: 'auto',
                    padding: '16px',
                    maxWidth: '100%',
                    boxSizing: 'border-box'
                }}>
                    {children}
                </div>
            </div>
        );
    }

    // Mobile responsive layout
    if (isMobile) {
        return (
            <div style={{
                minHeight: '100vh',
                backgroundColor: '#f8fafc',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            }}>
                {/* Mobile Header */}
                {(title || showBackButton) && (
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        padding: '16px 20px',
                        backgroundColor: '#ffffff',
                        borderBottom: '1px solid #e5e7eb',
                        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                        position: 'sticky',
                        top: 0,
                        zIndex: 100
                    }}>
                        {showBackButton && (
                            <button
                                onClick={onBackClick}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    fontSize: '20px',
                                    cursor: 'pointer',
                                    marginRight: '12px',
                                    padding: '8px',
                                    borderRadius: '8px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    backgroundColor: '#f3f4f6'
                                }}
                            >
                                ←
                            </button>
                        )}
                        {title && (
                            <Text 
                                size="lg" 
                                weight="bold"
                                style={{ 
                                    color: '#111827',
                                    margin: 0,
                                    flex: 1
                                }}
                            >
                                {title}
                            </Text>
                        )}
                    </div>
                )}
                
                {/* Mobile Content */}
                <div style={{
                    padding: '20px',
                    maxWidth: '100%',
                    boxSizing: 'border-box'
                }}>
                    {children}
                </div>
            </div>
        );
    }

    // Desktop layout
    return (
        <div style={{
            minHeight: '100vh',
            backgroundColor: '#f1f5f9',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }}>
            {/* Desktop Header */}
            {(title || showBackButton) && (
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '20px 40px',
                    backgroundColor: '#ffffff',
                    borderBottom: '1px solid #e2e8f0',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                }}>
                    {showBackButton && (
                        <button
                            onClick={onBackClick}
                            style={{
                                background: 'none',
                                border: '1px solid #d1d5db',
                                fontSize: '16px',
                                cursor: 'pointer',
                                marginRight: '16px',
                                padding: '8px 16px',
                                borderRadius: '8px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                backgroundColor: '#ffffff',
                                transition: 'all 0.2s ease'
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.backgroundColor = '#f9fafb';
                                e.currentTarget.style.borderColor = '#9ca3af';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.backgroundColor = '#ffffff';
                                e.currentTarget.style.borderColor = '#d1d5db';
                            }}
                        >
                            ← Back
                        </button>
                    )}
                    {title && (
                        <Text 
                            size="xl" 
                            weight="bold"
                            style={{ 
                                color: '#1f2937',
                                margin: 0,
                                flex: 1
                            }}
                        >
                            {title}
                        </Text>
                    )}
                </div>
            )}
            
            {/* Desktop Content */}
            <div style={{
                padding: '40px',
                maxWidth: '1200px',
                margin: '0 auto',
                boxSizing: 'border-box'
            }}>
                {children}
            </div>
        </div>
    );
};

// Responsive grid component
export const ResponsiveGrid = ({ 
    children, 
    columns = { mobile: 1, tablet: 2, desktop: 3 },
    gap = '20px'
}: {
    children: React.ReactNode;
    columns?: { mobile: number; tablet: number; desktop: number };
    gap?: string;
}) => {
    const [isMobile, setIsMobile] = useState(false);
    const [isTablet, setIsTablet] = useState(false);

    useEffect(() => {
        const checkDevice = () => {
            const width = window.innerWidth;
            setIsMobile(width <= 768);
            setIsTablet(width > 768 && width <= 1024);
        };

        checkDevice();
        window.addEventListener('resize', checkDevice);
        return () => window.removeEventListener('resize', checkDevice);
    }, []);

    const getColumns = () => {
        if (isMobile) return columns.mobile;
        if (isTablet) return columns.tablet;
        return columns.desktop;
    };

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${getColumns()}, 1fr)`,
            gap: gap,
            width: '100%'
        }}>
            {children}
        </div>
    );
};

// Responsive card component
export const ResponsiveCard = ({ 
    children, 
    title, 
    subtitle,
    onClick,
    style = {}
}: {
    children: React.ReactNode;
    title?: string;
    subtitle?: string;
    onClick?: () => void;
    style?: React.CSSProperties;
}) => {
    const [isMobile, setIsMobile] = useState(false);
    const [isTelegram, setIsTelegram] = useState(false);

    useEffect(() => {
        const checkDevice = () => {
            setIsMobile(window.innerWidth <= 768);
            setIsTelegram(isTelegramMiniApp());
        };

        checkDevice();
        window.addEventListener('resize', checkDevice);
        return () => window.removeEventListener('resize', checkDevice);
    }, []);

    const baseStyle: React.CSSProperties = {
        backgroundColor: '#ffffff',
        borderRadius: isTelegram ? '12px' : '8px',
        padding: isMobile ? '16px' : '24px',
        boxShadow: isTelegram 
            ? '0 2px 8px rgba(0, 0, 0, 0.08)'
            : isMobile 
                ? '0 1px 3px rgba(0, 0, 0, 0.1)'
                : '0 4px 6px rgba(0, 0, 0, 0.1)',
        border: isTelegram ? '1px solid #e5e7eb' : 'none',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease',
        ...style
    };

    return (
        <div
            style={baseStyle}
            onClick={onClick}
            onMouseOver={(e) => {
                if (onClick) {
                    e.currentTarget.style.transform = isMobile ? 'scale(1.02)' : 'scale(1.01)';
                    e.currentTarget.style.boxShadow = isTelegram 
                        ? '0 4px 12px rgba(0, 0, 0, 0.12)'
                        : '0 6px 12px rgba(0, 0, 0, 0.15)';
                }
            }}
            onMouseOut={(e) => {
                if (onClick) {
                    e.currentTarget.style.transform = 'scale(1)';
                    e.currentTarget.style.boxShadow = baseStyle.boxShadow;
                }
            }}
        >
            {title && (
                <Text 
                    size={isMobile ? "md" : "lg"} 
                    weight="bold" 
                    style={{ 
                        marginBottom: subtitle ? '4px' : '16px',
                        color: '#1f2937'
                    }}
                >
                    {title}
                </Text>
            )}
            {subtitle && (
                <Text 
                    size="sm" 
                    style={{ 
                        marginBottom: '16px',
                        color: '#6b7280'
                    }}
                >
                    {subtitle}
                </Text>
            )}
            {children}
        </div>
    );
};

// Responsive button component
export const ResponsiveButton = ({ 
    children, 
    onClick, 
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    fullWidth = false,
    style = {}
}: {
    children: React.ReactNode;
    onClick?: () => void;
    variant?: 'primary' | 'secondary' | 'outline';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    loading?: boolean;
    fullWidth?: boolean;
    style?: React.CSSProperties;
}) => {
    const [isMobile, setIsMobile] = useState(false);
    const [isTelegram, setIsTelegram] = useState(false);

    useEffect(() => {
        const checkDevice = () => {
            setIsMobile(window.innerWidth <= 768);
            setIsTelegram(isTelegramMiniApp());
        };

        checkDevice();
        window.addEventListener('resize', checkDevice);
        return () => window.removeEventListener('resize', checkDevice);
    }, []);

    const getStyles = () => {
        const baseStyles = {
            border: 'none',
            borderRadius: isTelegram ? '12px' : '8px',
            cursor: disabled || loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            fontFamily: 'inherit',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            opacity: disabled ? 0.6 : 1,
            ...style
        };

        const sizeStyles = {
            sm: {
                padding: isMobile ? '8px 12px' : '6px 12px',
                fontSize: isMobile ? '14px' : '12px',
                minHeight: isMobile ? '36px' : '32px'
            },
            md: {
                padding: isMobile ? '12px 20px' : '10px 20px',
                fontSize: isMobile ? '16px' : '14px',
                minHeight: isMobile ? '44px' : '40px'
            },
            lg: {
                padding: isMobile ? '16px 24px' : '14px 24px',
                fontSize: isMobile ? '18px' : '16px',
                minHeight: isMobile ? '52px' : '48px'
            }
        };

        const variantStyles = {
            primary: {
                backgroundColor: '#1DB954',
                color: '#ffffff',
            },
            secondary: {
                backgroundColor: '#f3f4f6',
                color: '#374151',
            },
            outline: {
                backgroundColor: 'transparent',
                color: '#1DB954',
                border: '2px solid #1DB954'
            }
        };

        return {
            ...baseStyles,
            ...sizeStyles[size],
            ...variantStyles[variant],
            width: fullWidth ? '100%' : 'auto'
        };
    };

    return (
        <button
            style={getStyles()}
            onClick={onClick}
            disabled={disabled || loading}
        >
            {loading && (
                <div style={{
                    width: '16px',
                    height: '16px',
                    border: '2px solid transparent',
                    borderTop: '2px solid currentColor',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                }} />
            )}
            {children}
        </button>
    );
};
