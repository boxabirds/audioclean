import argparse
from pathlib import Path
import torch
from pydub import AudioSegment
import os
import numpy as np
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
import ffmpeg
from scipy.io import wavfile

def extract_audio(video_path, temp_wav_path):
    """Extract audio from MOV file and save as WAV"""
    command = f"ffmpeg -y -i {video_path} -ab 160k -ac 2 -ar 44100 -vn {temp_wav_path}"
    os.system(command)

def apply_compressor(audio_data, sample_rate, threshold=-10, ratio=4, attack=0.02, release=0.1, knee=5, makeup_gain=0):
    """Apply a compressor effect to the audio data and normalize the output"""
    # Convert threshold from dB to linear scale
    threshold_linear = 10 ** (threshold / 20)
    
    # Initialize gain reduction
    gain_reduction = np.ones_like(audio_data, dtype=np.float32)
    
    # Attack and release coefficients
    attack_coeff = np.exp(-1.0 / (sample_rate * attack))
    release_coeff = np.exp(-1.0 / (sample_rate * release))
    
    # Check if audio is stereo
    if len(audio_data.shape) > 1:
        # Process each channel separately
        for channel in range(audio_data.shape[1]):
            gain_reduction[:, channel] = process_channel(audio_data[:, channel], threshold_linear, ratio, attack_coeff, release_coeff, knee)
    else:
        # Process mono audio
        gain_reduction = process_channel(audio_data, threshold_linear, ratio, attack_coeff, release_coeff, knee)
    
    # Apply gain reduction and makeup gain
    compressed_audio = audio_data * gain_reduction * (10 ** (makeup_gain / 20))
    
    # Normalize the audio
    max_val = np.max(np.abs(compressed_audio))
    if max_val > 0:
        normalization_factor = 32767 / max_val  # Normalize to 16-bit PCM range
        compressed_audio = compressed_audio * normalization_factor
    
    return compressed_audio

def process_channel(channel_data, threshold_linear, ratio, attack_coeff, release_coeff, knee):
    """Process a single audio channel for compression"""
    gain_reduction = np.ones_like(channel_data, dtype=np.float32)
    
    for i in range(1, len(channel_data)):
        input_level = abs(channel_data[i])
        
        # Soft knee
        if knee > 0:
            if threshold_linear - knee / 2 < input_level < threshold_linear + knee / 2:
                input_level = threshold_linear + (input_level - threshold_linear) / (1 + (input_level - threshold_linear) / knee)
        
        # Compression
        if input_level > threshold_linear:
            gain_reduction[i] = 1 / ratio
        else:
            gain_reduction[i] = 1
        
        # Apply attack and release
        if gain_reduction[i] < gain_reduction[i-1]:
            gain_reduction[i] = attack_coeff * gain_reduction[i-1] + (1 - attack_coeff) * gain_reduction[i]
        else:
            gain_reduction[i] = release_coeff * gain_reduction[i-1] + (1 - release_coeff) * gain_reduction[i]
    
    return gain_reduction

def process_audio_with_vad(wav_path, output_wav_path, hpf_freq=None, punch=False):
    """Process audio with silero-vad and replace non-speech with silence"""
    model = load_silero_vad()
    
    wav = read_audio(wav_path)
    speech_timestamps = get_speech_timestamps(wav, model, return_seconds=True)
    
    print(f"VAD detected {len(speech_timestamps)} speech segments:")
    for i, segment in enumerate(speech_timestamps):
        print(f"  Segment {i+1}: {segment['start']:.2f}s - {segment['end']:.2f}s")
    
    # Load the original audio file
    original_audio = AudioSegment.from_wav(wav_path)
    
    # Create a silent segment of the same length
    silence_segment = AudioSegment.silent(duration=len(original_audio))
    
    # Overlay speech segments on silence
    for segment in speech_timestamps:
        start, end = int(segment['start'] * 1000), int(segment['end'] * 1000)
        silence_segment = silence_segment.overlay(original_audio[start:end], start)
    
    # Export to WAV for further processing
    silence_segment.export(output_wav_path, format="wav")
    
    # Apply high pass filter if specified
    if hpf_freq:
        temp_filtered_path = Path(output_wav_path).with_suffix('.filtered.wav')
        stream = ffmpeg.input(str(output_wav_path))
        stream = ffmpeg.output(stream, str(temp_filtered_path), af=f"highpass=f={hpf_freq}")
        ffmpeg.run(stream, overwrite_output=True)
        os.replace(temp_filtered_path, output_wav_path)
    
    # Apply compressor if punch is enabled
    if punch:
        sample_rate, audio_data = wavfile.read(output_wav_path)
        compressed_audio = apply_compressor(audio_data, sample_rate)
        wavfile.write(output_wav_path, sample_rate, compressed_audio.astype(np.int16))

def combine_video_and_audio(video_path, audio_path, output_path):
    """Combine processed audio with original video"""
    print(f"Combining {video_path} with {audio_path} to {output_path}")
    
    # Use ffmpeg directly to avoid MoviePy metadata parsing issues
    video = ffmpeg.input(str(video_path))
    audio = ffmpeg.input(str(audio_path))
    # Map only video from original file and audio from processed file
    stream = ffmpeg.output(video['v'], audio['a'], str(output_path), vcodec='copy', acodec='aac', map_metadata=0)
    ffmpeg.run(stream, overwrite_output=True)

def main(input_mov_path, output_mov_path, hpf_freq=None, punch=False):
    temp_wav_path = Path(input_mov_path).with_suffix('.wav')
    processed_wav_path = Path(input_mov_path).with_suffix('.processed.wav')
    
    extract_audio(str(input_mov_path), str(temp_wav_path))
    process_audio_with_vad(str(temp_wav_path), str(processed_wav_path), hpf_freq, punch)
    combine_video_and_audio(str(input_mov_path), str(processed_wav_path), str(output_mov_path))
    
    # Clean up temporary files
    os.remove(str(temp_wav_path))
    os.remove(str(processed_wav_path))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean MOV file using silero-vad")
    parser.add_argument("input", type=str, help="Input MOV file path")
    parser.add_argument("--filter", type=int, nargs='?', const=250, default=250, help="Apply high pass filter at specified Hz (default: 250 Hz, use 0 to disable)")
    parser.add_argument("--punch", action='store_true', help="Apply compressor to enhance voice")
    args = parser.parse_args()

    input_mov_path = Path(args.input)
    output_mov_path = input_mov_path.with_name(f"{input_mov_path.stem}-cleaned{input_mov_path.suffix}")

    hpf_freq = args.filter
    if hpf_freq == 0:
        hpf_freq = None  # Disable HPF
    elif hpf_freq < 100 or hpf_freq > 2000:
        print("Warning: High pass filter frequency should be between 100 and 2000 Hz. Using 250 Hz.")
        hpf_freq = 250

    main(str(input_mov_path), str(output_mov_path), hpf_freq, args.punch)
