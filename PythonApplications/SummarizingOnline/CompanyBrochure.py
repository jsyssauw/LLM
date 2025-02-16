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

#################################################################
# 2. Initialize, constants and class definitions
#################################################################
debug = False
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

if api_key and api_key.startswith('sk-proj-') and len(api_key)>10:
    if debug:
        print("API key looks good so far")
else:
    print("There might be a problem with the OpenAI API key. Please contact your provider!")
MODEL = 'gpt-4o-mini'
openai = OpenAI()

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
        model=MODEL,
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

company_name = input("Provide the company name: ")
website_url = input("Provide full url to website: ")
marketing_tone = input("Which tone would you like to have the text written in: ")
marketing_type = input("What type of material do you want: ")
target_audience = input("Who is the content for?: ")
language = input("What language do you want this in?")

website_object = Website(website_url)
if debug:
    print("\n\nAll links found on website:")
    for link in website_object.links:
        print(link)
# ## First step: Have GPT-4o-mini figure out which links are relevant
# ### Use a call to gpt-4o-mini to read the links on a webpage, and respond in structured JSON.  
# It should decide which links are relevant, and replace relative links such as "/about" with "https://company.com/about".  
# We will use "one shot prompting" in which we provide an example of how it should respond in the prompt.

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

if debug: 
    print("\n\nThe link system prompt: \n" + link_system_prompt)
    print("\n\nThe link user prompt: \n" + get_links_user_prompt(website_object,marketing_type))

###############################################################
# ## Second step: make the brochure!
# Assemble all the details into another prompt to GPT4-o
###############################################################

system_prompt = f"You are an assistant that analyzes the contents of several relevant pages from a company website \
and creates a short {marketing_tone} {marketing_type} about the company for {target_audience}. Respond in markdown.\
Write the content in the language {language}.\
Include relevant details for {target_audience} where applicable of company culture, customers and careers/jobs if you have the information."

# Or uncomment the lines below for a more humorous brochure - this demonstrates how easy it is to incorporate 'tone':

# system_prompt = "You are an assistant that analyzes the contents of several relevant pages from a company website \
# and creates a short humorous, entertaining, jokey brochure about the company for prospective customers, investors and recruits. Respond in markdown.\
# Include details of company culture, customers and careers/jobs if you have the information."

if debug:
    print("\n\nThe system prompt: \n" + system_prompt)
    print("\n\nThe user prompt: \n" + get_brochure_user_prompt(company_name, website_url,marketing_type, marketing_tone, language))


if not debug: 
    def create_brochure(company_name, url, marketing_type, marketing_tone, language):
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": get_brochure_user_prompt(company_name, url, marketing_type, marketing_tone, language)}
            ],
        )
        result = response.choices[0].message.content
        ##display(Markdown(result))
        print(result)

    create_brochure(company_name,website_url,marketing_type, marketing_tone, language)

# ## Finally - a minor improvement
# With a small adjustment, we can change this so that the results stream back from OpenAI,
# with the familiar typewriter animation

# def stream_brochure(company_name, url, marketing_type):
#     stream = openai.chat.completions.create(
#         model=MODEL,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": get_brochure_user_prompt(company_name, url, marketing_type)}
#           ],
#         stream=True         ## STREAMING!
#     )
    
#     response = ""
#     display_handle = display(Markdown(""), display_id=True)
#     for chunk in stream:
#         response += chunk.choices[0].delta.content or ''
#         response = response.replace("```","").replace("markdown", "")
#         update_display(Markdown(response), display_id=display_handle.display_id)


# stream_brochure(company_name,website_url, marketing_type)


# <table style="margin: 0; text-align: left;">
#     <tr>
#         <td style="width: 150px; height: 150px; vertical-align: middle;">
#             <img src="../business.jpg" width="150" height="150" style="display: block;" />
#         </td>
#         <td>
#             <h2 style="color:#181;">Business applications</h2>
#             <span style="color:#181;">In this exercise we extended the Day 1 code to make multiple LLM calls, and generate a document.
# 
# This is perhaps the first example of Agentic AI design patterns, as we combined multiple calls to LLMs. This will feature more in Week 2, and then we will return to Agentic AI in a big way in Week 8 when we build a fully autonomous Agent solution.
# 
# Generating content in this way is one of the very most common Use Cases. As with summarization, this can be applied to any business vertical. Write marketing content, generate a product tutorial from a spec, create personalized email content, and so much more. Explore how you can apply content generation to your business, and try making yourself a proof-of-concept prototype.</span>
#         </td>
#     </tr>
# </table>

# <table style="margin: 0; text-align: left;">
#     <tr>
#         <td style="width: 150px; height: 150px; vertical-align: middle;">
#             <img src="../important.jpg" width="150" height="150" style="display: block;" />
#         </td>
#         <td>
#             <h2 style="color:#900;">Before you move to Week 2 (which is tons of fun)</h2>
#             <span style="color:#900;">Please see the week1 EXERCISE notebook for your challenge for the end of week 1. This will give you some essential practice working with Frontier APIs, and prepare you well for Week 2.</span>
#         </td>
#     </tr>
# </table>

# <table style="margin: 0; text-align: left;">
#     <tr>
#         <td style="width: 150px; height: 150px; vertical-align: middle;">
#             <img src="../resources.jpg" width="150" height="150" style="display: block;" />
#         </td>
#         <td>
#             <h2 style="color:#f71;">A reminder on 2 useful resources</h2>
#             <span style="color:#f71;">1. The resources for the course are available <a href="https://edwarddonner.com/2024/11/13/llm-engineering-resources/">here.</a><br/>
#             2. I'm on LinkedIn <a href="https://www.linkedin.com/in/eddonner/">here</a> and I love connecting with people taking the course!
#             </span>
#         </td>
#     </tr>
# </table>

# <table style="margin: 0; text-align: left;">
#     <tr>
#         <td style="width: 150px; height: 150px; vertical-align: middle;">
#             <img src="../thankyou.jpg" width="150" height="150" style="display: block;" />
#         </td>
#         <td>
#             <h2 style="color:#090;">Finally! I have a special request for you</h2>
#             <span style="color:#090;">
#                 My editor tells me that it makes a MASSIVE difference when students rate this course on Udemy - it's one of the main ways that Udemy decides whether to show it to others. If you're able to take a minute to rate this, I'd be so very grateful! And regardless - always please reach out to me at ed@edwarddonner.com if I can help at any point.
#             </span>
#         </td>
#     </tr>
# </table>
