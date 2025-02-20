########################################################################################
##
##  jsyssauw    19-02-2025
##  v0.1        this code basically takes  a wav, mp3 or m4a file and optionally transcribes 
##          If the sound file is short (<chunk_threshold_seconds> we transcribe the sound file in 1 go. 
##          If longer, we chunck up the sound file in bits of chunksize secs, with a small overlay, and paste everything together
##          this is because Whisper only deals with 448 token (444 output tokens)
##          Caution: 
##              1) this might lead to words being repeated when just at the junction, or if very unfortunate a word to be missed
##              2) the punctuation to be wrong.
##              3) or chunks of word to be repeated. Minimal testing has shown that at normal speaking speed, chunksize = 30 works reasonably well, 
#                   much lower gives a lot of repetition, much higher starts to lose content.
##          INPUT
##              1) audio_file = input("Input file name in current directory: ")  # audio file in .wav or .m4a format
##              2) language_code = input("Audio language code (en/nl/...) - avoid autodetect: ")
##          OUTPUT
##              1) .txt with the txt transcript
########################################################################################


from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch
import soundfile as sf
import numpy as np
from pydub import AudioSegment
import os
import re
from datetime import datetime
import warnings
import whisper
import librosa

DEBUG_MODE = True
CHUNKSIZE = 30 # for large audio files we can't use the direct translation so we are chunking it up in chunksize of seconds. Default in chunksizes of 15'
"""
People generally speak about 125 to 150 words per minute in normal conversation. At that rate:
At 150 words per minute: 333 ÷ 150 ≈ 2.22 minutes, which is about 2 minutes 13 seconds.
At 125 words per minute: 333 ÷ 125 ≈ 2.66 minutes, or roughly 2 minutes 40 seconds.
So, speaking 333 words(aka 444 tokens) would typically take around 2 to 3 minutes, with an average of about 2 minutes 20–30 seconds.
"""

CHUNK_THRESHOLD_SECONDS = 60  # if duration of sounds file is under 60 secs, we are using the transcribe all in 1 go model, over 60 secs we are using the chuncked method
"""
For an RTX 4070 Ti with 12 GB of VRAM, a good rule of thumb is:
Up to about 30 seconds: You can often transcribe the entire audio file in one go using whisper.load_model("large") without running into memory or token-limit issues.
Longer than 30 seconds: It's safer to use a chunked transcription method to avoid exceeding the model's context (≈448 tokens) and to keep GPU memory usage manageable.
While you might sometimes process a bit more than 30 seconds depending on the audio content and model settings, 30 seconds is a conservative and generally reliable upper limit for full-file transcription on a 12 GB GPU.
"""

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

if DEBUG_MODE:
    print("Using device:", DEVICE)

# Load the processor and model from Hugging Face Hub
model_name = "openai/whisper-large-v3-turbo"
processor = WhisperProcessor.from_pretrained(model_name)
model = WhisperForConditionalGeneration.from_pretrained(model_name).to(DEVICE)

def write_to_file(content, file_name):
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(content)
    if DEBUG_MODE:
        print(f"Transcript successfully saved to {file_name}")

def load_audio(audio_file, target_sr=16000):
    """
    Load an audio file, supporting both .wav and .m4a formats.
    Returns a numpy array of audio samples at the target sampling rate.
    """
    ext = os.path.splitext(audio_file)[1].lower()
    if ext == ".m4a":
        # Using pydub to load m4a
        audio_segment = AudioSegment.from_file(audio_file, format="m4a")
        if audio_segment.channels > 1:
            audio_segment = audio_segment.set_channels(1)
        if audio_segment.frame_rate != target_sr:
            audio_segment = audio_segment.set_frame_rate(target_sr)
        audio_data = np.array(audio_segment.get_array_of_samples()).astype(np.float32) / 32768.0
    else:
        audio_data, sr = sf.read(audio_file)
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        if sr != target_sr:
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=target_sr)
    return audio_data

def remove_repeated_overlap(text, max_ngram=5):
    """
    Removes overlapping repeated words or phrases from stitched text.
    Splits text on sentence boundaries and removes duplicates.
    """
    segments = re.split(r'(?<=[.!?])\s+', text)
    cleaned_segments = [segments[0]]  # Start with the first segment
    for i in range(1, len(segments)):
        prev_segment = cleaned_segments[-1].split()
        curr_segment = segments[i].split()
        overlap_index = 0
        for n in range(max_ngram, 0, -1):
            if len(prev_segment) >= n and len(curr_segment) >= n:
                if prev_segment[-n:] == curr_segment[:n]:
                    overlap_index = n
                    break
        cleaned_segments.append(" ".join(curr_segment[overlap_index:]))
    return " ".join(cleaned_segments)

