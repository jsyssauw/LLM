# imports
import os
import requests
from bs4 import BeautifulSoup
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr # oh yeah!
# from load_api_keys import load_api_keys

# load the api keys d
# load_api_keys(False)

openai_api_key = os.getenv('OPENAI_API_KEY')
  
if not openai_api_key:
    print("OpenAI API Key not set")

#intiliaze the objects
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

    # def get_contents(self):
    #     return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"

def get_article_content(website_url):
    website_object = Website(website_url)
    return website_object.text

def message_gpt(website_content, content_type, language):
    system_prompt = "You are an advanced summarization assistant. Your goal is to read and understand web articles or blog posts and generate summaries that follow this structure:\
                        1. **Headline/Title**: Provide a concise title for the summary.\
                        2. **Introduction/Overview**: Briefly introduce the article's topic, context, and purpose.\
                        3. **Key Points/Takeaways**: Highlight the most important points in bullet points or short paragraphs.\
                        4. **Supporting Details (Optional)**: Add examples or context for critical points, if necessary. \
                        5. **Implications/Conclusion**: Summarize the broader implications or next steps. \
                        6. **Call to Action/Recommendations (Optional)**: Suggest actions or further steps based on the content.\
                    Be concise, neutral in tone, and ensure clarity. Adapt summaries based on user requests for focus or level of detail."
    user_prompt = f"Summarize the following article/blog post {website_content}'. Follow the structure provided in the system instructions. If possible, include actionable insights or recommendations. Optimize to be used as {content_type}. Write the summary in the {language}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
      ]
    
    return messages

### with gradio you have to return the whole build up as you beld up.
def stream_gpt(url, content_type, language):
   
    messages = message_gpt(get_article_content(url),content_type, language)

    stream = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        stream=True
    )
    result = ""
    for chunk in stream:
        result += chunk.choices[0].delta.content or ""
        yield result


force_dark_mode = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""
# view = gr.Interface(
#     fn=stream_gpt,
#     inputs=[
#         gr.Textbox(label="The url to article: ", lines=1), 
#         gr.Dropdown(["Facebook Post", "LinkedIN post","Article Summary"], label="Select Content Type", value="Article Summary"), 
#         gr.Textbox(label="Language of summary: ", lines=1, value= "English")
#         ],
#     outputs=[gr.Markdown(label="Response:")],
#     flagging_mode="never",
#     js=force_dark_mode
#     )
## view.launch(share=False)

with gr.Blocks(js=force_dark_mode, title="Article Summarizer") as ui:
    gr.Markdown("# Article Summarizer")  # Page title as Markdown
    # Arrange fields in a column
    with gr.Column():
        url = gr.Textbox(label="Url to Article: ", lines=1)
        content_type = gr.Dropdown(["Facebook Post", "LinkedIN post", "Article Summary"], 
                                   label="Select Content Type", value="Article Summary")
        language = gr.Textbox(label="Language of summary: ", lines=1, value="English")
        summary = gr.Markdown(label="Summary:")

    # Add a row for the button
    with gr.Row():
        convert = gr.Button("Summarize")
    # Add a disclaimer at the bottom of the page
    gr.Markdown(
        """
        **Disclaimer:**  
        The summary is automatically generated and may not always be accurate. 
        Please validate the content before using it for any critical purposes.
        """,
        elem_id="disclaimer"
    )
    # Link the button to the function
    convert.click(stream_gpt, inputs=[url, content_type, language], outputs=[summary])

# Launch Gradio with the UI
ui.launch(inbrowser=True)



