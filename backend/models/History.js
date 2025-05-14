const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');
const User = require('./User');

const History = sequelize.define('History', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true
    },
    userId: {
        type: DataTypes.INTEGER,
        allowNull: false,
        references: {
            model: User,
            key: 'id'
        }
    },
    action: {
        type: DataTypes.STRING,
        allowNull: false
    },
    description: {
        type: DataTypes.TEXT
    },
    ipAddress: {
        type: DataTypes.STRING
    },
    userAgent: {
        type: DataTypes.STRING
    },
    city: {
        type: DataTypes.STRING
    },
    country: {
        type: DataTypes.STRING
    },
    accessType: {
        type: DataTypes.ENUM('frontend', 'api'),
        allowNull: false
    },
    metadata: {
        type: DataTypes.JSON,
        allowNull: true,
        get() {
            const value = this.getDataValue('metadata');
            if (value) {
                if (typeof value === 'string') {
                    try {
                        return JSON.parse(value);
                    } catch (e) {
                        return value;
                    }
                }
                return value;
            }
            return null;
        },
        set(value) {
            this.setDataValue('metadata',
                value ? (typeof value === 'string' ? value : JSON.stringify(value)) : null
            );
        }
    }
});
History.belongsTo(User, { foreignKey: 'userId' });
User.hasMany(History, { foreignKey: 'userId' });

module.exports = History;