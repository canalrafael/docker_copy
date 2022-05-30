#!/usr/bin/python3
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

def split_receivers(to_addr):
    to_addrs = []

    if to_addr.find(',') > 0:        
        to_addrs = to_addr.split(',')
    else:
        to_addrs.append(to_addr)

    return to_addrs

def email(from_addr, from_pw, to_addrs, subject, message, attachments):
    if len(from_addr) == 0:
        from_addr = "information.iase.ia@gmail.com"
        from_pw = "1473384656695769"

    subject = 'IASE - '+subject

    content_message = "Hi,\n\nThis is an automatic email sent from IASE. \n\n"
    content_message += message
    content_message += "\n\n[do not reply]"

    problems_send = False

    for to_addr in split_receivers(to_addrs):
        #EMAIL
        if len(to_addr.strip()) == 0:
            continue

        msg = MIMEMultipart(subject)    
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = subject

        body = MIMEText(content_message, 'plain')
        msg.attach(body)

        if len(attachments) > 0:
            for type_attached, filename in attachments:
                if type_attached == "image":
                    with open(filename, 'rb') as fp:
                        img_attchment = MIMEImage(fp.read(), name=filename)
                        img_attchment.add_header('Content-Disposition', 'attachment; filename="%s"' % filename)
                        msg.attach(img_attchment)
                else:
                    with open(filename, 'r') as f:
                        txt_attchment = MIMEText(f.read())
                        txt_attchment.add_header('Content-Disposition', 'attachment', filename=filename)       
                        msg.attach(txt_attchment)

        send = False

        for _ in range(0, 5):
            if send: break
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.ehlo()
                server.login(from_addr, from_pw)
                server.send_message(msg, from_addr=from_addr, to_addrs=to_addr)
                server.close()
                send = True
                print(f"Email sent to {to_addr}!")
            except Exception as e:
                server.close()
                time.sleep(1)
                print(f"{_}/5 |{to_addr}| - Something went wrong... "+ str(e))

        if not send:
            print(f"|{to_addr}| Something went wrong... ")
            problems_send = True

    return True if not problems_send else False
