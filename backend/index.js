const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const dotenv = require('dotenv');
const sequelize = require('./config/database');
const { connectWithRetry } = require('./config/database');
const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const historyRoutes = require('./routes/history');
const pdfLogsRoutes = require('./routes/pdfLogs');
const apiKeyMiddleware = require('./middleware/apiKey');
const { initializeAdmin } = require('./init-data');
const swaggerUi = require('swagger-ui-express');
const swaggerDocument = require('./swagger.json');
try {
    console.log('Loading swagger document:', swaggerDocument);
} catch (error) {
    console.error('Error loading swagger document:', error);
}

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
app.use('/api/pdfLogs', pdfLogsRoutes);

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'OK', message: 'PDF Editor API is running' });
});

// Swagger API documentation
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ message: 'Something went wrong!' });
});

const PORT = process.env.PORT || 3000;

// Database sync and server start
connectWithRetry()
    .then(async () => {
        await sequelize.sync({ alter: true });
        console.log('Database connected and synced successfully');

        // Initialize admin user if it doesn't exist
        await initializeAdmin();

        app.listen(PORT, '0.0.0.0', () => {
            console.log(`Server running on port ${PORT}`);
        });
    })
    .catch(err => {
        console.error('Unable to connect to the database after multiple retries:', err);
        process.exit(1);
    });

