########################################################################################
##
##  jsyssauw
##  v0.1    initial local transcribe using whisper-large-v3-turbo with fixed file
##          support m4a and wav.
##          We chunck up the sound file in bits of xx secs, with a small overlay, and past everything together
##          this is because Whisper only deals with 448 token (444 output tokens)
##          Caution: 
##              1) this might lead to words being repeated when just at the junction, or if very unfortunate a word to be missed
##              2) the punctuation to be wrong.
##        
########################################################################################

import os
from anthropic import Anthropic
import datetime
import re
from datetime import datetime
import requests

DEBUG_MODE = True
OLLAMA_URL = "http://localhost:11434/api/generate"  # Adjust if running Ollama on a different port

# def anthropic_model_response ():

#     anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
#     os.environ['ANTHROPIC_API_KEY'] = anthropic_api_key
#     client = Anthropic()
    
#     # Insert the context into the prompt
#     model_prompt_text = model_prompt(meeting_type, transcript, output_type)  # Call function to get the actual string

#     ## prompt = model_prompt_text.replace("{{EMAIL_BODY}}", email_body).replace("{{SENDER_NAME}}", sender_name)

#     # Send a request to Claude
#     response = client.messages.create(
#         model=model_name,
#         max_tokens=2000,
#         messages=[
#             {"role": "user", "content": prompt}        
#         ]
#     )
#     output = response.content[0].text

#     print(output)
#     return output


def ollama_response (meeting_type, transcript, output_type):
    """Send a request to Ollama for inference using the specified model."""
    model_prompt_text = model_prompt(meeting_type, transcript, output_type)   # Call function to get the prompt template
    print (model_prompt_text)
    ## return model_prompt_text
    """Send a request to Ollama for inference using the specified model."""
    model_name = "llama3.2"
    payload = {
        "model": model_name,
        "prompt": model_prompt_text,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        print(response)
        if response.status_code == 200:
            print(response.json().get("response", ""))
            return response.json().get("response", "")
        else:
            print(response.text)
            return f"Error: {response.text}"
    except Exception as e:
        print(e)
        return str(e)

def model_prompt (meeting_type, transcript_text,output_type ="meeting minutes"):
    now = datetime.now()
    formatted_time = str(now.strftime("%Y-%m-%d %H:%M:%S"))
    setting_the_role = """
    You are Betty, a fantastic PA. Your job is to transform recording transcripts into structured summaries or meeting minutes if the transcript type is a meeting.:
    """

    instruction_pt1 = f"""
    1. Review the following recording. It was a {meeting_type}
    <transcript>
    {transcript_text}
    </transcript>
    The current time is {formatted_time}. 
    """
    if output_type == "meeting minutes":
        
        instruction_pt2 = """
        2. Analyze the transcript of the meeting. 
        - Start by noting the current time of the meeting notes.
        - Summarize the essence from the mail in a short recap. It's OK for this section to be quite long as you thoroughly break down the email.
        - Summarize the discussed topics in bullets, makes sure to cover all.  
        - Conclude with summarizing the discussed action points and who has ownership and the expected delivery date when known.
        """
        instruction_pt3 = """
        Remember:
        - Be objective and focus on the content of the transcript.
        """
    elif output_type == "blog post":
        instruction_pt2 = f"""
        2. Analyze the transcript. 
        Create an detailed {output_type} from the transcript
        Make sure all the context is represented correctly. 
        """
        instruction_pt3 = """
        Remember:
        - Be objective and focus on the content of the transcript.
        """
    else:
        instruction_pt2 = f"""
        2. Analyze the transcript. 
        Create an detailed {output_type} from the transcript
        Make sure all the context is represented correctly. 
        """
        instruction_pt3 = """
        Remember:
        - Be objective and focus on the content of the transcript.
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
def read_file(file_to_read):
    with open(file_to_read, "r", encoding="utf-8") as file:
        content = file.read()
    if DEBUG_MODE:
        print(content)  # Prints the file content as a single string
    return content

def rewrite_file(file_to_read, file_language, file_language_code, new_file_type):
    content = read_file(file_to_read)
    ollama_response(new_file_type, content, new_file_type)

# Test the transcription function
if __name__ == "__main__":
    print("##################################################################################")
    print("## Rewriting of file")
    print("##################################################################################")

    # file_to_read = input("Input name of file in this directory to rewrite: ")
    # file_content = input("What is the file about: ")
    # file_language = input("Input the language of the file: ")
    # file_language_code = input("Audio language code (en/nl/...) - avoid autodetect: ")
    # new_file_type = input("Which type of content do you want: ")
    
    file_to_read = "Building_OpenAI_o1_(20250220013857.txt"
    file_content = "a person explaining a topic"
    file_language = "english"
    file_language_code = "en"
    new_file_type = "a blog post"

    # .strip()
    rewrite_file(file_to_read, file_language, file_language_code, new_file_type, )

    print('Files created. Extraction completed.')