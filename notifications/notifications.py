"""
Terraform Notification Middleware
Processes notifications from HCP Terraform/Terraform Enterprise and triggers runs.

Environment Variables (aligned with TFE provider):
----------------------------------------------------
Required:
  TFE_TOKEN           - API token for Terraform authentication

Optional:
  TFE_HOSTNAME        - Hostname of TFE/HCP Terraform instance 
                        (default: "app.terraform.io")
                        Examples: 
                        - "app.terraform.io" for HCP Terraform
                        - "terraform.company.com" for TFE

  TFE_SSL_SKIP_VERIFY - Skip SSL certificate verification
                        (default: "false", use "true" for self-signed certs)

  TFE_NOTIFICATION_TOKEN - HMAC token for verifying notification authenticity
                           If set, validates X-TFE-Notification-Signature header
                           (recommended for production)

  TFE_AUTO_APPLY      - Automatically apply runs after successful plan
                        (default: "false", use "true" to enable auto-apply)

  PORT                - Port for the middleware to listen on (default: 5000)
  DEBUG               - Enable Flask debug mode (default: "false")

For more info on TFE provider variables:
https://registry.terraform.io/providers/hashicorp/tfe/latest/docs

For notification authenticity:
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/notification-configurations#notification-authenticity
"""

import json
import logging
import os
import hmac
import hashlib
from typing import Dict, Optional, Literal
from dataclasses import dataclass
import requests
from flask import Flask, request, jsonify

# Configure logging with better formatting
logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG", "false").lower() == "true" else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Middleware to log all requests and responses
@app.before_request
def log_request_info():
    """Log all incoming request details"""
    logger.info("="*80)
    logger.info(f">>> INCOMING REQUEST: {request.method} {request.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Query Params: {dict(request.args)}")
    
    # Log body for POST/PUT requests
    if request.method in ['POST', 'PUT', 'PATCH']:
        # Get raw body for logging
        body = request.get_data(as_text=True)
        if body:
            try:
                # Try to parse as JSON for pretty printing
                json_body = json.loads(body)
                logger.info(f"Request Body (JSON):\n{json.dumps(json_body, indent=2)}")
            except json.JSONDecodeError:
                logger.info(f"Request Body (Raw): {body}")
        else:
            logger.info("Request Body: <empty>")
    logger.info("="*80)

@app.after_request
def log_response_info(response):
    """Log all outgoing response details"""
    logger.info("-"*80)
    logger.info(f"<<< RESPONSE STATUS: {response.status}")
    
    # Log response body if it's JSON
    if response.content_type == 'application/json':
        try:
            response_data = response.get_json()
            logger.info(f"Response Body:\n{json.dumps(response_data, indent=2)}")
        except:
            logger.info(f"Response Body: {response.get_data(as_text=True)}")
    logger.info("-"*80 + "\n")
    
    return response


@dataclass
class TerraformConfig:
    """Configuration for Terraform API access"""
    api_token: str
    hostname: str = "app.terraform.io"  # Default to HCP Terraform
    ssl_skip_verify: bool = False
    notification_token: Optional[str] = None  # HMAC token for verification
    auto_apply: bool = False  # Whether to auto-apply runs after successful plan
    
    @property
    def base_url(self) -> str:
        """Construct base URL from hostname"""
        protocol = "https"
        return f"{protocol}://{self.hostname}/api/v2"
    
    @classmethod
    def from_env(cls) -> 'TerraformConfig':
        """
        Create config from environment variables
        Aligned with TFE provider: https://registry.terraform.io/providers/hashicorp/tfe/latest/docs
        
        Environment variables:
        - TFE_TOKEN: API token for authentication
        - TFE_HOSTNAME: Hostname of TFE/HCP Terraform instance (default: app.terraform.io)
        - TFE_SSL_SKIP_VERIFY: Skip SSL verification (default: false)
        - TFE_NOTIFICATION_TOKEN: HMAC token for notification verification (optional but recommended)
        - TFE_AUTO_APPLY: Auto-apply runs after successful plan (default: false)
        """
        token = os.environ.get("TFE_TOKEN")
        
        if not token:
            raise ValueError("TFE_TOKEN environment variable is required")
        
        return cls(
            api_token=token,
            hostname=os.environ.get("TFE_HOSTNAME", "app.terraform.io"),
            ssl_skip_verify=os.environ.get("TFE_SSL_SKIP_VERIFY", "false").lower() in ["true", "1", "yes"],
            notification_token=os.environ.get("TFE_NOTIFICATION_TOKEN"),
            auto_apply=os.environ.get("TFE_AUTO_APPLY", "false").lower() in ["true", "1", "yes"]
        )


