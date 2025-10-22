const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Database file path
const dbPath = path.join(__dirname, 'users.db');

// Create database connection
const db = new sqlite3.Database(dbPath);

// Initialize database tables
function initializeDatabase() {
    return new Promise((resolve, reject) => {
        db.serialize(() => {
            // Create users table
            db.run(`
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    firstName TEXT NOT NULL,
                    lastName TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    newsletter BOOLEAN DEFAULT 0,
                    emailVerified BOOLEAN DEFAULT 0,
                    emailVerificationToken TEXT,
                    emailVerificationExpires TEXT,
                    createdAt TEXT NOT NULL
                )
            `, (err) => {
                if (err) {
                    console.error('Error creating users table:', err);
                    reject(err);
                    return;
                }
                console.log('Database initialized successfully');
                resolve();
            });
        });
    });
}

// User operations
const userOperations = {
    // Create a new user
    createUser: (userData) => {
        return new Promise((resolve, reject) => {
            const { id, firstName, lastName, email, password, newsletter, emailVerified, emailVerificationToken, emailVerificationExpires, createdAt } = userData;
            db.run(
                'INSERT INTO users (id, firstName, lastName, email, password, newsletter, emailVerified, emailVerificationToken, emailVerificationExpires, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                [id, firstName, lastName, email, password, newsletter ? 1 : 0, emailVerified ? 1 : 0, emailVerificationToken, emailVerificationExpires, createdAt],
                function(err) {
                    if (err) {
                        reject(err);
                    } else {
                        resolve({ id, firstName, lastName, email, newsletter, emailVerified, createdAt });
                    }
                }
            );
        });
    },

    // Find user by email
    findByEmail: (email) => {
        return new Promise((resolve, reject) => {
            db.get(
                'SELECT * FROM users WHERE email = ?',
                [email],
                (err, row) => {
                    if (err) {
                        reject(err);
                    } else {
                        resolve(row);
                    }
                }
            );
        });
    },

    // Find user by ID
    findById: (id) => {
        return new Promise((resolve, reject) => {
            db.get(
                'SELECT * FROM users WHERE id = ?',
                [id],
                (err, row) => {
                    if (err) {
                        reject(err);
                    } else {
                        resolve(row);
                    }
                }
            );
        });
    },

    // Find user by verification token
    findByVerificationToken: (token) => {
        return new Promise((resolve, reject) => {
            db.get(
                'SELECT * FROM users WHERE emailVerificationToken = ?',
                [token],
                (err, row) => {
                    if (err) {
                        reject(err);
                    } else {
                        resolve(row);
                    }
                }
            );
        });
    },

    // Get all users (for development)
    getAllUsers: () => {
        return new Promise((resolve, reject) => {
            db.all(
                'SELECT id, firstName, lastName, email, newsletter, createdAt FROM users',
                (err, rows) => {
                    if (err) {
                        reject(err);
                    } else {
                        resolve(rows);
                    }
                }
            );
        });
    },

    // Update user
    updateUser: (id, updates) => {
        return new Promise((resolve, reject) => {
            const fields = Object.keys(updates);
            const values = Object.values(updates);
            const setClause = fields.map(field => `${field} = ?`).join(', ');
            
            db.run(
                `UPDATE users SET ${setClause} WHERE id = ?`,
                [...values, id],
                function(err) {
                    if (err) {
                        reject(err);
                    } else {
                        resolve({ changes: this.changes });
                    }
                }
            );
        });
    },

    // Delete user
    deleteUser: (id) => {
        return new Promise((resolve, reject) => {
            db.run(
                'DELETE FROM users WHERE id = ?',
                [id],
                function(err) {
                    if (err) {
                        reject(err);
                    } else {
                        resolve({ changes: this.changes });
                    }
                }
            );
        });
    }
};

// Close database connection
function closeDatabase() {
    return new Promise((resolve) => {
        db.close((err) => {
            if (err) {
                console.error('Error closing database:', err);
            } else {
                console.log('Database connection closed');
            }
            resolve();
        });
    });
}

module.exports = {
    initializeDatabase,
    userOperations,
    closeDatabase
};
