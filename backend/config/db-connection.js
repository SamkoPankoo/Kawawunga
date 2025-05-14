const sequelize = require('./database');

async function connectWithRetry(maxRetries = 10, delay = 5000) {
    let retries = 0;

    console.log('Attempting to connect to database...');

    while (retries < maxRetries) {
        try {
            await sequelize.authenticate();
            console.log('Database connection established successfully');
            return true;
        } catch (error) {
            retries++;
            console.error(`Database connection attempt ${retries}/${maxRetries} failed:`, error.message);

            if (retries >= maxRetries) {
                console.error('Maximum connection retries reached. Giving up.');
                throw error;
            }

            console.log(`Waiting ${delay/1000} seconds before next attempt...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
}

async function syncDatabase(options = { force: false, alter: true }) {
    try {
        // Najprv sa pokúsime o bežnú synchronizáciu
        console.log(`Syncing database with options: ${JSON.stringify(options)}`);
        await sequelize.sync(options);
        console.log('Database synced successfully');
        return true;
    } catch (error) {
        console.error('Error during database sync:', error.message);

        // Ak zlyhá kvôli problému s kľúčmi, a pokúšame sa o alter, vyskúšajme force
        if (options.alter && !options.force &&
            error.name === 'SequelizeDatabaseError' &&
            error.parent && error.parent.code === 'ER_TOO_MANY_KEYS') {

            console.log('Detected too many keys issue. Attempting force sync instead...');
            return syncDatabase({ force: true });
        }

        throw error;
    }
}

module.exports = {
    sequelize,
    connectWithRetry,
    syncDatabase
};