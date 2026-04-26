import { lazy } from 'react';
import { Navigate, Route } from 'react-router';

import { ConsumerShell } from '/@/renderer/features/consumer/layout';
import { AppRoute } from '/@/renderer/router/routes';
import { isTelegramMiniApp } from '/@/renderer/utils/telegram';

const NowPlayingRoute = lazy(
    () => import('/@/renderer/features/consumer/screens/now-playing-screen'),
);
const ConsumerSearchRoute = lazy(
    () => import('/@/renderer/features/consumer/screens/search-screen'),
);
const ConsumerLibraryRoute = lazy(
    () => import('/@/renderer/features/consumer/screens/library-screen'),
);

const ProfilePage = lazy(() => import('/@/renderer/pages/Profile'));

// Aligned pages (current working implementation)
const AlignedMarketplacePage = lazy(() => import('/@/renderer/pages/AlignedMarketplace'));
const AlignedPaymentsPage = lazy(() => import('/@/renderer/pages/AlignedPayments'));
const MusicPlatformHome = lazy(() => import('/@/renderer/pages/MusicPlatformHome'));

// Future refactored pages (not yet ready)
const RefactoredMarketplacePage = lazy(() => import('/@/renderer/pages/RefactoredMarketplace'));
const RefactoredPaymentsPage = lazy(() => import('/@/renderer/pages/RefactoredPayments'));

// Feature flag to switch between implementations
const getImplementationType = () => {
    const enableRefactored = import.meta.env?.VITE_ENABLE_NEW_MUSIC_DOMAIN === 'true';
    const enablePayment = import.meta.env?.VITE_ENABLE_NEW_PAYMENT_DOMAIN === 'true';
    
    if (enableRefactored && enablePayment) {
        return 'refactored';  // Future implementation
    } else {
        return 'aligned';    // Current working implementation
    }
};

const MOBILE_BREAKPOINT = 768;

const getInitialConsumerRoute = () => {
    if (isTelegramMiniApp()) {
        return AppRoute.HOME;
    }

    if (typeof window !== 'undefined' && window.matchMedia) {
        const isMobile = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`).matches;
        return isMobile ? AppRoute.HOME : AppRoute.NOW_PLAYING;
    }

    return AppRoute.HOME;
};

const InitialLandingRoute = () => <Navigate replace to={getInitialConsumerRoute()} />;

export const consumerRoutes = (
    <Route element={<ConsumerShell />}>
        <Route element={<InitialLandingRoute />} index />
        <Route element={<MusicPlatformHome />} path={AppRoute.HOME} />
        <Route element={<ConsumerSearchRoute />} path={AppRoute.SEARCH} />
        <Route element={<ConsumerLibraryRoute />} path={AppRoute.LIBRARY} />
        <Route element={<NowPlayingRoute />} path={AppRoute.NOW_PLAYING} />
        <Route element={<MusicPlatformHome />} path={AppRoute.FAVORITES} />
        <Route element={<MusicPlatformHome />} path={AppRoute.SETTINGS} />
        
        {/* Implementation-based routing */}
        <Route
            element={
                getImplementationType() === 'refactored' ? (
                    <RefactoredMarketplacePage />
                ) : (
                    <AlignedMarketplacePage />
                )
            }
            path={AppRoute.MARKETPLACE}
        />
        <Route
            element={
                getImplementationType() === 'refactored' ? (
                    <RefactoredPaymentsPage />
                ) : (
                    <AlignedPaymentsPage />
                )
            }
            path={AppRoute.PAYMENTS}
        />
        
        <Route element={<ProfilePage />} path={AppRoute.PROFILE} />
    </Route>
);
