const User = require('../models/User');
const History = require('../models/History');
const { getLocationInfo } = require('../utils/location');

const apiKeyMiddleware = async (req, res, next) => {
    try {
        const apiKey = req.headers['x-api-key'];

        if (!apiKey) {
            console.error('API key missing in request headers');
            return res.status(401).json({ message: 'API key required' });
        }

        // Debug výpis
        console.log(`Received API request with key: ${apiKey.substring(0, 10)}...`);

        const user = await User.findOne({ where: { apiKey } });

        if (!user) {
            console.error(`Invalid API key: ${apiKey.substring(0, 10)}... not found in database`);
            return res.status(401).json({ message: 'Invalid API key' });
        }

        console.log(`API key authenticated for user: ${user.email} (ID: ${user.id})`);
        req.user = user;

        // Log API access
        const location = await getLocationInfo(req.ip);
        await History.create({
            userId: user.id,
            action: req.method + ' ' + req.path,
            description: `API access: ${req.method} ${req.path}`,
            ipAddress: req.ip,
            userAgent: req.headers['user-agent'],
            city: location.city,
            country: location.country,
            accessType: 'api'
        });

        next();
    } catch (error) {
        console.error('API key authentication error:', error);
        res.status(401).json({ message: 'API authentication failed' });
    }
};

module.exports = apiKeyMiddleware;