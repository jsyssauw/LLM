from anthropic import Anthropic
# Load environment variables
from helper import load_env
import re
import sqlite3
load_env()

### https://learn.deeplearning.ai/courses/building-toward-computer-use-with-anthropic/lesson/7/tool-use

MODEL_NAME="claude-3-5-sonnet-20241022"
client = Anthropic()

class sqlite_atabase:
    # Connect to the SQLite database (or create it if it doesn't exist)
    def connect_db(self):
        conn = sqlite3.connect("D:\Programs\LLM\projects\llm_engineering\Anthropic\SQLLITEDB\cache_db")
        # Create a cursor object using the connection
        cursor = conn.cursor()
 
    def disconnect_db(self): 
        # Close the connection to the database
        conn.close()

    # Create a table if it doesn't exist
    def create_table(self):
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL
        )
        ''')

    def insert_into_table(self, vname:str, vage:int):
        # Insert rows into the table
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO users (name, age) VALUES ('{vname}', {vage})")

        # Commit the changes to the database
        conn.commit()
        
    # Update a row in the table
    def change_age(self, vname:str, vage:int):
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET age = {vage} WHERE name = '{vname}'")
        conn.commit()

    # Retrieve and print all rows from the table
    def show_record(self, vname:str):
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM users where name = '{vname}'")
        rows = cursor.fetchall()
        if len(rows) == 1:
            return rows[1]
        elif len(rows) == 0:
            return None 
        elif:
            return rows[1]

    # Retrieve and print all rows from the table
    def show_all_records(self, vname:str):
        cursor = conn.cursor()
        if not vname or not isinstance(vname, str):
            cursor.execute(f"SELECT * FROM users where name = '{vname}'")
        else:
            cursor.execute(f"SELECT * FROM users where name = '{vname}'")
        rows = cursor.fetchall()
        return rows

    # def get_user(self, key, value):
    #     if key in {"email", "phone", "username"}:
    #         for customer in self.customers:
    #             if customer[key] == value:
    #                 return customer
    #         return f"Couldn't find a user with {key} of {value}"
    #     else:
    #         raise ValueError(f"Invalid key: {key}")
        
    #     return None

 db = sqlite_atabase()


#########################################################
## JSON SCHEMA to define the tool
#########################################################
tools = [
    {
        "name": "show_all_records",
        "description": "Show all records in the database or all records for a specific name",
        "input_schema": {
            "type": "object",
            "properties": {
                "vname": {
                    "type": "string",
                    "description": "All or the name of the user for which we need to retrieve all values"
                }
            },
            "required": []
        }
    },
    {
        "name": "insert_into_table",
        "description": "insert a new row in the database with name and age.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vname": {
                    "type": "string",
                    "description": "The name to be inserted into the table."
                },                
                "vage": {
                    "type": "int",
                    "description": "The age to be inserted into the table."
                }
            },
            "required": ["vname","vage"]
        }
    }
]


# Message(
#     id='msg_011Dro6iKrQaH2qqavb33QfF', 
#     content=[
#         TextBlock(
#             text="I'll help you look up your orders. Let me first get your user details using your username, and then I can retrieve your orders.", 
#             type='text'), 
#         ToolUseBlock(
#             id='toolu_01GCpTk9QqXiZveGzXV6ZYNR', 
#             input={'key': 'username', 'value': 'priya123'}, 
#             name='get_user', 
#             type='tool_use')
#         ], 
#     model='claude-3-5-sonnet-20241022', 
#     role='assistant', 
#     stop_reason='tool_use', 
#     stop_sequence=None, 
#     type='message', 
#     usage=Usage(cache_creation_input_tokens=0, cache_read_input_tokens=0, input_tokens=725, output_tokens=101)
#     )


print (response.content[1])   ##<-- this is the action

def process_tool_call(tool_name, tool_input):
    if tool_name == "show_all_records":
        return db.show_all_records(self, vname:str):get_user(tool_input["key"], tool_input["value"])
    elif tool_name == "insert_into_table":
        return db.get_order_by_id(tool_input["order_id"])

tool_use = response.content[-1] 
tool_name = tool_use.name
tool_input = tool_use.input

tool_result = process_tool_call(tool_name, tool_input)
print(tool_result)
prompt = {
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": str(tool_result),
        }
    ],
}


def extract_reply(text):
    pattern = r'<reply>(.*?)</reply>'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return None    
    
def simple_chat():
    system_prompt = """
    You are a customer support chat bot for an online retailer
    called Acme Co.Your job is to help users look up their account, 
    orders, and cancel orders.Be helpful and brief in your responses.
    You have access to a set of tools, but only use them when needed.  
    If you do not have enough information to use a tool correctly, 
    ask a user follow up questions to get the required inputs.
    Do not call any of the tools unless you have the required 
    data from a user. 

    In each conversational turn, you will begin by thinking about 
    your response. Once you're done, you will write a user-facing 
    response. It's important to place all user-facing conversational 
    responses in <reply></reply> XML tags to make them easy to parse.
    """
    user_message = input("\nUser: ")
    messages = [{"role": "user", "content": user_message}]
    while True:
        if user_message == "quit":
            break
        #If the last message is from the assistant, 
        # get another input from the user
        if messages[-1].get("role") == "assistant":
            user_message = input("\nUser: ")
            messages.append({"role": "user", "content": user_message})

        #Send a request to Claude
        response = client.messages.create(
            model=MODEL_NAME,
            system=system_prompt,
            max_tokens=4096,
            tools=tools,
            messages=messages
        )
        # Update messages to include Claude's response
        messages.append(
            {"role": "assistant", "content": response.content}
        )

        #If Claude stops because it wants to use a tool:
        if response.stop_reason == "tool_use":
            #Naive approach assumes only 1 tool is called at a time
            tool_use = response.content[-1] 
            tool_name = tool_use.name
            tool_input = tool_use.input
            print(f"=====Claude wants to use the {tool_name} tool=====")


            #Actually run the underlying tool functionality on our db
            tool_result = process_tool_call(tool_name, tool_input)

            #Add our tool_result message:
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": str(tool_result),
                        }
                    ],
                },
            )
        else: 
            #If Claude does NOT want to use a tool, 
            #just print out the text reponse
            model_reply = extract_reply(response.content[0].text)
            print("\nAcme Co Support: " + f"{model_reply}" )

simple_chat()



finally:
    # Ensure the connection is closed even if an exception occurs
    close_connection(conn)