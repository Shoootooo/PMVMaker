# AI-Powered PMV Generator

This desktop application automatically creates beat-synced PMVs (Porn Music Videos) from a collection of video clips and a music track, using AI for clip classification.

## Features

- **Automatic Scene Detection:** Uses `scenedetect` to break long video files into individual shots.
- **AI-Powered Clip Classification:** Employs a CLIP model to analyze scenes and automatically categorize them based on text prompts (e.g., "kissing," "oral sex").
- **Beat-Synced Editing:** Analyzes a song to find beats and cuts video clips precisely to the rhythm.
- **Music-Length Matching:** The final video is rendered to match the exact duration of the selected song.
- **Progression Logic:** Arranges clips to build intensity, from lighter scenes to a climax.
- **High-Quality Rendering:** Uses `ffmpeg` to produce the final video, preserving aspect ratios.
- **User-Friendly GUI:** A simple interface to select your media and start the process.

## How It Works

1.  **Scene Detection:** The application first scans the source videos and uses `scenedetect` to find the scene boundaries, splitting the original files into many smaller clips.
2.  **Music Analysis:** The app loads your chosen music track and uses `librosa` to detect the beat timestamps and the total song duration.
3.  **AI Classification:** Each scene clip is analyzed by a CLIP model. The model scores the clip against a list of text prompts to determine its category.
4.  **Timeline Generation:** The "Director" module creates an edit list, mapping the AI-categorized clips to the beat timestamps, ensuring the edit list covers the entire duration of the song.
5.  **Rendering:** The "Renderer" module uses `ffmpeg` to cut the required segments from the scene clips and stitch them together with the music into the final PMV.

## Setup

1.  Clone the repository.
2.  Install the required Python packages. It is highly recommended to do this in a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `torch` can be a large download. If you have a CUDA-enabled GPU, you may want to install a specific version of torch that supports it for better performance.*
3.  Ensure you have `ffmpeg` installed on your system and accessible in your PATH.
4.  Run the application:
    ```bash
    python src/main.py
    ```