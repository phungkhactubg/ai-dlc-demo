import axios, { AxiosInstance } from 'axios';
import { Example } from '../../core/models/example.model';

// In a real app, this instance would come from a shared 'infrastructure/api' module with interceptors
const apiClient: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '/api/v1',
    timeout: 10000,
});

export const exampleApi = {
    getById: async (id: string) => {
        return apiClient.get<Example>(`/examples/${id}`);
    },
    create: async (data: unknown) => {
        return apiClient.post<Example>('/examples', data);
    },
    update: async (id: string, data: unknown) => {
        return apiClient.put<Example>(`/examples/${id}`, data);
    },
    delete: async (id: string) => {
        return apiClient.delete<void>(`/examples/${id}`);
    },
};
