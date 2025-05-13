const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');
const bcrypt = require('bcryptjs');

const User = sequelize.define('User', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true
    },
    email: {
        type: DataTypes.STRING,
        allowNull: false,
        unique: true,
        validate: {
            isEmail: true
        }
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

// Hash password before saving
User.beforeCreate(async (user) => {
    if (user.password) {
        user.password = await bcrypt.hash(user.password, 10);
    }
});

User.beforeUpdate(async (user) => {
    if (user.changed('password')) {
        user.password = await bcrypt.hash(user.password, 10);
    }
});

// Method to validate password
User.prototype.validatePassword = async function(password) {
    try {
        if (!password || !this.password) {
            console.error('Missing password data');
            return false;
        }
        return await bcrypt.compare(password, this.password);
    } catch (error) {
        console.error('Password validation error:', error);
        return false;
    }
};

module.exports = User;