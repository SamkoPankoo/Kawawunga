// backend/middleware/auth.js
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const { getLocationInfo } = require('../utils/location');
const History = require('../models/History');

const authMiddleware = async (req, res, next) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];

        if (!token) {
            return res.status(401).json({ message: 'No token provided' });
        }

        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
        const user = await User.findByPk(decoded.id);

        if (!user) {
            return res.status(401).json({ message: 'Invalid token' });
        }

        req.user = decoded;

        // For certain routes, log the access (if it's not a request to check auth status)
        if (!req.path.includes('/auth/me') && !req.path.includes('/auth/verify')) {
            try {
                // Extract the real client IP with proper header handling
                const ip = extractRealIP(req);
                console.log(`Auth middleware: Client IP address: ${ip}`);

                // Get location info
                const location = await getLocationInfo(ip);
                console.log(`Auth middleware: Location for ${ip}: ${location.city}, ${location.country}`);

                // Log the access
                await History.create({
                    userId: user.id,
                    action: `${req.method} ${req.path}`,
                    description: `Authenticated access: ${req.method} ${req.path}`,
                    ipAddress: ip,
                    userAgent: req.headers['user-agent'],
                    city: location.city,
                    country: location.country,
                    accessType: 'frontend'
                });
            } catch (logError) {
                console.error('Error logging authenticated access:', logError);
                // Continue anyway
            }
        }

        next();
    } catch (error) {
        console.error('Authentication error:', error);
        res.status(401).json({ message: 'Unauthorized' });
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

module.exports = authMiddleware;