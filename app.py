from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import resend
from pypdf import PdfReader
from flask import Flask, request, jsonify
from flask_cors import CORS


load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def verify_recaptcha(token):
    """Verify reCAPTCHA v3 token with Google"""
    secret_key = os.getenv("RECAPTCHA_SECRET_KEY")
    
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


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Javier Santiago Panchi"
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. Limit your answer to 200 words and \
try to start with my latest career experience and certifications"

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

app = Flask(__name__)
CORS(app)

# Initialize once at process start
me = Me()


@app.get("/health")
def health_check():
    return jsonify({"status": "ok"})


@app.post("/contact")
def contact_endpoint():
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

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <h2 style="color: #2d5016; border-bottom: 2px solid #2d5016; padding-bottom: 10px;">New Contact Form Submission</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px 0; font-weight: bold; color: #333;">Full Name:</td>
                        <td style="padding: 10px 0; color: #555;">{full_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; font-weight: bold; color: #333;">Email:</td>
                        <td style="padding: 10px 0; color: #555;"><a href="mailto:{email}">{email}</a></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; font-weight: bold; color: #333;">Company:</td>
                        <td style="padding: 10px 0; color: #555;">{company}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; font-weight: bold; color: #333;">Project Focus:</td>
                        <td style="padding: 10px 0; color: #555;">{project_focus}</td>
                    </tr>
                </table>
                <h3 style="color: #2d5016; margin-top: 20px;">Message:</h3>
                <p style="background: #f9f9f9; padding: 15px; border-radius: 5px; color: #555;">{message}</p>
            </div>
        </body>
        </html>
        """

        resend.api_key = os.getenv("RESEND_API_KEY")
        
        resend.Emails.send({
            "from": os.getenv("RESEND_FROM", "onboarding@resend.dev"),
            "to": "santiago@mightyideas.org",
            "subject": f"New Contact: {full_name} - {project_focus}",
            "html": html_content
        })

        return jsonify({"status": "ok", "message": "Email sent successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/chat")
def chat_endpoint():
    try:
        payload = request.get_json(silent=True) or {}
        message = payload.get("message")
        history = payload.get("history") or []
        if not isinstance(history, list):
            return jsonify({"error": "history must be a list of messages"}), 400
        if not message or not isinstance(message, str):
            return jsonify({"error": "message is required and must be a string"}), 400

        reply = me.chat(message=message, history=history)
        return jsonify({"reply": reply})
    except Exception as e:
        # Keep response minimal but useful
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Default to port 8000 for local dev
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)