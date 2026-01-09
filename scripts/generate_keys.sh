#!/bin/bash

# Script to generate RSA keys for JWT signing (RS256)
# Requires openssl

set -e

# Directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
IDENTITY_SVC_DIR="$PROJECT_ROOT/services/identity-service"

echo "Generating RSA keys for Identity Service..."

# Generate private key
openssl genpkey -algorithm RSA -out "$IDENTITY_SVC_DIR/private_key.pem" -pkeyopt rsa_keygen_bits:2048

# Generate public key
openssl rsa -pubout -in "$IDENTITY_SVC_DIR/private_key.pem" -out "$IDENTITY_SVC_DIR/public_key.pem"

echo "------------------------------------------------"
echo "Keys generated successfully in $IDENTITY_SVC_DIR"
echo "------------------------------------------------"
echo ""
echo "To use these in your .env file, you need them as single-line strings with \n for newlines."
echo "Here are the formatted strings for your .env file:"
echo ""

# Format private key for .env
PRIVATE_KEY=$(cat "$IDENTITY_SVC_DIR/private_key.pem" | awk '{printf "%s\\n", $0}')
echo "JWT_PRIVATE_KEY=\"$PRIVATE_KEY\""
echo ""

# Format public key for .env
PUBLIC_KEY=$(cat "$IDENTITY_SVC_DIR/public_key.pem" | awk '{printf "%s\\n", $0}')
echo "JWT_PUBLIC_KEY=\"$PUBLIC_KEY\""
echo ""
echo "------------------------------------------------"
echo "Copy and paste the above lines into your services/identity-service/.env file."
