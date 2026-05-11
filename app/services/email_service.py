import aiosmtplib
from email.message import EmailMessage
import logging
from app import db, config

logger = logging.getLogger(__name__)

async def send_digest_email():
    """
    Fetches all active projects, formats them into a digest HTML,
    fetches the mailing list, and sends the email via SMTP.
    """
    subscribers = await db.get_mailing_list()
    if not subscribers:
        logger.info("No subscribers in the mailing list. Skipping digest email.")
        return

    projects = await db.get_projects(status='active', sort='stars')
    
    if not projects:
        logger.info("No active projects found. Skipping digest email.")
        return

    # Build HTML Digest
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            h2 { color: #0078D7; }
            .project { border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 5px; }
            .badge { display: inline-block; padding: 2px 6px; background: #eee; border-radius: 3px; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <h2>HOIISP Weekly Project Digest</h2>
        <p>Here are the currently active projects on the Habib Open Innovation & Independent Study Platform:</p>
    """

    for p in projects:
        html_content += f"""
        <div class="project">
            <h3 style="margin-top:0;">{p['title']}</h3>
            <p><strong>Domain:</strong> {p.get('domain', 'N/A')}</p>
            <p><strong>Team Size:</strong> {p.get('team_size', 0)}</p>
            <p><strong>Milestones Completed:</strong> {p.get('completed_milestones', 0)} / {p.get('total_milestones', 0)}</p>
            <p><strong>Stars:</strong> {p.get('stars', 0)}</p>
            <p><a href="{config.HOIISP_BASE_URL}/projects/{p['slug']}">View Full Details</a></p>
        </div>
        """

    html_content += """
        <hr>
        <p style="font-size: 0.8em; color: #777;">You are receiving this because you are subscribed to the HOIISP admin mailing list.</p>
    </body>
    </html>
    """

    message = EmailMessage()
    
    smtp_host = await db.get_setting('smtp_host', config.SMTP_HOST)
    smtp_port_str = await db.get_setting('smtp_port', str(config.SMTP_PORT))
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        smtp_port = config.SMTP_PORT
        
    smtp_user = await db.get_setting('smtp_user', config.SMTP_USER)
    smtp_sender = await db.get_setting('smtp_sender', smtp_user)
    smtp_password = await db.get_setting('smtp_password', config.SMTP_PASSWORD)

    message["From"] = smtp_sender
    message["Subject"] = "HOIISP Project Digest"
    message.set_content("Please view this email in an HTML-compatible client.")
    message.add_alternative(html_content, subtype="html")

    # Bcc all subscribers to preserve privacy
    recipients = [s['email'] for s in subscribers]
    message["Bcc"] = ", ".join(recipients)

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            use_tls=True if smtp_port == 465 else False,
            start_tls=True if smtp_port in [587, 2525] else False,
        )
        logger.info(f"✅ EMAIL SUCCESS: Digest email successfully sent to {len(recipients)} recipients via {smtp_host}.")
        
        # Log to digest_log
        db_conn = await db.get_db()
        await db_conn.execute("INSERT INTO digest_log (recipient_count, status) VALUES (?, ?)", (len(recipients), "success"))
        await db_conn.commit()
        await db_conn.close()
        
    except Exception as e:
        logger.error(f"❌ EMAIL FAILED: Failed to send digest email: {e}")
        db_conn = await db.get_db()
        await db_conn.execute("INSERT INTO digest_log (recipient_count, status) VALUES (?, ?)", (len(recipients), f"failed: {str(e)}"))
        await db_conn.commit()
        await db_conn.close()
