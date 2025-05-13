// backend/scripts/fix-admin.js
const { Sequelize, DataTypes } = require('sequelize');
const bcrypt = require('bcryptjs');
const crypto = require('crypto');
require('dotenv').config();

// Create a direct database connection
const sequelize = new Sequelize('pdfeditor', 'root', 'rootpassword', {
    host: 'db',
    dialect: 'mysql'
});

// Define User model directly in the script
const User = sequelize.define('User', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true
    },
    email: {
        type: DataTypes.STRING,
        allowNull: false,
        unique: true
    },
    password: {
        type: DataTypes.STRING,
        allowNull: false
    },
    role: {
        type: DataTypes.ENUM('user', 'admin'),
        defaultValue: 'user'
    },
    apiKey: {
        type: DataTypes.STRING,
        unique: true
    },
    lastLogin: {
        type: DataTypes.DATE
    }
});

async function fixAdmin() {
    try {
        await sequelize.authenticate();
        console.log('Database connection successful');

        // Manually hash the password
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash('adminpassword123', salt);

        // Check if admin already exists
        const existingAdmin = await User.findOne({ where: { email: 'admin@example.com' } });

        if (existingAdmin) {
            console.log('Admin user found, updating password...');
            existingAdmin.password = hashedPassword;
            existingAdmin.apiKey = crypto.randomBytes(32).toString('hex');
            await existingAdmin.save();
            console.log('Admin password and API key updated');
        } else {
            console.log('Creating new admin user...');
            await User.create({
                email: 'admin@example.com',
                password: hashedPassword,
                role: 'admin',
                apiKey: crypto.randomBytes(32).toString('hex')
            });
            console.log('Admin user created');
        }
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await sequelize.close();
        process.exit(0);
    }
}

fixAdmin();