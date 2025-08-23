<?php

namespace App\Services;

use Exception;

class ValidationService
{
    public function validateRegistration(array $data): void
    {
        $errors = [];
        
        // Validate first name
        if (empty($data['first_name']) || !$this->isValidName($data['first_name'])) {
            $errors[] = 'First name is required and must contain only letters, spaces, and hyphens (2-50 characters).';
        }
        
        // Validate last name
        if (empty($data['last_name']) || !$this->isValidName($data['last_name'])) {
            $errors[] = 'Last name is required and must contain only letters, spaces, and hyphens (2-50 characters).';
        }
        
        // Validate email
        if (empty($data['email']) || !$this->isValidEmail($data['email'])) {
            $errors[] = 'A valid email address is required.';
        }
        
        // Validate password
        if (empty($data['password'])) {
            $errors[] = 'Password is required.';
        } else {
            $passwordErrors = $this->validatePassword($data['password']);
            $errors = array_merge($errors, $passwordErrors);
        }
        
        if (!empty($errors)) {
            throw new Exception(implode(' ', $errors));
        }
    }
    
    public function validateLogin(array $data): void
    {
        $errors = [];
        
        // Validate email
        if (empty($data['email']) || !$this->isValidEmail($data['email'])) {
            $errors[] = 'A valid email address is required.';
        }
        
        // Validate password
        if (empty($data['password'])) {
            $errors[] = 'Password is required.';
        }
        
        if (!empty($errors)) {
            throw new Exception(implode(' ', $errors));
        }
    }
    
    public function validateEmailVerification(array $data): void
    {
        if (empty($data['token']) || !$this->isValidToken($data['token'])) {
            throw new Exception('Invalid verification token.');
        }
    }
    
    public function validatePasswordReset(array $data): void
    {
        $errors = [];
        
        // Validate email
        if (empty($data['email']) || !$this->isValidEmail($data['email'])) {
            $errors[] = 'A valid email address is required.';
        }
        
        if (!empty($errors)) {
            throw new Exception(implode(' ', $errors));
        }
    }
    
    public function validatePasswordResetConfirm(array $data): void
    {
        $errors = [];
        
        // Validate token
        if (empty($data['token']) || !$this->isValidToken($data['token'])) {
            $errors[] = 'Invalid reset token.';
        }
        
        // Validate password
        if (empty($data['password'])) {
            $errors[] = 'Password is required.';
        } else {
            $passwordErrors = $this->validatePassword($data['password']);
            $errors = array_merge($errors, $passwordErrors);
        }
        
        // Validate password confirmation
        if (empty($data['password_confirmation'])) {
            $errors[] = 'Password confirmation is required.';
        } elseif ($data['password'] !== $data['password_confirmation']) {
            $errors[] = 'Passwords do not match.';
        }
        
        if (!empty($errors)) {
            throw new Exception(implode(' ', $errors));
        }
    }
    
    private function isValidName(string $name): bool
    {
        // Allow letters, spaces, hyphens, and apostrophes, 2-50 characters
        return preg_match('/^[a-zA-Z\s\'-]{2,50}$/', trim($name));
    }
    
    private function isValidEmail(string $email): bool
    {
        // Use PHP's built-in email validation
        return filter_var(trim($email), FILTER_VALIDATE_EMAIL) !== false;
    }
    
    private function validatePassword(string $password): array
    {
        $errors = [];
        $passwordService = new PasswordService();
        
        $strengthErrors = $passwordService->validatePasswordStrength($password);
        if (!empty($strengthErrors)) {
            $errors = array_merge($errors, $strengthErrors);
        }
        
        return $errors;
    }
    
    private function isValidToken(string $token): bool
    {
        // Validate token format (64 character hex string)
        return preg_match('/^[a-f0-9]{64}$/', $token);
    }
    
    public function sanitizeInput(string $input): string
    {
        // Remove null bytes
        $input = str_replace(chr(0), '', $input);
        
        // Convert to UTF-8
        if (!mb_check_encoding($input, 'UTF-8')) {
            $input = mb_convert_encoding($input, 'UTF-8', 'UTF-8');
        }
        
        // Normalize whitespace
        $input = preg_replace('/\s+/', ' ', $input);
        
        // Trim whitespace
        $input = trim($input);
        
        return $input;
    }
    
    public function sanitizeEmail(string $email): string
    {
        $email = $this->sanitizeInput($email);
        return strtolower($email);
    }
    
    public function sanitizeName(string $name): string
    {
        $name = $this->sanitizeInput($name);
        
        // Capitalize first letter of each word
        $name = ucwords(strtolower($name));
        
        return $name;
    }
    
    public function validateCSRFToken(string $token, string $sessionToken): bool
    {
        if (empty($token) || empty($sessionToken)) {
            return false;
        }
        
        return hash_equals($sessionToken, $token);
    }
    
    public function generateCSRFToken(): string
    {
        return bin2hex(random_bytes(32));
    }
    
    public function validateRateLimit(string $identifier, int $maxAttempts = 5, int $timeWindow = 900): bool
    {
        // This would typically integrate with Redis or a similar cache
        // For now, we'll return true (no rate limiting)
        // In production, implement proper rate limiting
        return true;
    }
}
