const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const dotenv = require('dotenv');
const sequelize = require('./config/database');
const authRoutes = require('./routes/auth');
const userRoutes = require('./models/User');
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

app.get('/api/api-docs-spec', (req, res) => {
    try {
        res.json(require('./swagger.json'));
    } catch (error) {
        console.error('Error loading swagger document:', error);
        res.status(500).json({ error: 'Failed to load API documentation' });
    }
});
// Swagger API documentation
app.get('/api-docs-spec', (req, res) => {
    res.json(swaggerDocument);
});
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument, {
    explorer: true,
    customCss: '.swagger-ui .topbar { display: none }',
    swaggerOptions: {
        docExpansion: 'list',
        filter: true,
        showRequestDuration: true,
    }
}));

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ message: 'Something went wrong!' });
});

const PORT = process.env.PORT || 3000;

// Database sync and server start
const { connectWithRetry, syncDatabase } = require('./config/db-connection');

connectWithRetry()
    .then(() => syncDatabase({ alter: true }))
    .then(async () => {
        console.log('Database connected and synced successfully');

        // Initialize admin user if it doesn't exist
        await initializeAdmin();

        app.listen(PORT, '0.0.0.0', () => {
            console.log(`Server running on port ${PORT}`);
        });
    })
    .catch(err => {
        console.error('Unable to connect to the database:', err);
    });
