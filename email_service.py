"""Email service using Resend."""
import resend
from config import get_env


def send_contact_email(full_name: str, email: str, company: str, project_focus: str, message: str) -> None:
    """
    Send a formatted HTML email for contact form submissions.
    
    Args:
        full_name: Full name of the contact
        email: Email address of the contact
        company: Company/organization name
        project_focus: Selected project focus
        message: Message content
    """
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

    resend.api_key = get_env("RESEND_API_KEY")
    
    resend.Emails.send({
        "from": get_env("RESEND_FROM", "onboarding@resend.dev"),
        "to": "santiago@mightyideas.org",
        "subject": f"New Contact: {full_name} - {project_focus}",
        "html": html_content
    })

