<?php

namespace App\Services;

use Exception;

class EmailService
{
    private string $smtpHost;
    private int $smtpPort;
    private string $smtpUsername;
    private string $smtpPassword;
    private string $smtpEncryption;
    private string $fromEmail;
    private string $fromName;
    private string $appUrl;
    
    public function __construct()
    {
        $this->smtpHost = $_ENV['SMTP_HOST'] ?? 'smtp.gmail.com';
        $this->smtpPort = (int)($_ENV['SMTP_PORT'] ?? 587);
        $this->smtpUsername = $_ENV['SMTP_USERNAME'] ?? '';
        $this->smtpPassword = $_ENV['SMTP_PASSWORD'] ?? '';
        $this->smtpEncryption = $_ENV['SMTP_ENCRYPTION'] ?? 'tls';
        $this->fromEmail = $_ENV['SMTP_USERNAME'] ?? 'noreply@example.com';
        $this->fromName = $_ENV['APP_NAME'] ?? 'Setosa';
        $this->appUrl = $_ENV['APP_URL'] ?? 'http://localhost:8000';
    }
    
    public function sendVerificationEmail(string $email, string $token): bool
    {
        $subject = 'Verify Your Email Address';
        $verificationUrl = $this->appUrl . '/verify-email?token=' . $token;
        
        $htmlBody = $this->getVerificationEmailTemplate($verificationUrl);
        $textBody = $this->getVerificationEmailTextTemplate($verificationUrl);
        
        return $this->sendEmail($email, $subject, $htmlBody, $textBody);
    }
    
    public function sendPasswordResetEmail(string $email, string $token): bool
    {
        $subject = 'Reset Your Password';
        $resetUrl = $this->appUrl . '/reset-password?token=' . $token;
        
        $htmlBody = $this->getPasswordResetEmailTemplate($resetUrl);
        $textBody = $this->getPasswordResetEmailTextTemplate($resetUrl);
        
        return $this->sendEmail($email, $subject, $htmlBody, $textBody);
    }
    
    public function sendWelcomeEmail(string $email, string $firstName): bool
    {
        $subject = 'Welcome to Setosa!';
        
        $htmlBody = $this->getWelcomeEmailTemplate($firstName);
        $textBody = $this->getWelcomeEmailTextTemplate($firstName);
        
        return $this->sendEmail($email, $subject, $htmlBody, $textBody);
    }
    
    private function sendEmail(string $to, string $subject, string $htmlBody, string $textBody): bool
    {
        // In a real implementation, you would use PHPMailer or similar
        // For now, we'll simulate email sending
        
        try {
            // Log the email for development
            if ($_ENV['APP_ENV'] === 'development') {
                error_log("Email would be sent to: {$to}");
                error_log("Subject: {$subject}");
                error_log("HTML Body: {$htmlBody}");
            }
            
            // In production, implement actual email sending
            // Example with PHPMailer:
            /*
            $mail = new PHPMailer(true);
            $mail->isSMTP();
            $mail->Host = $this->smtpHost;
            $mail->SMTPAuth = true;
            $mail->Username = $this->smtpUsername;
            $mail->Password = $this->smtpPassword;
            $mail->SMTPSecure = $this->smtpEncryption;
            $mail->Port = $this->smtpPort;
            
            $mail->setFrom($this->fromEmail, $this->fromName);
            $mail->addAddress($to);
            $mail->isHTML(true);
            $mail->Subject = $subject;
            $mail->Body = $htmlBody;
            $mail->AltBody = $textBody;
            
            return $mail->send();
            */
            
            return true; // Simulate success
            
        } catch (Exception $e) {
            error_log('Email sending failed: ' . $e->getMessage());
            return false;
        }
    }
    
