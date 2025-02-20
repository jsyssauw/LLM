import os
import json
from dotenv import load_dotenv
import pandas as pd
from openai import OpenAI
import gradio as gr
from load_api_keys import load_api_keys
import bookagenda as book


# Load environment variables and API keys from .env
load_api_keys(False)

# Configurations
flights_file_name = "flights.xlsx"
flights_sheet_name = "flights"

SCOPES = ['https://www.googleapis.com/auth/calendar']
SYSTEM_MESSAGE = "You are a helpful assistant for an Airline called FlightAI. "
SYSTEM_MESSAGE += "Give short, courteous answers, no more than 1 sentence. "
SYSTEM_MESSAGE += "Always be accurate. If you don't know the answer, say so."
SYSTEM_MESSAGE += "Your objective it to ask people where they want to travel to. Inform them first about the price. When they ask about the price, gentley ask them if they are interested to book the flight"
SYSTEM_MESSAGE += "Always be accurate. If you don't know the answer, say so."

force_dark_mode = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""
# Read the Excel sheet into a pandas DataFrame
# Convert the DataFrame into a dictionary
try:
    df = pd.read_excel(flights_file_name, sheet_name=flights_sheet_name)
    ticket_prices = dict(zip(df["destination"], df["ticket_prices"]))
except FileNotFoundError:
    print(f"Error: File '{flights_file_name}' not found.")
    ticket_prices = {}
except Exception as e:
    print(f"Error loading flights data: {e}")
    ticket_prices = {}

openai = OpenAI()
## claude = anthropic.Anthropic()
GPT_MODEL = "gpt-4o-mini"
# claude_model = "claude-3-haiku-20240307"
# model_type = "Claude"


def get_ticket_price(destination_city):
    if not destination_city:
        return "Invalid destination. Please provide a valid city."
    print(f"Tool get_ticket_price called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")


def chat(message, history):
    # messages = [{"role": "system", "content": SYSTEM_MESSAGE}] + history + [{"role": "user", "content": message}]
    # response = openai.chat.completions.create(model=GPT_MODEL, messages=messages)
    # return response.choices[0].message.content
    messages = [{"role": "system", "content": SYSTEM_MESSAGE}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=GPT_MODEL, messages=messages, tools=tools)

    if response.choices[0].finish_reason=="tool_calls":
        ## debug see the tool that is calledprint(response.choices[0].finish_reason)
        ##print(response)
        message = response.choices[0].message
        tool_call = message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        ddate = arguments.get('travel_date')
        city = arguments.get('destination_city')

        if response.choices[0].message.tool_calls[0].function.name =="get_ticket_price":
            response, city = handle_tool_call(message)
            print(f"Ticket price for : {city}")
        elif response.choices[0].message.tool_calls[0].function.name =="make_booking_int":
            response = book.make_booking_int(city,ddate, tool_call.id)
            print(f"Flight booked for : {city} on {ddate}")
        else:
            print("Not a common message.")

        messages.append(message)
        messages.append(response)
        response = openai.chat.completions.create(model=GPT_MODEL, messages=messages)
    
    return response.choices[0].message.content

def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    city = arguments.get('destination_city')
    price = get_ticket_price(city)
    response = {
        "role": "tool",
        "content": json.dumps({"destination_city": city,"price": price}),
        "tool_call_id": tool_call.id
    }
    return response, city

# def handle_tool_call(message):
#     tool_call = message.tool_calls[0]
#     arguments = tool_call.function.get("arguments", "{}")
#     try:
#         arguments = json.loads(arguments)
#     except json.JSONDecodeError:
#         return {"role": "tool", "content": json.dumps({"error": "Invalid arguments"}), "tool_call_id": tool_call.id}, None
    
#     city = arguments.get("destination_city")
#     if not city:
#         return {"role": "tool", "content": json.dumps({"error": "City not specified"}), "tool_call_id": tool_call.id}, None

#     price = get_ticket_price(city)
#     response = {
#         "role": "tool",
#         "content": json.dumps({"destination_city": city, "price": price}),
#         "tool_call_id": tool_call.id
#     }
#     return response, city

price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city. Call this whenever you need to know the ticket price, for example when a customer asks 'How much is a ticket to this city'",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

calendar_book_function = {
    "name": "make_booking_int",
    "description": "Put the flight to the destination into the calendar. Make that the user knows what the price is for the flight. \
        Ask which date the flight needs to be booked. Call this whenever the flight needs to be booked, for example when a customer says 'ok, go ahead and book the flight'",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
            "travel_date": {
                "type": "string",
                "format": "date",
                "description": "The date that the customer wants to travel on",
            },
        },
        "required": ["destination_city","travel_date"],
        "additionalProperties": False
    }
}



# And this is included in a list of tools:
tools = [
    {"type": "function", "function": price_function},
    {"type": "function", "function": calendar_book_function},
]

# gr.ChatInterface(fn=chat, type="messages", js=force_dark_mode ).launch()µ

gr.ChatInterface(
    fn=chat,
    type="messages",
    js=force_dark_mode,
    description="Welcome to FlightAI! Ask about flight prices or book a flight.",
).launch()