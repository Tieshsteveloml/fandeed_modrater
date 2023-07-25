import smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

subject = "Here is your discord profile in a nutshell"
sender_email = "erpsystem.msg@gmail.com"
#sender_email='louisa@fandeed.com'
#sender_apperance_email='Louisa Lu <louisa@fandeed.com>'
#password='esfxmhsfqvthwamq'
#
#password='F1rocketfuel'
sender_apperance_email='Louisa Lu <hello@fandeed.com>'
#password = 'ERPSYSTEM1'
password='ruzhoztfojgkneja'

receiver_email_list = ["luyilousia@gmail.com"]


def send_simple_email(body, receiver_email, title='New Order34'):
    message = MIMEMultipart()
    message["From"] = sender_apperance_email
    message["To"] = receiver_email
    message["Subject"] = title
    message["Cc"] = 'luyilousia@gmail.com'  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    # Encode file in ASCII characters to send by email
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
        if not receiver_email == 'luyilousia@gmail.com':
            server.sendmail(sender_email, 'luyilousia@gmail.com', text)

def send_internal_email_master(body, receiver_email_list=receiver_email_list):
    for receiver_email in receiver_email_list:
        send_simple_email(body, receiver_email, title='Alert: Users activities')


def send_sys_email(receiver_email, filename, name):
    message = MIMEMultipart()
    message["From"] = sender_apperance_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = 'luyilousia@gmail.com'  # Recommended for mass emails
    message["Cc"] = 'luyilousia@gmail.com'  # Recommended for mass emails

    # Add body to email
    body = "Attached please find your discord profile. Let me know if you have any comments and thoughts. You can reach me by replying All, or luyilousia@gmail.com \n\n Best, \n Louisa"
    body = 'Hi ' + name + "," + "\n\n" + body
    message.attach(MIMEText(body, "plain"))
    with open(filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)
    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )
    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
        server.sendmail(sender_email, 'luyilousia@gmail.com', text)

