import os
import ffmpeg
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg

def detect_and_split_scenes(video_path, output_dir):
    """
    Detects scenes in a video and splits it into individual clips.

    Args:
        video_path (str): Path to the source video file.
        output_dir (str): Directory to save the scene clips.

    Returns:
        list: A list of paths to the generated scene clips.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return []

    os.makedirs(output_dir, exist_ok=True)

    try:
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector())

        print("Detecting scenes...")
        scene_manager.detect_scenes(video=video, show_progress=True)
        scene_list = scene_manager.get_scene_list()

        print(f"Found {len(scene_list)} scenes.")

        if not scene_list:
            return []

        # The splitter generates filenames like 'video_filename-Scene-001.mp4'
        split_video_ffmpeg(video_path, scene_list, output_dir=output_dir, show_progress=True)

        # Instead of guessing filenames, list the directory to find the created clips.
        created_clips = [
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.endswith('.mp4')
        ]
        return sorted(created_clips)

    except Exception as e:
        print(f"An error occurred during scene detection: {e}")
        return []

def _create_dummy_video(path, duration_sec=10, width=320, height=240, rate=30):
    """Creates a simple dummy video with color changes for scene detection testing."""
    if os.path.exists(path):
        return

    # Create 3 solid color clips and concatenate them
    total_frames = duration_sec * rate
    frames_per_scene = total_frames // 3

    # Scene 1: Red
    (
        ffmpeg
        .input(f'color=c=red:s={width}x{height}:r={rate}', f='lavfi', t=frames_per_scene/rate)
        .output('temp/scene1.mp4', vcodec='libx264', pix_fmt='yuv420p')
        .run(overwrite_output=True, quiet=True)
    )
    # Scene 2: Green
    (
        ffmpeg
        .input(f'color=c=green:s={width}x{height}:r={rate}', f='lavfi', t=frames_per_scene/rate)
        .output('temp/scene2.mp4', vcodec='libx264', pix_fmt='yuv420p')
        .run(overwrite_output=True, quiet=True)
    )
    # Scene 3: Blue
    (
        ffmpeg
        .input(f'color=c=blue:s={width}x{height}:r={rate}', f='lavfi', t=frames_per_scene/rate)
        .output('temp/scene3.mp4', vcodec='libx264', pix_fmt='yuv420p')
        .run(overwrite_output=True, quiet=True)
    )

    # Concatenate
    (
        ffmpeg
        .input('temp/scene1.mp4')
        .concat(ffmpeg.input('temp/scene2.mp4'), ffmpeg.input('temp/scene3.mp4'))
        .output(path, vcodec='libx264', pix_fmt='yuv420p')
        .run(overwrite_output=True, quiet=True)
    )
    print(f"Created dummy video at {path}")

if __name__ == '__main__':
    dummy_video_path = 'temp/test_scene_video.mp4'
    output_directory = 'temp/detected_scenes'

    print("--- Testing Scene Detector ---")
    _create_dummy_video(dummy_video_path)

    print(f"\nRunning detector on: {dummy_video_path}")
    scene_clips = detect_and_split_scenes(dummy_video_path, output_directory)

    if scene_clips:
        print("\nSuccessfully split video into the following clips:")
        for clip in scene_clips:
            print(f" - {clip}")
        # Clean up the large number of created files
        for f in os.listdir(output_directory):
            os.remove(os.path.join(output_directory, f))
        os.rmdir(output_directory)
    else:
        print("\nScene detection failed or found no scenes.")