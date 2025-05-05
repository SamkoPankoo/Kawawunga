const axios = require('axios');

async function getLocationInfo(ip) {
    try {
        // For development, use a default IP
        if (ip === '::1' || ip === '127.0.0.1') {
            return {
                city: 'Local',
                country: 'Development'
            };
        }

        // Use a free IP geolocation service
        const response = await axios.get(`http://ip-api.com/json/${ip}`);
        const data = response.data;

        return {
            city: data.city || 'Unknown',
            country: data.country || 'Unknown'
        };
    } catch (error) {
        console.error('Failed to get location info:', error);
        return {
            city: 'Unknown',
            country: 'Unknown'
        };
    }
}

module.exports = {
    getLocationInfo
};