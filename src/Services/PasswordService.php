<?php

namespace App\Services;

use Exception;

class PasswordService
{
    private const HASH_ALGO = PASSWORD_ARGON2ID;
    private const MIN_LENGTH = 8;
    
    public function hashPassword(string $password): string
    {
        if (strlen($password) < self::MIN_LENGTH) {
            throw new Exception('Password must be at least ' . self::MIN_LENGTH . ' characters long.');
        }
        
        $hash = password_hash($password, self::HASH_ALGO, [
            'memory_cost' => 65536,    // 64MB
            'time_cost' => 4,          // 4 iterations
            'threads' => 3             // 3 threads
        ]);
        
        if ($hash === false) {
            throw new Exception('Failed to hash password.');
        }
        
        return $hash;
    }
    
    public function verifyPassword(string $password, string $hash): bool
    {
        return password_verify($password, $hash);
    }
    
    public function needsRehash(string $hash): bool
    {
        return password_needs_rehash($hash, self::HASH_ALGO, [
            'memory_cost' => 65536,
            'time_cost' => 4,
            'threads' => 3
        ]);
    }
    
    public function validatePasswordStrength(string $password): array
    {
        $errors = [];
        
        if (strlen($password) < self::MIN_LENGTH) {
            $errors[] = 'Password must be at least ' . self::MIN_LENGTH . ' characters long.';
        }
        
        if (!preg_match('/[A-Z]/', $password)) {
            $errors[] = 'Password must contain at least one uppercase letter.';
        }
        
        if (!preg_match('/[a-z]/', $password)) {
            $errors[] = 'Password must contain at least one lowercase letter.';
        }
        
        if (!preg_match('/[0-9]/', $password)) {
            $errors[] = 'Password must contain at least one number.';
        }
        
        if (!preg_match('/[^A-Za-z0-9]/', $password)) {
            $errors[] = 'Password must contain at least one special character.';
        }
        
        return $errors;
    }
    
    public function generateSecurePassword(int $length = 16): string
    {
        $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
        $password = '';
        
        // Ensure at least one character from each required category
        $password .= $this->getRandomChar('abcdefghijklmnopqrstuvwxyz'); // lowercase
        $password .= $this->getRandomChar('ABCDEFGHIJKLMNOPQRSTUVWXYZ'); // uppercase
        $password .= $this->getRandomChar('0123456789'); // number
        $password .= $this->getRandomChar('!@#$%^&*()_+-=[]{}|;:,.<>?'); // special
        
        // Fill the rest with random characters
        for ($i = 4; $i < $length; $i++) {
            $password .= $this->getRandomChar($chars);
        }
        
        // Shuffle the password to make it more random
        return str_shuffle($password);
    }
    
    private function getRandomChar(string $chars): string
    {
        return $chars[random_int(0, strlen($chars) - 1)];
    }
}
