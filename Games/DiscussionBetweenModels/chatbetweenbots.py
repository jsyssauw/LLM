# imports

import os
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
from IPython.display import Markdown, display, update_display

# import for google
# in rare cases, this seems to give an error on some systems, or even crashes the kernel
# If this happens to you, simply ignore this cell - I give an alternative approach for using Gemini later
# import google.generativeai

# Load environment variables in a file called .env
# Print the key prefixes to help with any debugging

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
if anthropic_api_key:
    print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
else:
    print("Anthropic API Key not set")

if google_api_key:
    print(f"Google API Key exists and begins {google_api_key[:8]}")
else:
    print("Google API Key not set")

# Connect to OpenAI, Anthropic

openai = OpenAI()
claude = anthropic.Anthropic()

# Let's make a conversation between GPT-4o-mini and Claude-3-haiku
# We're using cheap versions of models so the costs will be minimal

gpt_model = "gpt-4o-mini"
claude_model = "claude-3-haiku-20240307"
profile_gpt = "Bart de Wever bot"
profile_claude = "HLN reporter"

claude_system = "Je bent een reporter van Het Laatste Nieuws, en wil Bart de Wever op de rooster leggen over de formatie van een regering."
gpt_system = "Je bent Bart de Wever, formateuur en N-VA politieker uit België. Je antwoordt degelijk maar kort. Je gebruikt graag Latijnse gezegden"

# gpt_system = "You are a AA Gent soccerteam supporter who is very enthousiastic but you are feeling a bit sad about the bad performance of the team this year; \
# You are enthousiasitc, but pessistmic about this year's chances to win the championship or even to qualify for Europe next year. You complain that your team is already elminated in the Belgian cup tournament this year. \
# You like to refer back to the one time that they won the championship. You are alwys in for a fun conversation and a joke, in a cheaky, super funny way. You talk in dutch and answer in rather short answers"

# claude_system = "You are a polite, courteous Club Brugge fan that is enormously aware that Club Brugge has done very well in the local competition and the champions leaque this year. You like to challenge the AA Gent fan \
# and you love a fun conversation. You talk in dutch"

def call_gpt():
    messages = [{"role": "system", "content": gpt_system}]
    for gpt, claude in zip(gpt_messages, claude_messages):
        messages.append({"role": "assistant", "content": gpt})
        messages.append({"role": "user", "content": claude})
    completion = openai.chat.completions.create(
        model=gpt_model,
        messages=messages
    )
    return completion.choices[0].message.content

def call_claude():
    messages = []
    for gpt, claude_message in zip(gpt_messages, claude_messages):
        messages.append({"role": "user", "content": gpt})
        messages.append({"role": "assistant", "content": claude_message})
    messages.append({"role": "user", "content": gpt_messages[-1]})
    message = claude.messages.create(
        model=claude_model,
        system=claude_system,
        messages=messages,
        max_tokens=200
    )
    return message.content[0].text

gpt_messages = ["Halo"]
claude_messages = ["Hi, wat vind jij van dit kranten artikel: Formatie lijkt steeds meer een soap: terwijl verwijten in het rond vliegen, probeert De Wever Arizona te redden \
Eind januari moet de Arizona-regering er zijn. Dat is formateur Bart De Wever (N-VA) zondagavond overeengekomen met de andere partijen. “We gaan het tempo versnellen!” \
Na Nieuwjaar volgen intense onderhandelingen. Ondertussen vliegen de verwijten in het rond en lijkt de formatie steeds meer op een soap. \
Eentje met een cliffhanger van jewelste: wat als De Wever binnenkort finaal de handdoek gooit?"]

print(f"{profile_gpt}:\n{gpt_messages[0]}\n")
print(f"{profile_claude}:\n{claude_messages[0]}\n")

for i in range(5):
    gpt_next = call_gpt()
    print(f"{profile_gpt}:\n{gpt_next}\n")
    gpt_messages.append(gpt_next)
    
    claude_next = call_claude()
    print(f"{profile_claude}:\n{claude_next}\n")
    claude_messages.append(claude_next)