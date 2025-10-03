import librosa
import numpy as np

def get_beat_timestamps(audio_path):
    """
    Analyzes an audio file to find beat timestamps.

    Args:
        audio_path (str): The path to the audio file.

    Returns:
        np.ndarray: An array of timestamps (in seconds) corresponding to the detected beats.
    """
    try:
        y, sr = librosa.load(audio_path)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
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

    dummy_audio_path = 'temp/dummy_audio_analyzer.wav'
    sr = 22050
    duration = 60 # seconds
    y = np.random.randn(sr * duration) # 60 seconds of white noise
    sf.write(dummy_audio_path, y, sr)

    print("--- Testing Music Analyzer ---")

    print(f"Analyzing dummy audio file: {dummy_audio_path}")

    duration = get_audio_duration(dummy_audio_path)
    print(f"Detected audio duration: {duration:.2f} seconds")

    timestamps = get_beat_timestamps(dummy_audio_path)
    print(f"Detected {len(timestamps)} beat timestamps.")
    print("First 10 beats:", timestamps[:10])