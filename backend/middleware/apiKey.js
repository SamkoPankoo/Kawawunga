const User = require('../models/User');
const History = require('../models/History');
const { getLocationInfo } = require('../utils/location');

const apiKeyMiddleware = async (req, res, next) => {
    try {
        const apiKey = req.headers['x-api-key'];

        if (!apiKey) {
            return res.status(401).json({ message: 'API key required' });
        }

        const user = await User.findOne({ where: { apiKey } });

        if (!user) {
            return res.status(401).json({ message: 'Invalid API key' });
        }

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
        console.error(error);
        res.status(401).json({ message: 'API authentication failed' });
    }
};

module.exports = apiKeyMiddleware;