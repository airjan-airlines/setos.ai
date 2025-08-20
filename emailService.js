const nodemailer = require('nodemailer');
const crypto = require('crypto');

// Try to load config file, fall back to environment variables
let config;
try {
    config = require('./config.js');
} catch (error) {
    console.warn('Config file not found, using environment variables or defaults');
    config = {
        email: {
            user: process.env.EMAIL_USER || 'your-email@gmail.com',
            pass: process.env.EMAIL_PASS || 'your-app-password',
            host: process.env.SMTP_HOST || 'smtp.gmail.com',
            port: process.env.SMTP_PORT || 587
        }
    };
}


// Log email configuration (without password)
console.log('Email configuration loaded:');
console.log(`- Host: ${config.email.host}`);
console.log(`- Port: ${config.email.port}`);
console.log(`- User: ${config.email.user}`);
console.log(`- Password: ${config.email.pass ? '[SET]' : '[NOT SET]'}`);

// Email configuration
const emailConfig = {
    host: config.email.host,
    port: config.email.port,
    secure: false, // true for 465, false for other ports
    auth: {
        user: config.email.user,
        pass: config.email.pass
    }
};

// Create transporter
const transporter = nodemailer.createTransport(emailConfig);

// Check if we have valid email configuration
const hasValidEmailConfig = config.email.user && 
                           config.email.pass && 
                           config.email.user !== 'your-email@gmail.com' && 
                           config.email.pass !== 'your-app-password';

// Generate verification token (6-digit code)
function generateVerificationToken() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

// Send verification email
async function sendVerificationEmail(email, firstName, verificationToken, baseUrl) {
    // Check if we have valid email configuration
    if (!hasValidEmailConfig) {
        console.log('⚠️  Email not configured - showing verification code instead');
        console.log(`📧 Verification code for ${email}: ${verificationToken}`);
        console.log(`🔗 Verification URL: ${baseUrl}/verify-email?token=${verificationToken}`);
        return true; // Return true to simulate success
    }

    const verificationUrl = `${baseUrl}/verify-email?token=${verificationToken}`;
    
    const mailOptions = {
        from: `"setosa" <${emailConfig.auth.user}>`,
        to: email,
        subject: 'Verify your setosa account',
        html: `
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to setosa!</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #333; margin-top: 0;">Hi ${firstName},</h2>
                    
                    <p style="color: #666; line-height: 1.6;">
                        Thank you for creating your setosa account! To complete your registration and start your academic journey, 
                        please verify your email address using the verification code below.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f0f4ff; border-radius: 10px; border: 2px solid #667eea;">
                        <h3 style="color: #333; margin: 0 0 10px 0; font-size: 16px;">Your 6-Digit Verification Code:</h3>
                        <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px; text-align: center;">
                            ${verificationToken}
                        </div>
                        <p style="color: #666; font-size: 14px; margin: 10px 0 0 0;">
                            Enter this 6-digit code on the sign-up page to verify your email
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${verificationUrl}" 
                           style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                  color: white; 
                                  padding: 15px 30px; 
                                  text-decoration: none; 
                                  border-radius: 25px; 
                                  display: inline-block; 
                                  font-weight: bold;
                                  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                            Or Click Here to Verify
                        </a>
                    </div>
                    
                    <p style="color: #666; line-height: 1.6; font-size: 14px;">
                        Alternatively, you can copy and paste this link into your browser:
                    </p>
                    
                    <p style="color: #667eea; word-break: break-all; font-size: 14px;">
                        ${verificationUrl}
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        This verification link will expire in 24 hours. If you didn't create a setosa account, 
                        you can safely ignore this email.
                    </p>
                </div>
            </div>
        `
    };

    try {
        await transporter.sendMail(mailOptions);
        console.log(`Verification email sent to ${email}`);
        return true;
    } catch (error) {
        console.error('Error sending verification email:', error);
        return false;
    }
}

// Send password reset email
async function sendPasswordResetEmail(email, firstName, resetToken, baseUrl) {
    const resetUrl = `${baseUrl}/reset-password?token=${resetToken}`;
    
    const mailOptions = {
        from: `"setosa" <${emailConfig.auth.user}>`,
        to: email,
        subject: 'Reset your setosa password',
        html: `
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">Password Reset Request</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #333; margin-top: 0;">Hi ${firstName},</h2>
                    
                    <p style="color: #666; line-height: 1.6;">
                        We received a request to reset your setosa account password. Click the button below to create a new password.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${resetUrl}" 
                           style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                  color: white; 
                                  padding: 15px 30px; 
                                  text-decoration: none; 
                                  border-radius: 25px; 
                                  display: inline-block; 
                                  font-weight: bold;
                                  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                            Reset Password
                        </a>
                    </div>
                    
                    <p style="color: #666; line-height: 1.6; font-size: 14px;">
                        If the button doesn't work, you can copy and paste this link into your browser:
                    </p>
                    
                    <p style="color: #667eea; word-break: break-all; font-size: 14px;">
                        ${resetUrl}
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        This reset link will expire in 1 hour. If you didn't request a password reset, 
                        you can safely ignore this email.
                    </p>
                </div>
            </div>
        `
    };

    try {
        await transporter.sendMail(mailOptions);
        console.log(`Password reset email sent to ${email}`);
        return true;
    } catch (error) {
        console.error('Error sending password reset email:', error);
        return false;
    }
}

module.exports = {
    generateVerificationToken,
    sendVerificationEmail,
    sendPasswordResetEmail
};
