import random
import os
import cv2

def get_video_duration(video_path):
    """Gets the duration of a video file using OpenCV."""
    if not os.path.exists(video_path):
        return 0.0
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        return duration
    except Exception as e:
        print(f"Error getting duration for {video_path}: {e}")
        return 0.0

def create_edit_list(categorized_clips, beat_times, music_duration, progression):
    """
    Creates a chronological list of video clips to be rendered, matching the music duration.

    Args:
        categorized_clips (dict): Clips classified by the AI.
        beat_times (list): Beat timestamps from the music.
        music_duration (float): Total duration of the music track.
        progression (list): The desired order of categories.

    Returns:
        list: A list of tuples: (clip_path, start_in_clip, duration_to_cut).
    """
    if not any(categorized_clips.values()) or not beat_times.any() or music_duration <= 0:
        return []

    edit_list = []

    # Cache clip durations to avoid repeated lookups
    clip_durations = {
        path: get_video_duration(path)
        for category in categorized_clips for path in categorized_clips[category]
    }

    # Filter out any clips that have no duration
    for category in categorized_clips:
        categorized_clips[category] = [
            p for p in categorized_clips[category] if clip_durations.get(p, 0) > 0.1
        ]

    time_per_stage = music_duration / len(progression)
    current_time = 0.0

    for i, category in enumerate(progression):
        stage_end_time = (i + 1) * time_per_stage

        available_clips = categorized_clips.get(category)
        if not available_clips:
            print(f"Warning: No valid clips for category '{category}'. Skipping stage.")
            current_time = stage_end_time
            continue

        # Find the beats within this stage's time window
        stage_beats = [b for b in beat_times if current_time <= b < stage_end_time]
        if not stage_beats:
            # If no beats, just fill the time
            stage_beats = [current_time]

        beat_idx = 0
        while current_time < stage_end_time and beat_idx < len(stage_beats):
            # Pick a clip
            clip_path = random.choice(available_clips)
            clip_len = clip_durations.get(clip_path, 0)

            if clip_len == 0:
                continue

            # Determine the cut's duration
            start_beat_time = stage_beats[beat_idx]

            # Decide how many beats this shot should last (e.g., 2, 4, 8 beats)
            shot_beat_length = random.choice([1, 2, 4, 8])
            end_beat_idx = beat_idx + shot_beat_length

            if end_beat_idx < len(stage_beats):
                end_beat_time = stage_beats[end_beat_idx]
            else:
                # If we're at the end of the beats for this stage, go to the stage's end time
                end_beat_time = stage_end_time

            duration_to_cut = end_beat_time - start_beat_time

            # Ensure we don't overshoot the stage end time
            if start_beat_time + duration_to_cut > stage_end_time:
                duration_to_cut = stage_end_time - start_beat_time

            if duration_to_cut <= 0.1:
                beat_idx += 1
                continue

            # Pick a random start point from the clip
            max_start_in_clip = max(0, clip_len - duration_to_cut)
            start_in_clip = random.uniform(0, max_start_in_clip)

            edit_list.append((clip_path, start_in_clip, duration_to_cut))

            current_time = start_beat_time + duration_to_cut
            # Move to the next beat after the one we just ended on
            while beat_idx < len(stage_beats) and stage_beats[beat_idx] < current_time:
                beat_idx += 1

    return edit_list


if __name__ == '__main__':
    import numpy as np

    print("--- Testing Director ---")

    # 1. Create dummy classified clips
    dummy_clips = {
        'intro': ['temp/intro_1.mp4', 'temp/intro_2.mp4'],
        'main': ['temp/main_1.mp4', 'temp/main_2.mp4'],
        'outro': ['temp/outro_1.mp4']
    }
    # Create empty files for duration testing
    os.makedirs('temp', exist_ok=True)
    for clips in dummy_clips.values():
        for clip in clips:
            if not os.path.exists(clip):
                open(clip, 'a').close()

    # 2. Mock get_video_duration to avoid needing real video files
    original_get_duration = get_video_duration
    def mock_get_duration(path):
        return random.uniform(5.0, 10.0) # All clips are 5-10s long

    # Since we are in the main block, we can just redefine it for the test
    get_video_duration = mock_get_duration

    # 3. Define music properties
    music_len = 180.0  # 3 minutes
    # 120 BPM = 2 beats/sec
    beats = np.arange(0, music_len, 0.5)
    prog = ['intro', 'main', 'outro']

    # 4. Run the director
    edit_list = create_edit_list(dummy_clips, beats, music_len, prog)

    # 5. Verify the output
    print(f"Generated an edit list with {len(edit_list)} cuts.")
    total_duration = sum(duration for _, _, duration in edit_list)
    print(f"Total duration of cuts: {total_duration:.2f}s")
    print(f"Target music duration: {music_len:.2f}s")

    assert abs(total_duration - music_len) < 1.0, "Total duration should be close to music length"
    print("\nFirst 5 cuts:")
    for path, start, dur in edit_list[:5]:
        print(f" - Clip: {os.path.basename(path)}, Start: {start:.2f}s, Duration: {dur:.2f}s")

    # Restore for other potential imports
    get_video_duration = original_get_duration
    print("\nDirector test successful!")