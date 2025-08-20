const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const path = require('path');
const { initializeDatabase, userOperations } = require('./database');
const { generateVerificationToken, sendVerificationEmail } = require('./emailService');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// JWT secret (in production, use environment variable)
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production';

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Register endpoint
app.post('/api/register', async (req, res) => {
    try {
        const { firstName, lastName, email, password, newsletter } = req.body;

        // Validate input
        if (!firstName || !lastName || !email || !password) {
            return res.status(400).json({ 
                success: false, 
                message: 'All fields are required' 
            });
        }

        // Check if user already exists
        const existingUser = await userOperations.findByEmail(email);
        if (existingUser) {
            return res.status(400).json({ 
                success: false, 
                message: 'User with this email already exists' 
            });
        }

        // Check if email has been verified during registration
        if (!global.pendingVerifications || !global.pendingVerifications[email] || !global.pendingVerifications[email].verified) {
            return res.status(400).json({ 
                success: false, 
                message: 'Please verify your email address before creating an account' 
            });
        }

        // Hash password
        const saltRounds = 10;
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        // Create user object (email is already verified)
        const newUser = {
            id: Date.now().toString(),
            firstName,
            lastName,
            email,
            password: hashedPassword,
            newsletter: newsletter === 'on',
            emailVerified: true, // Email is already verified
            emailVerificationToken: null,
            emailVerificationExpires: null,
            createdAt: new Date().toISOString()
        };

        // Add user to database
        const savedUser = await userOperations.createUser(newUser);

        // Clean up pending verification data
        delete global.pendingVerifications[email];

        // Create JWT token for immediate login
        const token = jwt.sign(
            { userId: savedUser.id, email: savedUser.email },
            JWT_SECRET,
            { expiresIn: '24h' }
        );

        // Return success response (without password)
        const { password: _, ...userWithoutPassword } = savedUser;
        
        res.status(201).json({
            success: true,
            message: 'Account created successfully! You are now logged in.',
            user: userWithoutPassword,
            token
        });

    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Internal server error' 
        });
    }
});

// Login endpoint
app.post('/api/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        // Validate input
        if (!email || !password) {
            return res.status(400).json({ 
                success: false, 
                message: 'Email and password are required' 
            });
        }

        // Find user
        const user = await userOperations.findByEmail(email);
        if (!user) {
            return res.status(401).json({ 
                success: false, 
                message: 'Invalid email or password' 
            });
        }

        // Check password
        const isPasswordValid = await bcrypt.compare(password, user.password);
        if (!isPasswordValid) {
            return res.status(401).json({ 
                success: false, 
                message: 'Invalid email or password' 
            });
        }

        // Check if email is verified
        if (!user.emailVerified) {
            return res.status(401).json({ 
                success: false, 
                message: 'Please verify your email address before logging in. Check your inbox for a verification link.' 
            });
        }

        // Create JWT token
        const token = jwt.sign(
            { userId: user.id, email: user.email },
            JWT_SECRET,
            { expiresIn: '24h' }
        );

        // Return success response (without password)
        const { password: _, ...userWithoutPassword } = user;
        
        res.json({
            success: true,
            message: 'Login successful',
            user: userWithoutPassword,
            token
        });

    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Internal server error' 
        });
    }
});

// Protected route example
app.get('/api/profile', authenticateToken, async (req, res) => {
    try {
        const user = await userOperations.findById(req.user.userId);
        if (!user) {
            return res.status(404).json({ 
                success: false, 
                message: 'User not found' 
            });
        }

        const { password: _, ...userWithoutPassword } = user;
        res.json({
            success: true,
            user: userWithoutPassword
        });
    } catch (error) {
        console.error('Profile error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Internal server error' 
        });
    }
});

// Middleware to authenticate JWT token
function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ 
            success: false, 
            message: 'Access token required' 
        });
    }

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) {
            return res.status(403).json({ 
                success: false, 
                message: 'Invalid or expired token' 
            });
        }
        req.user = user;
        next();
    });
}

// Email verification endpoint
app.get('/verify-email', async (req, res) => {
    try {
        const { token } = req.query;
        
        if (!token) {
            return res.status(400).json({ 
                success: false, 
                message: 'Verification token is required' 
            });
        }

        // Find user by verification token
        const user = await userOperations.findByVerificationToken(token);
        if (!user) {
            return res.status(400).json({ 
                success: false, 
                message: 'Invalid or expired verification token' 
            });
        }

        // Check if token is expired
        if (new Date() > new Date(user.emailVerificationExpires)) {
            return res.status(400).json({ 
                success: false, 
                message: 'Verification token has expired. Please request a new one.' 
            });
        }

        // Update user to verified
        await userOperations.updateUser(user.id, {
            emailVerified: true,
            emailVerificationToken: null,
            emailVerificationExpires: null
        });

        // Send HTML response
        res.send(`
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Email Verified - setosa</title>
                <style>
                    body {
                        font-family: 'Inter', sans-serif;
                        margin: 0;
                        padding: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 20px;
                        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                        text-align: center;
                        max-width: 500px;
                        width: 90%;
                    }
                    .success-icon {
                        width: 80px;
                        height: 80px;
                        background: #10b981;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 20px;
                        font-size: 40px;
                        color: white;
                    }
                    h1 {
                        color: #333;
                        margin-bottom: 10px;
                    }
                    p {
                        color: #666;
                        line-height: 1.6;
                        margin-bottom: 30px;
                    }
                    .btn {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 15px 30px;
                        text-decoration: none;
                        border-radius: 25px;
                        display: inline-block;
                        font-weight: 500;
                        transition: transform 0.2s;
                    }
                    .btn:hover {
                        transform: translateY(-2px);
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">✓</div>
                    <h1>Email Verified!</h1>
                    <p>Your email address has been successfully verified. You can now log in to your setosa account and start your academic journey.</p>
                    <a href="/login.html" class="btn">Go to Login</a>
                </div>
            </body>
            </html>
        `);

    } catch (error) {
        console.error('Email verification error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Internal server error' 
        });
    }
});

