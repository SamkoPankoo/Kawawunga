// backend/utils/location.js
const axios = require('axios');

/**
 * Enhanced function to get geolocation information from an IP address
 * with special handling for Docker environments
 */
async function getLocationInfo(ip) {
    try {
        // For Docker environment, always use mock location
        if (process.env.NODE_ENV === 'development' ||
            process.env.USE_MOCK_LOCATION === 'true' ||
            !ip ||
            ip === '::1' ||
            ip === '127.0.0.1' ||
            ip.startsWith('172.') ||
            ip.startsWith('192.168.')) {
            console.log(`Using mock location for IP: ${ip}`);
            return getMockLocation();
        }

        // For production with real IPs
        console.log(`Looking up location for real IP: ${ip}`);
        try {
            const response = await axios.get(`https://ip-api.com/json/${ip}`, {
                timeout: 3000,
                headers: { 'User-Agent': 'PDF Editor Service' }
            });

            const data = response.data;
            if (data && data.status !== 'fail') {
                console.log(`Location found for ${ip}: ${data.city}, ${data.country}`);
                return {
                    city: data.city || 'Unknown',
                    country: data.country || 'Unknown'
                };
            }
        } catch (err) {
            console.log(`Geolocation service failed: ${err.message}, using mock location`);
        }

        // Always fall back to mock location if real lookup fails
        return getMockLocation();
    } catch (error) {
        console.error('Error in getLocationInfo:', error);
        return getMockLocation();
    }
}

// Mock location generator with more realistic distribution
function getMockLocation() {
    // List of realistic locations with higher probability for Slovakia
    const mockLocations = [
        { city: 'Bratislava', country: 'Slovakia' },
        { city: 'Košice', country: 'Slovakia' },
        { city: 'Banská Bystrica', country: 'Slovakia' },
        { city: 'Žilina', country: 'Slovakia' },
        { city: 'Nitra', country: 'Slovakia' },
        { city: 'Trnava', country: 'Slovakia' },
        { city: 'Prešov', country: 'Slovakia' },
        { city: 'Nové Zámky', country: 'Slovakia' }, // Added your location
        { city: 'Prague', country: 'Czech Republic' },
        { city: 'Brno', country: 'Czech Republic' },
        { city: 'Vienna', country: 'Austria' },
        { city: 'Budapest', country: 'Hungary' },
        { city: 'Warsaw', country: 'Poland' },
        { city: 'Berlin', country: 'Germany' }
    ];

    // Get a random location from the list
    const randomIndex = Math.floor(Math.random() * mockLocations.length);
    const location = mockLocations[randomIndex];

    console.log(`Using mock location: ${location.city}, ${location.country}`);
    return location;
}

module.exports = {
    getLocationInfo
};