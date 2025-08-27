#!/usr/bin/env node
/**
 * Ref-Tools MCP Client for ACIMguide Agent System (Node.js)
 * Provides token-efficient access to technical documentation for all agents
 * Compatible with both CommonJS and ES modules
 */

const axios = require('axios');
const { URL } = require('url');

/**
 * Configuration class for Ref-Tools MCP client
 */
class RefToolsConfig {
    constructor(options = {}) {
        this.baseURL = options.baseURL || process.env.REF_MCP_URL || 
                      `http://${process.env.REF_MCP_HOST || 'localhost'}:${process.env.REF_MCP_PORT || 4102}`;
        this.port = options.port || parseInt(process.env.REF_MCP_PORT) || 4102;
        this.transport = options.transport || process.env.REF_MCP_TRANSPORT || 'http';
        this.timeout = options.timeout || 20000;
        this.maxRetries = options.maxRetries || 3;
        this.fallbackUrls = options.fallbackUrls || [
            'https://ref-tools-mcp.acimguide.com',
            'http://localhost:8080'
        ];
    }
}

/**
 * High-level client for Ref-Tools MCP service
 * Provides token-efficient documentation access for agents
 */
class RefToolsClient {
    constructor(config = null) {
        this.config = config || new RefToolsConfig();
        
        // Create axios instance with default headers
        this.axios = axios.create({
            timeout: this.config.timeout,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'ACIMguide-Agent-System/1.0'
            }
        });
    }

    /**
     * Make HTTP request to MCP server with fallback support
     */
    async _makeRequest(endpoint, payload = null, method = 'POST') {
        const urlsToTry = [this.config.baseURL, ...this.config.fallbackUrls];
        
        for (let attempt = 0; attempt < urlsToTry.length; attempt++) {
            try {
                const baseURL = urlsToTry[attempt];
                const url = new URL(endpoint, baseURL).toString();
                
                console.debug(`Attempting ${method} ${url} (attempt ${attempt + 1})`);
                
                let response;
                if (method.toUpperCase() === 'POST') {
                    response = await this.axios.post(url, payload);
                } else {
                    response = await this.axios.get(url);
                }
                
                return response.data;
                
            } catch (error) {
                console.warn(`Request to ${urlsToTry[attempt]} failed:`, error.message);
                
                if (attempt === urlsToTry.length - 1) {
                    throw new RefToolsConnectionError(
                        `Failed to connect to Ref-Tools MCP service after trying ${urlsToTry.length} endpoints`
                    );
                }
            }
        }
    }

    /**
     * Check if the MCP service is healthy and responsive
     */
    async healthCheck() {
        try {
            return await this._makeRequest('/health', null, 'GET');
        } catch (error) {
            return {
                status: 'unhealthy',
                error: error.message,
                timestamp: Date.now()
            };
        }
    }

    /**
     * Get documentation for a specific library or API
     * 
     * @param {string} library - Name of the library/API (e.g., 'firebase', 'openai', 'react')
     * @param {string} query - Specific search query within the documentation
     * @param {number} maxTokens - Maximum tokens to return (helps with cost optimization)
     * @returns {Promise<Object>} Dictionary containing relevant documentation snippets
     */
    async getDocs(library, query = '', maxTokens = 2000) {
        const payload = {
            library,
            query,
            max_tokens: maxTokens,
            format: 'json'
        };
        
        return await this._makeRequest('/docs', payload);
    }

    /**
     * Search for specific API endpoints and usage patterns
     * 
     * @param {string} apiName - Name of the API (e.g., 'Firebase Admin', 'OpenAI')
     * @param {string} endpointPattern - Pattern to search for (e.g., '/users', 'chat/completions')
     * @param {string} method - HTTP method filter (GET, POST, etc.)
     * @returns {Promise<Object>} API documentation and examples
     */
    async searchAPI(apiName, endpointPattern = '', method = '') {
        const payload = {
            api: apiName,
            endpoint: endpointPattern,
            method: method.toUpperCase(),
            include_examples: true
        };
        
        return await this._makeRequest('/api', payload);
    }

    /**
     * Get code examples for specific technologies and use cases
     * 
     * @param {string} technology - Technology name (e.g., 'typescript', 'python', 'react')
     * @param {string} useCase - Specific use case (e.g., 'authentication', 'database-query')
     * @returns {Promise<Object>} Code examples and best practices
     */
    async getExamples(technology, useCase = '') {
        const payload = {
            technology,
            use_case: useCase,
            format: 'code_snippets'
        };
        
        return await this._makeRequest('/examples', payload);
    }

    /**
     * Get best practices for a specific domain or framework
     * 
     * @param {string} domain - Domain area (e.g., 'security', 'performance', 'testing')
     * @param {string} framework - Specific framework (e.g., 'firebase', 'react', 'nodejs')
     * @returns {Promise<Object>} Best practices and guidelines
     */
    async getBestPractices(domain, framework = '') {
        const payload = {
            domain,
            framework,
            include_antipatterns: true
        };
        
        return await this._makeRequest('/best-practices', payload);
    }

    /**
     * Search for solutions to specific error messages
     * 
     * @param {string} errorMessage - The error message or pattern
     * @param {string} technology - Technology context (e.g., 'firebase', 'typescript')
     * @returns {Promise<Object>} Common solutions and troubleshooting steps
     */
    async searchErrors(errorMessage, technology = '') {
        const payload = {
            error: errorMessage,
            technology,
            include_solutions: true,
            include_prevention: true
        };
        
        return await this._makeRequest('/errors', payload);
    }
}

