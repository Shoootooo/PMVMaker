import librosa
import numpy as np
import os
import ffmpeg

def normalize_audio(input_path):
    """
    Converts any audio file to a standardized WAV file to fix metadata issues.

    Args:
        input_path (str): The path to the source audio file.

    Returns:
        str: The path to the new, normalized temporary WAV file, or None on error.
    """
    if not os.path.exists(input_path):
        print(f"Error: Audio file not found at {input_path}")
        return None

    output_path = os.path.join('temp', 'normalized_audio.wav')
    print(f"Normalizing audio to {output_path}...")

    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, acodec='pcm_s16le', ar='44100', ac=2) # Standard CD quality WAV
            .run(overwrite_output=True, quiet=True)
        )
        return output_path
    except ffmpeg.Error as e:
        print(f"Error during audio normalization: {e.stderr.decode()}")
        return None

def get_beat_timestamps(audio_path, tightness=100):
    """
    Analyzes an audio file to find beat timestamps.

    Args:
        audio_path (str): The path to the audio file.
        tightness (int): How strictly to follow the tempo. Higher values mean
                         more strict, resulting in fewer beats.

    Returns:
        np.ndarray: An array of timestamps (in seconds) corresponding to the detected beats.
    """
    try:
        y, sr = librosa.load(audio_path)
        # Pass the tightness parameter to the beat tracker
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, tightness=tightness)
        beat_times = librosa.frames_to_time(beats, sr=sr)
        return beat_times
    except Exception as e:
        print(f"Error processing audio file: {e}")
        return np.array([])

def get_audio_duration(audio_path):
    """
    Gets the duration of an audio file.

    Args:
        audio_path (str): The path to the audio file.

    Returns:
        float: The duration in seconds.
    """
    try:
        return librosa.get_duration(path=audio_path)
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0.0

if __name__ == '__main__':
    # Example usage:
    import soundfile as sf

    dummy_audio_path = 'temp/dummy_audio_analyzer.mp3' # Use mp3 to simulate a non-wav file
    if not os.path.exists('temp'):
        os.makedirs('temp')
    sr = 22050
    duration_sec = 5 # Reduced duration to keep test files small
    y = np.random.randn(sr * duration_sec)
    sf.write(dummy_audio_path, y, sr)

    print("--- Testing Music Analyzer with Normalization ---")

    # 1. Normalize the audio
    normalized_path = normalize_audio(dummy_audio_path)
    assert normalized_path is not None, "Normalization should produce a file path."
    assert os.path.exists(normalized_path), "Normalized file should exist."
    print(f"Successfully normalized audio to: {normalized_path}\n")

    # 2. Run analysis on the NORMALIZED file
    audio_duration = get_audio_duration(normalized_path)
    print(f"Audio duration from normalized file: {audio_duration:.2f}s\n")

    # 3. Test with different tightness values
    settings = {
        "Relaxed (fewer beats)": 200,
        "Normal (default)": 100,
        "Intense (more beats)": 50
    }

    for name, tightness_val in settings.items():
        timestamps = get_beat_timestamps(normalized_path, tightness=tightness_val)
        print(f"Setting: '{name}' (tightness={tightness_val})")
        print(f" -> Detected {len(timestamps)} beats.")

    print("\nMusic analyzer test complete.")