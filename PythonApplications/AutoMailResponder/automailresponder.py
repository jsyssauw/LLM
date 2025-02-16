import imaplib
import email
from email.header import decode_header
import datetime
import requests
import json
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from anthropic import Anthropic
import sys

OLLAMA_URL = "http://localhost:11434/api/generate"  # Adjust if running Ollama on a different port
DEBUG_MODE = False
# This script connects to your email inbox, finds messages
# then sends the content to an Ollama model to generate a response.

##############################
# Step 1: Email retrieval
##############################

# def fetch_emails_from_ann(username: str, password: str, imap_server: str = 'imap.gmail.com', search_email: str = 'ann.neuville@syssauw.com'):
def fetch_emails_from(username: str, password: str, imap_server: str = 'imap.stackmail.com', search_email: str =''):
    """Fetch all emails from the specified sender within the last 24 hours."""
    
    # Connect to the server and log in
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(username, password)
    mail.select("inbox")

    # Calculate the date for the last 24 hours
    date_since = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%d-%b-%Y")

    # Construct the search query
    # Search by FROM address and the SINCE date
    ## status, data = mail.search(None, f'(FROM "{search_email}" SINCE "{date_since}")')
    status, data = mail.search(None,"ALL")
    emails = []
    if status == 'OK':
        # data[0] is a space separated string of email IDs
        email_ids = data[0].split()
        for eid in email_ids:
            res, msg_data = mail.fetch(eid, '(RFC822)')
            if res == 'OK' and msg_data and isinstance(msg_data[0], tuple):  # CHANGED: ensure msg_data[0] is valid
                msg = email.message_from_bytes(msg_data[0][1])
                # emails.append(msg)
                emails.append((eid, msg))

    mail.close()
    mail.logout()
    return emails

##############################
# Step 2: Send to Ollama Llama 3.2
##############################

def ollama_response(sender_name, email_body, model_name):
    """Send a request to Ollama for inference using the specified model."""
    model_prompt_text = model_prompt()   # Call function to get the prompt template
    
    # Convert bytes to string if necessary
    sender_name = sender_name.decode('utf-8') if isinstance(sender_name, bytes) else sender_name  # CHANGED
    email_body = email_body.decode('utf-8') if isinstance(email_body, bytes) else email_body       # CHANGED
    
    prompt = model_prompt_text.replace("{{EMAIL_BODY}}", email_body).replace("{{SENDER_NAME}}", sender_name)

    """Send a request to Ollama for inference using the specified model."""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        if response.status_code == 200:
            print(response.json().get("response", ""))
            return response.json().get("response", "")
        else:
            return f"Error: {response.text}"
    except Exception as e:
        return str(e)

##############################
# Step 2b: Build prompt for Anthropic
##############################

def model_prompt ():
    setting_the_role = """
    You are Betty, an automated, multi-lingual AI assistant for Jan Syssauw, specialized in analyzing incoming professional emails and answering emails on behalf of Jan Syssauw. 
    Jan Syssauw lives in Merelbeke, Oost Vlaanderen, Belgium. 
    Your task is to analyze what the send of the emails wants and to craft a professional answer and response.
    You always answer in the language of the email itself.
    Please follow these instructions carefully:
    """

    instruction_pt1 = """
    1. Review the following email:
    <email>
    {{EMAIL_BODY}}
    </email>
    """

    instruction_pt2 = """
    2. Analyze the mail using the following steps. 
    - Summarize the essence from the mail in a short recap. It's OK for this section to be quite long as you thoroughly break down the email.
    - Any requests that have a local aspect and the location is not specified can be assumed to be in the home location of Jan Syssauw.  
    - Any date and time related questions should be date and time specific, if the date or time information is not specified, ask for it.
    """

    instruction_pt3 = """
    3. Based on your analysis, generate an answer to send the sender of the email.
    Use the following structure
    1. greet the user, with his/her name {{SENDER_NAME}}
    2. say that this is automated response from Betty, Jan's AI assistant (this is you)
    3. recap what the sender of the email said or asked for
    4. formulate your answer and make suggestions.

    Remember:
    - Be objective and focus on the email sender question.
    """
    
    if not DEBUG_MODE:
        instruction_pt3 += """
        IMPORTANT: You only return the actual email response, not the reasoning."""
    
    final_prompt = f"""
        {setting_the_role}
        {instruction_pt1}
        {instruction_pt2}
        {instruction_pt3}
        """
    return final_prompt

