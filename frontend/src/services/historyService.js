// src/services/historyService.js - Updated with better pagination support
import api, { getAuthHeaders } from './api';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

export default {
    // Get recent history with improved pagination
    async getRecentHistory(limit = 8) {
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

    // Get PDF operation history with improved pagination
    async getPdfHistory(page = 1, limit = 8) {
        try {
            const authStore = useAuthStore();

            // Ensure we have auth info
            if (!authStore.token && !authStore.user?.apiKey) {
                console.warn('No authentication credentials available for PDF history request');
                return { items: [], pagination: { page: 1, pages: 1, total: 0 } };
            }

            // Get auth headers
            const headers = getAuthHeaders(authStore.token, authStore.user?.apiKey);

            // Try multiple approaches to get history data with proper pagination

            // First try: Using the specific PDF logs endpoint with pagination
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

            // Second try: Use the history endpoint with pagination parameters
            try {
                const historyResponse = await api.get('/history/recent', {
                    params: {
                        page,
                        limit
                    }
                });

                if (Array.isArray(historyResponse.data)) {
                    // Filter for PDF operations - moved to component to avoid duplicating logic
                    const historyItems = historyResponse.data;

                    // Simulated pagination if the API doesn't support it
                    return {
                        items: historyItems,
                        pagination: {
                            page,
                            // Assume there's at least one more page if we got a full page of results
                            pages: historyItems.length >= limit ? page + 1 : page,
                            total: historyItems.length + (historyItems.length >= limit ? limit : 0)
                        }
                    };
                }
            } catch (historyErr) {
                console.error('Error fetching from history endpoint:', historyErr.message);
            }

            // If we reach here, all attempts failed
            return {
                items: [],
                pagination: {
                    page: 1,
                    pages: 1,
                    total: 0
                }
            };
        } catch (error) {
            console.error('Failed to fetch PDF history:', error);
            return {
                items: [],
                pagination: {
                    page: 1,
                    pages: 1,
                    total: 0
                }
            };
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