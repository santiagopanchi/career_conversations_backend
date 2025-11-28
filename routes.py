"""Flask routes and endpoints."""
from flask import request, jsonify
from recaptcha import verify_recaptcha
from email_service import send_contact_email
from me import Me


def register_routes(app, me_instance: Me):
    """
    Register all routes with the Flask app.
    
    Args:
        app: Flask application instance
        me_instance: Me class instance for chat functionality
    """
    
    @app.get("/health")
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "ok"})

    @app.post("/contact")
    def contact_endpoint():
        """Handle contact form submissions."""
        try:
            payload = request.get_json(silent=True) or {}
            
            # Verify reCAPTCHA token
            recaptcha_token = payload.get("recaptchaToken")
            is_valid, error_message = verify_recaptcha(recaptcha_token)
            
            if not is_valid:
                return jsonify({
                    "error": "reCAPTCHA verification failed",
                    "details": error_message
                }), 400
            
            full_name = payload.get("fullName", "Not provided")
            email = payload.get("email", "Not provided")
            company = payload.get("company", "Not provided")
            project_focus = payload.get("projectFocus", "Not provided")
            message = payload.get("message", "Not provided")

            send_contact_email(full_name, email, company, project_focus, message)

            return jsonify({"status": "ok", "message": "Email sent successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.post("/chat")
    def chat_endpoint():
        """Handle chat messages."""
        try:
            payload = request.get_json(silent=True) or {}
            message = payload.get("message")
            history = payload.get("history") or []
            if not isinstance(history, list):
                return jsonify({"error": "history must be a list of messages"}), 400
            if not message or not isinstance(message, str):
                return jsonify({"error": "message is required and must be a string"}), 400

            reply = me_instance.chat(message=message, history=history)
            return jsonify({"reply": reply})
        except Exception as e:
            # Keep response minimal but useful
            return jsonify({"error": str(e)}), 500

