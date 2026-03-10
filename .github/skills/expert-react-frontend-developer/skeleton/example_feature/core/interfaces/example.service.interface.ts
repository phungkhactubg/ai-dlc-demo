import { Example, CreateExampleRequest } from '../models/example.model';

// Interface defining the contract for the service layer
// UI components should NOT depend on this directly if possible, use Hooks instead.
export interface IExampleService {
    getById(id: string): Promise<Example>;
    create(data: CreateExampleRequest): Promise<Example>;
    update(id: string, data: Partial<CreateExampleRequest>): Promise<Example>;
    delete(id: string): Promise<void>;
}
