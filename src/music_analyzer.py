import librosa
import numpy as np
import os

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

    dummy_audio_path = 'temp/dummy_audio_analyzer.wav'
    if not os.path.exists('temp'):
        os.makedirs('temp')
    sr = 22050
    duration_sec = 60
    y = np.random.randn(sr * duration_sec)
    sf.write(dummy_audio_path, y, sr)

    print("--- Testing Music Analyzer with Tightness Settings ---")

    audio_duration = get_audio_duration(dummy_audio_path)
    print(f"Audio duration: {audio_duration:.2f}s\n")

    # Test with different tightness values
    settings = {
        "Relaxed (fewer beats)": 200,
        "Normal (default)": 100,
        "Intense (more beats)": 50
    }

    for name, tightness_val in settings.items():
        timestamps = get_beat_timestamps(dummy_audio_path, tightness=tightness_val)
        print(f"Setting: '{name}' (tightness={tightness_val})")
        print(f" -> Detected {len(timestamps)} beats.")

    print("\nMusic analyzer test complete.")