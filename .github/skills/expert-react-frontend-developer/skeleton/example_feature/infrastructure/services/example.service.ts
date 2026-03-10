import { IExampleService } from '../../core/interfaces/example.service.interface';
import { Example, ExampleSchema, CreateExampleRequest } from '../../core/models/example.model';
import { exampleApi } from '../api/example.api';

// Service Implementation
// Handles business logic, data mapping, and validation before returning to UI/Store
export class ExampleService implements IExampleService {
    async getById(id: string): Promise<Example> {
        const response = await exampleApi.getById(id);
        // Runtime Validation: Ensure API response matches our Zod Schema
        return ExampleSchema.parse(response.data);
    }

    async create(data: CreateExampleRequest): Promise<Example> {
        const response = await exampleApi.create(data);
        return ExampleSchema.parse(response.data);
    }

    async update(id: string, data: Partial<CreateExampleRequest>): Promise<Example> {
        const response = await exampleApi.update(id, data);
        return ExampleSchema.parse(response.data);
    }

    async delete(id: string): Promise<void> {
        await exampleApi.delete(id);
    }
}

// Singleton export
export const exampleService = new ExampleService();
