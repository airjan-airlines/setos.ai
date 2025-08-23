<?php

namespace App\Models;

use App\Database\Database;
use App\Services\PasswordService;
use App\Services\ValidationService;
use Exception;
use Ramsey\Uuid\Uuid;

class User
{
    private Database $database;
    private PasswordService $passwordService;
    private ValidationService $validationService;
    
    public function __construct()
    {
        $this->database = Database::getInstance();
        $this->passwordService = new PasswordService();
        $this->validationService = new ValidationService();
    }
    
    public function create(array $data): array
    {
        // Validate input data
        $this->validationService->validateRegistration($data);
        
        // Check if user already exists
        if ($this->findByEmail($data['email'])) {
            throw new Exception('An account with this email already exists.');
        }
        
        // Hash password
        $passwordHash = $this->passwordService->hashPassword($data['password']);
        
        // Generate UUID
        $userId = Uuid::uuid4()->toString();
        
        // Generate email verification token
        $verificationToken = bin2hex(random_bytes(32));
        $verificationExpires = date('Y-m-d H:i:s', strtotime('+24 hours'));
        
        $sql = "
            INSERT INTO users (
                id, first_name, last_name, email, password_hash,
                email_verification_token, email_verification_expires_at,
                newsletter_subscribed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW())
        ";
        
        try {
            $stmt = $this->database->prepare($sql);
            $stmt->execute([
                $userId,
                $data['first_name'],
                $data['last_name'],
                $data['email'],
                $passwordHash,
                $verificationToken,
                $verificationExpires,
                $data['newsletter_subscribed'] ?? false
            ]);
            
            return [
                'id' => $userId,
                'first_name' => $data['first_name'],
                'last_name' => $data['last_name'],
                'email' => $data['email'],
                'email_verified_at' => null,
                'newsletter_subscribed' => $data['newsletter_subscribed'] ?? false,
                'email_verification_token' => $verificationToken,
                'created_at' => date('Y-m-d H:i:s')
            ];
        } catch (Exception $e) {
            throw new Exception('Failed to create user: ' . $e->getMessage());
        }
    }
    
    public function findByEmail(string $email): ?array
    {
        $sql = "SELECT * FROM users WHERE email = ? AND is_active = TRUE";
        
        try {
            $stmt = $this->database->prepare($sql);
            $stmt->execute([$email]);
            $user = $stmt->fetch();
            
            return $user ?: null;
        } catch (Exception $e) {
            throw new Exception('Failed to find user: ' . $e->getMessage());
        }
    }
    
    public function findById(string $id): ?array
    {
        $sql = "SELECT * FROM users WHERE id = ? AND is_active = TRUE";
        
        try {
            $stmt = $this->database->prepare($sql);
            $stmt->execute([$id]);
            $user = $stmt->fetch();
            
            return $user ?: null;
        } catch (Exception $e) {
            throw new Exception('Failed to find user: ' . $e->getMessage());
        }
    }
    
    public function findByVerificationToken(string $token): ?array
    {
        $sql = "
            SELECT * FROM users 
            WHERE email_verification_token = ? 
            AND email_verification_expires_at > NOW()
            AND is_active = TRUE
        ";
        
        try {
            $stmt = $this->database->prepare($sql);
            $stmt->execute([$token]);
            $user = $stmt->fetch();
            
            return $user ?: null;
        } catch (Exception $e) {
            throw new Exception('Failed to find user by verification token: ' . $e->getMessage());
        }
    }
    
    public function verifyEmail(string $token): bool
    {
        $user = $this->findByVerificationToken($token);
        if (!$user) {
            return false;
        }
        
        $sql = "
            UPDATE users 
            SET email_verified_at = NOW(),
                email_verification_token = NULL,
                email_verification_expires_at = NULL,
                updated_at = NOW()
            WHERE id = ?
        ";
        
        try {
            $stmt = $this->database->prepare($sql);
            return $stmt->execute([$user['id']]);
        } catch (Exception $e) {
            throw new Exception('Failed to verify email: ' . $e->getMessage());
        }
    }
    
