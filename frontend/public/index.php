<?php

require_once __DIR__ . '/../vendor/autoload.php';

use App\Controllers\AuthController;
use App\Database\Migration;
use App\Services\JWTService;
use Dotenv\Dotenv;

// Load environment variables
$dotenv = Dotenv::createImmutable(__DIR__ . '/..');
$dotenv->load();

// Set error reporting based on environment
if ($_ENV['APP_ENV'] === 'production') {
    error_reporting(0);
    ini_set('display_errors', 0);
} else {
    error_reporting(E_ALL);
    ini_set('display_errors', 1);
}

// Set headers for CORS and JSON responses
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Initialize database and run migrations
try {
    $migration = new Migration();
    $migration->runAllMigrations();
} catch (Exception $e) {
    error_log('Database migration failed: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'Database initialization failed'
    ]);
    exit();
}

// Simple router
$requestMethod = $_SERVER['REQUEST_METHOD'];
$requestUri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$path = trim($requestUri, '/');

// Remove 'public' from path if present
$path = str_replace('public/', '', $path);

try {
    $authController = new AuthController();
    
    switch ($path) {
        case 'api/register':
            if ($requestMethod !== 'POST') {
                http_response_code(405);
                echo json_encode(['success' => false, 'message' => 'Method not allowed']);
                break;
            }
            $response = $authController->register();
            echo json_encode($response);
            break;
            
        case 'api/login':
            if ($requestMethod !== 'POST') {
                http_response_code(405);
                echo json_encode(['success' => false, 'message' => 'Method not allowed']);
                break;
            }
            $response = $authController->login();
            echo json_encode($response);
            break;
            
        case 'api/verify-email':
            if ($requestMethod !== 'POST') {
                http_response_code(405);
                echo json_encode(['success' => false, 'message' => 'Method not allowed']);
                break;
            }
            $response = $authController->verifyEmail();
            echo json_encode($response);
            break;
            
        case 'api/forgot-password':
            if ($requestMethod !== 'POST') {
                http_response_code(405);
                echo json_encode(['success' => false, 'message' => 'Method not allowed']);
                break;
            }
            $response = $authController->forgotPassword();
            echo json_encode($response);
            break;
            
        case 'api/reset-password':
            if ($requestMethod !== 'POST') {
                http_response_code(405);
                echo json_encode(['success' => false, 'message' => 'Method not allowed']);
                break;
            }
            $response = $authController->resetPassword();
            echo json_encode($response);
            break;
            
        case 'api/refresh-token':
            if ($requestMethod !== 'POST') {
                http_response_code(405);
                echo json_encode(['success' => false, 'message' => 'Method not allowed']);
                break;
            }
            $response = $authController->refreshToken();
            echo json_encode($response);
            break;
            
        case 'api/logout':
            if ($requestMethod !== 'POST') {
                http_response_code(405);
                echo json_encode(['success' => false, 'message' => 'Method not allowed']);
                break;
            }
            $response = $authController->logout();
            echo json_encode($response);
            break;
            
        case 'api/profile':
            if ($requestMethod !== 'GET') {
                http_response_code(405);
                echo json_encode(['success' => false, 'message' => 'Method not allowed']);
                break;
            }
            $response = $authController->profile();
            echo json_encode($response);
            break;
            
        case '':
        case 'index.html':
            // Serve the main application
            header('Content-Type: text/html');
            readfile(__DIR__ . '/../index.html');
            break;
            
        default:
            // Check if it's a static file
            $filePath = __DIR__ . '/' . $path;
            if (file_exists($filePath) && is_file($filePath)) {
                $extension = pathinfo($filePath, PATHINFO_EXTENSION);
                $contentTypes = [
                    'html' => 'text/html',
                    'css' => 'text/css',
                    'js' => 'application/javascript',
                    'png' => 'image/png',
                    'jpg' => 'image/jpeg',
                    'jpeg' => 'image/jpeg',
                    'gif' => 'image/gif',
                    'svg' => 'image/svg+xml',
                    'ico' => 'image/x-icon'
                ];
                
                if (isset($contentTypes[$extension])) {
                    header('Content-Type: ' . $contentTypes[$extension]);
                    readfile($filePath);
                } else {
                    http_response_code(404);
                    echo json_encode(['success' => false, 'message' => 'Not found']);
                }
            } else {
                http_response_code(404);
                echo json_encode(['success' => false, 'message' => 'Not found']);
            }
            break;
    }
    
} catch (Exception $e) {
    error_log('Application error: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => $_ENV['APP_ENV'] === 'production' ? 'Internal server error' : $e->getMessage()
    ]);
}