class TerraformClient:
    """Client for interacting with Terraform API"""
    
    def __init__(self, config: TerraformConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/vnd.api+json"
        })
        
        # Configure SSL verification
        if config.ssl_skip_verify:
            self.session.verify = False
            # Suppress SSL warnings if verification is disabled
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def create_run(
        self,
        workspace_id: str,
        run_type: Literal["apply", "destroy"],
        message: Optional[str] = None,
        is_destroy: bool = False,
        auto_apply: bool = False
    ) -> Dict:
        """
        Create a new run in a workspace
        According to: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run#create-a-run
        
        Args:
            workspace_id: The workspace ID to run
            run_type: Type of run ("apply" or "destroy")
            message: Optional message for the run
            is_destroy: Whether this is a destroy run
            auto_apply: Whether to auto-apply after plan
        
        Returns:
            API response as dict
        """
        url = f"{self.config.base_url}/runs"
        
        # Prepare the run payload according to API spec
        run_data = {
            "data": {
                "attributes": {
                    "is-destroy": is_destroy or run_type == "destroy",
                    "message": message or f"Triggered by notification middleware - {run_type}",
                    "auto-apply": auto_apply  # This is the correct location per API docs
                },
                "type": "runs",
                "relationships": {
                    "workspace": {
                        "data": {
                            "type": "workspaces",
                            "id": workspace_id
                        }
                    }
                }
            }
        }
        
        logger.info(f"Creating {run_type} run for workspace {workspace_id}")
        logger.info(f"Run payload auto-apply setting: {auto_apply}")
        logger.debug(f"Full run payload: {json.dumps(run_data, indent=2)}")
        
        try:
            response = self.session.post(url, json=run_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create run: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_workspace_by_id(self, workspace_id: str) -> Dict:
        """Get workspace details by ID"""
        url = f"{self.config.base_url}/workspaces/{workspace_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get workspace: {e}")
            raise