def model_response (sender_name, email_body, model_name):

    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    os.environ['ANTHROPIC_API_KEY'] = anthropic_api_key
    client = Anthropic()
    
    # Insert the context into the prompt
    model_prompt_text = model_prompt()  # Call function to get the actual string

    # Convert bytes to string if necessary
    email_body = email_body.decode('utf-8') if isinstance(email_body, bytes) else email_body
    sender_name = sender_name.decode('utf-8') if isinstance(sender_name, bytes) else sender_name

    prompt = model_prompt_text.replace("{{EMAIL_BODY}}", email_body).replace("{{SENDER_NAME}}", sender_name)

    # Send a request to Claude
    response = client.messages.create(
        model=model_name,
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}        
        ]
    )
    output = response.content[0].text

    print(output)
    return output


##############################
# Step 3: Reply to sender
##############################

def reply_to_sender(smtp_server, smtp_port, username, password, original_msg, reply_body):
    """Reply to the sender of the original_msg with the reply_body text."""
    # Create a MIMEMultipart email
    reply = MIMEMultipart()

    # Extract original sender
    from_header = original_msg["From"]
    subject_raw = original_msg["Subject"]
    
    if subject_raw is None:
        subject_raw = "(No Subject)"  # handle None subject

    subject, encoding = decode_header(subject_raw)[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else 'utf-8')

    # If you'd like to prefix with 'Re:', ensure it doesn't already have one.
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    # Setup the headers
    reply["Subject"] = subject
    reply["From"] = username
    reply["To"] = from_header

    # Add the body text
    body = reply_body
    reply.attach(MIMEText(body, "plain"))

    # Send the email
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(username, password)
        server.sendmail(username, from_header, reply.as_string())

##############################
# Step 4: Main
##############################
def main():
    
    # SMTP server and port for stackmail
    smtp_server = "mail.stackmail.com"  
    smtp_port = 465  # SSL port typically
    
    # Provide your email creds (replace with environment variables in practice)
    username = "test@syssauw.com"
    load_dotenv()
    password = os.getenv('TESTSYSSAUW_PWD')
    
    try:
        parameter = sys.argv[1].replace(" ", "").lower() 
    except Exception:
        parameter = "somethingelse"

    if parameter == "claude":
        model="claude-3-5-sonnet-20241022"
    else:
        model = "llama3.2"

    print(parameter, model)

    # Fetch all emails (for demonstration) from inbox
    emails = fetch_emails_from(username, password)

    for eid, msg in emails:
        # decode subject
        subject_raw = msg.get("Subject")
        if subject_raw is None:
            subject_raw = "(No Subject)"  # Default value if no subject exists

        subject, encoding = decode_header(subject_raw)[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')

        # parse the body
        body_text = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body_text = part.get_payload(decode=True).decode('utf-8', errors='replace')
        else:
            body_text = msg.get_payload(decode=True).decode('utf-8', errors='replace')

        # Build prompt
        if parameter == "claude":
            answer = model_response(eid, body_text, model)
        else:
            prompt = f"Subject: {subject}\nBody: {body_text}\n\nAnswer:"
            answer= ollama_response(eid, body_text, model)
##          answer = generate_response(model, prompt)
        if DEBUG_MODE:
            print("\nEmail ID:", eid)
            print("Subject:", subject)
            print("Body:", body_text)
            print("\nModel Answer:\n", answer)
            print("-------------------------------------------------------\n")

        ## Reply with the answer
        reply_to_sender(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=username,
            password=password,
            original_msg=msg,
            reply_body=answer
        )
        # break


if __name__ == "__main__":
    main()
