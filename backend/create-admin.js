const { Sequelize, DataTypes } = require('sequelize');
const bcrypt = require('bcryptjs');
const crypto = require('crypto');
require('dotenv').config();

// Vytvorenie Sequelize inštancie
const sequelize = new Sequelize('pdfeditor', 'root', 'rootpassword', {
    host: 'db',
    dialect: 'mysql'
});

// Definovanie User modelu priamo v skripte
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

async function createAdmin() {
    try {
        await sequelize.authenticate();
        console.log('Pripojenie k databáze úspešné');

        // Manuálne zahashujeme heslo
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash('adminpassword123', salt);

        // Skontrolujeme, či admin už existuje
        const existingAdmin = await User.findOne({ where: { email: 'admin@example.com' } });

        if (existingAdmin) {
            console.log('Admin používateľ už existuje, aktualizujem heslo...');
            existingAdmin.password = hashedPassword;
            await existingAdmin.save();
            console.log('Admin heslo aktualizované');
        } else {
            console.log('Vytváram admin používateľa...');
            await User.create({
                email: 'admin@example.com',
                password: hashedPassword,
                role: 'admin',
                apiKey: crypto.randomBytes(32).toString('hex')
            });
            console.log('Admin používateľ vytvorený');
        }
    } catch (error) {
        console.error('Chyba:', error);
    } finally {
        await sequelize.close();
        process.exit(0);
    }
}

createAdmin();