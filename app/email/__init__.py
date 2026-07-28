"""Email delivery and HTML template rendering."""
from app.email.templates import render_verify_email_template, render_forgot_password_template

__all__ = ["render_verify_email_template", "render_forgot_password_template"]
