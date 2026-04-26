// @ts-nocheck
import { useState } from 'react';
import { Button } from '/@/shared/components/button/button';
import { Stack } from '/@/shared/components/stack/stack';
import { Text } from '/@/shared/components/text/text';
import { Card } from '/@/shared/components/card/card';
import { Icon } from '/@/shared/components/icon/icon';
import { toast } from '/@/shared/components/toast/toast';

interface BackendErrorPageProps {
    onRetry?: () => void;
    error?: string;
}

const BackendErrorPage = ({ onRetry, error }: BackendErrorPageProps) => {
    const [isRetrying, setIsRetrying] = useState(false);

    const handleRetry = async () => {
        setIsRetrying(true);
        try {
            await onRetry?.();
            toast.success({
                message: 'Backend connection restored!',
            });
        } catch (err) {
            toast.error({
                message: 'Backend still not available. Please check the server.',
            });
        } finally {
            setIsRetrying(false);
        }
    };

    const handleOpenConfig = () => {
        // Open configuration page in new window
        window.open('/configure-feishin.html', '_blank');
    };

    return (
        <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            minHeight: '100vh',
            padding: '20px',
            backgroundColor: '#f5f5f5'
        }}>
            <Card style={{ 
                maxWidth: '600px', 
                width: '100%', 
                padding: '40px',
                textAlign: 'center',
                backgroundColor: 'white'
            }}>
                <Stack spacing="xl">
                    {/* Error Icon */}
                    <div style={{ fontSize: '64px', textAlign: 'center' }}>
                        🚫
                    </div>

                    {/* Error Title */}
                    <Text size="xl" weight="bold" color="error">
                        Backend Connection Error
                    </Text>

                    {/* Error Description */}
                    <Text color="dimmed" size="lg">
                        The music platform backend is not accessible. This could be because:
                    </Text>

                    {/* Possible Reasons */}
                    <Stack spacing="md" style={{ textAlign: 'left' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <Icon name="x-circle" color="error" size="sm" />
                            <Text size="sm">Backend server is not running</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <Icon name="x-circle" color="error" size="sm" />
                            <Text size="sm">Network connectivity issues</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <Icon name="x-circle" color="error" size="sm" />
                            <Text size="sm">Incorrect server configuration</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <Icon name="x-circle" color="error" size="sm" />
                            <Text size="sm">Backend running on different port</Text>
                        </div>
                    </Stack>

                    {/* Error Details */}
                    {error && (
                        <Card style={{ 
                            backgroundColor: '#fff5f5', 
                            padding: '15px',
                            textAlign: 'left',
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            color: '#666'
                        }}>
                            <Text size="sm" weight="bold">Error Details:</Text>
                            <Text size="sm">{error}</Text>
                        </Card>
                    )}

                    {/* Solution Steps */}
                    <Card style={{ backgroundColor: '#f0f9ff', padding: '20px', textAlign: 'left' }}>
                        <Text weight="bold" size="md" style={{ marginBottom: '10px' }}>Quick Solutions:</Text>
                        <Stack spacing="sm">
                            <Text size="sm">1. Start the backend server:</Text>
                            <div style={{ 
                                backgroundColor: '#f5f5f5', 
                                padding: '10px', 
                                borderRadius: '4px', 
                                fontFamily: 'monospace', 
                                fontSize: '12px',
                                marginBottom: '10px'
                            }}>
                                cd backend<br />
                                uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
                            </div>
                            
                            <Text size="sm">2. Configure Feishin to connect to the backend:</Text>
                            <div style={{ marginBottom: '10px' }}>
                                <Button size="sm" onClick={handleOpenConfig}>
                                    Open Configuration Tool
                                </Button>
                            </div>
                            
                            <Text size="sm">3. Check if backend is running on port 8000</Text>
                        </Stack>
                    </Card>

                    {/* Action Buttons */}
                    <Stack spacing="md" direction="row" justify="center">
                        <Button onClick={handleRetry} loading={isRetrying}>
                            Retry Connection
                        </Button>
                        <Button variant="outline" onClick={handleOpenConfig}>
                            Configure Server
                        </Button>
                    </Stack>

                    {/* Help Text */}
                    <Text size="sm" color="dimmed">
                        If you continue to experience issues, please check the backend logs and ensure all dependencies are installed.
                    </Text>
                </Stack>
            </Card>
        </div>
    );
};

export default BackendErrorPage;
