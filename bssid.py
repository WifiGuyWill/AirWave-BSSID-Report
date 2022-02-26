#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#(c) 2022 Will Smith - WILL@WIFI-GUYS.COM

"""Connect to Airwave REST API to get AP BSSID, Create PDF then Send as Email Attachment"""

# Debian packages: python3-requests, python3-lxml
import xml.etree.ElementTree as ET # libxml2 and libxslt
import requests                    # HTTP requests
from fpdf import FPDF              # Create PDF
import pandas as pd                # Create CSV
import urllib3                     # Suppress SSL Errors
import smtplib, ssl                # Send Email

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Set csv or pdf
list_type = 'pdf'

# Email Parameters
gmail_user = 'eamil@gmail.com'
gmail_password = 'gmail_pw'
receiver_email_address = "email@email.com"

# Login/password for Airwave (read-only account)
LOGIN = 'airwave_admin'
PASSWD = 'airwave_PW!'

# URL for REST API
LOGIN_URL = 'https://airwave.your-company.com/LOGIN'
AP_BSSID_URL = 'https://airwave.your-company.com/api/ap_bssid_list.xml'


# HTTP headers for each HTTP request
HEADERS = {
    'Content-Type' : 'application/x-www-form-urlencoded',
    'Cache-Control' : 'no-cache'
}

# Misc
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #Disable SSL Warnings

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

# AirWave Authentication
def open_session():
    """Open HTTPS session with login"""

    ampsession = requests.Session()
    data = 'credential_0={0}&credential_1={1}&destination=/&login=Log In'.format(LOGIN, PASSWD)
    loginamp = ampsession.post(LOGIN_URL, headers=HEADERS, data=data, verify=False)
    return {'session' : ampsession, 'login' : loginamp}

# Gather AP BSSID Info
def get_ap_bssid(session):
    """Get XML data and returns a dictionnaries list"""
    output = session.get(AP_BSSID_URL, headers=HEADERS, verify=False)
    ap_bssid_output = output.content
     # Parse XML for desired attributes and build a dictionnaries list
    xml_data = ET.fromstring(ap_bssid_output)
    aps = xml_data.findall("ap")
    for ap in aps:
        for radio in ap.findall("radio"):
            bunch_of_bssids = [b.attrib.get("mac", "ERROR") for b in radio.findall("bssid")]
            bssd_str = ','.join(bunch_of_bssids)
            bssid_data = ((f"{ap.attrib['name']},{bssd_str}"))
            with open('bssid.txt', 'a') as f:
                f.write(bssid_data + '\n')

# Create PDF from Dict
class PDF(FPDF):
    def header(self):
#        self.image('aruba_logo.png', 170, 275, 33) #bottom right
        self.image('aruba_logo.png', 170, 10, 33) #top right
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Aruba AP BSSID List', 0, 1, 'C')

def create_pdf():
    with open('bssid.txt', 'r') as data:
        plaintext = data.read()
    plaintext = plaintext.replace(',', ' ')
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 12)
    pdf.multi_cell(200, 8, txt=plaintext, align = 'L')
    pdf.output("bssid.pdf")

# Create CSV Files
def create_csv():
    df = pd.read_csv('bssid.txt',sep=';')
    df.to_csv('bssid.csv', index=None)
#    print(df.to_csv(index=None))

# Removes data from temp file
def cleanup():
    open("bssid.txt", "w").close()

# Send Email (Gmail)
def send_email():
    try:
        subject = "Aruba BSSID List"
        body = "Please see attachment."
        sender_email = gmail_user 
        receiver_email = receiver_email_address
        password = gmail_password
        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message["Bcc"] = receiver_email  # Send copy to self

        # Add body to email
        message.attach(MIMEText(body, "plain"))
        if list_type == "pdf":
            filename = "bssid.pdf"
        else:
            filename = "bssid.csv"

        # Open PDF file in binary mode
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
        # print("Email Sent")
    except:
        print("Problem Sending Email")

# Mission Control
def main():
    session = open_session()
    get_ap_bssid(session['session'])
    if list_type == "pdf":
        create_pdf()
    else:    
        create_csv()
    send_email()
    cleanup()

main()
