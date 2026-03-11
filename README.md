# Career Conversations API

Flask API exposing a conversational chat endpoint backed by OpenAI, using your existing `Me` profile logic.

## Setup

1. Create a `.env` file with:

```
OPENAI_API_KEY=sk-...
PUSHOVER_TOKEN=...
PUSHOVER_USER=...
RESEND_API_KEY=re_...
RESEND_FROM=your-email@yourdomain.com
RECAPTCHA_SECRET_KEY=...
```

2. Create and activate virtual environment, then install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Run the server (make sure the virtual environment is activated):

```bash
source venv/bin/activate  # Activate virtual environment if not already active
python app.py
```

**Note:** Always activate the virtual environment before running the app. If you see `ModuleNotFoundError`, it means the virtual environment is not activated.

Server starts on `http://localhost:8000`.

## Health Check

```bash
curl http://localhost:8000/health
```

## Chat Endpoint

- URL: `POST /chat`
- Body (JSON):

```json
{
  "message": "Hi there!",
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"}
  ]
}
```

- Response:

```json
{
  "reply": "...assistant reply..."
}
```

Notes:
- `history` is optional and should be a list of `{role, content}` messages.
- The server reads `me/summary.txt` and `me/linkedin.pdf` at startup; ensure those files exist.

## Contact Endpoint

- URL: `POST /contact`
- Body (JSON):

```json
{
  "fullName": "Jane Smith",
  "email": "jane@example.com",
  "company": "Acme Inc",
  "projectFocus": "Web Development",
  "message": "I would like to discuss a new project.",
  "recaptchaToken": "token_from_recaptcha"
}
```

- Response:

```json
{
  "status": "ok",
  "message": "Email sent successfully"
}
```

The contact form sends a formatted HTML email to `santiago@mightyideas.org` using Resend.

## Docker Setup

### Building and Running Locally

1. Build the Docker image:
```bash
docker build -t career-conversations-backend .
```

2. Run the container:
```bash
docker run -d \
  --name career-conversations-backend \
  -p 8000:8000 \
  --env-file .env \
  career-conversations-backend
```

3. Check logs:
```bash
docker logs -f career-conversations-backend
```

4. Stop the container:
```bash
docker stop career-conversations-backend
docker rm career-conversations-backend
```

### Running from DockerHub

If you want to use the pre-built image from DockerHub:

1. Pull the image:
```bash
docker pull santiagopanchi/career-conversations-backend:latest
```

2. Create a `.env` file with required environment variables:
```env
OPENAI_API_KEY=sk-...
PUSHOVER_TOKEN=...
PUSHOVER_USER=...
PORT=8000
```

3. Run the container:
```bash
docker run -d \
  --name career-conversations-backend \
  -p 8000:8000 \
  --env-file .env \
  santiagopanchi/career-conversations-backend:latest
```

**Important:** The following environment variables are required at runtime:
- `OPENAI_API_KEY` - OpenAI API key for chat functionality
- `PUSHOVER_TOKEN` - Pushover API token for notifications
- `PUSHOVER_USER` - Pushover user key for notifications
- `RESEND_API_KEY` - Resend API key for sending emails
- `RESEND_FROM` - Email address to send from (defaults to onboarding@resend.dev)
- `RECAPTCHA_SECRET_KEY` - reCAPTCHA secret key for contact form verification
- `PORT` - (Optional) Server port, defaults to 8000

Make sure to set these when running the container, either via `--env-file .env` or individual `-e` flags.

## Kubernetes Deployment

This application is designed to be deployed on Kubernetes. The Docker image is automatically built and pushed to DockerHub via GitHub Actions.

To deploy to Kubernetes, you'll need to:
1. Create Kubernetes manifests (Deployment, Service, ConfigMap, Secret)
2. Configure environment variables as Kubernetes Secrets
3. Apply the manifests to your cluster

The Docker image `santiagopanchi/career-conversations-backend:latest` is available on DockerHub and ready for Kubernetes deployment.


