<?php

namespace App\Database;

use PDO;
use PDOException;
use Exception;

class Database
{
    private static ?Database $instance = null;
    private ?PDO $connection = null;
    
    private function __construct()
    {
        $this->connect();
    }
    
    public static function getInstance(): Database
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function connect(): void
    {
        try {
            $host = $_ENV['DB_HOST'] ?? 'localhost';
            $dbname = $_ENV['DB_NAME'] ?? 'setosa';
            $username = $_ENV['DB_USER'] ?? 'root';
            $password = $_ENV['DB_PASSWORD'] ?? '';
            $charset = $_ENV['DB_CHARSET'] ?? 'utf8mb4';
            
            $dsn = "mysql:host={$host};dbname={$dbname};charset={$charset}";
            
            $this->connection = new PDO($dsn, $username, $password, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ]);
        } catch (PDOException $e) {
            throw new Exception("Database connection failed: " . $e->getMessage());
        }
    }
    
    public function getConnection(): PDO
    {
        return $this->connection;
    }
    
    public function beginTransaction(): bool
    {
        return $this->connection->beginTransaction();
    }
    
    public function commit(): bool
    {
        return $this->connection->commit();
    }
    
    public function rollback(): bool
    {
        return $this->connection->rollback();
    }
    
    public function prepare(string $sql): \PDOStatement
    {
        return $this->connection->prepare($sql);
    }
    
    public function lastInsertId(): string
    {
        return $this->connection->lastInsertId();
    }
}
