import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import EMAIL_CONFIG

class EmailService:
    @staticmethod
    def send_email(subject: str, body: str):
        """
        Envía un correo electrónico utilizando la configuración definida.
        """
        sender = EMAIL_CONFIG["sender"]
        password = EMAIL_CONFIG["password"]
        recipient = EMAIL_CONFIG["recipient"]
        
        if not password:
            print("⚠️ Email password not set. Skipping email send.")
            return False

        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            if EMAIL_CONFIG["smtp_port"] == 465:
                server = smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"], timeout=10)
            else:
                server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"], timeout=10)
                server.starttls()
            
            server.login(sender, password)
            text = msg.as_string()
            server.sendmail(sender, recipient, text)
            server.quit()
            print(f"✅ Email sent to {recipient}")
            return True
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            # Re-raise exception to show in API response
            raise e
