# coding: utf-8

# # Day 3 - Conversational AI - aka Chatbot!


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
# Print the key prefixes to help with any debugging

# load the api keys
load_api_keys(True)

system_message = "You are a helpful assistant \
You are a helpful assistant in a clothes store. You should try to gently encourage \
the customer to try items that are on sale. Hats are 60% off, and most other items are 50% off. \
For example, if the customer says 'I'm looking to buy a hat', \
you could reply something like, 'Wonderful - we have lots of hats - including several that are part of our sales evemt.'\
Encourage the customer to buy hats if they are unsure what to get."

# It's now just 1 line of code to prepare the input to OpenAI!

system_message += "\nIf the customer asks for shoes, you should respond that shoes are not on sale today, \
but remind the customer to look at hats!"

def chat_gpt(message, history):

    relevant_system_message = system_message
    if 'belt' in message:
        relevant_system_message += " The store does not sell belts; if you are asked for belts, be sure to point out other items on sale."
    
    messages = [{"role": "system", "content": relevant_system_message}] + history + [{"role": "user", "content": message}]

    stream = openai.chat.completions.create(model=gpt_model, messages=messages, stream=True)

    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        yield response

def chat_claude(message, history):
    relevant_system_message = system_message
    if 'belt' in message:
        relevant_system_message += " The store does not sell belts; if you are asked for belts, be sure to point out other items on sale."

       # Combine the system message and history into the required prompt format
    messages = "\n\n".join(
        [f"Human: {msg['content']}" if msg["role"] == "user" else f"Assistant: {msg['content']}" for msg in history] +
        [f"Human: {message}"]
    )
    # print("Claude responds:")
    # result = claude.messages.stream(
    #     model=claude_model,
    #     max_tokens=1000,
    #     temperature=0.7,
    #     system=relevant_system_message,
    #     messages=messages,
    # )
    # response = ""
    # print(f"Streaming {messages}")
    # with result as stream:
    #     for text in stream.text_stream:
    #         response += text or ""
    #         yield response
    # Print debug information
    print("Claude responds:")
    print(f"Streaming {messages}")

    # Initialize the Claude client
    client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))  # Replace with your API key if not using environment variables

    # Send the prompt to Claude and stream the response
    result = claude.messages.stream(
        model=claude_model,
        max_tokens=1000,
        temperature=0.7,
        system= relevant_system_message,
        messages=f"{messages}"
    )

def chat_claude2(
    message: "",
    history: List[Dict[str, str]],
    system_message: str = ""
) -> Generator[str, None, None]:
    """
    Streams responses from Claude API with proper message handling and error checking.
    
    Args:
        message: Current user message
        history: List of previous messages with 'role' and 'content' keys
        system_message: System prompt to guide Claude's behavior
        model: Claude model identifier
        max_tokens: Maximum tokens in response
        temperature: Response randomness (0-1)
    
    Yields:
        Streamed response chunks from Claude
    """
    try:
        # Update system message if needed
        if 'belt' in message.lower():
            system_message += " The store does not sell belts; if you are asked for belts, be sure to point out other items on sale."

        # Format conversation history
        formatted_messages = []
        for msg in history:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                raise ValueError("Invalid message format in history")
            formatted_messages.append(
                f"Human: {msg['content']}" if msg['role'] == "user" 
                else f"Assistant: {msg['content']}"
            )
        formatted_messages.append(f"Human: {message}")
        
        # Stream response
        response = ""
        with client.messages.stream(
            model=claude_model,
            max_tokens=1000,
            temperature=0.7,
            system=system_message,
            messages="\n\n".join(formatted_messages)
        ) as stream:
            for chunk in stream.text_stream:
                response += chunk or ""
                yield response
                
    except anthropic.APIError as e:
        yield f"API Error: {str(e)}"
    except Exception as e:
        yield f"Error: {str(e)}"
    # Stream the response back
    response = ""
    for chunk in result:
        response += chunk["completion"] or ""
        yield response

if model_type == "Claude":
    gr.ChatInterface(fn=chat_claude2, type="messages").launch()
else: 
    gr.ChatInterface(fn=chat_gpt, type="messages").launch()