class NotificationProcessor:
    """Process Terraform notifications and trigger appropriate actions"""
    
    def __init__(self, client: TerraformClient):
        self.client = client
    
    def verify_signature(self, payload_body: bytes, signature: str, token: str) -> bool:
        """
        Verify the HMAC signature of the notification
        
        Args:
            payload_body: Raw request body as bytes
            signature: X-TFE-Notification-Signature header value
            token: HMAC token configured in notification settings
        
        Returns:
            True if signature is valid, False otherwise
        """
        # Compute HMAC-SHA512
        computed_signature = hmac.new(
            token.encode('utf-8'),
            payload_body,
            hashlib.sha512
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed_signature, signature)
    
    def extract_workspace_info(self, payload: Dict) -> tuple[str, str, str]:
        """
        Extract workspace ID, organization name, and workspace name from notification payload
        
        Args:
            payload: Notification payload from Terraform
        
        Returns:
            Tuple of (workspace_id, org_name, workspace_name)
        """
        logger.info("Starting workspace extraction")
        
        # First check at top level (for run notifications)
        workspace_id = payload.get("workspace_id", "")
        workspace_name = payload.get("workspace_name", "")
        org_name = payload.get("organization_name", "")
        
        if workspace_id:
            logger.info(f"Found workspace at TOP LEVEL: id={workspace_id}, name={workspace_name}, org={org_name}")
        else:
            # For drift/assessment notifications, workspace info is in details
            logger.info("No workspace at top level, checking details...")
            details = payload.get("details", {})
            if details:
                workspace_id = details.get("workspace_id", "")
                workspace_name = details.get("workspace_name", "")
                org_name = details.get("organization_name", "")
                logger.info(f"Found workspace in DETAILS: id={workspace_id}, name={workspace_name}, org={org_name}")
            else:
                logger.warning("No details object in payload")
        
        if not workspace_id:
            logger.error(f"Failed to find workspace_id. Payload keys: {list(payload.keys())}")
            if 'details' in payload:
                logger.error(f"Details contains: {list(payload.get('details', {}).keys())}")
            raise ValueError("workspace_id not found in notification payload")
        
        return workspace_id, org_name, workspace_name
    
    def process_notification(
        self,
        payload: Dict,
        action: Literal["apply", "destroy"],
        auto_apply: bool = False
    ) -> Dict:
        """
        Process a notification and trigger the appropriate run
        
        Args:
            payload: Notification payload from Terraform
            action: Action to perform ("apply" or "destroy")
            auto_apply: Whether to auto-apply after plan
        
        Returns:
            Response from run creation
        """
        # Extract workspace information
        workspace_id, org_name, workspace_name = self.extract_workspace_info(payload)
        
        logger.info(f"Processing notification for workspace '{workspace_name}' in org '{org_name}'")
        logger.info(f"Action: {action}, Auto-apply: {auto_apply}")
        
        # Get notification context
        trigger = payload.get("trigger", "")
        trigger_scope = payload.get("trigger_scope", "")
        notification_message = payload.get("message", "")
        
        # Get run context if this is a run notification
        run_id = payload.get("run_id", "")
        run_status = payload.get("run_status", "")
        run_message = payload.get("run_message", "")
        
        # Create a descriptive message for the new run
        if trigger:
            message = f"Triggered by {trigger}: {notification_message}"
        elif run_id:
            message = f"Triggered by notification from run {run_id} (status: {run_status})"
            if run_message:
                message += f" - Previous run message: {run_message}"
        else:
            message = f"Triggered by notification middleware - {action}"
        
        logger.info(f"Creating run with message: {message}")
        
        # Create the run
        result = self.client.create_run(
            workspace_id=workspace_id,
            run_type=action,
            message=message,
            is_destroy=(action == "destroy"),
            auto_apply=auto_apply
        )
        
        logger.info(f"Successfully created {action} run: {result.get('data', {}).get('id', 'unknown')}")
        
        return result


# Helper function to check if this is a verification request
def is_verification_request(payload: Dict) -> bool:
    """
    Check if the request is a verification/test request from Terraform
    
    Args:
        payload: Request payload
    
    Returns:
        True if this is a verification request
    """
    # Log what we're checking
    logger.info(f"Checking if verification request. Payload keys: {payload.keys()}")
    
    # Verification requests have a 'notifications' array with trigger="verification"
    # This is different from regular notifications which have 'trigger' at top level
    notifications = payload.get("notifications", [])
    
    if notifications:
        logger.info(f"Found {len(notifications)} notifications")
        for notification in notifications:
            trigger = notification.get("trigger", "")
            logger.info(f"Notification trigger: '{trigger}'")
            if trigger == "verification":
                logger.info("Detected verification request")
                return True
    
    # Also check top-level trigger (shouldn't be there for verification, but just in case)
    trigger = payload.get("trigger", "")
    if trigger:
        logger.info(f"Top-level trigger value: '{trigger}'")
    
    logger.info("Not a verification request")
    return False


# Helper function for signature verification
def verify_notification_signature(config: TerraformConfig, is_verification: bool = False) -> Optional[tuple[bool, str]]:
    """
    Verify the notification signature if token is configured
    
    Args:
        config: Terraform configuration
        is_verification: Whether this is a verification request (for logging)
    
    Returns:
        None if no verification needed
        (True, message) if verification passed
        (False, error_message) if verification failed
    """
    if not config.notification_token:
        # No token configured, skip verification
        logger.debug("No notification token configured, skipping signature verification")
        return None
    
    signature = request.headers.get("X-TFE-Notification-Signature", "")
    
    # Handle empty signature header (present but empty string)
    if signature == "":
        logger.warning(f"Empty signature header for {'verification' if is_verification else 'notification'} request")
        # For verification requests with no token configured in Terraform, the header may be empty
        # We'll allow this if it's a verification request
        if is_verification:
            logger.info("Allowing verification request with empty signature (notification may not have token configured)")
            return None
        return False, "Empty X-TFE-Notification-Signature header"
    
    if not signature:
        logger.warning(f"Missing signature header for {'verification' if is_verification else 'notification'} request")
        return False, "Missing X-TFE-Notification-Signature header"
    
    # Get raw request body for signature verification
    payload_body = request.get_data()
    
    # Log signature details for debugging
    logger.debug(f"Signature verification for {'verification' if is_verification else 'notification'} request:")
    logger.debug(f"  Received signature: {signature[:20]}...")
    logger.debug(f"  Payload length: {len(payload_body)} bytes")
    
    # Create a processor instance temporarily for verification
    processor = NotificationProcessor(None)  # Client not needed for verification
    
    # Compute expected signature
    computed_signature = hmac.new(
        config.notification_token.encode('utf-8'),
        payload_body,
        hashlib.sha512
    ).hexdigest()
    
    logger.debug(f"  Computed signature: {computed_signature[:20]}...")
    
    if not processor.verify_signature(payload_body, signature, config.notification_token):
        logger.warning(f"Signature mismatch for {'verification' if is_verification else 'notification'} request")
        return False, "Invalid signature"
    
    logger.info(f"Signature verified successfully for {'verification' if is_verification else 'notification'} request")
    return True, "Signature valid"


