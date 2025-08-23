<?php

namespace App\Services;

use Firebase\JWT\JWT;
use Firebase\JWT\Key;
use Exception;

class JWTService
{
    private string $secret;
    private string $algorithm;
    private int $expiry;
    
    public function __construct()
    {
        $this->secret = $_ENV['JWT_SECRET'] ?? 'your-secret-key-change-in-production';
        $this->algorithm = 'HS256';
        $this->expiry = (int)($_ENV['JWT_EXPIRY'] ?? 86400); // 24 hours default
    }
    
    public function generateToken(array $payload): string
    {
        $issuedAt = time();
        $expiration = $issuedAt + $this->expiry;
        
        $tokenPayload = [
            'iss' => $_ENV['APP_URL'] ?? 'http://localhost', // Issuer
            'aud' => $_ENV['APP_URL'] ?? 'http://localhost', // Audience
            'iat' => $issuedAt,                              // Issued at
            'nbf' => $issuedAt,                              // Not before
            'exp' => $expiration,                            // Expiration
            'jti' => bin2hex(random_bytes(16)),              // JWT ID
            'data' => $payload                               // Custom data
        ];
        
        try {
            return JWT::encode($tokenPayload, $this->secret, $this->algorithm);
        } catch (Exception $e) {
            throw new Exception('Failed to generate JWT token: ' . $e->getMessage());
        }
    }
    
    public function validateToken(string $token): array
    {
        try {
            $decoded = JWT::decode($token, new Key($this->secret, $this->algorithm));
            
            // Convert to array
            $payload = json_decode(json_encode($decoded), true);
            
            // Validate required fields
            if (!isset($payload['data']) || !isset($payload['exp'])) {
                throw new Exception('Invalid token structure.');
            }
            
            // Check if token is expired
            if ($payload['exp'] < time()) {
                throw new Exception('Token has expired.');
            }
            
            return $payload['data'];
        } catch (Exception $e) {
            throw new Exception('Invalid token: ' . $e->getMessage());
        }
    }
    
    public function refreshToken(string $token): string
    {
        try {
            // Decode the current token without validation
            $decoded = JWT::decode($token, new Key($this->secret, $this->algorithm));
            $payload = json_decode(json_encode($decoded), true);
            
            // Remove timestamp fields
            unset($payload['iat'], $payload['nbf'], $payload['exp'], $payload['jti']);
            
            // Generate new token
            return $this->generateToken($payload['data']);
        } catch (Exception $e) {
            throw new Exception('Failed to refresh token: ' . $e->getMessage());
        }
    }
    
    public function getTokenExpiration(string $token): int
    {
        try {
            $decoded = JWT::decode($token, new Key($this->secret, $this->algorithm));
            $payload = json_decode(json_encode($decoded), true);
            
            return $payload['exp'] ?? 0;
        } catch (Exception $e) {
            throw new Exception('Failed to get token expiration: ' . $e->getMessage());
        }
    }
    
    public function isTokenExpired(string $token): bool
    {
        try {
            $expiration = $this->getTokenExpiration($token);
            return $expiration < time();
        } catch (Exception $e) {
            return true; // Consider invalid tokens as expired
        }
    }
    
    public function generateUserToken(array $user): string
    {
        $payload = [
            'user_id' => $user['id'],
            'email' => $user['email'],
            'first_name' => $user['first_name'],
            'last_name' => $user['last_name'],
            'email_verified' => !empty($user['email_verified_at'])
        ];
        
        return $this->generateToken($payload);
    }
    
    public function validateUserToken(string $token): array
    {
        $payload = $this->validateToken($token);
        
        // Validate required user fields
        $requiredFields = ['user_id', 'email'];
        foreach ($requiredFields as $field) {
            if (!isset($payload[$field])) {
                throw new Exception("Missing required field: {$field}");
            }
        }
        
        return $payload;
    }
}
