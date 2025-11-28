"""reCAPTCHA verification functions."""
import requests
from config import get_env


def verify_recaptcha(token: str) -> tuple[bool, str | None]:
    """
    Verify reCAPTCHA v3 token with Google.
    
    Args:
        token: The reCAPTCHA token to verify
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if verification passed, False otherwise
        - error_message: None if valid, error message string if invalid
    """
    secret_key = get_env("RECAPTCHA_SECRET_KEY")
    
    if not secret_key:
        print("Warning: RECAPTCHA_SECRET_KEY not set", flush=True)
        return False, "reCAPTCHA secret key not configured"
    
    if not token:
        return False, "reCAPTCHA token missing"
    
    try:
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": secret_key,
                "response": token
            },
            timeout=5
        )
        
        result = response.json()
        
        # For reCAPTCHA v3, check the score (0.0 - 1.0)
        # 0.0 is very likely a bot, 1.0 is very likely a human
        success = result.get("success", False)
        score = result.get("score", 0.0)
        action = result.get("action", "")
        
        print(f"reCAPTCHA verification: success={success}, score={score}, action={action}", flush=True)
        
        # Require score of at least 0.5 for v3
        if success and score >= 0.5:
            return True, None
        elif success:
            return False, f"reCAPTCHA score too low: {score}"
        else:
            error_codes = result.get("error-codes", [])
            return False, f"reCAPTCHA verification failed: {error_codes}"
            
    except Exception as e:
        print(f"reCAPTCHA verification error: {str(e)}", flush=True)
        return False, f"reCAPTCHA verification error: {str(e)}"