# Flask routes for the middleware
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


@app.route("/webhook/apply", methods=["POST"])
def trigger_apply():
    """Webhook endpoint to trigger an apply run"""
    logger.info("=== Starting /webhook/apply handler ===")
    try:
        # Get payload first
        payload = request.json
        if not payload:
            logger.error("No payload provided")
            return jsonify({"error": "No payload provided"}), 400
        
        logger.info(f"Received payload with keys: {list(payload.keys())}")
        
        # CHECK FOR VERIFICATION REQUEST FIRST - BEFORE ANYTHING ELSE
        is_verification = is_verification_request(payload)
        logger.info(f"Is verification request: {is_verification}")
        
        # HANDLE VERIFICATION IMMEDIATELY
        if is_verification:
            logger.info("Handling verification request - returning 200 OK")
            return jsonify({
                "status": "success",
                "message": "Webhook verified successfully",
                "type": "verification"
            }), 200
        
        logger.info("Not a verification request, processing as normal notification")
        
        # For regular notifications, initialize config and verify signature
        config = TerraformConfig.from_env()
        
        # Verify signature if token is configured
        verification_result = verify_notification_signature(config, is_verification)
        if verification_result is not None:
            valid, message = verification_result
            if not valid:
                logger.warning(f"Signature verification failed: {message}")
                return jsonify({"error": f"Unauthorized: {message}"}), 401
        
        # Initialize client and processor for regular notifications
        client = TerraformClient(config)
        processor = NotificationProcessor(client)
        
        # Process the notification - USE CONFIG.AUTO_APPLY HERE
        logger.info(f"Using auto_apply from config: {config.auto_apply}")
        result = processor.process_notification(payload, "apply", auto_apply=config.auto_apply)
        
        return jsonify({
            "status": "success",
            "run_id": result.get("data", {}).get("id"),
            "message": "Apply run created successfully"
        }), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/webhook/destroy", methods=["POST"])
def trigger_destroy():
    """Webhook endpoint to trigger a destroy run"""
    logger.info("=== Starting /webhook/destroy handler ===")
    try:
        # Get payload first
        payload = request.json
        if not payload:
            logger.error("No payload provided")
            return jsonify({"error": "No payload provided"}), 400
        
        logger.info(f"Received payload with keys: {list(payload.keys())}")
        
        # CHECK FOR VERIFICATION REQUEST FIRST - BEFORE ANYTHING ELSE
        is_verification = is_verification_request(payload)
        logger.info(f"Is verification request: {is_verification}")
        
        # HANDLE VERIFICATION IMMEDIATELY
        if is_verification:
            logger.info("Handling verification request - returning 200 OK")
            return jsonify({
                "status": "success",
                "message": "Webhook verified successfully",
                "type": "verification"
            }), 200
        
        logger.info("Not a verification request, processing as normal notification")
        
        # For regular notifications, initialize config and verify signature
        config = TerraformConfig.from_env()
        
        # Verify signature if token is configured
        verification_result = verify_notification_signature(config, is_verification)
        if verification_result is not None:
            valid, message = verification_result
            if not valid:
                logger.warning(f"Signature verification failed: {message}")
                return jsonify({"error": f"Unauthorized: {message}"}), 401
        
        # Initialize client and processor for regular notifications
        client = TerraformClient(config)
        processor = NotificationProcessor(client)
        
        # Process the notification - USE CONFIG.AUTO_APPLY HERE
        logger.info(f"Using auto_apply from config: {config.auto_apply}")
        result = processor.process_notification(payload, "destroy", auto_apply=config.auto_apply)
        
        return jsonify({
            "status": "success",
            "run_id": result.get("data", {}).get("id"),
            "message": "Destroy run created successfully"
        }), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/webhook/conditional", methods=["POST"])
