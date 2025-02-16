# coding: utf-8

# BUSINESS CHALLENGE:
# Build a brochure for a company to be used for prospective clients, investors, and potential recruits.
# Inputs: Company name and primary website URL.

#################################################################
# 1. Imports
#################################################################
import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import gradio as gr
from openai import OpenAI
import anthropic
from load_api_keys import load_api_keys

#################################################################
# 2. Initialization, Constants, and Class Definitions
#################################################################
load_api_keys(False)
openai = OpenAI()
claude = anthropic.Anthropic()

# Constants
debug = False
MODEL_GPT = 'gpt-4o-mini'
MODEL_CLAUDE = 'claude-3-haiku-20240307'

# Headers for HTTP requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:
    """Utility class to represent a scraped website."""
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

#################################################################
# 3. Helper Functions
#################################################################

def get_links(url, mtype="brochure"):
    """Retrieve relevant links from the website using GPT."""
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

def get_links_user_prompt(website, mtype="brochure"):
    """Compose user prompt for retrieving relevant links."""
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += f"please decide which of these are relevant web links for a {mtype} about the company, respond with the full https URL in JSON format. \n"
    user_prompt += "Do not include Terms of Service, Privacy, or email links.\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

def get_brochure_user_prompt(company_name, url, mtype="brochure", mtone="formal", llanguage="English"):
    """Compose the user prompt for generating the brochure."""
    user_prompt = f"You are looking at a company called: {company_name}\n"
    user_prompt += f"Here are the contents of its landing page and other relevant pages; use this information to build a short {mtone} {mtype} of the company in markdown and in the {llanguage} language.\n"
    user_prompt += get_all_details(url)
    user_prompt = user_prompt[:5000]  # Truncate to 5,000 characters if necessary
    return user_prompt

def get_all_details(url):
    """Retrieve cleaned-up content and links from the given URL."""
    result = "Landing page:\n"
    result += Website(url).get_contents()
    links = get_links(url)
    for link in links["links"]:
        result += f"\n\n{link['type']}\n"
        result += Website(link["url"]).get_contents()
    return result

#################################################################
# 4. System Prompts
#################################################################

link_system_prompt = f"You are provided with a list of links found on a webpage. \n"
link_system_prompt += "You are able to decide which of the links would be most relevant to include in a {marketing_type} about the company, \n"
link_system_prompt += "such as links to an About page, or a Company page, or Careers/Jobs pages.\n"
link_system_prompt += "Respond in JSON as in this example:\n"
link_system_prompt += """
{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

system_prompt = f"You are an assistant that analyzes the contents of several relevant pages from a company website \n"
system_prompt += f"and creates a short {marketing_tone} {marketing_type} about the company for {target_audience}. Respond in markdown. \n"
system_prompt += f"Write the content in the language {language}. \n"
system_prompt += f"Include relevant details for #target_audience# where applicable of company culture, customers, and careers/jobs if you have the information."

#################################################################
# 5. Streaming Functions
#################################################################

def stream_gpt(company_name, url, marketing_type, target_audience, marketing_tone, language):
    """Stream GPT response."""
    stream = openai.chat.completions.create(
        model=MODEL_GPT,
        messages=[
            {"role": "system", "content": system_prompt.replace("#target_audience#", target_audience)},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url, marketing_type, marketing_tone, language)}
        ],
        stream=True
    )
    result = ""
    print("Streaming Brochure with GPT")
    for chunk in stream:
        result += chunk.choices[0].delta.content or ""
        yield result

def stream_claude(company_name, url, marketing_type, target_audience, marketing_tone, language):
    """Stream Claude response."""
    result = claude.messages.stream(
        model=MODEL_CLAUDE,
        max_tokens=2000,
        temperature=0.7,
        system=system_prompt.replace("#target_audience#", target_audience),
        messages=[
            {"role": "user", "content": get_brochure_user_prompt(company_name, url, marketing_type, marketing_tone, language)},
        ],
    )
    response = ""
    print("Streaming Brochure with Claude")
    with result as stream:
        for text in stream.text_stream:
            response += text or ""
            yield response

def stream_model(company_name, website_url, marketing_type, target_audience, marketing_tone, language, mmodel):
    """Stream response based on selected model."""
    if mmodel == "GPT":
        print("Streaming with GPT")
        result = stream_gpt(company_name, website_url, marketing_type, target_audience, marketing_tone, language)
    elif mmodel == "Claude":
        print("Streaming with Claude")
        result = stream_claude(company_name, website_url, marketing_type, target_audience, marketing_tone, language)
    else:
        raise ValueError("Unknown model")
    yield from result

#################################################################
# 6. Gradio Interface
#################################################################

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
    inputs=[
        gr.Textbox(label="Company Name:"),
        gr.Textbox(label="Company URL:"),
        gr.Textbox(label="Marketing Type:"),
        gr.Textbox(label="Target Audience:"),
        gr.Textbox(label="Marketing Tone:"),
        gr.Dropdown(["English", "Dutch", "French", "West-Vlaams"], label="Select Language", value="English"),
        gr.Dropdown(["GPT", "Claude"], label="Select Model", value="GPT")
    ],
    outputs=[gr.Markdown(label="Response:")],
    flagging_mode="never",
    js=force_dark_mode
)

view.launch(share=True)
