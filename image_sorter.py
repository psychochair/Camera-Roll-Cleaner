# Image Sorter for Ubuntu
#
# Description:
# This script creates a graphical application to sort images and videos.
# It previews images and video thumbnails. Press the spacebar to play videos
# in a larger pop-up window.
# Navigate with arrow keys and delete with the Delete key.
# It remembers the last used folder for convenience.
#
# Author: Gemini
#
# Requirements:
# - Python 3
# - Tkinter (usually included with Python)
# - Pillow, pillow-heif, OpenCV, and pygame
#
# How to Install Dependencies:
# Open your terminal and run:
# pip install Pillow pillow-heif opencv-python pygame

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import pillow_heif
import cv2 # OpenCV for video thumbnails and playback
import pygame # For audio playback
import tempfile
import subprocess

# Register the HEIF/HEIC opener with Pillow
pillow_heif.register_heif_opener()

class ImageSorterApp:
    """A simple GUI application for sorting images and videos in a folder."""

    def __init__(self, root):
        """Initialize the application."""
        self.root = root
        self.root.title("File Sorter")
        self.root.geometry("850x700")
        self.root.configure(bg='#2e2e2e')
        self.root.minsize(500, 400)

        self.folder_path = ""
        self.image_files = []
        self.current_index = -1
        self.config_file = os.path.join(os.path.expanduser('~'), '.sorter_config')

        # --- UI Elements ---
        # Main frame
        main_frame = tk.Frame(root, bg='#2e2e2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Top bar for the button
        top_frame = tk.Frame(main_frame, bg='#2e2e2e')
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self.open_button = tk.Button(
            top_frame,
            text="Select Folder",
            command=self.select_folder,
            bg='#4a4a4a',
            fg='white',
            font=('Inter', 12),
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        self.open_button.pack()

        # Image display label
        self.image_label = tk.Label(main_frame, bg='#2e2e2e')
        self.image_label.pack(pady=10, fill=tk.BOTH, expand=True)

        # Bottom frame for instructions
        instructions_frame = tk.Frame(main_frame, bg='#3a3a3a', padx=10, pady=10)
        instructions_frame.pack(fill=tk.X, pady=(10, 0))

        self.instructions_label = tk.Label(
            instructions_frame,
            text="", # Will be set dynamically
            bg='#3a3a3a',
            fg='white',
            font=('Inter', 11)
        )
        self.instructions_label.pack()


        # --- Keyboard Bindings ---
        self.root.bind('<Left>', self.show_prev_image)
        self.root.bind('<Right>', self.show_next_image)
        self.root.bind('<Delete>', self.delete_current_image)
        self.root.bind('<d>', self.delete_current_image)
        self.root.bind('<space>', self.play_video)

        # Initial message
        self.show_message("Select a folder to start sorting.")
        
        # Try to load the last used folder on startup
        self.root.after(100, self.load_last_folder) # Use 'after' to let the main window initialize

    def select_folder(self):
        """Open a dialog to select a folder."""
        path = filedialog.askdirectory(initialdir=self.folder_path or os.path.expanduser('~'))
        if path:
            self.load_images_from_path(path)
            
    def load_images_from_path(self, path):
        """Loads all supported files from a given path."""
        self.folder_path = path
        supported_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.heic', '.mov')
        
        try:
            self.image_files = sorted([
                f for f in os.listdir(path)
                if f.lower().endswith(supported_extensions)
            ])
        except FileNotFoundError:
            self.show_message(f"Error: Folder not found.\n{path}")
            return

        if not self.image_files:
            messagebox.showinfo("No Files Found", "The selected folder contains no supported files.")
            self.current_index = -1
            self.show_message("No supported files found in the selected folder.")
        else:
            self.current_index = 0
            self.display_image()
            self.save_last_folder(path)

    def save_last_folder(self, folder_path):
        """Saves the given folder path to the config file."""
        try:
            with open(self.config_file, 'w') as f:
                f.write(folder_path)
        except IOError as e:
            print(f"Warning: Could not save last folder path: {e}")

    def load_last_folder(self):
        """Loads images from the last used folder if the config file exists."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    last_folder = f.read().strip()
                if last_folder and os.path.isdir(last_folder):
                    self.load_images_from_path(last_folder)
        except IOError as e:
            print(f"Warning: Could not read config file: {e}")

    def get_video_thumbnail(self, video_path):
        """Extracts the first frame from a video file."""
        cap = cv2.VideoCapture(video_path)
        success, frame = cap.read()
        cap.release()
        if success:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame_rgb)
            draw = ImageDraw.Draw(image)
            try:
                font = ImageFont.load_default(size=24)
            except AttributeError:
                 font = ImageFont.load_default()
            draw.text((10, 10), "VIDEO (Press Spacebar to play)", fill="white", font=font,
                      stroke_width=2, stroke_fill="black")
            return image
        return None

    def display_image(self):
        """Load and display the current file's preview."""
        if self.current_index < 0 or self.current_index >= len(self.image_files):
            self.show_message("All files have been deleted or the folder is empty.")
            return

        try:
            filename = self.image_files[self.current_index]
            file_path = os.path.join(self.folder_path, filename)
            image = None
            
            is_video = filename.lower().endswith('.mov')
            
            # Update instructions based on file type
            base_instructions = "← Previous | → Next | [Delete] or [d] Delete File"
            if is_video:
                self.instructions_label.config(text=f"{base_instructions} | [Spacebar] Play Video")
            else:
                self.instructions_label.config(text=base_instructions)

            if is_video:
                image = self.get_video_thumbnail(file_path)
                if image is None:
                    raise IOError("Could not read first frame of video.")
            else:
                image = Image.open(file_path)
                if image.mode == 'RGBA':
                    image = image.convert('RGB')

            self.root.update_idletasks()
            container_width = self.image_label.winfo_width()
            container_height = self.image_label.winfo_height()
            
            if container_width <= 1 or container_height <= 1:
                return

            image.thumbnail((container_width, container_height), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo

            self.root.title(f"File Sorter ({self.current_index + 1}/{len(self.image_files)}) - {filename}")

        except Exception as e:
            error_message = f"Error loading file: {self.image_files[self.current_index]}\n\n{e}"
            self.image_label.config(image=None, text=error_message, fg='red')
            self.image_label.image = None

    def show_message(self, message):
        """Display a message in the image label area."""
        self.instructions_label.config(text="← Previous | → Next | [Delete] or [d] Delete File")
        self.image_label.config(
            image=None,
            text=message,
            fg='white',
            bg='#2e2e2e',
            font=('Inter', 14)
        )
        self.image_label.image = None
        self.root.title("File Sorter")

    def show_next_image(self, event=None):
        """Navigate to the next file."""
        if self.image_files and self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.display_image()

    def show_prev_image(self, event=None):
        """Navigate to the previous file."""
        if self.image_files and self.current_index > 0:
            self.current_index -= 1
            self.display_image()

    def play_video(self, event=None):
        """Play the current video file in a large, new window with audio."""
        if self.current_index == -1 or not self.image_files:
            return

        filename = self.image_files[self.current_index]
        if not filename.lower().endswith('.mov'):
            return

        file_path = os.path.join(self.folder_path, filename)

        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                messagebox.showerror("Playback Error", "Cannot open video file.")
                return

            # Get video FPS for proper timing
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps == 0:
                fps = 30  # Default fallback
            delay = int(1000 / fps)  # milliseconds per frame

            window_name = f"Playing: {filename}"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            # Set a larger default size for the video window
            cv2.resizeWindow(window_name, 1280, 720)

            # Initialize pygame mixer for audio
            audio_temp_file = None
            try:
                pygame.mixer.init()

                # Extract audio to temporary file using ffmpeg
                audio_temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                audio_path = audio_temp_file.name
                audio_temp_file.close()

                # Extract audio with ffmpeg (suppressing output)
                result = subprocess.run(
                    ['ffmpeg', '-i', file_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', '-y', audio_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # Play audio if extraction succeeded
                has_audio = result.returncode == 0 and os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
                if has_audio:
                    pygame.mixer.music.load(audio_path)
                    pygame.mixer.music.play()

            except Exception as audio_error:
                print(f"Warning: Could not load audio: {audio_error}")
                has_audio = False

            # Play video
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break # Video ended

                cv2.imshow(window_name, frame)

                # Exit on 'q' key or if window is closed
                key_pressed = cv2.waitKey(delay) & 0xFF
                if key_pressed == ord('q') or cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break

            # Cleanup
            cap.release()
            cv2.destroyWindow(window_name)

            # Stop audio and cleanup
            if has_audio:
                pygame.mixer.music.stop()
                pygame.mixer.quit()

            # Delete temporary audio file
            if audio_temp_file and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except:
                    pass

        except Exception as e:
            messagebox.showerror("Playback Error", f"An error occurred while playing the video:\n\n{e}")

    def delete_current_image(self, event=None):
        """Delete the currently displayed file."""
        if self.current_index == -1 or not self.image_files:
            messagebox.showwarning("No File", "There is no file to delete.")
            return

        filename = self.image_files[self.current_index]
        image_path = os.path.join(self.folder_path, filename)

        is_sure = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete this file?\n\n{filename}"
        )

        if is_sure:
            try:
                os.remove(image_path)
                print(f"Deleted: {image_path}")
                self.image_files.pop(self.current_index)
                if self.current_index >= len(self.image_files) and self.image_files:
                    self.current_index -= 1
                
                if self.image_files:
                    self.display_image()
                else:
                    self.show_message("Folder is now empty.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete file.\n\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSorterApp(root)
    root.mainloop()

