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

class ClipManager:
    """Manages clip usage to ensure variety."""
    def __init__(self, clips):
        self.all_clips = list(clips)
        self.shuffled_clips = []

    def get_clip(self):
        """Gets the next clip, re-shuffling if necessary."""
        if not self.shuffled_clips:
            if not self.all_clips:
                return None
            self.shuffled_clips = random.sample(self.all_clips, len(self.all_clips))
        return self.shuffled_clips.pop()

def create_edit_list(categorized_clips, beat_times, music_duration, progression):
    """
    Creates a chronological list of video clips to be rendered, matching the music duration.
    This version handles empty categories and ensures clip variety.
    """
    if not any(categorized_clips.values()) or not beat_times.any() or music_duration <= 0:
        return []

    edit_list = []

    # Filter out clips with no duration and create ClipManagers
    clip_managers = {}
    valid_categories = []
    for category in progression:
        clips = categorized_clips.get(category, [])
        valid_clips = [p for p in clips if get_video_duration(p) > 0.1]
        if valid_clips:
            clip_managers[category] = ClipManager(valid_clips)
            valid_categories.append(category)

    if not valid_categories:
        print("Error: No valid clips found for any of the categories in the progression.")
        return []

    # Redistribute time only among valid categories
    time_per_stage = music_duration / len(valid_categories)
    current_time = 0.0

    for i, category in enumerate(valid_categories):
        stage_end_time = (i + 1) * time_per_stage
        clip_manager = clip_managers[category]

        stage_beats = [b for b in beat_times if current_time <= b < stage_end_time]
        if not stage_beats:
            stage_beats = [current_time]

        beat_idx = 0
        while current_time < stage_end_time and beat_idx < len(stage_beats):
            clip_path = clip_manager.get_clip()
            if not clip_path:
                print(f"Warning: Ran out of clips for category '{category}' and cannot continue this stage.")
                break

            clip_len = get_video_duration(clip_path)
            start_beat_time = stage_beats[beat_idx]

            # Decide how many beats this shot should last
            shot_beat_length = random.choice([1, 2, 4, 8])
            end_beat_idx = beat_idx + shot_beat_length

            end_beat_time = stage_beats[end_beat_idx] if end_beat_idx < len(stage_beats) else stage_end_time

            duration_to_cut = end_beat_time - start_beat_time
            if start_beat_time + duration_to_cut > stage_end_time:
                duration_to_cut = stage_end_time - start_beat_time

            if duration_to_cut <= 0.1:
                beat_idx += 1
                continue

            max_start_in_clip = max(0, clip_len - duration_to_cut)
            start_in_clip = random.uniform(0, max_start_in_clip)

            edit_list.append((clip_path, start_in_clip, duration_to_cut))

            current_time = start_beat_time + duration_to_cut
            while beat_idx < len(stage_beats) and stage_beats[beat_idx] < current_time:
                beat_idx += 1

    return edit_list


if __name__ == '__main__':
    import numpy as np

    print("--- Testing Director with Improved Logic ---")

    # 1. Create dummy classified clips
    # 'outro' category is intentionally left empty to test time redistribution.
    # 'intro' has few clips to test the ClipManager's non-repeating logic.
    dummy_clips = {
        'intro': ['temp/intro_1.mp4', 'temp/intro_2.mp4'],
        'main': [f'temp/main_{i}.mp4' for i in range(10)],
        'outro': []
    }
    # Create empty files for duration testing
    os.makedirs('temp', exist_ok=True)
    all_dummy_files = [clip for clips in dummy_clips.values() for clip in clips]
    for f in all_dummy_files:
        if not os.path.exists(f):
            open(f, 'a').close()

    # 2. Mock get_video_duration to avoid needing real video files
    original_get_duration = get_video_duration
    def mock_get_duration(path):
        return 10.0 # All clips are 10s long for predictability
    get_video_duration = mock_get_duration

    # 3. Define music properties
    music_len = 120.0  # 2 minutes
    beats = np.arange(0, music_len, 0.5) # 120 BPM
    # Progression includes the empty 'outro' category
    prog = ['intro', 'main', 'outro']

    # 4. Run the director
    edit_list = create_edit_list(dummy_clips, beats, music_len, prog)

    # 5. Verify the output
    print(f"\nGenerated an edit list with {len(edit_list)} cuts.")
    total_duration = sum(duration for _, _, duration in edit_list)
    print(f"Total duration of cuts: {total_duration:.2f}s")
    print(f"Target music duration: {music_len:.2f}s")

    # Test 1: Time redistribution
    # The duration should still be correct even with an empty category.
    assert abs(total_duration - music_len) < 1.0, "Total duration should match music length after redistributing time."
    print("✅ Test 1 Passed: Time redistribution for empty categories is working.")

    # Test 2: Clip variety
    # The first stage ('intro') has 2 clips. The first 2 cuts should use different clips.
    intro_stage_duration = music_len / 2 # Since 'outro' is empty, time is split between 'intro' and 'main'
    intro_cuts = [path for path, _, dur in edit_list if sum(d for _,_,d in edit_list[:edit_list.index((path,_,dur))]) < intro_stage_duration]
    if len(intro_cuts) >= 2:
        assert intro_cuts[0] != intro_cuts[1], "First two clips in a stage should not be the same."
        print("✅ Test 2 Passed: ClipManager prevents immediate clip repetition.")
    else:
        print("ℹ️ Test 2 Skipped: Not enough cuts generated in the intro stage to verify non-repetition.")

    # Restore original function
    get_video_duration = original_get_duration
    print("\nDirector test successful!")