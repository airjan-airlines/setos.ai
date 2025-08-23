<?php

/**
 * Setosa Setup Script
 * 
 * This script helps you set up the PHP authentication system
 */

echo "🚀 Setosa Setup Script\n";
echo "==============================\n\n";

// Check PHP version
if (version_compare(PHP_VERSION, '8.1.0', '<')) {
    echo "❌ Error: PHP 8.1 or higher is required. Current version: " . PHP_VERSION . "\n";
    exit(1);
}

echo "✅ PHP version: " . PHP_VERSION . "\n";

// Check if Composer is installed
if (!file_exists('vendor/autoload.php')) {
    echo "❌ Error: Composer dependencies not installed. Run 'composer install' first.\n";
    exit(1);
}

echo "✅ Composer dependencies found\n";

// Check if .env file exists
if (!file_exists('.env')) {
    echo "📝 Creating .env file from template...\n";
    
    if (file_exists('env.example')) {
        copy('env.example', '.env');
        echo "✅ .env file created. Please edit it with your configuration.\n";
    } else {
        echo "❌ Error: env.example file not found.\n";
        exit(1);
    }
} else {
    echo "✅ .env file exists\n";
}

// Load environment variables
require_once 'vendor/autoload.php';
$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->load();

echo "\n📋 Configuration Summary:\n";
echo "Database Host: " . ($_ENV['DB_HOST'] ?? 'Not set') . "\n";
echo "Database Name: " . ($_ENV['DB_NAME'] ?? 'Not set') . "\n";
echo "Database User: " . ($_ENV['DB_USER'] ?? 'Not set') . "\n";
echo "App Environment: " . ($_ENV['APP_ENV'] ?? 'Not set') . "\n";
echo "App URL: " . ($_ENV['APP_URL'] ?? 'Not set') . "\n";

echo "\n🔧 Testing database connection...\n";

try {
    $host = $_ENV['DB_HOST'] ?? 'localhost';
    $dbname = $_ENV['DB_NAME'] ?? 'setosa';
    $username = $_ENV['DB_USER'] ?? 'root';
    $password = $_ENV['DB_PASSWORD'] ?? '';
    
    $dsn = "mysql:host={$host};dbname={$dbname};charset=utf8mb4";
    $pdo = new PDO($dsn, $username, $password, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    
    echo "✅ Database connection successful\n";
    
    // Run migrations
    echo "\n🗄️ Running database migrations...\n";
    
    $migration = new App\Database\Migration();
    $migration->runAllMigrations();
    
    echo "✅ Database setup complete\n";
    
} catch (PDOException $e) {
    echo "❌ Database connection failed: " . $e->getMessage() . "\n";
    echo "\n💡 Troubleshooting tips:\n";
    echo "1. Make sure MySQL is running\n";
    echo "2. Check your database credentials in .env file\n";
    echo "3. Create the database if it doesn't exist:\n";
    echo "   CREATE DATABASE setosa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n";
    exit(1);
} catch (Exception $e) {
    echo "❌ Migration failed: " . $e->getMessage() . "\n";
    exit(1);
}

echo "\n🎉 Setup completed successfully!\n\n";

echo "📖 Next steps:\n";
echo "1. Configure your web server to point to the 'public' directory\n";
echo "2. Set up your SMTP settings in .env for email functionality\n";
echo "3. Test the API endpoints:\n";
echo "   - POST /api/register\n";
echo "   - POST /api/login\n";
echo "   - GET /api/profile\n";
echo "\n4. For development, you can run:\n";
echo "   php -S localhost:8000 -t public\n";
echo "\n5. Visit http://localhost:8000 to see your application\n";

echo "\n🔐 Security reminders:\n";
echo "- Change JWT_SECRET in production\n";
echo "- Set APP_ENV=production in production\n";
echo "- Configure proper SMTP settings\n";
echo "- Set up HTTPS in production\n";

echo "\n📚 Documentation: See README.md for detailed API documentation\n";
