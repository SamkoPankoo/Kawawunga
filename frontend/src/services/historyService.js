// src/services/historyService.js
import api, { getAuthHeaders } from './api';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

export default {
    // Get recent history
    async getRecentHistory(limit = 10) {
        try {
            const authStore = useAuthStore();

            // Ensure we have auth info
            if (!authStore.token && !authStore.user?.apiKey) {
                console.warn('No authentication credentials available for history request');
                return [];
            }

            // Use the api instance with interceptors
            const response = await api.get('/history/recent', {
                params: { limit }
            });

            return response.data;
        } catch (error) {
            console.error('Failed to fetch history:', error);
            return [];
        }
    },

    // Get PDF operation history
    async getPdfHistory(page = 1, limit = 10) {
        try {
            const authStore = useAuthStore();

            // Ensure we have auth info
            if (!authStore.token && !authStore.user?.apiKey) {
                console.warn('No authentication credentials available for PDF history request');
                return { items: [], pagination: { page: 1, pages: 1, total: 0 } };
            }

            // Get auth headers
            const headers = getAuthHeaders(authStore.token, authStore.user?.apiKey);

            // Try multiple approaches to get history data

            // First try: Using the specific PDF logs endpoint
            try {
                const response = await api.get('/pdfLogs', {
                    params: { page, limit }
                });

                if (response.data && response.data.data) {
                    return {
                        items: response.data.data,
                        pagination: response.data.pagination
                    };
                }
            } catch (err) {
                console.warn('Error fetching from pdfLogs endpoint:', err.message);
            }

            // Second try: Check the history by type endpoint
            try {
                const typeResponse = await api.get('/history/by-type/pdf-merge', {
                    params: { limit }
                });

                if (Array.isArray(typeResponse.data) && typeResponse.data.length > 0) {
                    return {
                        items: typeResponse.data,
                        pagination: {
                            page: 1,
                            pages: 1,
                            total: typeResponse.data.length
                        }
                    };
                }
            } catch (typeErr) {
                console.warn('Error fetching from by-type endpoint:', typeErr.message);
            }

            // Third try: Filter from recent history
            try {
                const historyResponse = await api.get('/history/recent', {
                    params: { limit: limit * 2 }
                });

                if (Array.isArray(historyResponse.data)) {
                    // Filter for PDF operations
                    const pdfItems = historyResponse.data.filter(item =>
                            item.action && (
                                item.action.startsWith('pdf-') ||
                                item.action.includes('pdf')
                            )
                    );

                    return {
                        items: pdfItems,
                        pagination: {
                            page: 1,
                            pages: 1,
                            total: pdfItems.length
                        }
                    };
                }
            } catch (historyErr) {
                console.error('Error fetching from history endpoint:', historyErr.message);
            }

            return { items: [], pagination: { page: 1, pages: 1, total: 0 } };
        } catch (error) {
            console.error('Failed to fetch PDF history:', error);
            return { items: [], pagination: { page: 1, pages: 1, total: 0 } };
        }
    },

    // Log PDF operation
    async logPdfOperation(action, description, metadata = {}) {
        try {
            console.log(`Logging operation: ${action} - ${description}`, metadata);

            const authStore = useAuthStore();

            // Ensure we have auth info
            if (!authStore.token && !authStore.user?.apiKey) {
                console.error('No authentication credentials available, cannot log operation');
                return false;
            }

            // Format the action with pdf- prefix if needed
            const formattedAction = action.startsWith('pdf-') ? action : `pdf-${action}`;

            // Prepare payload
            const payload = {
                action: formattedAction,
                description: description || `${action} operation`,
                metadata: {
                    ...metadata,
                    timestamp: new Date().toISOString()
                }
            };

            // Try multiple approaches to log the operation

            // First try: Use the history log endpoint with our API instance
            try {
                const response = await api.post('/history/log', payload);
                console.log('Operation logged successfully:', response.data);
                return true;
            } catch (directErr) {
                console.warn('Failed to log with standard API, trying alternative approach:', directErr.message);
            }

            // Second try: Try the pdfLogs endpoint
            try {
                const pdfResponse = await api.post('/pdfLogs/log', payload);
                console.log('Operation logged via pdfLogs endpoint:', pdfResponse.data);
                return true;
            } catch (pdfErr) {
                console.warn('Failed to log with pdfLogs endpoint:', pdfErr.message);
            }

            // If all else fails, log the failure
            console.error('All logging attempts failed');
            return false;
        } catch (error) {
            console.error('Failed to log operation:', error);
            return false;
        }
    }
};