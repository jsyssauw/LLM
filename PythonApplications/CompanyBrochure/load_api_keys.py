import os
from dotenv import load_dotenv


def load_api_keys(verbose = False):

    load_dotenv()

    openai_api_key = os.getenv('OPENAI_API_KEY')
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')

    
    if openai_api_key:
        if verbose:
            print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
        else:
            None
    else:
        print("OpenAI API Key not set")
        
    if anthropic_api_key:
        if verbose:
            print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
        else:
            None
    else:
        print("Anthropic API Key not set")

    if google_api_key:
        if verbose:
            print(f"Google API Key exists and begins {google_api_key[:8]}")
        else:
            None
    else:
        print("Google API Key not set")

    if not verbose:
        print("API keys for OpenAI, Anthopic and Google loaded.")    
    else:
        print(f"Verbose mode API key Loading:{verbose}")