/**
 * Agent integration helper for JavaScript/Node.js agents
 */
class AgentRefToolsHelper {
    constructor(agentName = 'unknown') {
        this.agentName = agentName;
        this.client = new RefToolsClient();
    }

    /**
     * Intelligent lookup based on agent task and required technologies
     * 
     * @param {string} taskDescription - Description of the task
     * @param {Array<string>} technologies - List of technologies (optional)
     * @returns {Promise<Object>} Comprehensive lookup results
     */
    async lookupForTask(taskDescription, technologies = null) {
        if (!technologies) {
            technologies = this._extractTechnologies(taskDescription);
        }

        const results = {
            task: taskDescription,
            agent: this.agentName,
            technologies,
            documentation: {},
            examples: {},
            bestPractices: {}
        };

        for (const tech of technologies) {
            try {
                // Get docs for each technology
                results.documentation[tech] = await this.client.getDocs(tech, taskDescription);
                
                // Get relevant examples
                results.examples[tech] = await this.client.getExamples(tech, taskDescription);
                
                // Get best practices
                results.bestPractices[tech] = await this.client.getBestPractices(tech);
                
            } catch (error) {
                console.warn(`Failed to get info for ${tech}:`, error.message);
                results.documentation[tech] = { error: error.message };
            }
        }

        return results;
    }

    /**
     * Extract likely technologies from task description
     */
    _extractTechnologies(taskDescription) {
        const techKeywords = {
            firebase: ['firebase', 'firestore', 'functions'],
            typescript: ['typescript', 'ts', 'type'],
            javascript: ['javascript', 'js', 'node'],
            react: ['react', 'jsx', 'component'],
            nodejs: ['node', 'express', 'npm'],
            openai: ['openai', 'gpt', 'ai', 'llm']
        };

        const foundTechs = [];
        const taskLower = taskDescription.toLowerCase();

        for (const [tech, keywords] of Object.entries(techKeywords)) {
            if (keywords.some(keyword => taskLower.includes(keyword))) {
                foundTechs.push(tech);
            }
        }

        return foundTechs.length > 0 ? foundTechs : ['general'];
    }
}

// Convenience functions for direct usage
async function queryRef(endpoint, payload = null) {
    const client = new RefToolsClient();
    return await client._makeRequest(endpoint, payload);
}

async function getDocs(library, query = '', maxTokens = 2000) {
    const client = new RefToolsClient();
    return await client.getDocs(library, query, maxTokens);
}

async function searchAPI(apiName, endpointPattern = '', method = '') {
    const client = new RefToolsClient();
    return await client.searchAPI(apiName, endpointPattern, method);
}

async function getExamples(technology, useCase = '') {
    const client = new RefToolsClient();
    return await client.getExamples(technology, useCase);
}

async function getBestPractices(domain, framework = '') {
    const client = new RefToolsClient();
    return await client.getBestPractices(domain, framework);
}

async function searchErrors(errorMessage, technology = '') {
    const client = new RefToolsClient();
    return await client.searchErrors(errorMessage, technology);
}

// Exception classes
class RefToolsConnectionError extends Error {
    constructor(message) {
        super(message);
        this.name = 'RefToolsConnectionError';
    }
}

class RefToolsAPIError extends Error {
    constructor(message) {
        super(message);
        this.name = 'RefToolsAPIError';
    }
}

// Global client instance for easy access
let _defaultClient = null;

function getDefaultClient() {
    if (!_defaultClient) {
        _defaultClient = new RefToolsClient();
    }
    return _defaultClient;
}

// Firebase Cloud Functions integration helpers
const firebaseFunctions = {
    /**
     * Initialize ref-tools client for Firebase Cloud Functions
     * Should be called once at function startup
     */
    initialize() {
        const client = new RefToolsClient();
        global.refClient = client;
        return client;
    },

    /**
     * Get the global ref-tools client instance
     */
    getClient() {
        if (!global.refClient) {
            return this.initialize();
        }
        return global.refClient;
    }
};

// Export for both CommonJS and ES modules
module.exports = {
    RefToolsClient,
    RefToolsConfig,
    AgentRefToolsHelper,
    RefToolsConnectionError,
    RefToolsAPIError,
    queryRef,
    getDocs,
    searchAPI,
    getExamples,
    getBestPractices,
    searchErrors,
    getDefaultClient,
    firebaseFunctions
};

// ES modules export
if (typeof exports !== 'undefined' && exports.__esModule) {
    exports.default = RefToolsClient;
}

// Test the client if run directly
if (require.main === module) {
    (async () => {
        try {
            const client = new RefToolsClient();
            const health = await client.healthCheck();
            console.log('Ref-Tools MCP Health:', health);
            
            // Example usage
            const docs = await getDocs('firebase', 'authentication');
            console.log('Firebase auth docs:', docs.summary || 'No summary available');
            
        } catch (error) {
            console.error('Error testing Ref-Tools client:', error.message);
        }
    })();
}
