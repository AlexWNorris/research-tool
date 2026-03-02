import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def send_email(body):
    """
    send email to my university adress from my personal email
    """
    # config
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "alexwnorris@gmail.com"
    app_password = os.environ.get("GMAIL_APP_PASSCODE")
    receiver_email = "an631@exeter.ac.uk"

    # Remove rogue SSLKEYLOGFILE environment variable if it exists
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
        print(f"An unexspected error occured: {e}")
        return False
    
    # ensure connection is always closed
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass
    
    #email sucsefully sent
    return True


