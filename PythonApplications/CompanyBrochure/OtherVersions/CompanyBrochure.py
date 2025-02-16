# coding: utf-8

# ### BUSINESS CHALLENGE:
# product that builds a Brochure for a company to be used for prospective clients, investors and potential recruits.
# - provided a company name and their primary website.
# 

#################################################################
# 1. imports
#################################################################

import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from IPython.display import Markdown, display, update_display
from openai import OpenAI
import anthropic
import gradio as gr # oh yeah!
from load_api_keys import load_api_keys

#################################################################
# 2. Initialize, constants and class definitions
#################################################################
load_api_keys(False)
openai = OpenAI()
claude = anthropic.Anthropic()
debug = False
MODEL_GPT ='gpt-4o-mini'
MODEL_claude ='claude-3-haiku-20240307'

# A class to represent a Webpage
# Some websites need you to use proper headers when fetching them:
headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:              ## A utility class to represent a Website that we have scraped, now with links
    def __init__(self, url):
        self.url = url
        response = requests.get(url, headers=headers)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""
        links = [link.get('href') for link in soup.find_all('a')]
        self.links = [link for link in links if link]

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"

## this functions gets the cleaned up page content, pases it to GPT with the build system & user prompt and retrieves the links in a json format
def get_links(url, mtype = "brochure"):
    website = Website(url)
    response = openai.chat.completions.create(
        model=MODEL_GPT,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(website, mtype)}
      ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    return json.loads(result)

# this function composes the user_prompt for getting the relevant links based upon the website object that is passed on. (was on row 112)
def get_links_user_prompt(website, mtype="brochure"):
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += f"please decide which of these are relevant web links for a {mtype} about the company, respond with the full https URL in JSON format. \
Do not include Terms of Service, Privacy, email links.\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

# creating the user prompt to compose the brochure for the specified company-name & url, building the user prompt
def get_brochure_user_prompt(company_name, url, mtype="brochure", mtone="formal", llanguage="English"):
    user_prompt = f"You are looking at a company called: {company_name}\n"
    user_prompt += f"Here are the contents of its landing page and other relevant pages; use this information to build a short {mtone} {mtype} of the company in markdown and in the {llanguage} language.\n"
    user_prompt += get_all_details(url)
    user_prompt = user_prompt[:5_000] # Truncate if more than 5,000 characters
    return user_prompt

# for the specified url, we are building the response, containing 
#  1. the cleaned up content for the specified url
#  2. the cleaned up content for the pages of the found (relevant) urls
def get_all_details(url):
    result = "Landing page:\n"
    result += Website(url).get_contents()
    links = get_links(url)
    ## print("\n\nFound links:\n", links)
    for link in links["links"]:
        result += f"\n\n{link['type']}\n"
        result += Website(link["url"]).get_contents()
    return result

#################################################################
# 3. get input & validate the links
#################################################################

# company_name = input("Provide the company name: ")
# website_url = input("Provide full url to website: ")
# marketing_tone = input("Which tone would you like to have the text written in: ")
# marketing_type = input("What type of material do you want: ")
# target_audience = input("Who is the content for: ")
# language = input("What language do you want this in: ")
company_name = ""
website_url = ""
marketing_tone = ""
marketing_type = ""
target_audience = "Investors, Customers and Prospects"
language = ""

#################################################################
# 4. prompt engineering - Links
#################################################################

link_system_prompt = f"You are provided with a list of links found on a webpage. \
You are able to decide which of the links would be most relevant to include in a {marketing_type} about the company, \
such as links to an About page, or a Company page, or Careers/Jobs pages.\n"
link_system_prompt += "You should respond in JSON as in this example:"
link_system_prompt += """
{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page": "url": "https://another.full.url/careers"}
    ]
}
"""
###############################################################
# ## Second step: make the brochure!
# Assemble all the details into another prompt to GPT4-o
###############################################################

system_prompt = f"You are an assistant that analyzes the contents of several relevant pages from a company website \
and creates a short {marketing_tone} {marketing_type} about the company for {target_audience}. Respond in markdown.\
Write the content in the language {language}.\
Include relevant details for #target_audience# where applicable of company culture, customers and careers/jobs if you have the information."

# Or uncomment the lines below for a more humorous brochure - this demonstrates how easy it is to incorporate 'tone':

# system_prompt = "You are an assistant that analyzes the contents of several relevant pages from a company website \
# and creates a short humorous, entertaining, jokey brochure about the company for prospective customers, investors and recruits. Respond in markdown.\
# Include details of company culture, customers and careers/jobs if you have the information."


def stream_gpt(company_name, url, marketing_type, target_audience, marketing_tone, language):
    stream = openai.chat.completions.create(
        model=MODEL_GPT,
        messages=[
            {"role": "system", "content": system_prompt.replace("#target_audience#", target_audience)},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url, marketing_type, marketing_tone, language)}
        ],
        stream=True
    )
    
    result = ""
    print(f"Streaming Brochure with GPT")
    for chunk in stream:
        result += chunk.choices[0].delta.content or ""
        yield result

def stream_claude(company_name, url, marketing_type, target_audience, marketing_tone, language):
    result = claude.messages.stream(
        model=MODEL_claude,
        max_tokens=2000,
        temperature=0.7,
        system=system_prompt.replace("#target_audience#", target_audience),
        messages=[
            {"role": "user", "content": get_brochure_user_prompt(company_name, url, marketing_type, marketing_tone, language)},
        ],
    )
    response = ""
    print(f"Streaming Brochure with Claude")
    with result as stream:
        for text in stream.text_stream:
            response += text or ""
            yield response


def stream_model(company_name,website_url,marketing_type, target_audience, marketing_tone, language, mmodel):
    if mmodel=="GPT":
        print("Streaming with GPT")
        result = stream_gpt(company_name,website_url,marketing_type,target_audience,  marketing_tone, language)
    elif mmodel=="Claude":
        print("Streaming with Claude")
        result = stream_claude(company_name,website_url,marketing_type, target_audience, marketing_tone, language)
    else:
        raise ValueError("Unknown model")
    yield from result


force_dark_mode = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""

view = gr.Interface(
    fn=stream_model,
    inputs=[gr.Textbox(label="Company Name:"), 
            gr.Textbox(label="Company URL:"), 
            gr.Textbox(label="Marketing Type:"), 
            gr.Textbox(label="Target Audience:"), 
            gr.Textbox(label="Marketing Tone:"),
            gr.Dropdown(["English", "Dutch", "French","West-Vlaams"], label="Select Language", value="English"),
            gr.Dropdown(["GPT", "Claude"], label="Select model", value="GPT")],
    outputs=[gr.Markdown(label="Response:")],
    flagging_mode="never",
    js=force_dark_mode
    )

view.launch(share=True)
#share=False