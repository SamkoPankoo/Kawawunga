const { Sequelize } = require('sequelize');
const dotenv = require('dotenv');
const path = require('path');
const fs = require('fs');


const env = process.env.NODE_ENV || 'development';
const envPath = path.resolve(process.cwd(), `.env.${env}`);


if (fs.existsSync(envPath)) {
    console.log(`Using environment config from ${envPath}`);
    dotenv.config({ path: envPath });
} else {
    console.log('Using default .env file');
    dotenv.config();
}


const config = {
    development: {
        host: process.env.DB_HOST || 'localhost',
        port: process.env.DB_PORT || 3306,
        database: process.env.DB_NAME || 'pdfeditor',
        username: process.env.DB_USER || 'root',
        password: process.env.DB_PASSWORD || 'rootpassword',
        dialect: 'mysql',
        logging: console.log
    },
    production: {
        host: process.env.DB_HOST,
        port: process.env.DB_PORT || 3306,
        database: process.env.DB_NAME,
        username: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        dialect: 'mysql',
        logging: false,
        pool: {
            max: 10,
            min: 0,
            acquire: 30000,
            idle: 10000
        }
    },
    test: {
        host: process.env.DB_HOST || 'localhost',
        port: process.env.DB_PORT || 3306,
        database: process.env.DB_NAME || 'pdfeditor_test',
        username: process.env.DB_USER || 'root',
        password: process.env.DB_PASSWORD || 'rootpassword',
        dialect: 'mysql',
        logging: false
    }
};


const dbConfig = config[env];

console.log(`Connecting to ${dbConfig.dialect} database at ${dbConfig.host}:${dbConfig.port}/${dbConfig.database}`);

const sequelize = new Sequelize(
    dbConfig.database,
    dbConfig.username,
    dbConfig.password,
    {
        host: dbConfig.host,
        port: dbConfig.port,
        dialect: dbConfig.dialect,
        logging: dbConfig.logging,
        pool: dbConfig.pool || {
            max: 5,
            min: 0,
            acquire: 30000,
            idle: 10000
        }
    }
);

module.exports = sequelize;