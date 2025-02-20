import subprocess
import os
import gradio as gr
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
import requests
from dotenv import load_dotenv

DEBUG_MODE = True

#######################
# Spotify API Settings
#######################
load_dotenv()

SPOTIFY_CLIENT_ID=os.getenv('SPOTIFY_CLIENT_ID_TOKEN')
SPOTIFY_CLIENT_SECRET=os.getenv('SPOTIFY_CLIENT_SECRET_TOKEN')
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"  # Ensure this matches your Spotify app settings
SCOPES = "playlist-read-private playlist-modify-public playlist-modify-private user-read-playback-state user-modify-playback-state"
OLLAMA_URL = "http://localhost:11434/api/generate"  # Adjust if running Ollama on a different port

def get_spotify_client():
    """Return a Spotipy client after authenticating via SpotifyOAuth."""
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPES
    )
    return spotipy.Spotify(auth_manager=auth_manager)

#########################
# Spotify Action Functions
#########################

def list_my_playlists(sp):
    """Return a list of your playlists (name and id)."""
    playlists = sp.current_user_playlists()
    output = []
    for item in playlists['items']:
        output.append(f"{item['name']} (ID: {item['id']})")
    return output

def list_playlist_tracks(sp, playlist_id):
    """Return the tracks in a given playlist."""
    results = sp.playlist_tracks(playlist_id)
    output = []
    for item in results['items']:
        track = item['track']
        output.append(f"{track['name']} - {track['artists'][0]['name']}")
    return output

def browse_featured_playlists(sp):
    """Return a list of featured playlists."""
    featured = sp.featured_playlists()
    output = []
    for item in featured['playlists']['items']:
        output.append(f"{item['name']} (ID: {item['id']})")
    return output

def add_song_to_playlist(sp, playlist_id, track_uri):
    """Add a track to a playlist."""
    sp.playlist_add_items(playlist_id, [track_uri])
    return f"Added {track_uri} to playlist {playlist_id}."

def remove_song_from_playlist(sp, playlist_id, track_uri):
    """Remove a track from a playlist."""
    sp.playlist_remove_all_occurrences_of_items(playlist_id, [track_uri])
    return f"Removed {track_uri} from playlist {playlist_id}."

def control_playback(sp, action):
    """Control playback: action can be 'play', 'pause', or 'skip'."""
    if action.lower() == "play":
        sp.start_playback()
        return "Playback started."
    elif action.lower() == "pause":
        sp.pause_playback()
        return "Playback paused."
    elif action.lower() == "skip":
        sp.next_track()
        return "Skipped to next track."
    else:
        return f"Unknown playback command: {action}"

##############################
# Local Llama Model Integration
##############################
def chat_with_llama(prompt):
    """
    Send a prompt to the local Llama 3.2 model via Ollama and return its response.
    """
    # try:
    if DEBUG_MODE:
        print("Prompt: ",prompt)
    """Send a request to Ollama for inference using the specified model."""
    model_name = "llama3.2"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    if DEBUG_MODE:
        print(response)
    if response.status_code == 200:
        print(response.json().get("response", ""))
        return response.json().get("response", "")
    else:
        print(response.text)
        return f"Error: {response.text}"
    # except Exception as e:
    #     print("Error Calling OLLAMA: ", e)
    #     return f"Error calling local Llama: {str(e)}"       # result = subprocess.run(
    #     #     ["ollama", "chat", "--prompt", prompt],
    #     #     capture_output=True,
    #     #     text=True,
    #     #     check=True
    #     #return result.stdout.strip()
 


##############################
# Command Interpreter for Spotify
##############################
def process_command(user_input):
    print("""
    Uses the local Llama model to interpret the command and trigger Spotify actions.
    The function returns a combined response.
    """)
    # Call the local Llama model with the user prompt.
    llama_response = chat_with_llama(user_input)
    response_text = f"Llama Response: {llama_response}\n"
    
    # Get a Spotify client.
    sp = get_spotify_client()
    if DEBUG_MODE:
        print(sp)
        print("Authenticating with Spotify")
    try:
        user = sp.current_user()
        print("Authenticated as:", user["display_name"])
    except Exception as e:
        print("Spotify authentication error:", e)

    # A very basic command parser based on keywords.
    # (You may wish to improve parsing logic as needed.)
    if DEBUG_MODE:
        print (llama_response)
    if "list my playlists" in llama_response.lower():
        playlists = list_my_playlists(sp)
        response_text += "Your Playlists:\n" + "\n".join(playlists) + "\n"
    if "list tracks" in llama_response.lower():
        # Expecting the command to mention a playlist ID.
        # For simplicity, assume the playlist ID is provided after the phrase "playlist id:"
        if "playlist id:" in llama_response.lower():
            try:
                playlist_id = llama_response.lower().split("playlist id:")[1].strip().split()[0]
                tracks = list_playlist_tracks(sp, playlist_id)
                response_text += f"Tracks in Playlist {playlist_id}:\n" + "\n".join(tracks) + "\n"
            except Exception as e:
                response_text += f"Error listing tracks: {str(e)}\n"
    if "browse featured playlists" in llama_response.lower():
        featured = browse_featured_playlists(sp)
        response_text += "Featured Playlists:\n" + "\n".join(featured) + "\n"
    if "add song" in llama_response.lower():
        # Expect command format: "add song <track_uri> to playlist <playlist_id>"
        parts = llama_response.lower().split()
        try:
            # This is rudimentary extraction; you might need a more robust parser.
            track_uri_index = parts.index("song") + 1
            to_index = parts.index("to")
            playlist_id_index = parts.index("playlist") + 1
            track_uri = parts[track_uri_index]
            playlist_id = parts[playlist_id_index]
            res = add_song_to_playlist(sp, playlist_id, track_uri)
            response_text += res + "\n"
        except Exception as e:
            response_text += f"Error parsing add song command: {str(e)}\n"
    if "remove song" in llama_response.lower():
        # Expect command format: "remove song <track_uri> from playlist <playlist_id>"
        parts = llama_response.lower().split()
        try:
            track_uri_index = parts.index("song") + 1
            from_index = parts.index("from")
            playlist_id_index = parts.index("playlist") + 1
            track_uri = parts[track_uri_index]
            playlist_id = parts[playlist_id_index]
            res = remove_song_from_playlist(sp, playlist_id, track_uri)
            response_text += res + "\n"
        except Exception as e:
            response_text += f"Error parsing remove song command: {str(e)}\n"
    if "playback" in llama_response.lower():
        # Check for subcommands "play", "pause", "skip"
        if "play" in llama_response.lower():
            res = control_playback(sp, "play")
            response_text += res + "\n"
        elif "pause" in llama_response.lower():
            res = control_playback(sp, "pause")
            response_text += res + "\n"
        elif "skip" in llama_response.lower():
            res = control_playback(sp, "skip")
            response_text += res + "\n"
    
    # If no known command is detected, just return Llama's response.
    return response_text

##############################
# Gradio Interface
##############################
process_command("browse featured playlists")
# iface = gr.Interface(
#     fn=process_command,
#     inputs=gr.Textbox(lines=4, placeholder="Enter your Spotify command here..."),
#     outputs="text",
#     title="Spotify & Llama Chat Controller",
#     description=("A local Gradio interface that connects to Spotify and allows you to: \n"
#                  "1) List your playlists and tracks \n"
#                  "2) Browse featured playlists \n"
#                  "3) Add or remove songs from playlists \n"
#                  "4) Control playback \n\n"
#                  "Commands are interpreted by a local Llama 3.2 model running in Ollama.")
# )

# iface.launch()
