#!/usr/bin/env python
# coding: utf-8


# Let's build a useful LLM solution - in a matter of minutes.

# imports

import os
import requests                     ## HTTP requests. It simplifies interactions with web APIs, allowing you to send HTTP requests like GET, POST, PUT, DELETE, etc., and handle their responses easily.
from dotenv import load_dotenv
from bs4 import BeautifulSoup       ## parses and extracts specific elements or data from html or XML
from IPython.display import Markdown, display
from openai import OpenAI
import markdown as mmarkdown

## Connecting to OpenAI
# Load environment variables in a file called .env
load_dotenv(override=True)          ## When override=True, it forces the .env file's variables to overwrite any existing environment variables.
api_key = os.getenv('OPENAI_API_KEY')

# Check the key
if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")

openai = OpenAI()
# To give you a preview -- calling OpenAI with these messages is this easy. Any problems, head over to the Troubleshooting notebook.

message = "Hello, GPT! This is my first ever message to you! Hi!"
response = openai.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":message}])
print(response.choices[0].message.content)


# A class to represent a Webpage
# Some websites need you to use proper headers when fetching them:
headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

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

website_string = input("Provide website url to process:")
type_content = input("What type of content do you want ChatGPT to write: ")
type_objective = input("What purpose do you want to achieve: ")
ed = Website(website_string)

# Models like GPT4o have been trained to receive instructions in a particular way.
# They expect to receive:
# **A system prompt** that tells them what task they are performing and what tone they should use
# **A user prompt** -- the conversation starter that they should reply to

# Define our system prompt - you can experiment with this later, changing the last sentence to 'Respond in markdown in Spanish."
system_prompt = "You are an assistant that analyzes the contents of a website \
and writes " + type_content + " to " + type_objective + ", ignoring text that might be navigation related. \
Respond in markdown and in dutch."

# A function that writes a User Prompt that asks for summaries of websites:

def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled: {website.title}"
#    user_prompt += "\nThe contents of this website is as follows; \
#please provide a short summary of this website in markdown. \
#If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += "\nThe contents of this website is as follows; \
please provide " + type_content + " to " + type_objective + " of this website in markdown. \
If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

# ## Messages
# 
# The API from OpenAI expects to receive messages in a particular structure.
# Many of the other APIs share this structure:
# 
# ```
# [
#     {"role": "system", "content": "system message goes here"},
#     {"role": "user", "content": "user message goes here"}
# ]
# 
# To give you a preview, the next 2 cells make a rather simple call - we won't stretch the might GPT (yet!)
messages = [
    {"role": "system", "content": "You are a snarky assistant"},
    {"role": "user", "content": "What is 2 + 2?"}
]
# To give you a preview -- calling OpenAI with system and user messages:

response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
# print(response.choices[0].message.content)
print("OpenAI is responding correctly.")

# ## And now let's build useful messages for GPT-4o-mini, using a function

# See how this function creates exactly the format above

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(website)}
    ]

messages_for(ed)

# And now: call the OpenAI API. You will get very familiar with this!
def summarize(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model = "gpt-4o-mini",
        messages = messages_for(website)
    )
    return response.choices[0].message.content

summarize(website_string)

# A function to display this nicely in the Jupyter output, using markdown
def display_summary(url):
    summary = summarize(url)
    display(Markdown(summary))
    html_content = mmarkdown.markdown(summary)
    print(summary)

display_summary(website_string)
# Convert Markdown to HTML
