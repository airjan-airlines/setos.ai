const { spawn } = require('child_process');
const path = require('path');

console.log('Starting setosa...\n');

// Start Python backend
console.log('Starting Python Backend...');
const backend = spawn('python', ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000'], {
    stdio: 'inherit',
    shell: true
});

// Wait a moment for backend to start
setTimeout(() => {
    console.log('\nStarting Frontend...');
    const frontend = spawn('node', ['server.js'], {
        stdio: 'inherit',
        shell: true
    });

    frontend.on('close', (code) => {
        console.log(`\nFrontend process exited with code ${code}`);
        backend.kill();
        process.exit(code);
    });
}, 2000);

backend.on('close', (code) => {
    console.log(`\nBackend process exited with code ${code}`);
    process.exit(code);
});

// Handle process termination
process.on('SIGINT', () => {
    console.log('\nShutting down servers...');
    backend.kill();
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\nShutting down servers...');
    backend.kill();
    process.exit(0);
});