def trigger_conditional():
    """
    Webhook endpoint that determines action based on notification content
    You can customize this logic based on your needs
    """
    logger.info("=== Starting /webhook/conditional handler ===")
    try:
        # Get payload first
        payload = request.json
        if not payload:
            logger.error("No payload provided")
            return jsonify({"error": "No payload provided"}), 400
        
        logger.info(f"Received payload with keys: {list(payload.keys())}")
        
        # CHECK FOR VERIFICATION REQUEST FIRST - BEFORE ANYTHING ELSE
        is_verification = is_verification_request(payload)
        logger.info(f"Is verification request: {is_verification}")
        
        # HANDLE VERIFICATION IMMEDIATELY
        if is_verification:
            logger.info("Handling verification request - returning 200 OK")
            return jsonify({
                "status": "success",
                "message": "Webhook verified successfully",
                "type": "verification"
            }), 200
        
        logger.info("Not a verification request, processing as normal notification")
        
        # For regular notifications, initialize config and verify signature
        config = TerraformConfig.from_env()
        
        # Verify signature if token is configured
        verification_result = verify_notification_signature(config, is_verification)
        if verification_result is not None:
            valid, message = verification_result
            if not valid:
                logger.warning(f"Signature verification failed: {message}")
                return jsonify({"error": f"Unauthorized: {message}"}), 401
        
        # Initialize client and processor for regular notifications
        client = TerraformClient(config)
        processor = NotificationProcessor(client)
        
        # Determine action based on notification content
        # Example logic - customize based on your requirements:
        run_status = payload.get("run_status", "")
        run_message = payload.get("run_message", "").lower()
        
        # Example: If the previous run was a successful apply and message contains "destroy",
        # trigger a destroy. Otherwise, trigger an apply.
        if "destroy" in run_message or "teardown" in run_message:
            action = "destroy"
        elif run_status == "errored":
            # Maybe retry with apply if previous run errored
            action = "apply"
        else:
            action = "apply"
        
        # Process the notification - USE CONFIG.AUTO_APPLY HERE
        logger.info(f"Using auto_apply from config: {config.auto_apply}")
        result = processor.process_notification(payload, action, auto_apply=config.auto_apply)
        
        return jsonify({
            "status": "success",
            "run_id": result.get("data", {}).get("id"),
            "action": action,
            "message": f"{action.capitalize()} run created successfully"
        }), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Check for required environment variables
    if not os.environ.get("TFE_TOKEN"):
        logger.error("TFE_TOKEN environment variable is required")
        logger.error("See: https://registry.terraform.io/providers/hashicorp/tfe/latest/docs")
        exit(1)
    
    # Display configuration on startup
    try:
        config = TerraformConfig.from_env()
        logger.info(f"Terraform API Configuration:")
        logger.info(f"  Hostname: {config.hostname}")
        logger.info(f"  API URL: {config.base_url}")
        logger.info(f"  SSL Verify: {not config.ssl_skip_verify}")
        logger.info(f"  Auto-Apply: {config.auto_apply}")
        logger.info(f"  HMAC Verification: {'Enabled' if config.notification_token else 'Disabled (TFE_NOTIFICATION_TOKEN not set)'}")
        
        if not config.notification_token:
            logger.warning("⚠️  TFE_NOTIFICATION_TOKEN not set - webhook signatures will not be verified")
            logger.warning("   For production use, set TFE_NOTIFICATION_TOKEN to match your notification configuration")
        
        if config.auto_apply:
            logger.warning("⚠️  Auto-apply is ENABLED - runs will be automatically applied after successful plan")
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)
    
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting Terraform notification middleware on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)