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
import shutil
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
        self.root.title("Camera Roll Cleaner")
        self.root.geometry("1100x800")
        self.root.configure(bg='#0a0a0a')
        self.root.minsize(800, 600)

        self.folder_path = ""
        self.image_files = []
        self.current_index = -1
        self.config_file = os.path.join(os.path.expanduser('~'), '.sorter_config')

        # Modern color palette
        self.colors = {
            'bg': '#0a0a0a',
            'surface': '#141414',
            'surface_light': '#1e1e1e',
            'accent': '#3b82f6',
            'accent_hover': '#2563eb',
            'text_primary': '#ffffff',
            'text_secondary': '#a3a3a3',
            'border': '#262626',
            'danger': '#ef4444',
            'danger_hover': '#dc2626'
        }

        # --- UI Elements ---
        # Main container with padding
        main_frame = tk.Frame(root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)

        # Header section
        header_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 30))

        # App title
        title_label = tk.Label(
            header_frame,
            text="Camera Roll Cleaner",
            bg=self.colors['bg'],
            fg=self.colors['text_primary'],
            font=('SF Pro Display', 28, 'bold')
        )
        title_label.pack(side=tk.LEFT)

        # Action buttons container
        button_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        button_frame.pack(side=tk.RIGHT)

        # Select folder button
        self.open_button = tk.Button(
            button_frame,
            text="Select Folder",
            command=self.select_folder,
            bg=self.colors['accent'],
            fg=self.colors['text_primary'],
            font=('SF Pro Text', 13, 'bold'),
            relief=tk.FLAT,
            borderwidth=0,
            padx=24,
            pady=12,
            cursor='hand2',
            activebackground=self.colors['accent_hover'],
            activeforeground=self.colors['text_primary']
        )
        self.open_button.pack(side=tk.LEFT, padx=5)
        self._add_hover_effect(self.open_button, self.colors['accent'], self.colors['accent_hover'])

        # Image container with rounded effect
        self.image_container = tk.Frame(main_frame, bg=self.colors['surface'], highlightthickness=1,
                                   highlightbackground=self.colors['border'])
        self.image_container.pack(pady=(0, 20), fill=tk.BOTH, expand=True)

        # Image display label
        self.image_label = tk.Label(self.image_container, bg=self.colors['surface'])
        self.image_label.pack(padx=2, pady=2, fill=tk.BOTH, expand=True)

        # File info bar
        info_bar = tk.Frame(main_frame, bg=self.colors['surface_light'], highlightthickness=1,
                           highlightbackground=self.colors['border'])
        info_bar.pack(fill=tk.X, pady=(0, 15))

        info_content = tk.Frame(info_bar, bg=self.colors['surface_light'])
        info_content.pack(padx=20, pady=15)

        # File counter
        self.file_counter_label = tk.Label(
            info_content,
            text="",
            bg=self.colors['surface_light'],
            fg=self.colors['text_secondary'],
            font=('SF Pro Text', 12)
        )
        self.file_counter_label.pack(side=tk.LEFT, padx=(0, 30))

        # Filename display
        self.filename_label = tk.Label(
            info_content,
            text="",
            bg=self.colors['surface_light'],
            fg=self.colors['text_primary'],
            font=('SF Mono', 12)
        )
        self.filename_label.pack(side=tk.LEFT)

        # Keyboard shortcuts panel
        shortcuts_frame = tk.Frame(main_frame, bg=self.colors['surface'], highlightthickness=1,
                                   highlightbackground=self.colors['border'])
        shortcuts_frame.pack(fill=tk.X)

        shortcuts_content = tk.Frame(shortcuts_frame, bg=self.colors['surface'])
        shortcuts_content.pack(padx=20, pady=12)

        self.shortcuts_label = tk.Label(
            shortcuts_content,
            text="",
            bg=self.colors['surface'],
            fg=self.colors['text_secondary'],
            font=('SF Pro Text', 11),
            justify=tk.CENTER
        )
        self.shortcuts_label.pack()


        # --- Keyboard Bindings ---
        self.root.bind('<Left>', self.show_prev_image)
        self.root.bind('<Right>', self.show_next_image)
        self.root.bind('<Delete>', self.delete_current_image)
        self.root.bind('<d>', self.delete_current_image)
        self.root.bind('<space>', self.play_video)
        self.root.bind('<f>', self.add_to_favorites)

        # Initial message
        self.show_message("Select a folder to start sorting")

        # Try to load the last used folder on startup
        self.root.after(100, self.load_last_folder) # Use 'after' to let the main window initialize

    def _add_hover_effect(self, button, normal_color, hover_color):
        """Add hover effect to a button."""
        button.bind('<Enter>', lambda _: button.config(bg=hover_color))
        button.bind('<Leave>', lambda _: button.config(bg=normal_color))

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

            # Add modern video overlay badge
            draw = ImageDraw.Draw(image, 'RGBA')

            # Badge dimensions
            badge_width = 320
            badge_height = 70
            margin = 30
            x = margin
            y = margin

            # Draw semi-transparent rounded rectangle background
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rounded_rectangle(
                [(x, y), (x + badge_width, y + badge_height)],
                radius=12,
                fill=(20, 20, 20, 200)
            )
            image = Image.alpha_composite(image.convert('RGBA'), overlay)
            draw = ImageDraw.Draw(image)

            # Add play icon and text
            try:
                font_large = ImageFont.load_default(size=20)
                font_small = ImageFont.load_default(size=14)
            except AttributeError:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Play icon (triangle)
            icon_x = x + 20
            icon_y = y + badge_height // 2
            triangle = [(icon_x, icon_y - 12), (icon_x, icon_y + 12), (icon_x + 16, icon_y)]
            draw.polygon(triangle, fill='#3b82f6')

            # Text
            text_x = icon_x + 30
            draw.text((text_x, y + 14), "VIDEO", fill='white', font=font_large)
            draw.text((text_x, y + 38), "Press Space to play", fill='#a3a3a3', font=font_small)

            return image.convert('RGB')
        return None

    def display_image(self):
        """Load and display the current file's preview."""
        if self.current_index < 0 or self.current_index >= len(self.image_files):
            self.show_message("All files have been deleted or the folder is empty")
            return

        try:
            filename = self.image_files[self.current_index]
            file_path = os.path.join(self.folder_path, filename)
            image = None

            is_video = filename.lower().endswith('.mov')

            # Update file info
            self.file_counter_label.config(text=f"{self.current_index + 1} / {len(self.image_files)}")

            # Show favorite indicator in filename
            if self.is_favorited(filename):
                self.filename_label.config(text=f"⭐ {filename}")
            else:
                self.filename_label.config(text=filename)

            # Update keyboard shortcuts based on file type
            if is_video:
                shortcuts_text = "← Previous  •  → Next  •  Space Play Video  •  F Toggle Favorite  •  Delete Remove"
            else:
                shortcuts_text = "← Previous  •  → Next  •  F Toggle Favorite  •  Delete Remove"
            self.shortcuts_label.config(text=shortcuts_text)

            if is_video:
                image = self.get_video_thumbnail(file_path)
                if image is None:
                    raise IOError("Could not read first frame of video.")
            else:
                image = Image.open(file_path)
                if image.mode == 'RGBA':
                    image = image.convert('RGB')

            # Get container dimensions (use parent container for stable size)
            container_width = self.image_container.winfo_width()
            container_height = self.image_container.winfo_height()

            # Ensure dimensions are valid
            if container_width <= 1 or container_height <= 1:
                # Use default values on first load
                container_width = 1000
                container_height = 600

            # Calculate aspect ratio preserving size
            img_width, img_height = image.size
            aspect_ratio = img_width / img_height
            container_aspect = container_width / container_height

            if aspect_ratio > container_aspect:
                # Image is wider than container
                new_width = container_width - 20  # Padding
                new_height = int(new_width / aspect_ratio)
            else:
                # Image is taller than container
                new_height = container_height - 20  # Padding
                new_width = int(new_height * aspect_ratio)

            # Resize image with calculated dimensions
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo

            self.root.title(f"Camera Roll Cleaner ({self.current_index + 1}/{len(self.image_files)})")

        except Exception as e:
            error_message = f"Error loading file: {self.image_files[self.current_index]}\n\n{e}"
            self.image_label.config(image=None, text=error_message, fg=self.colors['danger'],
                                   font=('SF Pro Text', 13))
            self.image_label.image = None

    def show_message(self, message):
        """Display a message in the image label area."""
        self.shortcuts_label.config(text="← Previous  •  → Next  •  F Toggle Favorite  •  Delete Remove")
        self.file_counter_label.config(text="")
        self.filename_label.config(text="")
        self.image_label.config(
            image=None,
            text=message,
            fg=self.colors['text_secondary'],
            bg=self.colors['surface'],
            font=('SF Pro Text', 16)
        )
        self.image_label.image = None
        self.root.title("Camera Roll Cleaner")

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

    def is_favorited(self, filename):
        """Check if a file is in the favorites folder."""
        favorites_folder = os.path.join(self.folder_path, "favorites")
        destination_path = os.path.join(favorites_folder, filename)
        return os.path.exists(destination_path)

    def add_to_favorites(self, event=None):
        """Toggle the current file in/out of the favorites subfolder."""
        if self.current_index == -1 or not self.image_files:
            messagebox.showwarning("No File", "There is no file to favorite.")
            return

        filename = self.image_files[self.current_index]
        source_path = os.path.join(self.folder_path, filename)

        # Create favorites subfolder if it doesn't exist
        favorites_folder = os.path.join(self.folder_path, "favorites")
        destination_path = os.path.join(favorites_folder, filename)

        try:
            # Check if already favorited
            if self.is_favorited(filename):
                # Remove from favorites
                os.remove(destination_path)
                print(f"Removed from favorites: {destination_path}")
                self.show_temporary_message("☆ Removed from favorites", 1500)
            else:
                # Add to favorites
                os.makedirs(favorites_folder, exist_ok=True)
                shutil.copy2(source_path, destination_path)
                print(f"Added to favorites: {destination_path}")
                self.show_temporary_message("⭐ Added to favorites!", 1500)

            # Update display to reflect favorite status
            self.update_favorite_indicator()

        except Exception as e:
            messagebox.showerror("Error", f"Could not toggle favorite.\n\n{e}")

    def update_favorite_indicator(self):
        """Update the filename display to show favorite status."""
        if self.current_index == -1 or not self.image_files:
            return

        filename = self.image_files[self.current_index]
        if self.is_favorited(filename):
            self.filename_label.config(text=f"⭐ {filename}")
        else:
            self.filename_label.config(text=filename)

    def show_temporary_message(self, message, duration_ms):
        """Show a temporary overlay message on the image."""
        # Create a semi-transparent overlay
        if hasattr(self.image_label, 'image') and self.image_label.image:
            # Save current image
            saved_image = self.image_label.image

            # Create overlay label
            overlay = tk.Label(
                self.image_label,
                text=message,
                bg=self.colors['accent'],
                fg=self.colors['text_primary'],
                font=('SF Pro Text', 16, 'bold'),
                padx=30,
                pady=15
            )
            overlay.place(relx=0.5, rely=0.5, anchor='center')

            # Remove overlay after duration
            self.root.after(duration_ms, overlay.destroy)

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