def transcribe_long(audio_file, language_code, local_file_name_transcript, segment_length_seconds=15):
    """
    Transcribes audio by chunking into smaller segments and merging them intelligently.
    """

    audio_input = load_audio(audio_file, target_sr=16000)
    sample_rate = 16000
    segment_length = segment_length_seconds * sample_rate  

    # Improved fixed overlap of 2 seconds (2 sec * 16000 samples)
    overlap_size = 2 * sample_rate  # 32000 samples

    full_transcription = []
    previous_words = []  # Store only the last 20 words of previous segment

    # Process in chunks with overlap (advance by segment_length - overlap_size)
    for i in range(0, len(audio_input), segment_length - overlap_size):
        segment = audio_input[i:i + segment_length]
        if DEBUG_MODE:
            print("segment_lenght ",segment_length, overlap_size)

        if len(segment) == 0:  
            continue

        # Set pad token as EOS (workaround for Whisper)
        processor.tokenizer.pad_token = processor.tokenizer.eos_token

        inputs = processor(segment, sampling_rate=sample_rate, return_tensors="pt", padding=True)
        input_features = inputs.input_features.to(DEVICE)
        attention_mask = torch.ones(input_features.shape[0], input_features.shape[1], dtype=torch.long, device=DEVICE)

        predicted_ids = model.generate(
            input_features,
            attention_mask=attention_mask,
            forced_decoder_ids=processor.get_decoder_prompt_ids(language=language_code, task="transcribe"),
            max_new_tokens=444,  # Must be ≤ 444 to remain within Whisper's limit
            early_stopping=False,
            num_beams=3,  # Increased beam search width for better accuracy
            no_repeat_ngram_size=3
        )

        segment_transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

        # Remove duplicate overlap using only the last 20 words of the previous segment
        if previous_words:
            curr_words = segment_transcription.split()
            overlap_index = 0
            max_overlap = min(len(previous_words), len(curr_words))
            for j in range(max_overlap, 0, -1):
                if previous_words[-j:] == curr_words[:j]:
                    overlap_index = j
                    break
            segment_transcription = " ".join(curr_words[overlap_index:])
        
        full_transcription.append(segment_transcription)
        # Update previous_words with the last 20 words from the current segment
        words_in_segment = segment_transcription.split()
        previous_words = words_in_segment[-20:] if len(words_in_segment) >= 20 else words_in_segment

        if DEBUG_MODE:
            print(f"Segment {i // (segment_length - overlap_size) + 1} transcription:")
            print(segment_transcription)
            print("\n\n----")
    
    # Merge all transcriptions and clean up any remaining overlaps
    cleaned_text = remove_repeated_overlap(" ".join(full_transcription))
    write_to_file(cleaned_text, local_file_name_transcript)
    return cleaned_text

def transcribe_audio(audio_file, language_code, chunk_threshold_seconds=CHUNK_THRESHOLD_SECONDS):
    # Load the audio file at 16kHz
    audio_data = load_audio(audio_file, target_sr=16000)
    duration = len(audio_data) / 16000  # duration in seconds

    # Clean the file title to remove illegal characters and build a transcript filename
    now = datetime.now()
    formatted_time = now.strftime("%Y%m%d%H%M%S")  # Format as YYYYMMDDHHMMSS
    clean_title = re.sub(r'[\\/*?:"<>|]', "", audio_file[:-4])
    local_file_name_transcript = clean_title[:20] + formatted_time + ".txt"  


    if duration < chunk_threshold_seconds:
        # For short recordings, transcribe the full file at once
        print(f"Short recording detected of {duration} seconds. Transcribing in one go.")
        # Using the OpenAI Whisper API to transcribe the full audio
        model = whisper.load_model("large", device=DEVICE)  # Choose 'tiny', 'base', 'small', 'medium', 'large'
        result = model.transcribe(audio_file, language=language_code)
        write_to_file(result["text"], local_file_name_transcript)        
    else:
        # For longer recordings, use the chunked transcription method
        print(f"Long recording detected of {duration} seconds. Using chunked transcription.")
        result = transcribe_long(audio_file, language_code, local_file_name_transcript, segment_length_seconds=CHUNKSIZE)
        # 'transcribe' is your chunked transcription function that writes to file and returns file name,
        # you might need to adjust it to return the transcript text directly if desired.
    return (local_file_name_transcript, result)

# Test the transcription function
if __name__ == "__main__":
    print("##################################################################################")
    print("## Extract Text from Audio")
    print("##################################################################################")
    audio_file = input("Input file name in current directory: ")  # audio file in .wav or .m4a format
    language_code = input("Audio language code (en/nl/...) - avoid autodetect: ")
    file_written, final_result = transcribe_audio (audio_file, language_code, CHUNK_THRESHOLD_SECONDS)
    if DEBUG_MODE:
        print("Transcription file:", file_written)
        print("Transcription text:", final_result)
    print('Files created. Extraction completed.')
