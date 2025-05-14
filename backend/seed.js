const { connectWithRetry, syncDatabase } = require('./config/db-connection');
const User = require('./models/User');
const crypto = require('crypto');
require('dotenv').config();

async function seedDatabase() {
  try {
    // Připojení k databázi s opakovanými pokusy
    await connectWithRetry();

    // Synchronizace databáze
    await syncDatabase({ force: true });
    console.log('Database synced successfully');

    // Vytvoření admin uživatele
    const adminEmail = process.env.ADMIN_EMAIL || 'admin@example.com';
    const adminPassword = process.env.ADMIN_PASSWORD || 'adminpassword123';

    // Model User automaticky zahashuje heslo díky beforeCreate hook
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