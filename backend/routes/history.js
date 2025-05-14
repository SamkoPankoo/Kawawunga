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
        console.log('Logging frontend operation:', req.body);

        const { action, description, metadata } = req.body;

        if (!action) {
            return res.status(400).json({ message: 'Action is required' });
        }

        // Make sure PDF actions have prefix "pdf-"
        const finalAction = action.startsWith('pdf-') ? action : `pdf-${action}`;

        // Create history entry with more detailed information
        const historyEntry = await History.create({
            userId: req.user.id,
            action: finalAction,
            description: description || `${finalAction} operation`,
            ipAddress: req.ip,
            userAgent: req.headers['user-agent'],
            city: req.body.city || 'Unknown',
            country: req.body.country || 'Unknown',
            accessType: 'frontend',
            metadata: metadata || null
        });

        console.log('Operation logged to history successfully:', {
            id: historyEntry.id,
            action: historyEntry.action,
            userId: historyEntry.userId
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
router.get('/admin/all', authMiddleware, async (req, res) => {
    // Check if user is admin
    if (req.user.role !== 'admin') {
        return res.status(403).json({ message: 'Access denied' });
    }

    try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 20;
        const offset = (page - 1) * limit;

        const history = await History.findAndCountAll({
            order: [['createdAt', 'DESC']],
            limit,
            offset,
            include: [{ model: User, attributes: ['email'] }]
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
        console.error('Failed to fetch all history:', error);
        res.status(500).json({ message: 'Failed to fetch history' });
    }
});

// Admin-only route to export history to CSV
router.get('/admin/export', authMiddleware, async (req, res) => {
    if (req.user.role !== 'admin') {
        return res.status(403).json({ message: 'Access denied' });
    }

    try {
        const history = await History.findAll({
            order: [['createdAt', 'DESC']],
            include: [{ model: User, attributes: ['email'] }]
        });

        // Convert to CSV using json2csv (already in your dependencies)
        const { Parser } = require('json2csv');
        const fields = ['id', 'User.email', 'action', 'description', 'ipAddress', 'city', 'country', 'accessType', 'createdAt'];
        const parser = new Parser({ fields });
        const csv = parser.parse(history);

        res.header('Content-Type', 'text/csv');
        res.attachment('history-export.csv');
        return res.send(csv);
    } catch (error) {
        console.error('Failed to export history:', error);
        res.status(500).json({ message: 'Failed to export history' });
    }
});

// Admin-only route to delete all history
router.delete('/admin/clear', authMiddleware, async (req, res) => {
    if (req.user.role !== 'admin') {
        return res.status(403).json({ message: 'Access denied' });
    }

    try {
        await History.destroy({ where: {} });
        res.json({ message: 'All history cleared successfully' });
    } catch (error) {
        console.error('Failed to clear history:', error);
        res.status(500).json({ message: 'Failed to clear history' });
    }
});

module.exports = router;