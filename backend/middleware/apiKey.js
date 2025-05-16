// backend/middleware/apiKey.js
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

        // Debug output
        console.log(`Received API request with key: ${apiKey.substring(0, 10)}...`);

        const user = await User.findOne({ where: { apiKey } });

        if (!user) {
            console.error(`Invalid API key: ${apiKey.substring(0, 10)}... not found in database`);
            return res.status(401).json({ message: 'Invalid API key' });
        }

        console.log(`API key authenticated for user: ${user.email} (ID: ${user.id})`);
        req.user = user;

        // Extract the real client IP with proper header handling
        const ip = extractRealIP(req);
        console.log(`Client IP address: ${ip}`);

        // Log API access
        try {
            const location = await getLocationInfo(ip);
            console.log(`Location for ${ip}: ${location.city}, ${location.country}`);

            await History.create({
                userId: user.id,
                action: req.method + ' ' + req.path,
                description: `API access: ${req.method} ${req.path}`,
                ipAddress: ip,
                userAgent: req.headers['user-agent'],
                city: location.city,
                country: location.country,
                accessType: 'api'
            });
        } catch (logError) {
            console.error('Error logging API access:', logError);
            // Continue anyway, don't block the request
        }

        next();
    } catch (error) {
        console.error('API key authentication error:', error);
        res.status(401).json({ message: 'API authentication failed' });
    }
};

/**
 * Helper function to extract the real client IP from request headers
 * Properly handles common proxy headers in a Docker environment
 */
function extractRealIP(req) {
    // Check for various proxy headers in order of reliability
    // X-Forwarded-For: this contains the client IP plus proxy IPs
    if (req.headers['x-forwarded-for']) {
        // Get the first IP (client IP) from the comma-separated list
        const ips = req.headers['x-forwarded-for'].split(',');
        const clientIP = ips[0].trim();
        return clientIP;
    }

    // X-Real-IP: typically set by Nginx when it acts as a reverse proxy
    if (req.headers['x-real-ip']) {
        return req.headers['x-real-ip'];
    }

    // CF-Connecting-IP: used by Cloudflare
    if (req.headers['cf-connecting-ip']) {
        return req.headers['cf-connecting-ip'];
    }

    // True-Client-IP: used by some CDNs
    if (req.headers['true-client-ip']) {
        return req.headers['true-client-ip'];
    }

    // Fastly-Client-IP: used by Fastly CDN
    if (req.headers['fastly-client-ip']) {
        return req.headers['fastly-client-ip'];
    }

    // Fallback to the direct IP from the socket
    return req.socket.remoteAddress || req.ip || '127.0.0.1';
}

module.exports = apiKeyMiddleware;