
const sequelize = require('./config/database');
const User = require('./models/User');
const crypto = require('crypto');
require('dotenv').config();

async function seedDatabase() {
  try {
    // Sync database
    await sequelize.sync({ force: true });
    console.log('Database synced successfully');

    // Create admin user
    const adminEmail = process.env.ADMIN_EMAIL || 'admin@example.com';
    const adminPassword = process.env.ADMIN_PASSWORD || 'adminpassword123';

    const adminUser = await User.create({
      email: adminEmail,
      password: adminPassword,
      role: 'admin',
      apiKey: crypto.randomBytes(32).toString('hex')
    });

    console.log('Admin user created successfully');
    console.log('Email:', adminEmail);
    console.log('Password:', adminPassword);
    console.log('API Key:', adminUser.apiKey);

    process.exit(0);
  } catch (error) {
    console.error('Error seeding database:', error);
    process.exit(1);
  }
}

seedDatabase();
