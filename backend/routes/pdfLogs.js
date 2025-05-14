const express = require('express');
const router = express.Router();
const History = require('../models/History');
const apiKeyMiddleware = require('../middleware/apiKey');
const authMiddleware = require('../middleware/auth'); // Pridané pre podporu autentifikácie cez token
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
// OPRAVA: Pridaná podpora pre oba spôsoby autentifikácie
router.get('/', async (req, res) => {
    try {
        // Check for authentication via API key or token
        let user;

        // Najprv skúsime API kľúč
        if (req.headers['x-api-key']) {
            // Použitie rovnakej logiky ako v apiKeyMiddleware
            const apiKey = req.headers['x-api-key'];
            const User = require('../models/User');
            user = await User.findOne({ where: { apiKey } });

            if (!user) {
                return res.status(401).json({ message: 'Invalid API key' });
            }
        }
        // Potom skúsime JWT token
        else if (req.headers.authorization && req.headers.authorization.startsWith('Bearer ')) {
            const token = req.headers.authorization.split(' ')[1];
            const jwt = require('jsonwebtoken');

            try {
                const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
                const User = require('../models/User');
                user = await User.findByPk(decoded.id);

                if (!user) {
                    return res.status(401).json({ message: 'Invalid token' });
                }
            } catch (tokenError) {
                console.error('Token validation error:', tokenError);
                return res.status(401).json({ message: 'Invalid token' });
            }
        } else {
            return res.status(401).json({ message: 'Authentication required' });
        }

        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 10;
        const offset = (page - 1) * limit;

        // Debug info
        console.log(`Getting PDF operation history for user ${user.id} (${user.email})`);
        console.log(`Page: ${page}, Limit: ${limit}, Offset: ${offset}`);

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

        console.log(`Found ${history.count} history entries`);

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
// Route to check if history records exist (for debugging)
router.get('/check', async (req, res) => {
    try {
        const totalCount = await History.count();
        const pdfCount = await History.count({
            where: {
                action: { [require('sequelize').Op.like]: 'pdf-%' }
            }
        });

        res.json({
            total: totalCount,
            pdfOperations: pdfCount,
            status: 'OK',
            message: 'History check completed successfully'
        });
    } catch (error) {
        console.error('Error checking history records:', error);
        res.status(500).json({
            message: 'Failed to check history records',
            error: error.message
        });
    }
});
router.get('/test-log', async (req, res) => {
    try {
        // Vytvorte testovací záznam histórie
        const historyEntry = await History.create({
            userId: 3,  // Váš userId
            action: 'pdf-test',
            description: 'Test history entry',
            ipAddress: req.ip,
            userAgent: req.headers['user-agent'],
            city: 'Test City',
            country: 'Test Country',
            accessType: 'api'
        });

        res.json({
            success: true,
            historyEntry
        });
    } catch (error) {
        console.error('Test log failed:', error);
        res.status(500).json({ error: error.message });
    }
});

router.get('/debug-key', async (req, res) => {
    try {
        const User = require('../models/User');

        // Nájdeme užívateľa s ID 3 alebo prvého admin užívateľa
        let user = await User.findByPk(3) ||
            await User.findOne({ where: { role: 'admin' } }) ||
            await User.findOne();

        if (!user) {
            return res.status(404).json({ message: 'No user found' });
        }

        // Zobrazíme jeho API kľúč
        res.json({
            userId: user.id,
            email: user.email,
            apiKey: user.apiKey
        });
    } catch (error) {
        console.error('Error fetching debug key:', error);
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;