    private function getVerificationEmailTemplate(string $verificationUrl): string
    {
        return "
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset='utf-8'>
                <title>Verify Your Email</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #007bff; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background: #f9f9f9; }
                    .button { display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                    .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class='container'>
                    <div class='header'>
                        <h1>Verify Your Email Address</h1>
                    </div>
                    <div class='content'>
                        <p>Thank you for signing up for Setosa!</p>
                        <p>Please click the button below to verify your email address:</p>
                        <p style='text-align: center;'>
                            <a href='{$verificationUrl}' class='button'>Verify Email Address</a>
                        </p>
                        <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                        <p>{$verificationUrl}</p>
                        <p>This link will expire in 24 hours.</p>
                    </div>
                    <div class='footer'>
                        <p>If you didn't create an account, you can safely ignore this email.</p>
                    </div>
                </div>
            </body>
            </html>
        ";
    }
    
    private function getVerificationEmailTextTemplate(string $verificationUrl): string
    {
        return "
            Verify Your Email Address
            
            Thank you for signing up for Setosa!
            
            Please visit the following link to verify your email address:
            {$verificationUrl}
            
            This link will expire in 24 hours.
            
            If you didn't create an account, you can safely ignore this email.
        ";
    }
    
    private function getPasswordResetEmailTemplate(string $resetUrl): string
    {
        return "
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset='utf-8'>
                <title>Reset Your Password</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background: #f9f9f9; }
                    .button { display: inline-block; padding: 12px 24px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; }
                    .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class='container'>
                    <div class='header'>
                        <h1>Reset Your Password</h1>
                    </div>
                    <div class='content'>
                        <p>You requested a password reset for your Setosa account.</p>
                        <p>Click the button below to reset your password:</p>
                        <p style='text-align: center;'>
                            <a href='{$resetUrl}' class='button'>Reset Password</a>
                        </p>
                        <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                        <p>{$resetUrl}</p>
                        <p>This link will expire in 1 hour.</p>
                        <p>If you didn't request a password reset, you can safely ignore this email.</p>
                    </div>
                    <div class='footer'>
                        <p>For security reasons, this link will expire in 1 hour.</p>
                    </div>
                </div>
            </body>
            </html>
        ";
    }
    
    private function getPasswordResetEmailTextTemplate(string $resetUrl): string
    {
        return "
            Reset Your Password
            
            You requested a password reset for your Setosa account.
            
            Please visit the following link to reset your password:
            {$resetUrl}
            
            This link will expire in 1 hour.
            
            If you didn't request a password reset, you can safely ignore this email.
        ";
    }
    
    private function getWelcomeEmailTemplate(string $firstName): string
    {
        return "
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset='utf-8'>
                <title>Welcome to Setosa!</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #28a745; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background: #f9f9f9; }
                    .button { display: inline-block; padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; }
                    .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class='container'>
                    <div class='header'>
                        <h1>Welcome to Setosa!</h1>
                    </div>
                    <div class='content'>
                        <p>Hi {$firstName},</p>
                        <p>Welcome to Setosa! We're excited to have you on board.</p>
                        <p>Your account has been successfully created and verified. You can now:</p>
                        <ul>
                            <li>Access your dashboard</li>
                            <li>Access your personalized features</li>
                            <li>Collaborate with team members</li>
                            <li>Track your progress</li>
                        </ul>
                        <p style='text-align: center;'>
                            <a href='{$this->appUrl}/dashboard' class='button'>Go to Dashboard</a>
                        </p>
                        <p>If you have any questions, feel free to contact our support team.</p>
                    </div>
                    <div class='footer'>
                        <p>Thank you for choosing Setosa!</p>
                    </div>
                </div>
            </body>
            </html>
        ";
    }
    
    private function getWelcomeEmailTextTemplate(string $firstName): string
    {
        return "
            Welcome to Setosa!
            
            Hi {$firstName},
            
            Welcome to Setosa! We're excited to have you on board.
            
            Your account has been successfully created and verified. You can now:
            - Access your dashboard
            - Access your personalized features
            - Collaborate with team members
            - Track your progress
            
            Visit your dashboard: {$this->appUrl}/dashboard
            
            If you have any questions, feel free to contact our support team.
            
            Thank you for choosing Setosa!
        ";
    }
}
