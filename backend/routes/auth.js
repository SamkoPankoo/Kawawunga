const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const User = require('../models/User');
const History = require('../models/History');
const authMiddleware = require('../middleware/auth');
const { getLocationInfo } = require('../utils/location');

// Register
router.post('/register', async (req, res) => {
    try {
        const { email, password } = req.body;

        // Check if user already exists
        const existingUser = await User.findOne({ where: { email } });
        if (existingUser) {
            return res.status(400).json({ message: 'Email already registered' });
        }

        // Create user
        const user = await User.create({
            email,
            password,
            apiKey: crypto.randomBytes(32).toString('hex')
        });

        res.status(201).json({
            message: 'User registered successfully',
            user: {
                id: user.id,
                email: user.email,
                role: user.role
            }
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Registration failed' });
    }
});

// Login
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        // Find user
        const user = await User.findOne({ where: { email } });
        if (!user) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }

        // Validate password
        const isValid = await user.validatePassword(password);
        if (!isValid) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }

        // Generate token
        const token = jwt.sign(
            { id: user.id, email: user.email, role: user.role },
            process.env.JWT_SECRET || 'your-secret-key',
            { expiresIn: '24h' }
        );

        // Update last login
        user.lastLogin = new Date();
        await user.save();

        // Log history
        const location = await getLocationInfo(req.ip);
        await History.create({
            userId: user.id,
            action: 'login',
            description: 'User logged in',
            ipAddress: req.ip,
            userAgent: req.headers['user-agent'],
            city: location.city,
            country: location.country,
            accessType: 'frontend'
        });

        res.json({
            token,
            user: {
                id: user.id,
                email: user.email,
                role: user.role
            }
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Login failed' });
    }
});

// Get current user
router.get('/me', authMiddleware, async (req, res) => {
    try {
        const user = await User.findByPk(req.user.id, {
            attributes: ['id', 'email', 'role', 'apiKey', 'lastLogin']
        });
        res.json(user);
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Failed to fetch user' });
    }
});

// Generate new API key
router.post('/generate-api-key', authMiddleware, async (req, res) => {
    try {
        const user = await User.findByPk(req.user.id);
        user.apiKey = crypto.randomBytes(32).toString('hex');
        await user.save();

        res.json({ apiKey: user.apiKey });
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Failed to generate API key' });
    }
});

module.exports = router;
//backend/routes/auth.js