import secrets
import streamlit as st
from datetime import datetime, timezone, timedelta
from utils.db import fetchone, execute, execute_returning


def create_reset_token(user_id: int) -> str:
    """Generate a secure reset token, store it, and return it."""
    # Invalidate any existing tokens for this user
    execute("DELETE FROM password_reset_tokens WHERE user_id = %s", (user_id,))

    token      = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    execute(
        "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
        (user_id, token, expires_at)
    )
    return token


def validate_reset_token(token: str):
    """
    Check token is valid and not expired.
    Returns user row if valid, None otherwise.
    """
    row = fetchone("""
        SELECT prt.*, u.id as user_id, u.email, u.name, u.role
        FROM password_reset_tokens prt
        JOIN users u ON u.id = prt.user_id
        WHERE prt.token = %s AND prt.expires_at > NOW()
    """, (token,))
    return row


def consume_reset_token(token: str):
    """Delete the token after use so it can't be reused."""
    execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))


def send_reset_email(to_email: str, name: str, token: str):
    """Send password reset email with link."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    try:
        smtp_host  = st.secrets["SMTP_HOST"]
        smtp_port  = int(st.secrets.get("SMTP_PORT", 587))
        smtp_user  = st.secrets["SMTP_USER"]
        smtp_pass  = st.secrets["SMTP_PASSWORD"]
        portal_url = "https://5gticket.streamlit.app"

        reset_url = f"{portal_url}?reset_token={token}"

        html = f"""
        <html><body style="font-family:Arial,sans-serif; color:#333;">
          <div style="max-width:600px; margin:auto; border:1px solid #ddd; border-radius:8px; overflow:hidden;">
            <div style="background:#1a1a1a; padding:24px; text-align:center;">
              <h1 style="color:#E8000E; margin:0; font-size:1.8rem; letter-spacing:2px;">5G SECURITY</h1>
              <p style="color:#888; margin:4px 0 0 0; font-size:0.85rem; letter-spacing:1px;">PASSWORD RESET</p>
            </div>
            <div style="padding:32px;">
              <p style="font-size:1.1rem;">Hi {name},</p>
              <p>We received a request to reset your password for the 5G Security Customer Portal.</p>
              <p>Click the button below to set a new password. This link expires in <strong>1 hour</strong>.</p>

              <div style="text-align:center; margin:32px 0;">
                <a href="{reset_url}" style="background:#E8000E; color:white; padding:14px 36px;
                   border-radius:4px; text-decoration:none; font-weight:bold; font-size:1rem;
                   letter-spacing:1px;">
                  Reset My Password →
                </a>
              </div>

              <p style="color:#888; font-size:0.85rem;">
                If you didn't request this, you can safely ignore this email.
                Your password will not change.
              </p>
              <p style="color:#aaa; font-size:0.8rem;">
                Or copy this link into your browser:<br>
                <a href="{reset_url}" style="color:#E8000E; word-break:break-all;">{reset_url}</a>
              </p>

              <hr style="margin:32px 0; border:none; border-top:1px solid #eee;">
              <p style="color:#aaa; font-size:0.8rem; text-align:center; margin:0;">
                5G Security &nbsp;|&nbsp;
                <a href="mailto:{smtp_user}" style="color:#aaa;">Contact Us</a>
              </p>
            </div>
          </div>
        </body></html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "[5G Security] Password Reset Request"
        msg["From"]    = smtp_user
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())

        return True
    except Exception as e:
        st.warning(f"Reset email failed: {e}")
        return False
