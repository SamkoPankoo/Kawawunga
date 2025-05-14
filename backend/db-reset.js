// db-reset.js
const sequelize = require('./config/database');
const { initializeAdmin } = require('./init-data');

console.log('Resetting database...');

sequelize.sync({ force: true })
    .then(async () => {
        console.log('Database reset and synchronized successfully');

        // Initialize admin user
        await initializeAdmin();
        console.log('Admin user created');

        process.exit(0);
    })
    .catch(err => {
        console.error('Error resetting database:', err);
        process.exit(1);
    });