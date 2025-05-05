const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const dotenv = require('dotenv');
const sequelize = require('./config/database');
const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const historyRoutes = require('./routes/history');
const apiKeyMiddleware = require('./middleware/apiKey');
const { initializeAdmin } = require('./init-data');

dotenv.config();

const app = express();

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', apiKeyMiddleware, userRoutes);
app.use('/api/history', apiKeyMiddleware, historyRoutes);

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'OK', message: 'PDF Editor API is running' });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ message: 'Something went wrong!' });
});

const PORT = process.env.PORT || 3000;

// Database sync and server start
sequelize.sync({ alter: true })
    .then(async () => {
        console.log('Database connected successfully');

        // Inicializuj admin používateľa, ak neexistuje
        await initializeAdmin();

        app.listen(PORT, '0.0.0.0', () => {
            console.log(`Server running on port ${PORT}`);
        });
    })
    .catch(err => {
        console.error('Unable to connect to the database:', err);
    });