import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_ticket_notification(ticket: dict, customer: dict):
    """Send email to admin when a new ticket is submitted."""
    try:
        smtp_host   = st.secrets["SMTP_HOST"]
        smtp_port   = int(st.secrets.get("SMTP_PORT", 587))
        smtp_user   = st.secrets["SMTP_USER"]
        smtp_pass   = st.secrets["SMTP_PASSWORD"]
        admin_email = st.secrets["ADMIN_EMAIL"]

        urgency_colors = {
            "low":       "#6c757d",
            "normal":    "#0d6efd",
            "high":      "#fd7e14",
            "emergency": "#dc3545"
        }
        color = urgency_colors.get(ticket.get("urgency", "normal"), "#0d6efd")

        html = f"""
        <html><body style="font-family:Arial,sans-serif; color:#333;">
          <div style="max-width:600px; margin:auto; border:1px solid #ddd; border-radius:8px; overflow:hidden;">
            <div style="background:#1a1a2e; padding:20px;">
              <h2 style="color:white; margin:0;">🔒 5G Security — New Support Ticket</h2>
            </div>
            <div style="padding:24px;">
              <table style="width:100%; border-collapse:collapse;">
                <tr><td style="padding:8px; font-weight:bold; width:140px;">Customer:</td>
                    <td style="padding:8px;">{customer.get('company','N/A')}</td></tr>
                <tr style="background:#f8f9fa;">
                    <td style="padding:8px; font-weight:bold;">System:</td>
                    <td style="padding:8px;">{ticket.get('system_type','N/A').replace('_',' ').title()}</td></tr>
                <tr><td style="padding:8px; font-weight:bold;">Urgency:</td>
                    <td style="padding:8px;">
                      <span style="background:{color}; color:white; padding:2px 10px; border-radius:12px; font-size:0.85rem;">
                        {ticket.get('urgency','normal').upper()}
                      </span>
                    </td></tr>
                <tr style="background:#f8f9fa;">
                    <td style="padding:8px; font-weight:bold;">Title:</td>
                    <td style="padding:8px;">{ticket.get('title','')}</td></tr>
                <tr><td style="padding:8px; font-weight:bold; vertical-align:top;">Description:</td>
                    <td style="padding:8px;">{ticket.get('description','').replace(chr(10),'<br>')}</td></tr>
              </table>
              {"<p><a href='" + ticket['photo_url'] + "' style='color:#0d6efd;'>📎 View Attached Photo</a></p>" if ticket.get('photo_url') else ''}
              <hr style="margin:20px 0;">
              <p style="color:#666; font-size:0.85rem;">Log in to the admin panel to update this ticket's status.</p>
            </div>
          </div>
        </body></html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[5G Security] New Ticket — {ticket.get('urgency','').upper()} | {customer.get('company','Unknown')}"
        msg["From"]    = smtp_user
        msg["To"]      = admin_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, admin_email, msg.as_string())

        return True

    except Exception as e:
        st.warning(f"Ticket saved, but email notification failed: {e}")
        return False


def send_ticket_status_update(ticket: dict, customer_email: str, customer_name: str):
    """Notify the customer when their ticket status changes."""
    try:
        smtp_host  = st.secrets["SMTP_HOST"]
        smtp_port  = int(st.secrets.get("SMTP_PORT", 587))
        smtp_user  = st.secrets["SMTP_USER"]
        smtp_pass  = st.secrets["SMTP_PASSWORD"]

        status_labels = {
            "open":        ("📋 Open",       "#6c757d"),
            "in_progress": ("🔧 In Progress", "#fd7e14"),
            "resolved":    ("✅ Resolved",    "#198754"),
            "closed":      ("🔒 Closed",      "#1a1a2e"),
        }
        label, color = status_labels.get(ticket.get("status", "open"), ("Updated", "#333"))

        html = f"""
        <html><body style="font-family:Arial,sans-serif; color:#333;">
          <div style="max-width:600px; margin:auto; border:1px solid #ddd; border-radius:8px; overflow:hidden;">
            <div style="background:#1a1a2e; padding:20px;">
              <h2 style="color:white; margin:0;">🔒 5G Security — Ticket Update</h2>
            </div>
            <div style="padding:24px;">
              <p>Hi {customer_name},</p>
              <p>Your support ticket has been updated:</p>
              <table style="width:100%; border-collapse:collapse;">
                <tr><td style="padding:8px; font-weight:bold; width:120px;">Ticket:</td>
                    <td style="padding:8px;">#{ticket['id']} — {ticket.get('title','')}</td></tr>
                <tr style="background:#f8f9fa;">
                    <td style="padding:8px; font-weight:bold;">New Status:</td>
                    <td style="padding:8px;">
                      <span style="background:{color}; color:white; padding:2px 10px; border-radius:12px; font-size:0.85rem;">
                        {label}
                      </span>
                    </td></tr>
                {"<tr><td style='padding:8px; font-weight:bold; vertical-align:top;'>Notes:</td><td style='padding:8px;'>" + ticket.get('admin_notes','').replace(chr(10),'<br>') + "</td></tr>" if ticket.get('admin_notes') else ''}
              </table>
              <hr style="margin:20px 0;">
              <p>Log in to your portal to view full details.</p>
              <p style="color:#666; font-size:0.85rem;">5G Security | support@5gsecurity.com</p>
            </div>
          </div>
        </body></html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[5G Security] Ticket #{ticket['id']} Status Updated — {label}"
        msg["From"]    = smtp_user
        msg["To"]      = customer_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, customer_email, msg.as_string())

        return True
    except Exception as e:
        st.warning(f"Status updated, but customer email failed: {e}")
        return False
