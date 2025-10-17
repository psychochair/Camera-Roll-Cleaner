# Camera Roll Cleaner

A simple GUI application for sorting through images and videos in a folder. Quickly preview media files and delete unwanted ones using keyboard shortcuts.

## Features

- Preview images (PNG, JPG, JPEG, GIF, BMP, HEIC)
- Preview videos (MOV) with thumbnails
- Play videos with audio in full-screen window
- Navigate with arrow keys
- Delete files with Delete key or 'd'
- Remembers last used folder

## Installation

### 1. Install System Dependencies

Install ffmpeg for video audio support:

```bash
sudo apt install ffmpeg
```

### 2. Set Up Virtual Environment

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

Install Python packages using pip:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install Pillow pillow-heif opencv-python pygame
```

### 4. Run the Application

```bash
python image_sorter.py
```

Or in VS Code, press **F5** to run with the configured launch button.

## Usage

1. Click "Select Folder" or the app will load the last used folder
2. Navigate through files:
   - **Left Arrow**: Previous file
   - **Right Arrow**: Next file
   - **Delete** or **d**: Delete current file
   - **Spacebar**: Play video (for .mov files)
   - **q**: Quit video playback

## Requirements

- Python 3
- Tkinter (usually included with Python)
- ffmpeg (for video audio extraction)
