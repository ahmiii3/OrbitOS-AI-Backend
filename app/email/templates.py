from jinja2 import Template

VERIFY_EMAIL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email Address</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f7f6;
            margin: 0;
            padding: 0;
            color: #333333;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
            overflow: hidden;
            border: 1px solid #eaeaea;
        }
        .header {
            background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
            padding: 36px 40px;
            text-align: center;
            color: #ffffff;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        .content {
            padding: 40px;
            line-height: 1.6;
        }
        .content p {
            margin: 0 0 20px;
            font-size: 16px;
            color: #4b5563;
        }
        .code-box {
            text-align: center;
            margin: 36px 0;
        }
        .verification-code {
            display: inline-block;
            background: linear-gradient(135deg, #f0f0ff 0%, #e8e8ff 100%);
            border: 2px dashed #4f46e5;
            border-radius: 12px;
            padding: 20px 48px;
            font-size: 36px;
            font-weight: 800;
            letter-spacing: 12px;
            color: #4f46e5;
            font-family: 'Courier New', monospace;
        }
        .footer {
            background-color: #f9fafb;
            padding: 24px 40px;
            text-align: center;
            font-size: 13px;
            color: #9ca3af;
            border-top: 1px solid #f3f4f6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>OrbitOS AI</h1>
        </div>
        <div class="content">
            <p>Hi <strong>{{ name }}</strong>,</p>
            <p>Welcome to OrbitOS AI! Please use the verification code below to confirm your email address and activate your account:</p>
            <div class="code-box">
                <div class="verification-code">{{ code }}</div>
            </div>
            <p style="text-align: center; font-size: 14px; color: #6b7280;">Enter this code in the app to verify your email.</p>
            <p style="margin-top: 24px; font-size: 14px; color: #6b7280;">This code will expire in 24 hours. If you did not create an account, you can safely ignore this email.</p>
        </div>
        <div class="footer">
            &copy; 2026 OrbitOS AI. All rights reserved.
        </div>
    </div>
</body>
</html>
"""

FORGOT_PASSWORD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f7f6;
            margin: 0;
            padding: 0;
            color: #333333;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
            overflow: hidden;
            border: 1px solid #eaeaea;
        }
        .header {
            background: linear-gradient(135deg, #111827 0%, #374151 100%);
            padding: 36px 40px;
            text-align: center;
            color: #ffffff;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        .content {
            padding: 40px;
            line-height: 1.6;
        }
        .content p {
            margin: 0 0 20px;
            font-size: 16px;
            color: #4b5563;
        }
        .button-wrapper {
            text-align: center;
            margin: 36px 0;
        }
        .btn {
            display: inline-block;
            background-color: #ef4444;
            color: #ffffff !important;
            text-decoration: none;
            padding: 14px 32px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
            transition: background-color 0.2s ease;
        }
        .footer {
            background-color: #f9fafb;
            padding: 24px 40px;
            text-align: center;
            font-size: 13px;
            color: #9ca3af;
            border-top: 1px solid #f3f4f6;
        }
        .link-text {
            word-break: break-all;
            font-size: 13px;
            color: #6b7280;
            background: #f3f4f6;
            padding: 12px;
            border-radius: 6px;
        }
        .warning-box {
            background-color: #fef2f2;
            border-left: 4px solid #ef4444;
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 24px;
        }
        .warning-box p {
            margin: 0;
            color: #991b1b;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hi <strong>{{ name }}</strong>,</p>
            <p>We received a request to reset the password for your Enterprise SaaS account. Click the button below to choose a new password:</p>
            <div class="button-wrapper">
                <a href="{{ reset_url }}" class="btn">Reset Password</a>
            </div>
            <div class="warning-box">
                <p><strong>Note:</strong> For security reasons, this password reset link will expire in exactly 30 minutes.</p>
            </div>
            <p>If you cannot click the button, copy and paste this link into your browser:</p>
            <div class="link-text">{{ reset_url }}</div>
            <p style="margin-top: 24px; font-size: 14px; color: #6b7280;">If you did not request a password reset, please ignore this email or contact support if you suspect suspicious activity.</p>
        </div>
        <div class="footer">
            &copy; 2026 OrbitOS AI. All rights reserved.
        </div>
    </div>
</body>
</html>
"""


def render_verify_email_template(name: str, code: str) -> str:
    """Render the email verification HTML template with a 6-digit code."""
    template = Template(VERIFY_EMAIL_HTML)
    return template.render(name=name, code=code)


def render_forgot_password_template(name: str, reset_url: str) -> str:
    """Render the forgot password HTML template."""
    template = Template(FORGOT_PASSWORD_HTML)
    return template.render(name=name, reset_url=reset_url)
