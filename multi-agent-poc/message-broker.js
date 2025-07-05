#!/usr/bin/env node

// Simple HTTP Message Broker for Multi-Agent Communication
const http = require('http');
const { v4: uuidv4 } = require('uuid');

// Message storage
const messages = [];
const pendingRequests = new Map(); // Waiting for responses
const PORT = process.env.PORT || 3000;

// ANSI colors for console
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(level, message, data = null) {
  const timestamp = new Date().toISOString();
  const color = {
    'INFO': colors.blue,
    'MESSAGE': colors.green,
    'REQUEST': colors.yellow,
    'RESPONSE': colors.magenta,
    'ERROR': colors.red
  }[level] || colors.reset;
  
  console.log(`${color}[${timestamp}] ${level}: ${message}${colors.reset}`);
  if (data) {
    console.log(JSON.stringify(data, null, 2));
  }
}

// Request handler
const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  let body = '';
  req.on('data', chunk => body += chunk);
  
  req.on('end', () => {
    try {
      const data = body ? JSON.parse(body) : {};
      handleRequest(req.method, req.url, data, res);
    } catch (error) {
      res.writeHead(400);
      res.end(JSON.stringify({ error: 'Invalid JSON' }));
    }
  });
});

function handleRequest(method, url, data, res) {
  const path = url.split('?')[0];
  
  switch (path) {
    case '/send':
      handleSend(data, res);
      break;
      
    case '/send-and-wait':
      handleSendAndWait(data, res);
      break;
      
    case '/receive':
      handleReceive(data, res);
      break;
      
    case '/check':
      handleCheck(data, res);
      break;
      
    case '/respond':
      handleRespond(data, res);
      break;
      
    case '/status':
      handleStatus(res);
      break;
      
    default:
      res.writeHead(404);
      res.end(JSON.stringify({ error: 'Not found' }));
  }
}

// Send a message (fire and forget)
function handleSend(data, res) {
  const message = {
    id: uuidv4(),
    timestamp: Date.now(),
    agent_id: data.agent_id || 'unknown',
    tags: data.tags || [],
    content: data.content || {},
    description: data.description || ''
  };
  
  messages.push(message);
  log('MESSAGE', `${message.agent_id} sent: ${message.description}`, message);
  
  res.writeHead(200);
  res.end(JSON.stringify({ ok: true, id: message.id }));
}

// Send and wait for response
function handleSendAndWait(data, res) {
  const message = {
    id: uuidv4(),
    timestamp: Date.now(),
    agent_id: data.agent_id || 'unknown',
    tags: data.tags || [],
    content: data.content || {},
    description: data.description || '',
    awaiting_response: true
  };
  
  messages.push(message);
  log('REQUEST', `${message.agent_id} requests: ${message.description}`, message);
  
  // Store pending request
  pendingRequests.set(message.id, {
    resolve: (response) => {
      res.writeHead(200);
      res.end(JSON.stringify({ ok: true, id: message.id, response }));
    },
    timeout: setTimeout(() => {
      pendingRequests.delete(message.id);
      res.writeHead(408);
      res.end(JSON.stringify({ error: 'Request timeout' }));
    }, 30000) // 30 second timeout
  });
}

// Receive messages (with optional filters)
function handleReceive(data, res) {
  const { agent_ids, tags, consume = true } = data;
  
  // Find matching messages
  const matchingIndex = messages.findIndex(msg => {
    if (msg.consumed) return false;
    if (agent_ids && !agent_ids.includes(msg.agent_id)) return false;
    if (tags && !tags.some(tag => msg.tags.includes(tag))) return false;
    return true;
  });
  
  if (matchingIndex === -1) {
    res.writeHead(200);
    res.end(JSON.stringify({ ok: true, message: null }));
    return;
  }
  
  const message = messages[matchingIndex];
  if (consume) {
    message.consumed = true;
  }
  
  log('MESSAGE', `${data.agent_id || 'unknown'} received from ${message.agent_id}`, message);
  
  res.writeHead(200);
  res.end(JSON.stringify({ ok: true, message }));
}

// Check messages without consuming
function handleCheck(data, res) {
  const { agent_ids, tags } = data;
  
  const matching = messages.filter(msg => {
    if (msg.consumed) return false;
    if (agent_ids && !agent_ids.includes(msg.agent_id)) return false;
    if (tags && !tags.some(tag => msg.tags.includes(tag))) return false;
    return true;
  });
  
  res.writeHead(200);
  res.end(JSON.stringify({ ok: true, messages: matching }));
}

// Respond to a waiting request
function handleRespond(data, res) {
  const { request_id, response_content, responder_id } = data;
  
  const pending = pendingRequests.get(request_id);
  if (!pending) {
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Request not found or already responded' }));
    return;
  }
  
  const response = {
    id: uuidv4(),
    timestamp: Date.now(),
    agent_id: responder_id || 'unknown',
    content: response_content,
    response_to: request_id
  };
  
  log('RESPONSE', `${responder_id} responded to ${request_id}`, response);
  
  // Clear timeout and resolve
  clearTimeout(pending.timeout);
  pending.resolve(response);
  pendingRequests.delete(request_id);
  
  res.writeHead(200);
  res.end(JSON.stringify({ ok: true }));
}

// Get broker status
function handleStatus(res) {
  const status = {
    messages: {
      total: messages.length,
      unconsumed: messages.filter(m => !m.consumed).length,
      awaiting_response: messages.filter(m => m.awaiting_response).length
    },
    pending_requests: pendingRequests.size,
    uptime: process.uptime()
  };
  
  res.writeHead(200);
  res.end(JSON.stringify(status));
}

// Start server
server.listen(PORT, () => {
  console.log(`${colors.bright}${colors.green}🚀 Multi-Agent Message Broker${colors.reset}`);
  console.log(`${colors.cyan}➜ Listening on http://localhost:${PORT}${colors.reset}`);
  console.log(`${colors.yellow}➜ Status: http://localhost:${PORT}/status${colors.reset}\n`);
  
  console.log(`${colors.bright}Available Endpoints:${colors.reset}`);
  console.log('  POST /send           - Send a message');
  console.log('  POST /send-and-wait  - Send and wait for response');
  console.log('  POST /receive        - Receive messages');
  console.log('  POST /check          - Check messages without consuming');
  console.log('  POST /respond        - Respond to a waiting request');
  console.log('  GET  /status         - Broker statistics\n');
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log(`\n${colors.yellow}Shutting down message broker...${colors.reset}`);
  server.close(() => {
    console.log(`${colors.green}Message broker stopped.${colors.reset}`);
    process.exit(0);
  });
});