// Send email verification during registration
app.post('/api/send-registration-verification', async (req, res) => {
    try {
        const { email, firstName } = req.body;
        
        if (!email || !firstName) {
            return res.status(400).json({ 
                success: false, 
                message: 'Email and first name are required' 
            });
        }

        // Check if user already exists
        const existingUser = await userOperations.findByEmail(email);
        if (existingUser) {
            return res.status(400).json({ 
                success: false, 
                message: 'User with this email already exists' 
            });
        }

        // Generate verification token
        const verificationToken = generateVerificationToken();
        const verificationExpires = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

        // Store verification data temporarily (you might want to use Redis in production)
        // For now, we'll store it in a simple object
        if (!global.pendingVerifications) {
            global.pendingVerifications = {};
        }
        
        global.pendingVerifications[email] = {
            firstName,
            verificationToken,
            verificationExpires,
            timestamp: Date.now()
        };

        // Send verification email
        const baseUrl = req.protocol + '://' + req.get('host');
        const emailSent = await sendVerificationEmail(email, firstName, verificationToken, baseUrl);

        if (!emailSent) {
            return res.status(500).json({ 
                success: false, 
                message: 'Failed to send verification email. Please try again later.' 
            });
        }

        res.json({
            success: true,
            message: 'Verification email sent successfully'
        });

    } catch (error) {
        console.error('Send registration verification error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Internal server error' 
        });
    }
});

// Verify email during registration
app.post('/api/verify-registration-email', async (req, res) => {
    try {
        const { email, token } = req.body;
        
        if (!email || !token) {
            return res.status(400).json({ 
                success: false, 
                message: 'Email and verification token are required' 
            });
        }

        // Check if verification data exists
        if (!global.pendingVerifications || !global.pendingVerifications[email]) {
            return res.status(400).json({ 
                success: false, 
                message: 'No pending verification found for this email' 
            });
        }

        const verificationData = global.pendingVerifications[email];

        // Check if token matches
        if (verificationData.verificationToken !== token) {
            return res.status(400).json({ 
                success: false, 
                message: 'Invalid verification token' 
            });
        }

        // Check if token is expired
        if (new Date() > new Date(verificationData.verificationExpires)) {
            delete global.pendingVerifications[email];
            return res.status(400).json({ 
                success: false, 
                message: 'Verification token has expired. Please request a new one.' 
            });
        }

        // Mark email as verified for registration
        global.pendingVerifications[email].verified = true;

        res.json({
            success: true,
            message: 'Email verified successfully'
        });

    } catch (error) {
        console.error('Verify registration email error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Internal server error' 
        });
    }
});

// Resend verification email endpoint
app.post('/api/resend-verification', async (req, res) => {
    try {
        const { email } = req.body;
        
        if (!email) {
            return res.status(400).json({ 
                success: false, 
                message: 'Email is required' 
            });
        }

        // Find user
        const user = await userOperations.findByEmail(email);
        if (!user) {
            return res.status(404).json({ 
                success: false, 
                message: 'User not found' 
            });
        }

        if (user.emailVerified) {
            return res.status(400).json({ 
                success: false, 
                message: 'Email is already verified' 
            });
        }

        // Generate new verification token
        const verificationToken = generateVerificationToken();
        const verificationExpires = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

        // Update user with new token
        await userOperations.updateUser(user.id, {
            emailVerificationToken: verificationToken,
            emailVerificationExpires: verificationExpires
        });

        // Send verification email
        const baseUrl = req.protocol + '://' + req.get('host');
        const emailSent = await sendVerificationEmail(email, user.firstName, verificationToken, baseUrl);

        if (!emailSent) {
            return res.status(500).json({ 
                success: false, 
                message: 'Failed to send verification email. Please try again later.' 
            });
        }

        res.json({
            success: true,
            message: 'Verification email sent successfully'
        });

    } catch (error) {
        console.error('Resend verification error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Internal server error' 
        });
    }
});

// Get all users (for development purposes)
app.get('/api/users', async (req, res) => {
    try {
        const users = await userOperations.getAllUsers();
        res.json({
            success: true,
            users: users
        });
    } catch (error) {
        console.error('Get users error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Internal server error' 
        });
    }
});

// Initialize database and start server
async function startServer() {
    try {
        await initializeDatabase();
        app.listen(PORT, () => {
            console.log(`Server running on http://localhost:${PORT}`);
            console.log(`Registration API: http://localhost:${PORT}/api/register`);
            console.log(`Login API: http://localhost:${PORT}/api/login`);
            console.log('Database: SQLite (users.db)');
        });
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}

startServer();
