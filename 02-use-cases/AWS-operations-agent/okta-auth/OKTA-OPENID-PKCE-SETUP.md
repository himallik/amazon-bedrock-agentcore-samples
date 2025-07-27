# Okta OpenID Connect PKCE Setup Guide

---
## 📋 Navigation
**🏠 [README](../README.md)** | **📖 [Setup Guide](../docs/SETUP.md)** | **🏗️ [Architecture](../docs/ARCHITECTURE-FLOW.md)** | **🔧 [Scripts](../scripts/README.md)** | **🤖 [Client](../client/README.md)** | **⚙️ [Config](../configs/README.md)** | **🔐 [Okta Setup](OKTA-OPENID-PKCE-SETUP.md)**
---

## Overview

This guide sets up Okta PKCE authentication for Bedrock AgentCore Gateway using the existing `iframe-oauth-flow.html` - a complete, self-contained PKCE application.

## Prerequisites

- Okta Developer Account (free at [developer.okta.com](https://developer.okta.com))
- Access to Bedrock AgentCore Gateway (beta access required)
- nginx installed locally (see installation instructions below)

## Okta Setup

For detailed guidance on setting up Okta for PKCE authentication, refer to these official Okta documentation resources:

📖 **[Implement Authorization Code Flow with PKCE](https://developer.okta.com/docs/guides/implement-grant-type/authcodepkce/main/)** - Complete guide on implementing PKCE flow

📖 **[Create a Custom Authorization Server](https://developer.okta.com/docs/guides/terraform-create-custom-auth-server/main/)** - Setting up custom authorization servers (optional)

### Create an OIDC Application

1. Log in to your Okta Developer Console
2. Navigate to **Applications** → **Applications** → **Create App Integration**
3. Configure:
   ```
   App name: bedrock-agentcore-gateway-client
   Grant types: ✅ Authorization Code, ✅ Refresh Token
   Sign-in redirect URIs: http://localhost:8080/okta-auth/
   Allowed grant types: ✅ Authorization Code
   Client authentication: ✅ Use PKCE (for public clients)
   ```
4. Save the application

### Configure API Scopes

- **Security** → **API** → **Authorization Servers** → **default**
- Ensure scopes exist: `openid`, `profile`, `email`
- Add custom scopes if needed: `bedrock-agentcore:read`, `bedrock-agentcore:write`

## Local Setup

### Install nginx

#### macOS (Homebrew - Recommended)

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install nginx
brew install nginx

# Start nginx service
brew services start nginx

# Verify installation at http://localhost:8080
```

#### Other Platforms

For comprehensive installation instructions on all platforms including Linux, Windows, and other Unix systems, refer to the official nginx documentation:

**📖 [NGINX Open Source Installation Guide](https://docs.nginx.com/nginx/admin-guide/installing-nginx/installing-nginx-open-source/)**

The official guide covers:
- Package manager installations (recommended for production)
- Operating system default repositories 
- Compiling from source
- Platform-specific instructions for RHEL/CentOS, Debian/Ubuntu, Alpine Linux, Amazon Linux, SUSE, and more

### Configure Local nginx

1. **Update nginx configuration paths**:
   ```bash
   # Edit the nginx configuration file
   vi okta-auth/nginx/okta-local.conf
   ```
   
   Update the following paths to match your project structure:
   - Line 7: `root /path/to/your/project/okta-auth;`
   - Line 36: `alias /path/to/your/project/okta-auth;`

2. **Start nginx with the configuration**:
   ```bash
   # Navigate to the project directory
   cd /path/to/project

   # Start with provided configuration
   sudo nginx -c $(pwd)/okta-auth/nginx/okta-local.conf
   ```

### Configure OAuth Parameters

The `iframe-oauth-flow.html` file provides a web-based configuration interface. You can configure it in two ways:

#### Option 1: Configure via Web Interface (Recommended)
1. Open http://localhost:8080/okta-auth/ in your browser
2. Fill in the configuration form with your Okta details:
   - **Okta Domain**: Your Okta domain (e.g., `dev-12345678.okta.com`)
   - **Client ID**: From your Okta application
   - **Redirect URI**: `http://localhost:8080/okta-auth/`
   - **Auth Server ID**: `default` (or your custom server ID)
3. Click "Save Configuration" to validate and save

#### Option 2: Pre-configure in HTML File
1. Open `iframe-oauth-flow.html` in a text editor
2. Update the default values in the form inputs (around line 197):
   ```html
   <input type="text" id="clientId" name="clientId" value="YOUR_CLIENT_ID" required>
   ```
3. Update other form fields as needed:
   - **oktaDomain**: Your Okta domain
   - **redirectUri**: `http://localhost:8080/okta-auth/`
   - **authServerId**: `api://default`

*Note: The iframe file handles all PKCE logic, token management, and Bedrock AgentCore Gateway integration automatically.*

## Test the Setup

1. Open a browser and navigate to: http://localhost:8080/okta-auth/
2. Click "Login with Okta"
3. Complete the Okta authentication flow
4. You should see the access token displayed on the page
5. Copy this token for use with the client application

## Using the Token

```bash
# Step 1: Use the token management script
cd ../client
python src/save_token.py

# Step 2: Run the client
python src/main.py
```

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Ensure your Okta application has the correct redirect URI
   - Check that nginx is running with the provided configuration

2. **Invalid Client Error**:
   - Verify your Client ID is correct
   - Ensure PKCE is enabled for the application

3. **Token Not Working**:
   - Check token expiration (default is 1 hour)
   - Verify scopes match what's required by the gateway

### Debugging

```bash
# Check nginx configuration
nginx -t -c /path/to/okta-local.conf

# View nginx logs
tail -f /usr/local/var/log/nginx/error.log

# Test token with curl
curl -H "Authorization: Bearer YOUR_TOKEN" https://your-gateway-url/mcp
```

## Advanced Configuration

The `iframe-oauth-flow.html` file is a complete PKCE implementation that includes:

- Code challenge and verifier generation
- Authorization code flow
- Token exchange and refresh
- Complete PKCE implementation (lines 330+)
- Token display and management
- Bedrock AgentCore Gateway integration
- All necessary HTML, CSS, and JavaScript

You can customize this file for your specific needs or use it as a reference for implementing PKCE in your own applications.

---
