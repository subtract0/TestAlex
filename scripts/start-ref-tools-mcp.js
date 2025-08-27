#!/usr/bin/env node
/**
 * Universal launcher for ref-tools MCP server
 * Supports both local development and production deployment
 */

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

// Load environment configuration
const configPath = path.join(__dirname, '../config/ref-tools-mcp.env');
if (fs.existsSync(configPath)) {
    const envConfig = fs.readFileSync(configPath, 'utf8');
    envConfig.split('\n').forEach(line => {
        const [key, value] = line.split('=');
        if (key && value) {
            process.env[key] = value;
        }
    });
}

// Configuration
const PORT = process.env.REF_MCP_PORT || 4102;
const TRANSPORT = process.env.REF_MCP_TRANSPORT || 'http';
const HOST = process.env.REF_MCP_HOST || 'localhost';

console.log('🚀 Starting Ref-Tools MCP Server...');
console.log(`📡 Transport: ${TRANSPORT}`);
console.log(`🌐 Host: ${HOST}:${PORT}`);

// Health check function
function isPortAvailable(port) {
    return new Promise((resolve) => {
        const net = require('net');
        const server = net.createServer();
        
        server.listen(port, () => {
            server.once('close', () => resolve(true));
            server.close();
        });
        
        server.on('error', () => resolve(false));
    });
}

// Main launch function
async function startMCPServer() {
    try {
        // Check if port is available
        const portAvailable = await isPortAvailable(PORT);
        if (!portAvailable) {
            console.log(`⚠️  Port ${PORT} is already in use`);
            console.log('🔍 Checking if ref-tools-mcp is already running...');
            
            // Try to ping existing service
            try {
                const { default: fetch } = await import('node-fetch');
                const response = await fetch(`http://${HOST}:${PORT}/health`, { 
                    timeout: 2000 
                });
                if (response.ok) {
                    console.log('✅ Ref-Tools MCP is already running and healthy');
                    return;
                }
            } catch (e) {
                console.log('❌ Port occupied but service not responding');
                process.exit(1);
            }
        }

        // Set environment variables for the MCP server
        const env = {
            ...process.env,
            TRANSPORT: TRANSPORT,
            PORT: PORT,
            HOST: HOST
        };

        // Start the MCP server
        const mcpProcess = spawn('ref-tools-mcp', [], {
            env,
            stdio: ['ignore', 'pipe', 'pipe']
        });

        // Handle output
        mcpProcess.stdout.on('data', (data) => {
            console.log(`[MCP] ${data.toString().trim()}`);
        });

        mcpProcess.stderr.on('data', (data) => {
            console.error(`[MCP ERROR] ${data.toString().trim()}`);
        });

        // Handle process events
        mcpProcess.on('close', (code) => {
            console.log(`🔄 Ref-Tools MCP server exited with code ${code}`);
        });

        mcpProcess.on('error', (error) => {
            console.error('❌ Failed to start Ref-Tools MCP server:', error.message);
            process.exit(1);
        });

        // Wait a moment for the server to start
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Verify the server is running
        try {
            const { default: fetch } = await import('node-fetch');
            const response = await fetch(`http://${HOST}:${PORT}/health`, { 
                timeout: 5000 
            });
            if (response.ok) {
                console.log('✅ Ref-Tools MCP Server is running and healthy');
                console.log(`🌐 Available at: http://${HOST}:${PORT}`);
            } else {
                console.log('⚠️  Server started but health check failed');
            }
        } catch (e) {
            console.log('⚠️  Server started but health check timed out');
        }

        // Keep the process alive unless explicitly killed
        process.on('SIGINT', () => {
            console.log('🛑 Shutting down Ref-Tools MCP Server...');
            mcpProcess.kill('SIGTERM');
            process.exit(0);
        });

    } catch (error) {
        console.error('❌ Error starting Ref-Tools MCP Server:', error.message);
        process.exit(1);
    }
}

// Handle command line arguments
if (process.argv.includes('--help') || process.argv.includes('-h')) {
    console.log(`
Usage: node start-ref-tools-mcp.js [options]

Options:
  --help, -h     Show this help message
  --check        Only check if the service is running
  --kill         Kill any running ref-tools-mcp process

Environment Variables:
  REF_MCP_PORT      Port to run on (default: 4102)
  REF_MCP_TRANSPORT Transport type (default: http)
  REF_MCP_HOST      Host to bind to (default: localhost)

Examples:
  node start-ref-tools-mcp.js
  REF_MCP_PORT=8080 node start-ref-tools-mcp.js
  node start-ref-tools-mcp.js --check
    `);
    process.exit(0);
}

if (process.argv.includes('--check')) {
    (async () => {
        try {
            const { default: fetch } = await import('node-fetch');
            const response = await fetch(`http://${HOST}:${PORT}/health`, { 
                timeout: 3000 
            });
            if (response.ok) {
                console.log('✅ Ref-Tools MCP Server is running');
                process.exit(0);
            } else {
                console.log('❌ Ref-Tools MCP Server is not responding');
                process.exit(1);
            }
        } catch (e) {
            console.log('❌ Ref-Tools MCP Server is not running');
            process.exit(1);
        }
    })();
} else if (process.argv.includes('--kill')) {
    exec('pkill -f ref-tools-mcp', (error) => {
        if (error) {
            console.log('⚠️  No ref-tools-mcp processes found or error killing them');
        } else {
            console.log('✅ Killed ref-tools-mcp processes');
        }
        process.exit(0);
    });
} else {
    startMCPServer();
}
