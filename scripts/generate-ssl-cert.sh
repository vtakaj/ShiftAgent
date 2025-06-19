#!/bin/bash

# Generate self-signed SSL certificate for local development

echo "🔐 Generating self-signed SSL certificate for local development..."

# Generate private key
openssl genrsa -out localhost-key.pem 2048

# Generate certificate
openssl req -new -x509 -key localhost-key.pem -out localhost.pem -days 365 -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Natural Shift Planner/CN=localhost"

echo "✅ SSL certificate generated:"
echo "   - localhost-key.pem (private key)"
echo "   - localhost.pem (certificate)"
echo ""
echo "To use HTTPS:"
echo "  1. Run: make run-https"
echo "  2. Accept the security warning in your browser"
echo "  3. Update API_BASE_URL to https://localhost:8081" 