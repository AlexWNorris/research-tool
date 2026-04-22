"""
Module responsible for dispatching collected footprint surveys and metrics 
to an external inbox via SMTP mail relay.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def send_email(body):
    """
    Send an email from personal address relaying footprint data to the university target address.
    
    Args:
        body (str): The body text payload (usually encrypted JSON string).
        
    Returns:
        bool: True if successful, False otherwise.
    """
    # config
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "alexwnorris@gmail.com"
    app_password = os.environ.get("GMAIL_APP_PASSCODE")
    receiver_email = "an631@exeter.ac.uk"

    # Remove rogue SSLKEYLOGFILE environment variable if it exists, as this causes the system to fail \_o_/
    if "SSLKEYLOGFILE" in os.environ:
        del os.environ["SSLKEYLOGFILE"]

    # create email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "autoME"

    msg_body = body
    msg.attach(MIMEText(msg_body,"plain"))

    # connect to smtp server and attempt send
    server = None
    try:
        server = smtplib.SMTP(smtp_server,smtp_port)
        
        server.starttls()

        server.login(sender_email,app_password)

        text = msg.as_string()

        server.sendmail(sender_email,receiver_email,text)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    
    # ensure connection is always closed
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass
    
    # email successfully sent
    return True


