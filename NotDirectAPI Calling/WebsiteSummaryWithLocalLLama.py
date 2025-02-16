import os
import requests                     ## HTTP requests. It simplifies interactions with web APIs, allowing you to send HTTP requests like GET, POST, PUT, DELETE, etc., and handle their responses easily.
from bs4 import BeautifulSoup       ## parses and extracts specific elements or data from html or XML
from IPython.display import Markdown, display
import markdown as mmarkdown
import subprocess
import ollama

OLLAMA_API = "http://localhost:11434/api/chat"
headers = {"Content-Type": "application/json"}
MODEL = "llama3.2"

class Website:

    def __init__(self, url):
        """
        Create this Website object from the given url using the BeautifulSoup library
        """
        self.url = url
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)


def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled: {website.title}"
    user_prompt += "\nThe contents of this website is as follows; \
please provide a short summary of this website in markdown. \
If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

# Define our system prompt - you can experiment with this later, changing the last sentence to 'Respond in markdown in Spanish."
system_prompt = "You are an assistant that analyzes the contents of a website \
and writes cover letter for job applications, ignoring text that might be navigation related. \
Respond in markdown and in dutch."


website_string = input("Provide website url to process:")
ed = Website(website_string)


def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(website)}
    ]

messages_for(ed)

# messages = [
#    {"role": "user", "content": "Describe some of the business applications of Generative AI"},
#    {"role": "system", "content": "Describe some of the business applications of Generative AI"},
#]

payload = {
        "model": MODEL,
        "messages": messages_for(ed),
        "stream": False
    }

## !ollama pull llama3.2       ## this is jupyter
subprocess.run(["ollama", "pull", "llama3.2"], check=True)


response = ollama.chat(model=MODEL, messages=messages_for(ed))
print(response['message']['content'])
