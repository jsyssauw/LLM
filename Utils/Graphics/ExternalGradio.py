# imports

import os
import requests
from bs4 import BeautifulSoup
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai
import anthropic
import gradio as gr # oh yeah!
from load_api_keys import load_api_keys
import CompanyBrochure

# load the api keys
load_api_keys(False)

#intiliaze the objects
openai = OpenAI()
claude = anthropic.Anthropic()
google.generativeai.configure()

# Let's wrap a call to GPT-4o-mini in a simple function

def message_gpt(u_prompt,s_message = ""):
    s_message = "You are a helpful assistant"
    messages = [
        {"role": "system", "content": s_message},
        {"role": "user", "content": u_prompt}
      ]
    completion = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages
    )
    return completion.choices[0].message.content

### with gradio you have to return the whole build up as you beld up.
def stream_gpt(u_prompt):
    s_message = "You are a helpful assistant"
    messages = [
        {"role": "system", "content": s_message},
        {"role": "user", "content": u_prompt}
      ]
    stream = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        stream=True
    )
    result = ""
    print(f"Streaming {u_prompt}")
    for chunk in stream:
        result += chunk.choices[0].delta.content or ""
        yield result

def stream_claude(u_prompt):
    s_message = "You are a helpful assistant"
    result = claude.messages.stream(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0.7,
        system=s_message,
        messages=[
            {"role": "user", "content": u_prompt},
        ],
    )
    response = ""
    print(f"Streaming {u_prompt}")
    with result as stream:
        for text in stream.text_stream:
            response += text or ""
            yield response

def stream_model(prompt, model):
    if model=="GPT":
        result = stream_gpt(prompt)
    elif model=="Claude":
        result = stream_claude(prompt)
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
    inputs=[gr.Textbox(label="Your message:", lines=6), gr.Dropdown(["GPT", "Claude"], label="Select model", value="GPT")],
    outputs=[gr.Markdown(label="Response:")],
    flagging_mode="never",
    js=force_dark_mode
    )

view.launch(share=True)