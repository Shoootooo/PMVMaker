import ffmpeg
import os

def render_pmv(edit_list, music_path, output_path, music_duration, resolution=(1280, 720), on_progress=None):
    """
    Renders the final PMV by stitching clips together and syncing to the music duration.

    Args:
        edit_list (list): A list of tuples from the director: (clip_path, start, duration).
        music_path (str): Path to the music track.
        output_path (str): The path for the final output video.
        music_duration (float): The exact duration of the music track.
        resolution (tuple): The target video resolution (width, height).
        on_progress (function, optional): Callback for progress updates (0.0 to 1.0).
    """
    if not edit_list:
        print("Error: Edit list is empty. Cannot render video.")
        if on_progress: on_progress(-1.0)
        return

    width, height = resolution
    video_clips = []
    total_edits = len(edit_list)

    # 1. Prepare all video clips from the edit list
    temp_files = []
    for i, (clip_path, start_time, duration) in enumerate(edit_list):
        if not os.path.exists(clip_path):
            print(f"Warning: Clip not found, skipping: {clip_path}")
            continue

        # Create a temporary file for each segment to ensure smooth concatenation
        temp_output_path = os.path.join('temp', f'segment_{i:04d}.ts')
        temp_files.append(temp_output_path)

        try:
            (
                ffmpeg
                .input(clip_path, ss=start_time, t=duration)
                .output(
                    temp_output_path,
                    vf=f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:-1:-1:black,fps=30,format=yuv420p',
                    vcodec='libx264',
                    acodec='aac', # Include dummy audio to keep ffmpeg happy
                    preset='medium',
                    crf=23
                )
                .run(overwrite_output=True, quiet=True)
            )
            video_clips.append(ffmpeg.input(temp_output_path))

        except ffmpeg.Error as e:
            print(f"Error processing segment from {clip_path}: {e.stderr.decode()}")
            continue

        if on_progress:
            # First half of progress is preparing segments
            on_progress((i + 1) / (total_edits * 2))

    if not video_clips:
        print("Error: No valid video clips could be processed.")
        if on_progress: on_progress(-1.0)
        return

    # 2. Concatenate all processed video clips
    # We create a text file with all the temporary segment paths for ffmpeg to concatenate
    concat_file_path = os.path.join('temp', 'concat_list.txt')
    with open(concat_file_path, 'w') as f:
        for path in temp_files:
            if os.path.exists(path):
                f.write(f"file '{os.path.abspath(path)}'\n")

    concatenated_video = ffmpeg.input(concat_file_path, format='concat', safe=0)
    music_stream = ffmpeg.input(music_path).audio

    # 4. Combine video and audio, and trim to music duration
    output_stream = ffmpeg.output(
        concatenated_video,
        music_stream,
        output_path,
        vcodec='libx264',
        acodec='aac',
        t=music_duration,  # Trim output to music duration
        strict='-2' # Needed for some AAC encoder versions
    )

    print(f"Rendering final video to {output_path}...")
    print("FFmpeg command:", ' '.join(output_stream.compile()))

    try:
        if on_progress: on_progress(0.5)

        output_stream.run(overwrite_output=True, quiet=True)

        if on_progress: on_progress(1.0)
        print("Rendering complete!")

    except ffmpeg.Error as e:
        print("Error during final rendering:")
        print(e.stderr.decode())
        if on_progress: on_progress(-1.0)
    finally:
        # Clean up temporary files
        for path in temp_files + [concat_file_path]:
            if os.path.exists(path):
                os.remove(path)

if __name__ == '__main__':
    print("--- Simulating Renderer ---")

    # 1. Create dummy files
    dummy_clip_path = "temp/render_test_clip.mp4"
    dummy_music_path = "temp/render_test_music.wav"

    (
        ffmpeg.input('color=c=blue:s=128x128:r=15', f='lavfi', t=10)
        .output(dummy_clip_path, vcodec='libx264').run(overwrite_output=True, quiet=True)
    )
    (
        ffmpeg.input('anullsrc=r=44100:cl=stereo', f='lavfi', t=5)
        .output(dummy_music_path).run(overwrite_output=True, quiet=True)
    )

    # 2. Create dummy edit list and params
    dummy_edit_list = [
        (dummy_clip_path, 0, 2.5),
        (dummy_clip_path, 5, 3.0), # Total clip duration is 5.5s
    ]
    music_len = 5.0
    output_file = "temp/final_render.mp4"

    def progress_callback(p):
        print(f"Progress: {p*100:.2f}%")

    render_pmv(dummy_edit_list, dummy_music_path, output_file, music_len, on_progress=progress_callback)

    if os.path.exists(output_file):
        print(f"\nRender simulation successful. Output file created at {output_file}")
        # You can check the duration of this file to confirm it is 5s
    else:
        print("\nRender simulation failed.")