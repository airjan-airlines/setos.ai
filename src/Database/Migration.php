<?php

namespace App\Database;

use Exception;

class Migration
{
    private Database $database;
    
    public function __construct()
    {
        $this->database = Database::getInstance();
    }
    
    public function createUsersTable(): void
    {
        $sql = "
            CREATE TABLE IF NOT EXISTS users (
                id CHAR(36) PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email_verified_at TIMESTAMP NULL,
                email_verification_token VARCHAR(255) NULL,
                email_verification_expires_at TIMESTAMP NULL,
                newsletter_subscribed BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                failed_login_attempts INT DEFAULT 0,
                locked_until TIMESTAMP NULL,
                password_reset_token VARCHAR(255) NULL,
                password_reset_expires_at TIMESTAMP NULL,
                last_login_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_email (email),
                INDEX idx_email_verification_token (email_verification_token),
                INDEX idx_password_reset_token (password_reset_token),
                INDEX idx_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        ";
        
        try {
            $this->database->getConnection()->exec($sql);
            echo "Users table created successfully.\n";
        } catch (Exception $e) {
            throw new Exception("Failed to create users table: " . $e->getMessage());
        }
    }
    
    public function createUserSessionsTable(): void
    {
        $sql = "
            CREATE TABLE IF NOT EXISTS user_sessions (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36) NOT NULL,
                token_hash VARCHAR(255) NOT NULL,
                ip_address VARCHAR(45) NULL,
                user_agent TEXT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_token_hash (token_hash),
                INDEX idx_expires_at (expires_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        ";
        
        try {
            $this->database->getConnection()->exec($sql);
            echo "User sessions table created successfully.\n";
        } catch (Exception $e) {
            throw new Exception("Failed to create user sessions table: " . $e->getMessage());
        }
    }
    
    public function createLoginAttemptsTable(): void
    {
        $sql = "
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                ip_address VARCHAR(45) NOT NULL,
                user_agent TEXT NULL,
                success BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_email (email),
                INDEX idx_ip_address (ip_address),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        ";
        
        try {
            $this->database->getConnection()->exec($sql);
            echo "Login attempts table created successfully.\n";
        } catch (Exception $e) {
            throw new Exception("Failed to create login attempts table: " . $e->getMessage());
        }
    }
    
    public function runAllMigrations(): void
    {
        echo "Starting database migrations...\n";
        
        $this->createUsersTable();
        $this->createUserSessionsTable();
        $this->createLoginAttemptsTable();
        
        echo "All migrations completed successfully.\n";
    }
}
