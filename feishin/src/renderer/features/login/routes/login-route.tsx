import isElectron from 'is-electron';
import { nanoid } from 'nanoid/non-secure';
import { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router';

import styles from './login-route.module.css';

import { api } from '/@/renderer/api';
import { getRuntimeConfig } from '/@/renderer/config/runtime-config';
import {
    isLegacyAuth,
    isServerLock,
} from '/@/renderer/features/action-required/utils/window-properties';
import {
    getServerById,
    useAuthStoreActions,
    useCurrentServer,
    useServerList,
} from '/@/renderer/store';
import { Center } from '/@/shared/components/center/center';
import { Spinner } from '/@/shared/components/spinner/spinner';
import {
    AuthenticationResponse,
    ServerListItemWithCredential,
    ServerType,
} from '/@/shared/types/domain-types';

const localSettings = isElectron() ? window.api.localSettings : null;
const normalizeUrl = (url: string) => url.replace(/\/$/, '');

type ConnectionState = 'connecting' | 'failed';

const LoginRoute = () => {
    const [connectionState, setConnectionState] = useState<ConnectionState>('connecting');
    const { addServer, setCurrentServer, updateServer } = useAuthStoreActions();
    const currentServer = useCurrentServer();
    const serverList = useServerList();

    const serverConfig = useMemo(() => {
        const runtimeConfig = getRuntimeConfig();
        const serverLock = isServerLock();
        const serverType = runtimeConfig.serverType;
        const serverName = runtimeConfig.serverName;
        const serverPassword = runtimeConfig.serverPassword;
        const serverUrl = runtimeConfig.serverUrl;
        const serverUsername = runtimeConfig.serverUsername;

        return {
            isConfigured: Boolean(
                serverLock && serverType && serverUrl && serverUsername && serverPassword,
            ),
            legacyAuth: serverLock && isLegacyAuth(),
            serverName,
            serverPassword,
            serverType,
            serverUrl,
            serverUsername,
        };
    }, []);

    useEffect(() => {
        if (currentServer || !serverConfig.isConfigured || !serverConfig.serverType) {
            if (!serverConfig.isConfigured) {
                setConnectionState('failed');
            }
            return;
        }

        let mounted = true;

        const connectInternally = async () => {
            try {
                const normalizedUrl = normalizeUrl(serverConfig.serverUrl);
                const existingServer = Object.values(serverList).find(
                    (server) =>
                        normalizeUrl(server.url) === normalizedUrl &&
                        server.username === serverConfig.serverUsername,
                );

                if (existingServer?.credential) {
                    setCurrentServer(existingServer);
                    return;
                }

                const authFunction = api.controller.authenticate;

                if (!authFunction) {
                    throw new Error('Internal authentication is unavailable.');
                }

                const data: AuthenticationResponse | undefined = await authFunction(
                    serverConfig.serverUrl,
                    {
                        legacy: serverConfig.legacyAuth,
                        password: serverConfig.serverPassword,
                        username: serverConfig.serverUsername,
                    },
                    serverConfig.serverType as ServerType,
                );

                if (!data) {
                    throw new Error('Internal sign-in failed.');
                }

                const serverItem: ServerListItemWithCredential = {
                    credential: data.credential,
                    id: existingServer?.id || nanoid(),
                    isAdmin: data.isAdmin,
                    name: serverConfig.serverName,
                    savePassword: false,
                    type: serverConfig.serverType as ServerType,
                    url: normalizedUrl,
                    userId: data.userId,
                    username: data.username,
                };

                if (data.ndCredential !== undefined) {
                    serverItem.ndCredential = data.ndCredential;
                }

                if (existingServer) {
                    updateServer(existingServer.id, serverItem);
                    const updatedServer = getServerById(existingServer.id);

                    if (updatedServer) {
                        setCurrentServer(updatedServer);
                    }
                } else {
                    addServer(serverItem);
                    setCurrentServer(serverItem);
                }

                if (localSettings) {
                    localSettings.passwordRemove(serverItem.id);
                }
            } catch {
                if (mounted) {
                    setConnectionState('failed');
                }
            }
        };

        connectInternally();

        return () => {
            mounted = false;
        };
    }, [addServer, currentServer, serverConfig, serverList, setCurrentServer, updateServer]);

    if (currentServer) {
        return <Navigate replace to="/" />;
    }

    if (connectionState === 'connecting') {
        return (
            <Center h="100vh" w="100%">
                <Spinner container />
            </Center>
        );
    }

    return (
        <div className={styles.page}>
            <div className={styles.panel}>
                <div className={styles.brand}>Music</div>
                <h1>App unavailable</h1>
                <p>The internal music connection could not be started on this device.</p>
            </div>
        </div>
    );
};

export default LoginRoute;
