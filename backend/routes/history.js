// backend/routes/history.js
const express = require('express');
const router = express.Router();
const History = require('../models/History');
const authMiddleware = require('../middleware/auth');

// Get user's recent activity
router.get('/recent', authMiddleware, async (req, res) => {
    try {
        const limit = parseInt(req.query.limit) || 10;

        const activities = await History.findAll({
            where: {
                userId: req.user.id
            },
            order: [['createdAt', 'DESC']],
            limit: limit
        });

        res.json(activities);
    } catch (error) {
        console.error('Failed to fetch history:', error);
        // Return empty array instead of error to prevent breaking the client app
        res.json([]);
    }
});

// Get activity by type
router.get('/by-type/:type', authMiddleware, async (req, res) => {
    try {
        const { type } = req.params;
        const limit = parseInt(req.query.limit) || 10;

        const activities = await History.findAll({
            where: {
                userId: req.user.id,
                action: type
            },
            order: [['createdAt', 'DESC']],
            limit: limit
        });

        res.json(activities);
    } catch (error) {
        console.error(`Failed to fetch ${req.params.type} history:`, error);
        res.json([]);
    }
});

// Record manual activity log (for frontend operations)
router.post('/log', authMiddleware, async (req, res) => {
    try {
        const { action, description, fileId, fileName, operationType } = req.body;

        if (!action) {
            return res.status(400).json({ message: 'Action is required' });
        }

        const historyEntry = await History.create({
            userId: req.user.id,
            action,
            description: description || `${action} operation`,
            fileId,
            fileName,
            operationType: operationType || action,
            ipAddress: req.ip,
            userAgent: req.headers['user-agent'],
            city: 'Unknown', // Avoid IP geolocation to prevent errors
            country: 'Unknown',
            accessType: 'frontend'
        });

        res.json({
            message: 'Activity logged successfully',
            historyId: historyEntry.id
        });
    } catch (error) {
        console.error('Failed to log activity:', error);
        res.status(500).json({ message: 'Failed to log activity' });
    }
});

// Clear history (for this user only)
router.delete('/clear', authMiddleware, async (req, res) => {
    try {
        await History.destroy({
            where: {
                userId: req.user.id
            }
        });

        res.json({ message: 'History cleared successfully' });
    } catch (error) {
        console.error('Failed to clear history:', error);
        res.status(500).json({ message: 'Failed to clear history' });
    }
});

module.exports = router;