import re, os
import json
import sqlite3
from anthropic import Anthropic
from dotenv import load_dotenv
from pathlib import Path

### Configuring Anthropic API credentials
MODEL_NAME = "claude-3-5-sonnet-20241022"
load_dotenv()
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
os.environ['ANTHROPIC_API_KEY'] = anthropic_api_key
client = Anthropic()
DEBUG_MODE = False

class DatabaseManager:
    def __init__(self):
        self.conn = None

    def connect(self):
        #self.conn = sqlite3.connect('D:\Programs\LLM\projects\llm_engineering\Anthropic\SQLLITEDB\cache_db')
        self.conn = sqlite3.connect(str(Path.cwd() / 'SQLLITEDB' / 'cache_db'))
        self.create_table()

    def disconnect(self):
        if self.conn:
            self.conn.close()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL
        )
        ''')
        if DEBUG_MODE:
            cursor.execute("SELECT * FROM users")
            count = len(cursor.fetchall())
            print(f"Database Connection working: there are {count} rows in the user table ....")
        self.conn.commit()

    def show_all_records(self, vname: str):
        cursor = self.conn.cursor()
        if DEBUG_MODE:
            print("Show_all_records function call")
        if vname:
            cursor.execute("SELECT * FROM users WHERE name = ?", (vname,))
        else:
            cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    # def insert_record(self, record_data: dict):
    def insert_record(self, vname, vage):
        if DEBUG_MODE:
            print("im here")
            print(f"Insert name: {vname}, age is {vage}")
        if vname is None or vage is None:
            raise ValueError("record_data must contain 'vname' and 'vage'")
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", (vname, vage))
        self.conn.commit()
        return "success"

    def change_age(self, vname: str, vage: int):
        if DEBUG_MODE:
            print("DEBUG>>>>>>>>>>>> databasemanager.change_age - 66")  
            print(f"DEBUG>>>>>>>>>>>>>>>>> UPDATE users SET age = ? WHERE name = ?, ({vage}, {vname})")
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET age = ? WHERE name = ?", (vage, vname))
        self.conn.commit()

    def show_record(self, vname: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name = ?", (vname,))
        rows = cursor.fetchall()
        if len(rows) >= 1:
            return rows[0]
        else:
            return None

db_manager = DatabaseManager()
db_manager.connect()

def process_tool_call(tool_name, tool_input):
    vname = tool_input.get("vname", None)
    vage = tool_input.get("vage", None)
    if DEBUG_MODE:
        print("DEBUG>>>>>>>>>>>> process_tool_call - 86")
        print("DEBUG>>>>>>>>>>>>>>>>> TOOL NAME:")
        print(tool_name)
        print("DEBUG>>>>>>>>>>>>>>>>> TOOL INPUT:")
        print(tool_input)
    if tool_name == "show_all_records":
        if DEBUG_MODE:
            print("DEBUG>>>>>>>>>>>> process_tool_call.show_all_records - 93")  
        return db_manager.show_all_records(vname=vname)
    elif tool_name == "change_age":
        if DEBUG_MODE:
            print("DEBUG>>>>>>>>>>>> process_tool_call.change_age - 97")  
            print(f"Name: {vname}, new age: {vage}")
        return db_manager.change_age(vname, vage)
    # elif tool_name == "insert_record":
    #     # (self, record_data: dict):"
    #     print("I got to the insert call ##############################################################################")
    #     record_data = tool_input.get(vname, vage)
    #     print(record_data)
    #     return db_manager.insert_record(vname, vage)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

def extract_reply(text):
    pattern = r'<reply>(.*?)</reply>'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return None

def generate_system_prompt():
    system_prompt = """
    You are a database assistant that helps to update, retrieve and insert records into a database tracking name and age.
    You have access to a set of tools, but only use them when needed.  
    If you do not have enough information to use a tool correctly,
    ask a user follow up questions to get the required inputs.
    Do not call any of the tools unless you have the required data from a user.

    In each conversational turn, you will begin by thinking about
    your response. Once you're done, you will write a user-facing
    response. It's important to place all user-facing conversational
    responses in <reply></reply> XML tags to make them easy to parse.
    """
    prompt = system_prompt
    return prompt    

# def show_all_records(self, vname: str):
# def insert_record(self, record_data: dict):
# def change_age(self, vname: str, vage: int):
def set_tools():

    v_tools = [
    {
        "name": "show_all_records",
        "description": "Retrieve all records from the table in the database",
        "input_schema": {
            "type": "object",
            "properties": {
                "vname": {
                    "type": "string",
                    "description": "The name to use to search the table."
                }
            },
            "required": []
        },
    },
    {
        "name": "change_age",
        "description": "Update the age for the record where use is the provided vname",
        "input_schema": {
            "type": "object",
            "properties": {
                "vname": {
                    "type": "string",
                    "description": "The name of the user that we need to have for updating the age."
                },
                "vage": {
                    "type": "number",
                    "description": "age that we need to use to update the record"
                },
            },
            "required": ["vname","vage"]
        }
    }
    # ,
    # {
    #     "name": "insert_record",
    #     "description": "add a new record in the table with the name and the age",
    #     "input_schema": {
    #         "type": "object",
    #         "properties": {
    #             "vname": {
    #                 "type": "string",
    #                 "description": "The name of the user that we need to have for updating the age."
    #             },
    #             "vage": {
    #                 "type": "number",
    #                 "description": "age that we need to use to update the record"
    #             },
    #         },
    #         "required": ["vname","vage"]
    #     }
    # }
    ]
    
#     ,
#     {
#         "name": "get_order_by_id",
#         "description": "Retrieves the details of a specific order based on the order ID. Returns the order ID, product name, quantity, price, and order status.",
#         "input_schema": {
#             "type": "object",
#             "properties": {
#                 "order_id": {
#                     "type": "string",
#                     "description": "The unique identifier for the order."
#                 }
#             },
#             "required": ["order_id"]
#         }
#     },
#     {
#         "name": "get_customer_orders",
#         "description": "Retrieves the list of orders belonging to a user based on a user's customer id.",
#         "input_schema": {
#             "type": "object",
#             "properties": {
#                 "customer_id": {
#                     "type": "string",
#                     "description": "The customer_id belonging to the user"
#                 }
#             },
#             "required": ["customer_id"]
#         }
#     },
#     {
#         "name": "cancel_order",
#         "description": "Cancels an order based on a provided order_id.  Only orders that are 'processing' can be cancelled",
#         "input_schema": {
#             "type": "object",
#             "properties": {
#                 "order_id": {
#                     "type": "string",
#                     "description": "The order_id pertaining to a particular order"
#                 }
#             },
#             "required": ["order_id"]
#         }
#     }
# ]
    
#     v_tools = [
#         {
#             "name": "show_all_records",
#             "description": "Retrieve all records from the table in the database",
#             "input_schema": {
#                 "type": "object",
#                 "properties": {
#                     "vname": {
#                         "type": "string",
#                         "description": "The name to use to search the table."
#                     }
#                 },
#                 "required": []
#             }
#         },
#         {
#             "name": "change_age",
#             "description": "Update the age for the record where use is the provided vname",
#             "input_schema": {
#                 "type": "object",
#                 "properties": {
#                     "vname": {
#                         "type": "string",
#                         "description": "The name of the user that we need to have for updating the age."
#                     },
#                     "vage": {
#                         "type": "int",
#                         "description": "age that we need to use to update the record"
#                     },
#                 },
#                 "required": ["vname","vage"]
#             }
#         }
#     ]
    return v_tools

def simple_chat():
    user_message = input("\nUser: ")
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        if user_message.strip().lower() == "quit":
            break
        ## if last message is from the assistant, get another message
        ## print(messages)
        ## print("Summary: " + messages[0]["role"]+ messages[0]["content"])
        if messages[-1].get("role") == "assistant":
            user_message = input("\nUser: ")
            messages.append({"role": "user", "content": user_message})

        # send a request to anthropic
        response = client.messages.create(
            model=MODEL_NAME,
            system=generate_system_prompt(),
            max_tokens=4096,
            tools= set_tools(),
            messages=messages
        )
        messages.append(
            {"role": "assistant", "content": response.content}
        )
        ## print(response)
        if getattr(response, "stop_reason", None) == "tool_use":
            tool_use = response.content[-1]  ### be carefull if we call 2 , this only works for 1 tool call at the same time
            if DEBUG_MODE:
                print(tool_use)
            if not tool_use:
                print("No tool call found in response.")
                continue
            tool_name = tool_use.name
            tool_input = tool_use.input
            if DEBUG_MODE:
                print("tool use:")
                print(tool_input)
                print(f"=====Claude wants to use the {tool_name} tool=====")
            # try:
            if DEBUG_MODE:
                print(f"DEBUG>>>>>>>>>>>>> Simple Chat: 314 - Claude wants to use {tool_name}")
                print(tool_input)
            tool_result = process_tool_call(tool_name, tool_input)
            if DEBUG_MODE:
                print("tool result find")
            # except Exception as e:
            #     tool_result = str(e)
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": str(tool_result),
                        }
                    ]
                }
            )
        else:
            model_reply = response.content
            #print(model_reply[0])
            # print(type(model_reply[0]))  --> type <class 'anthropic.types.text_block.TextBlock'> to a string 
            user_reply = extract_reply(str(model_reply[0]))
            if user_reply:
                print(user_reply)

try:
    simple_chat()
finally:
    db_manager.disconnect()
