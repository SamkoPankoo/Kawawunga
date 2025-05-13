const User = require('./models/User');
const crypto = require('crypto');
const bcrypt = require('bcryptjs');
require('dotenv').config();

async function initializeAdmin() {
    try {
        // Check if admin exists
        const adminCount = await User.count({ where: { role: 'admin' } });

        if (adminCount === 0) {
            console.log('Admin user not found, creating default admin...');

            // Create admin user
            const adminEmail = process.env.ADMIN_EMAIL || 'admin@example.com';
            const adminPassword = process.env.ADMIN_PASSWORD || 'adminpassword123';

            // Hash password
            const salt = await bcrypt.genSalt(10);
            const hashedPassword = await bcrypt.hash(adminPassword, salt);

            // Create user
            const adminUser = await User.create({
                email: adminEmail,
                password: hashedPassword,
                role: 'admin',
                apiKey: crypto.randomBytes(32).toString('hex')
            });

            console.log(`Admin user created: ${adminEmail}`);
            return adminUser;
        } else {
            console.log('Admin user already exists, skipping creation');
            return await User.findOne({ where: { role: 'admin' } });
        }
    } catch (error) {
        console.error('Error initializing admin user:', error);
        throw error;
    }
}

module.exports = { initializeAdmin };