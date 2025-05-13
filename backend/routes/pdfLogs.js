const express = require('express');
const router = express.Router();
const History = require('../models/History');
const apiKeyMiddleware = require('../middleware/apiKey');
const { getLocationInfo } = require('../utils/location');

// Route to log PDF operations
router.post('/log', apiKeyMiddleware, async (req, res) => {
    try {
        const { action, description, fileId, fileName, operationType } = req.body;
        const user = req.user;

        if (!action) {
            return res.status(400).json({ message: 'Action is required' });
        }

        // Get location info
        const location = await getLocationInfo(req.ip);

        // Create history entry
        const historyEntry = await History.create({
            userId: user.id,
            action: `pdf-${action}`,
            description: description || `PDF operation: ${action}`,
            ipAddress: req.ip,
            userAgent: req.headers['user-agent'],
            city: location.city,
            country: location.country,
            accessType: 'api',
            metadata: {
                fileId,
                fileName,
                operationType
            }
        });

        res.json({
            message: 'Operation logged successfully',
            historyId: historyEntry.id
        });
    } catch (error) {
        console.error('Error logging PDF operation:', error);
        res.status(500).json({ message: 'Failed to log operation' });
    }
});

// Route to get PDF operation history for the current user
router.get('/', apiKeyMiddleware, async (req, res) => {
    try {
        const user = req.user;
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 10;
        const offset = (page - 1) * limit;

        // Get PDF operations history
        const history = await History.findAndCountAll({
            where: {
                userId: user.id,
                action: { [require('sequelize').Op.like]: 'pdf-%' }
            },
            order: [['createdAt', 'DESC']],
            limit,
            offset
        });

        res.json({
            data: history.rows,
            pagination: {
                total: history.count,
                page,
                pages: Math.ceil(history.count / limit)
            }
        });
    } catch (error) {
        console.error('Error fetching PDF operations history:', error);
        res.status(500).json({ message: 'Failed to fetch history' });
    }
});

module.exports = router;