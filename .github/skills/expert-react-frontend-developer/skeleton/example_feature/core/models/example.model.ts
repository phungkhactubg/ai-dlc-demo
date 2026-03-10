import { z } from 'zod';

// Zod Schema Definition
export const ExampleSchema = z.object({
    id: z.string().uuid(),
    name: z.string().min(3, 'Name must be at least 3 characters'),
    status: z.enum(['active', 'inactive', 'pending']),
    createdAt: z.string().datetime(),
    updatedAt: z.string().datetime(),
    metadata: z.record(z.string(), z.unknown()).optional(),
});

// TypeScript Type Inference (Zero duplication)
export type Example = z.infer<typeof ExampleSchema>;

// DTOs
export const CreateExampleSchema = ExampleSchema.pick({ name: true, status: true, metadata: true });
export type CreateExampleRequest = z.infer<typeof CreateExampleSchema>;
