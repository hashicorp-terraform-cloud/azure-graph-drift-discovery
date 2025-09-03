# Terraform Notification Middleware

A Python middleware service that receives webhook notifications from HCP Terraform/Terraform Enterprise and automatically triggers workspace runs in response to events like drift detection.

## Features

- Processes HCP Terraform/Terraform Enterprise webhook notifications
- Automatically creates apply or destroy runs based on notification triggers
- HMAC signature verification for webhook security
- Handles webhook verification requests during setup
- Optional auto-apply for unattended remediation
- Comprehensive request/response logging

## Requirements

- Python 3.7+
- `flask`
- `requests`

## Installation

```bash
pip install flask requests
```

## Configuration

Configure via environment variables aligned with the TFE provider:

### Required
- `TFE_TOKEN` - API token for Terraform authentication

### Optional
- `TFE_HOSTNAME` - Terraform instance hostname (default: `app.terraform.io`)
- `TFE_NOTIFICATION_TOKEN` - HMAC token for webhook signature verification (recommended)
- `TFE_AUTO_APPLY` - Auto-apply runs after successful plan (default: `false`)
- `TFE_SSL_SKIP_VERIFY` - Skip SSL verification for self-signed certificates (default: `false`)
- `PORT` - Port to listen on (default: `5000`)
- `DEBUG` - Enable debug logging (default: `false`)

## Usage

1. **Start the middleware:**
```bash
export TFE_TOKEN="your-api-token"
export TFE_NOTIFICATION_TOKEN="your-hmac-token"
export TFE_AUTO_APPLY="false"  # Set to true with caution
python notifications.py
```

2. **Configure webhook in HCP Terraform:**
   - Navigate to your workspace settings
   - Add a notification configuration
   - Set webhook URL: `https://your-domain.com/webhook/apply`
   - Set HMAC token to match `TFE_NOTIFICATION_TOKEN`
   - Select triggers (e.g., drift detection, run completion)

## Endpoints

- `GET /health` - Health check endpoint
- `POST /webhook/apply` - Trigger an apply run
- `POST /webhook/destroy` - Trigger a destroy run
- `POST /webhook/conditional` - Conditionally trigger based on notification content

## Security

- **HMAC Verification**: Set `TFE_NOTIFICATION_TOKEN` to validate webhook authenticity
- **HTTPS**: Always use HTTPS in production (e.g., via ngrok or reverse proxy)
- **API Token**: Store `TFE_TOKEN` securely, never commit to version control

## Example Deployment

Using ngrok for testing:
```bash
ngrok http 5000
# Use the HTTPS URL provided by ngrok in your Terraform notification configuration
```

## How It Works

1. HCP Terraform detects an event (e.g., drift)
2. Sends webhook notification to middleware
3. Middleware verifies HMAC signature (if configured)
4. Extracts workspace information from payload
5. Creates a new run via Terraform API
6. Run executes in HCP Terraform (with optional auto-apply)

## Supported Notifications

- Drift detection (`assessment:drifted`)
- Run completion events
- Webhook verification requests
- Extensible for other notification types