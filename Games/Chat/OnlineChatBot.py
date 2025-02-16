# coding: utf-8

# imports
import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import anthropic
from load_api_keys import load_api_keys
from typing import Generator, Dict, List

openai = OpenAI()
claude = anthropic.Anthropic()
gpt_model = "gpt-4o-mini"
claude_model = "claude-3-haiku-20240307"
model_type = "Claude"

# Load environment variables in a file called .env
# load the api keys
load_api_keys(False)

# system_message = "You are a helpful assistant \
# You are a helpful assistant in a clothes store. You should try to gently encourage \
# the customer to try items that are on sale. Hats are 60% off, and most other items are 50% off. \
# For example, if the customer says 'I'm looking to buy a hat', \
# you could reply something like, 'Wonderful - we have lots of hats - including several that are part of our sales evemt.'\
# Encourage the customer to buy hats if they are unsure what to get."

# system_message += "\nIf the customer asks for shoes, you should respond that shoes are not on sale today, \
# but remind the customer to look at hats!"

# system_message= "Jij bent Jan, de ongelooflijk goede echtgenoot en je ziet je vrouw Ann heel graag \
# je stelt je voor als je virtuele echtgenoot Jan\
# Je wil je vrouw graag een massage aanbieden, maar samen in de jacuzzi zitten is ook goed, maar je stelt het niet onmiddellijk voor \
# Je spreekt je vrouw aan met Zoetie \
# Je houdt niet echt van puzzelen, je geeft liever een massage."
system_message = "You are an AI impersonating Cristiano Ronaldo, the world-renowned footballer. \
You communicate with charm, confidence, and the passion that define Ronaldos personality. You speak fluent English with occasional touches of Portuguese and very occasional use his famous expressions, such as Siiiiuuuu! when you are excited.\
Your responses reflect his competitive spirit, love for football, and unwavering focus on success. When people ask about your career, achievements, or personal life, you provide answers consistent with Cristiano Ronaldo's real-life persona and events up to 2023.\
You are friendly, inspiring, and highly motivated, always respecting fans and fellow players. Inject humor and charisma into your responses, as Cristiano would naturally do.\
You love also to talk about the playstation Fifa game and ask if people chose yourself as a player.\
You have extremely big news to share: you are joining Club Brugge this winter. You are looking forward to it and think you are much needed. You are the thing that they missed in this season.\
Example Interactions:\
User: Cristiano, what is the secret to your success?\
AI (Cristiano): It is simple: hard work, discipline, and belief in yourself. Every day, I try to be better than I was the day before. That is my mindset. Siiiiuuuu!\
User: What was your favorite goal?\
AI (Cristiano): There have been many great goals, but my bicycle kick against Juventus in 2018 stands out. Even the Juventus fans applauded—that was unforgettable!\
User: What is your advice for young footballers?\
AI (Cristiano): Work hard, stay focused, and never give up. Your dreams are possible if you're willing to make sacrifices. And remember, always enjoy the game!"

force_dark_mode = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""
def chat_gpt(message, history):

    relevant_system_message = system_message
    if 'belt' in message:
        relevant_system_message += " The store does not sell belts; if you are asked for belts, be sure to point out other items on sale."
    
    print(message)
    messages = [{"role": "system", "content": relevant_system_message}] + history + [{"role": "user", "content": message}]

    stream = openai.chat.completions.create(model=gpt_model, messages=messages, stream=True)

    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        yield response

gr.ChatInterface(fn=chat_gpt, type="messages", js=force_dark_mode).launch(share=True)



