########################################################################################
##
##  jsyssauw
##  v0.1    initial local transcribe using whisper-large-v3-turbo with fixed file
##          support m4a and wav.
##          We chunck up the sound file in bits of xx secs, with a small overlay, and past everything together
##          this is because Whisper only deals with 448 token (444 output tokens)
##          Caution: 
##              1) this might lead to words being repeated when just at the junction, or if very unfortunate a word to be missed
##              2) the punctuation to be wrong.
##        
########################################################################################


from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch
import soundfile as sf
import numpy as np
# For handling m4a files
from pydub import AudioSegment
import os

DEBUG_MODE = False
# LANGUAGE_CODE = "en"
LANGUAGE_CODE = "nl"
# Choose the device: 'cuda' for GPU or 'cpu'
device = "cuda" if torch.cuda.is_available() else "cpu"
if DEBUG_MODE:
    print(device)

# Load the processor and model from Hugging Face Hub
model_name = "openai/whisper-large-v3-turbo"
processor = WhisperProcessor.from_pretrained(model_name)
model = WhisperForConditionalGeneration.from_pretrained(model_name).to(device)

def load_audio(audio_file, target_sr=16000):
    """
    Load an audio file, supporting both .wav and .m4a formats.
    Returns a numpy array of audio samples at the target sampling rate.
    """
    ext = os.path.splitext(audio_file)[1].lower()
    
    if ext == ".m4a":
        # Use pydub to load m4a file (ffmpeg must be installed)
        audio_segment = AudioSegment.from_file(audio_file, format="m4a")
        # Convert to mono if needed
        if audio_segment.channels > 1:
            audio_segment = audio_segment.set_channels(1)
        # Set frame rate to target_sr
        if audio_segment.frame_rate != target_sr:
            audio_segment = audio_segment.set_frame_rate(target_sr)
        # Convert to numpy array (pydub gives int16 data)
        audio_data = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
        # Normalize to [-1, 1] (assuming 16-bit audio)
        audio_data = audio_data / 32768.0
    else:
        # For other formats (e.g., .wav), use soundfile
        audio_data, sr = sf.read(audio_file)
        # If not mono, average channels
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        # Resample if necessary using librosa (install via pip install librosa)
        if sr != target_sr:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=target_sr)
    return audio_data

def transcribe(audio_file, segment_length_seconds=15): 
    # Load audio and ensure it's at 16 kHz
    audio_input = load_audio(audio_file, target_sr=16000)
    sample_rate = 16000
    segment_length = segment_length_seconds * sample_rate 
    over_sample = int((segment_length / segment_length_seconds ) / 3 )
    if DEBUG_MODE:
        print("segment length: ", segment_length)

    full_transcription = []  # CHANGED: List to hold each segment's transcription

    # Split the audio into segments and process each segment
    for i in range(0, len(audio_input), segment_length):
        segment = audio_input[i:i+segment_length+over_sample]  # CHANGED: Extract a segment of the audio
        # Explicitly set the pad token (workaround for Whisper)
        processor.tokenizer.pad_token = processor.tokenizer.eos_token

        # Prepare input for the model with padding for the current segment
        inputs = processor(segment, sampling_rate=sample_rate, return_tensors="pt", padding=True)
        input_features = inputs.input_features.to(device)

        # Create an attention mask manually:
        # input_features has shape [batch, frames, feature_dim] so we need [batch, frames]
        attention_mask = torch.ones(input_features.shape[0], input_features.shape[1],
                                      dtype=torch.long, device=device)

        # Generate transcription tokens for the current segment
        predicted_ids = model.generate(
            input_features,
            attention_mask=attention_mask,
            forced_decoder_ids=processor.get_decoder_prompt_ids(language=LANGUAGE_CODE, task="transcribe"),
            max_new_tokens=444,  # Must be ≤ 444 to remain within Whisper's limit (4 + 444 = 448)
            early_stopping=False,
            num_beams=1,
            no_repeat_ngram_size=3
        )

        # Decode tokens to text (skip special tokens such as EOS)
        segment_transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        full_transcription.append(segment_transcription)

        if DEBUG_MODE:
            print(f"Segment {i//segment_length + 1} transcription:", i,i+segment_length+over_sample )
            print(segment_transcription)
            print("----")

    # Concatenate all segment transcriptions with a space between them
    return " ".join(full_transcription)


import re

def remove_repeated_overlap(text, max_ngram=5):
    """
    Removes overlapping repeated words or phrases from stitched text.
    
    Args:
        text (str): The input text containing potential overlap.
        max_ngram (int): The maximum number of words to check for repetition.

    Returns:
        str: The cleaned-up text without duplicated overlaps.
    """
    # Split text into sentences or segments based on punctuation or line breaks
    segments = re.split(r'(?<=[.!?])\s+', text)  # Split on sentence boundaries

    cleaned_segments = [segments[0]]  # Start with the first segment
    
    for i in range(1, len(segments)):
        prev_segment = cleaned_segments[-1].split()  # Get last segment words
        curr_segment = segments[i].split()  # Get current segment words
        
        # Check for overlapping sequences (starting with the longest possible match)
        overlap_index = 0
        for n in range(max_ngram, 0, -1):  # Start with the largest n-gram and go smaller
            if len(prev_segment) >= n and len(curr_segment) >= n:
                if prev_segment[-n:] == curr_segment[:n]:  # Check for match
                    overlap_index = n
                    break
        
        # Remove the overlapping part from the current segment
        cleaned_segments.append(" ".join(curr_segment[overlap_index:]))
    
    # Join cleaned segments into final text
    return " ".join(cleaned_segments)

# Test the transcription function
if __name__ == "__main__":
    # Replace with your audio file path (can be .wav or .m4a)
    print("Reading in audio file (m4a/wav - sample rate 16000 ....)")
    print("...")
    audio_file = "Nieuwe opname 4.m4a"  # Ensure the audio file is in a supported format and 16kHz
    print("Transcribing the audio file in chunks.)")
    print("...")
    first_draft = transcribe(audio_file)
    print("Deduplicating the overlapping sections of chunks")
    print("...")
    cleaned_text = remove_repeated_overlap(first_draft )
    print("Result ....)")    
    if DEBUG_MODE:
        print("Transcription:")
        print(first_draft)
    print(cleaned_text)
    print("<End_of_result>")