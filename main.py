import argparse
from pathlib import Path
import torch
from pydub import AudioSegment
from moviepy import VideoFileClip, AudioFileClip
import os
import numpy as np
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

def extract_audio(video_path, temp_wav_path):
    """Extract audio from MOV file and save as WAV"""
    command = f"ffmpeg -i {video_path} -ab 160k -ac 2 -ar 44100 -vn {temp_wav_path}"
    os.system(command)

from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
import numpy as np
from pydub import AudioSegment

from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
from pydub import AudioSegment
import numpy as np

def process_audio_with_vad(wav_path, output_wav_path):
    """Process audio with silero-vad and replace non-speech with silence"""
    model = load_silero_vad()
    
    wav = read_audio(wav_path)
    speech_timestamps = get_speech_timestamps(wav, model, return_seconds=True)
    
    # Load the original audio file
    original_audio = AudioSegment.from_wav(wav_path)
    
    # Create a silent segment of the same length
    silence_segment = AudioSegment.silent(duration=len(original_audio))
    
    # Overlay speech segments on silence
    for segment in speech_timestamps:
        start, end = int(segment['start'] * 1000), int(segment['end'] * 1000)
        silence_segment = silence_segment.overlay(original_audio[start:end], start)
    
    silence_segment.export(output_wav_path, format="wav")




def combine_video_and_audio(video_path, audio_path, output_path):
    """Combine processed audio with original video"""
    print(f"Combining {video_path} with {audio_path} to {output_path}")
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    final_clip = video_clip.with_audio(audio_clip)
    # final_clip.write_videofile(output_path)
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

def main(input_mov_path, output_mov_path):
    temp_wav_path = Path(input_mov_path).with_suffix('.wav')
    processed_wav_path = Path(input_mov_path).with_suffix('.processed.wav')
    
    extract_audio(input_mov_path, temp_wav_path)
    process_audio_with_vad(temp_wav_path, processed_wav_path)
    combine_video_and_audio(input_mov_path, processed_wav_path, output_mov_path)
    
    # Clean up temporary files
    os.remove(temp_wav_path)
    os.remove(processed_wav_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean MOV file using silero-vad")
    parser.add_argument("input", type=str, help="Input MOV file path")
    args = parser.parse_args()

    input_mov_path = Path(args.input)
    output_mov_path = input_mov_path.with_name(f"{input_mov_path.stem}-cleaned{input_mov_path.suffix}")

    main(str(input_mov_path), str(output_mov_path))
