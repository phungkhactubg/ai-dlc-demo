import React, { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Box, CircularProgress, Alert } from '@mui/material';
import { ErrorBoundary } from 'react-error-boundary';

// Fallback component for ErrorBoundary
const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) => {
    return (
        <Box p={3}>
            <Alert severity="error" onClose={resetErrorBoundary}>
                <p>Something went wrong in Example Feature:</p>
                <pre>{error.message}</pre>
            </Alert>
        </Box>
    );
};

const ExampleFeatureLayout: React.FC = () => {
    return (
        <ErrorBoundary FallbackComponent={ErrorFallback}>
            <Box sx={{ p: 3, height: '100%' }}>
                {/* Lazy load suspension point */}
                <Suspense fallback={<Box display="flex" justifyContent="center"><CircularProgress /></Box>}>
                    <Outlet />
                </Suspense>
            </Box>
        </ErrorBoundary>
    );
};

export default ExampleFeatureLayout;
