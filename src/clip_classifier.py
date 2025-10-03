import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import cv2
import os
import numpy as np

class ClipClassifier:
    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        """
        Initializes the classifier by loading the CLIP model and processor.
        """
        print("Initializing Clip Classifier...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        try:
            self.model = CLIPModel.from_pretrained(model_name).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(model_name)
            print("CLIP model and processor loaded successfully.")
        except Exception as e:
            print(f"Error loading CLIP model: {e}")
            self.model = None
            self.processor = None

    def _extract_frames(self, video_path, num_frames=5):
        """
        Extracts a specified number of frames evenly spaced throughout a video clip.
        """
        if not os.path.exists(video_path):
            return []

        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames < num_frames:
                frame_indices = np.arange(total_frames)
            else:
                frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

            frames = []
            for i in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(Image.fromarray(frame))
            cap.release()
            return frames
        except Exception as e:
            print(f"Error extracting frames from {video_path}: {e}")
            return []

    def classify_clips(self, clip_paths, text_prompts):
        """
        Classifies a list of video clips based on text prompts.

        Args:
            clip_paths (list): List of paths to the video clips.
            text_prompts (dict): A dictionary where keys are category names and
                                 values are the text prompts for CLIP.

        Returns:
            dict: A dictionary where keys are category names and values are lists
                  of clip paths belonging to that category.
        """
        if not self.model or not self.processor:
            print("Classifier not initialized properly. Aborting classification.")
            return {category: [] for category in text_prompts.keys()}

        categorized_clips = {category: [] for category in text_prompts.keys()}
        prompt_list = list(text_prompts.values())
        category_list = list(text_prompts.keys())

        for i, clip_path in enumerate(clip_paths):
            print(f"Processing clip {i+1}/{len(clip_paths)}: {os.path.basename(clip_path)}")
            frames = self._extract_frames(clip_path)
            if not frames:
                print(f"  -> Could not extract frames. Skipping.")
                continue

            try:
                # Prepare inputs for the model
                inputs = self.processor(
                    text=prompt_list,
                    images=frames,
                    return_tensors="pt",
                    padding=True,
                    truncation=True
                ).to(self.device)

                # Get similarity scores
                with torch.no_grad():
                    outputs = self.model(**inputs)

                # The logits_per_image tensor gives the similarity scores
                # We average the scores across all frames for a more robust classification
                logits_per_image = outputs.logits_per_image
                avg_scores = logits_per_image.mean(dim=0)

                # Find the category with the highest score
                best_match_index = avg_scores.argmax().item()
                best_category = category_list[best_match_index]

                print(f"  -> Classified as: {best_category}")
                categorized_clips[best_category].append(clip_path)

            except Exception as e:
                print(f"  -> Error during classification: {e}")
                continue

        return categorized_clips

if __name__ == '__main__':
    import ffmpeg

    def _create_test_video(path, color):
        """Creates a simple, short video of a single color."""
        if os.path.exists(path):
            os.remove(path)
        (
            ffmpeg
            .input(f'color=c={color}:s=128x128:r=15', f='lavfi', t=2)
            .output(path, vcodec='libx264', pix_fmt='yuv420p')
            .run(overwrite_output=True, quiet=True)
        )
        print(f"Created test video: {path}")

    print("--- Testing Clip Classifier ---")

    # 1. Create dummy clips
    clip1_path = "temp/test_clip_red.mp4"
    clip2_path = "temp/test_clip_blue.mp4"
    _create_test_video(clip1_path, "red")
    _create_test_video(clip2_path, "blue")

    # 2. Define prompts
    prompts = {
        "red_things": "a vibrant red screen",
        "blue_things": "a deep blue screen",
        "other": "a picture of a cat"
    }

    # 3. Initialize classifier and run classification
    # This will download the model on the first run
    classifier = ClipClassifier()
    if classifier.model:
        results = classifier.classify_clips([clip1_path, clip2_path], prompts)

        print("\n--- Classification Results ---")
        for category, clips in results.items():
            print(f"Category '{category}':")
            if clips:
                for clip in clips:
                    print(f"  - {os.path.basename(clip)}")
            else:
                print("  - None")
    else:
        print("\nCould not run classification due to model loading failure.")