    public function authenticate(string $email, string $password): ?array
    {
        $user = $this->findByEmail($email);
        if (!$user) {
            return null;
        }
        
        // Check if account is locked
        if ($user['locked_until'] && $user['locked_until'] > date('Y-m-d H:i:s')) {
            throw new Exception('Account is temporarily locked. Please try again later.');
        }
        
        // Verify password
        if (!$this->passwordService->verifyPassword($password, $user['password_hash'])) {
            $this->incrementFailedLoginAttempts($user['id']);
            return null;
        }
        
        // Check if email is verified
        if (!$user['email_verified_at']) {
            throw new Exception('Please verify your email address before logging in.');
        }
        
        // Reset failed login attempts and update last login
        $this->resetFailedLoginAttempts($user['id']);
        $this->updateLastLogin($user['id']);
        
        // Remove sensitive data
        unset($user['password_hash']);
        unset($user['email_verification_token']);
        unset($user['password_reset_token']);
        
        return $user;
    }
    
    private function incrementFailedLoginAttempts(string $userId): void
    {
        $sql = "
            UPDATE users 
            SET failed_login_attempts = failed_login_attempts + 1,
                locked_until = CASE 
                    WHEN failed_login_attempts >= ? THEN DATE_ADD(NOW(), INTERVAL ? SECOND)
                    ELSE locked_until 
                END,
                updated_at = NOW()
            WHERE id = ?
        ";
        
        $maxAttempts = (int)($_ENV['MAX_LOGIN_ATTEMPTS'] ?? 5);
        $lockoutDuration = (int)($_ENV['LOGIN_LOCKOUT_DURATION'] ?? 900);
        
        try {
            $stmt = $this->database->prepare($sql);
            $stmt->execute([$maxAttempts, $lockoutDuration, $userId]);
        } catch (Exception $e) {
            // Log error but don't throw to avoid exposing internal errors
            error_log('Failed to increment login attempts: ' . $e->getMessage());
        }
    }
    
    private function resetFailedLoginAttempts(string $userId): void
    {
        $sql = "
            UPDATE users 
            SET failed_login_attempts = 0,
                locked_until = NULL,
                updated_at = NOW()
            WHERE id = ?
        ";
        
        try {
            $stmt = $this->database->prepare($sql);
            $stmt->execute([$userId]);
        } catch (Exception $e) {
            error_log('Failed to reset login attempts: ' . $e->getMessage());
        }
    }
    
    private function updateLastLogin(string $userId): void
    {
        $sql = "UPDATE users SET last_login_at = NOW(), updated_at = NOW() WHERE id = ?";
        
        try {
            $stmt = $this->database->prepare($sql);
            $stmt->execute([$userId]);
        } catch (Exception $e) {
            error_log('Failed to update last login: ' . $e->getMessage());
        }
    }
    
    public function update(array $data): bool
    {
        $allowedFields = ['first_name', 'last_name', 'newsletter_subscribed'];
        $updates = [];
        $values = [];
        
        foreach ($data as $field => $value) {
            if (in_array($field, $allowedFields)) {
                $updates[] = "{$field} = ?";
                $values[] = $value;
            }
        }
        
        if (empty($updates)) {
            return false;
        }
        
        $values[] = $data['id'];
        $sql = "UPDATE users SET " . implode(', ', $updates) . ", updated_at = NOW() WHERE id = ?";
        
        try {
            $stmt = $this->database->prepare($sql);
            return $stmt->execute($values);
        } catch (Exception $e) {
            throw new Exception('Failed to update user: ' . $e->getMessage());
        }
    }
    
    public function delete(string $id): bool
    {
        $sql = "UPDATE users SET is_active = FALSE, updated_at = NOW() WHERE id = ?";
        
        try {
            $stmt = $this->database->prepare($sql);
            return $stmt->execute([$id]);
        } catch (Exception $e) {
            throw new Exception('Failed to delete user: ' . $e->getMessage());
        }
    }
}
