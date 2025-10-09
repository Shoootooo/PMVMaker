# How to Compile the Application

This guide provides step-by-step instructions on how to compile the application into a standalone executable file.

## 1. Prerequisites

Before you begin, ensure you have the following software installed on your system:

- **Python**: This project requires Python 3.8 or newer. You can download it from [python.org](https://www.python.org/downloads/).
- **FFmpeg**: This is a crucial dependency for video and audio processing. You can download it from [ffmpeg.org](https://ffmpeg.org/download.html) or install it using a package manager:
    - **Windows (using Chocolatey)**: `choco install ffmpeg`
    - **macOS (using Homebrew)**: `brew install ffmpeg`
    - **Linux (using APT)**: `sudo apt-get update && sudo apt-get install -y ffmpeg`

## 2. Environment Setup

It is highly recommended to use a virtual environment to manage project dependencies.

1.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    ```

2.  **Activate the virtual environment**:
    - **Windows**: `venv\\Scripts\\activate`
    - **macOS/Linux**: `source venv/bin/activate`

3.  **Install dependencies**:
    Install all the required Python packages using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

## 3. Packaging with PyInstaller

We will use `PyInstaller` to bundle the application and its dependencies into a single executable.

1.  **Install PyInstaller**:
    If PyInstaller is not already listed in `requirements.txt`, install it manually:
    ```bash
    pip install pyinstaller
    ```

2.  **Run PyInstaller**:
    From the root directory of the project, run the following command:
    ```bash
    pyinstaller --name "PMV-Generator" --onefile --windowed src/main.py
    ```
    - `--name "PMV-Generator"`: Sets the name of the executable.
    - `--onefile`: Bundles everything into a single executable file.
    - `--windowed`: Prevents a console window from appearing when the application is run.
    - `src/main.py`: This should be the entry point of your application. **Note**: You might need to adjust this path if your main script is located elsewhere.

3.  **Locate the Executable**:
    After the process is complete, you will find the executable inside the `dist` directory.

## Additional Notes

- **Troubleshooting**: If you encounter issues with missing libraries (like the Qt platform plugin on Linux), you may need to install additional system dependencies. For example, on Debian-based systems:
  ```bash
  sudo apt-get install -y libxcb-cursor0
  ```
- **Customizing the Build**: `PyInstaller` offers many options for customization. Refer to the [official documentation](https://pyinstaller.readthedocs.io/en/stable/) for more advanced configurations.