<?php

namespace App\Controllers;

use App\Models\User;
use App\Services\JWTService;
use App\Services\ValidationService;
use App\Services\EmailService;
use Exception;

class AuthController
{
    private User $userModel;
    private JWTService $jwtService;
    private ValidationService $validationService;
    private EmailService $emailService;
    
    public function __construct()
    {
        $this->userModel = new User();
        $this->jwtService = new JWTService();
        $this->validationService = new ValidationService();
        $this->emailService = new EmailService();
    }
    
    public function register(): array
    {
        try {
            // Get and validate input
            $input = $this->getJsonInput();
            $this->validationService->validateRegistration($input);
            
            // Sanitize input
            $sanitizedData = [
                'first_name' => $this->validationService->sanitizeName($input['first_name']),
                'last_name' => $this->validationService->sanitizeName($input['last_name']),
                'email' => $this->validationService->sanitizeEmail($input['email']),
                'password' => $input['password'],
                'newsletter_subscribed' => $input['newsletter_subscribed'] ?? false
            ];
            
            // Create user
            $user = $this->userModel->create($sanitizedData);
            
            // Send verification email
            $this->emailService->sendVerificationEmail($user['email'], $user['email_verification_token']);
            
            // Generate JWT token
            $token = $this->jwtService->generateUserToken($user);
            
            return [
                'success' => true,
                'message' => 'Account created successfully! Please check your email to verify your account.',
                'user' => $this->sanitizeUserData($user),
                'token' => $token
            ];
            
        } catch (Exception $e) {
            return $this->errorResponse($e->getMessage());
        }
    }
    
    public function login(): array
    {
        try {
            // Get and validate input
            $input = $this->getJsonInput();
            $this->validationService->validateLogin($input);
            
            // Sanitize email
            $email = $this->validationService->sanitizeEmail($input['email']);
            $password = $input['password'];
            
            // Authenticate user
            $user = $this->userModel->authenticate($email, $password);
            
            if (!$user) {
                return $this->errorResponse('Invalid email or password.', 401);
            }
            
            // Generate JWT token
            $token = $this->jwtService->generateUserToken($user);
            
            return [
                'success' => true,
                'message' => 'Login successful',
                'user' => $this->sanitizeUserData($user),
                'token' => $token
            ];
            
        } catch (Exception $e) {
            return $this->errorResponse($e->getMessage());
        }
    }
    
    public function verifyEmail(): array
    {
        try {
            $input = $this->getJsonInput();
            $this->validationService->validateEmailVerification($input);
            
            $token = $input['token'];
            
            // Verify email
            $success = $this->userModel->verifyEmail($token);
            
            if (!$success) {
                return $this->errorResponse('Invalid or expired verification token.', 400);
            }
            
            return [
                'success' => true,
                'message' => 'Email verified successfully! You can now log in.'
            ];
            
        } catch (Exception $e) {
            return $this->errorResponse($e->getMessage());
        }
    }
    
    public function forgotPassword(): array
    {
        try {
            $input = $this->getJsonInput();
            $this->validationService->validatePasswordReset($input);
            
            $email = $this->validationService->sanitizeEmail($input['email']);
            
            // Find user
            $user = $this->userModel->findByEmail($email);
            
            if (!$user) {
                // Don't reveal if email exists or not
                return [
                    'success' => true,
                    'message' => 'If an account with that email exists, a password reset link has been sent.'
                ];
            }
            
            // Generate reset token
            $resetToken = bin2hex(random_bytes(32));
            $resetExpires = date('Y-m-d H:i:s', strtotime('+1 hour'));
            
            // Update user with reset token
            $this->userModel->update([
                'id' => $user['id'],
                'password_reset_token' => $resetToken,
                'password_reset_expires_at' => $resetExpires
            ]);
            
            // Send reset email
            $this->emailService->sendPasswordResetEmail($email, $resetToken);
            
            return [
                'success' => true,
                'message' => 'If an account with that email exists, a password reset link has been sent.'
            ];
            
        } catch (Exception $e) {
            return $this->errorResponse($e->getMessage());
        }
    }
    
    public function resetPassword(): array
    {
        try {
            $input = $this->getJsonInput();
            $this->validationService->validatePasswordResetConfirm($input);
            
            $token = $input['token'];
            $password = $input['password'];
            
            // Find user by reset token
            $user = $this->userModel->findByResetToken($token);
            
            if (!$user) {
                return $this->errorResponse('Invalid or expired reset token.', 400);
            }
            
            // Update password
            $passwordHash = (new \App\Services\PasswordService())->hashPassword($password);
            
            $this->userModel->update([
                'id' => $user['id'],
                'password_hash' => $passwordHash,
                'password_reset_token' => null,
                'password_reset_expires_at' => null
            ]);
            
            return [
                'success' => true,
                'message' => 'Password reset successfully! You can now log in with your new password.'
            ];
            
        } catch (Exception $e) {
            return $this->errorResponse($e->getMessage());
        }
    }
    
    public function refreshToken(): array
    {
        try {
            $headers = getallheaders();
            $authHeader = $headers['Authorization'] ?? $headers['authorization'] ?? '';
            
            if (!preg_match('/Bearer\s+(.*)$/i', $authHeader, $matches)) {
                return $this->errorResponse('No token provided.', 401);
            }
            
            $token = $matches[1];
            
            // Validate current token
            $payload = $this->jwtService->validateUserToken($token);
            
            // Generate new token
            $newToken = $this->jwtService->generateUserToken($payload);
            
            return [
                'success' => true,
                'message' => 'Token refreshed successfully',
                'token' => $newToken
            ];
            
        } catch (Exception $e) {
            return $this->errorResponse($e->getMessage(), 401);
        }
    }
    
    public function logout(): array
    {
        // In a stateless JWT system, logout is typically handled client-side
        // by removing the token. However, you could implement a blacklist.
        
        return [
            'success' => true,
            'message' => 'Logged out successfully'
        ];
    }
    
    public function profile(): array
    {
        try {
            $headers = getallheaders();
            $authHeader = $headers['Authorization'] ?? $headers['authorization'] ?? '';
            
            if (!preg_match('/Bearer\s+(.*)$/i', $authHeader, $matches)) {
                return $this->errorResponse('No token provided.', 401);
            }
            
            $token = $matches[1];
            $payload = $this->jwtService->validateUserToken($token);
            
            $user = $this->userModel->findById($payload['user_id']);
            
            if (!$user) {
                return $this->errorResponse('User not found.', 404);
            }
            
            return [
                'success' => true,
                'user' => $this->sanitizeUserData($user)
            ];
            
        } catch (Exception $e) {
            return $this->errorResponse($e->getMessage(), 401);
        }
    }
    
    private function getJsonInput(): array
    {
        $input = json_decode(file_get_contents('php://input'), true);
        
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception('Invalid JSON input.');
        }
        
        return $input ?? [];
    }
    
    private function sanitizeUserData(array $user): array
    {
        // Remove sensitive fields
        unset($user['password_hash']);
        unset($user['email_verification_token']);
        unset($user['password_reset_token']);
        unset($user['failed_login_attempts']);
        unset($user['locked_until']);
        
        return $user;
    }
    
    private function errorResponse(string $message, int $statusCode = 400): array
    {
        http_response_code($statusCode);
        
        return [
            'success' => false,
            'message' => $message
        ];
    }
}
