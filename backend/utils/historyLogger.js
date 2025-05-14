// backend/utils/historyLogger.js
const History = require('../models/History');

/**
 * Utility function to log user operations to the history table
 *
 * @param {Object} options - Options for the history entry
 * @param {number} options.userId - User ID
 * @param {string} options.action - Action performed (e.g., 'merge', 'split')
 * @param {string} options.description - Description of the action
 * @param {string} options.ipAddress - IP address of the user
 * @param {string} options.userAgent - User agent string
 * @param {string} options.fileName - Name of the file being operated on (optional)
 * @param {string} options.fileId - ID of the file being operated on (optional)
 * @param {string} options.operationType - Type of operation (optional)
 * @param {string} options.accessType - Type of access ('frontend' or 'api')
 * @returns {Promise<Object>} The created history entry
 */
async function logOperation(options) {
    try {
        const historyEntry = await History.create({
            userId: options.userId,
            action: options.action,
            description: options.description,
            ipAddress: options.ipAddress || '0.0.0.0',
            userAgent: options.userAgent || 'Unknown',
            city: options.city || 'Unknown',
            country: options.country || 'Unknown',
            fileName: options.fileName,
            fileId: options.fileId,
            operationType: options.operationType,
            accessType: options.accessType || 'frontend'
        });

        console.log('Operation logged to history:', options.action);
        return historyEntry;
    } catch (error) {
        console.error('Failed to log operation to history:', error);
        // Don't throw so it doesn't break the main operation
        return null;
    }
}

module.exports = { logOperation };