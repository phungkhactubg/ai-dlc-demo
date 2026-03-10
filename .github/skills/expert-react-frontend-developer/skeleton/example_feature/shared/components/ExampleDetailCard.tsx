import React, { memo } from 'react';
import { Card, CardContent, Typography, Skeleton, Chip, Box } from '@mui/material';
import { Example } from '../../../core/models/example.model';

interface ExampleDetailCardProps {
    data: Example;
    isLoading?: boolean;
}

// Presentational Component -> Pure, no side effects, memoized
export const ExampleDetailCard: React.FC<ExampleDetailCardProps> = memo(({ data, isLoading }) => {
    if (isLoading) {
        return <Skeleton variant="rectangular" height={200} />;
    }

    return (
        <Card elevation={2}>
            <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h5" component="div">
                        {data.name}
                    </Typography>
                    <Chip
                        label={data.status}
                        color={data.status === 'active' ? 'success' : 'default'}
                        size="small"
                    />
                </Box>
                <Typography variant="body2" color="text.secondary">
                    ID: {data.id}
                </Typography>
                <Typography variant="caption" display="block" mt={1}>
                    Created At: {new Date(data.createdAt).toLocaleString()}
                </Typography>
            </CardContent>
        </Card>
    );
});
