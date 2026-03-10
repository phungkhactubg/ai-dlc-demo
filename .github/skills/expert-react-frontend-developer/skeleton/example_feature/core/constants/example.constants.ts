export const EXAMPLE_CONSTANTS = {
    DEFAULT_STATUS: 'pending',
    MAX_RETRIES: 3,
    API_ENDPOINTS: {
        BASE: '/examples',
        BY_ID: (id: string) => `/examples/${id}`,
    },
} as const;

export const OBSERVER_EVENTS = {
    CREATED: 'example:created',
    UPDATED: 'example:updated',
} as const;
