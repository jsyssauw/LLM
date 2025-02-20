#######################################################################################################
##  jsyssauw    19-02-2025
##  v0.1        this code basically takes a url to a youtube video and
##                  a) extract the audio into a wav, mp3 or m4a file
##                  b) optionally transcribes the text by calling ExtractTextFromAudio.py
##          INPUT
##              1) Input url to Youtube video: https://www.youtube.com/watch?v=0XClPByn05g
##              2) Transcribe the video? [Y|n] default is yes
##              3) language code (en, nl, fr, ...)
##          OUTPUT
##              1) .wav/.m4A/mp3 file with the audio of the specified youtube.url
##              2) (optional) .txt with the txt transcript
##  v0.2    moving the sound file creation to the download folder (out of the git controlled folder)
#####################################################################################################

import yt_dlp
import whisper
import os
from datetime import datetime
# import warnings
import re
import ExtractTextFromAudio
import platform

DEBUG_MODE = False

system_name = platform.system()
if system_name == "Windows":
    # print("Running on Windows")
    DOWNLOAD_DIR = os.path.join(os.environ["USERPROFILE"], "Downloads")
    # print(downloads_dir)
elif system_name == "Darwin":
    # print("Running on macOS")
    DOWNLOAD_DIR = os.path.join(os.environ["HOME"], "Downloads")
    # print(downloads_dir)
elif system_name == "Linux":
    # print("Running on Linux")
    DOWNLOAD_DIR = os.path.join(os.environ["HOME"], "Downloads")
    # print(downloads_dir)

# Optionally suppress FP16 warning if running on CPU
# warnings.simplefilter("ignore", category=UserWarning)

# yt-dlp → Downloads YouTube videos and extracts audio.
# ffmpeg → Converts audio to WAV/MP3/M4A format.
# whisper → OpenAI’s speech recognition model.

# Define the YouTube video URL

# Output file name (choose WAV, MP3, or M4A)
audio_format = "wav"  # Change to "mp3" or "m4a" as needed 

def write_to_file(content, file_name):
    # Ensure the Downloads directory exists
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # Construct the full file path in the Downloads directory
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    # Save the text to a file
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(content)
    if DEBUG_MODE: 
        print(f"Transcript successfully saved to {file_name}")

## GET youtube video title
def get_youtube_title(video_url):
    ydl_opts = {
        'quiet': True,  # Suppress output logs
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)  # Get video info without downloading
        return info_dict.get('title', 'Unknown Title')

def extract_audio(youtube_url, title, audio_format, transcribe=False):
    # yt-dlp options to extract audio in best quality
    now = datetime.now()
    formatted_time = now.strftime("%Y%m%d%H%M%S")  

    # Construct file names using the title and formatted time
    clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
    local_file_name = clean_title.replace(" ", "_") + formatted_time
    local_file_name_transcript = os.path.join(DOWNLOAD_DIR, local_file_name[:20] + formatted_time + ".txt" ) 
    local_file_name_audio = os.path.join(DOWNLOAD_DIR, local_file_name[:20] + formatted_time)   # .wav is set in the outtmpl line

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{local_file_name_audio}.%(ext)s",  # File saved with proper extension
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,  # Supports "wav", "mp3", or "m4a"
                "preferredquality": "192",       # 128, 192, 256, 320
            }
        ],
    }
    # Download and extract audio
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    # Construct full audio file path with extension for checking and transcription
    audio_file_path = f"{local_file_name_audio}.{audio_format}"

    if os.path.exists(audio_file_path):
        print(f"Audio extracted and saved as: {audio_file_path}")
    else:
        if DEBUG_MODE:
            print("Error: Audio extraction failed.")
        return  # Exit the function if file doesn't exist

    # Load Whisper model and transcribe
    if transcribe:
        # model = whisper.load_model("large", device="cuda")  # Choose 'tiny', 'base', 'small', 'medium', 'large'
        # result = model.transcribe(audio_file_path)
        local_file_name_transcript, result= ExtractTextFromAudio.transcribe_audio(audio_file_path, language_code, local_file_name_transcript )
        if DEBUG_MODE:
            print("writing pathc in extract video: ",audio_file_path)
            print("ResultType:", type(result))
            print("--------------------------------")
            print(result)
            print("--------------------------------")
        # write_to_file(result["text"], local_file_name_transcript)
        if DEBUG_MODE:
            print("\nTranscription:\n", result)
    return (local_file_name_audio+"."+audio_format,local_file_name_transcript,transcribe )

if __name__ == "__main__":
    print("##################################################################################")
    print("## Extract Audio from Youtube")
    print("##################################################################################")
    youtube_url = input("Input url to Youtube video: ")
    transcribe_input = input("Transcribe the video? [Y|n] ").strip()
    language_code = input("Audio language code (en/nl/...) - avoid autodetect: ")
    title = get_youtube_title(youtube_url)
    if DEBUG_MODE:
        print("Video Title:", title)
    
    if transcribe_input.lower() == "y" or transcribe_input == "":
        transcribe = True
    else:
        transcribe = False
    file_audio, file_transcript, transcribed = extract_audio(youtube_url,title,audio_format, transcribe)
    if DEBUG_MODE:
        print(file_audio, file_transcript, transcribed)
    print('Files created. Extraction completed.')
