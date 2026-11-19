import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import os
import glob
import numpy as np
from PIL import Image, ImageTk
import threading
import logging
import datetime
import gc
import traceback

# Configure logging to file
logging.basicConfig(filename="panorama.log", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration class to hold application settings
class Config:
    def __init__(self):
        self.input_type = "video"
        self.mode = "PANORAMA"
        self.quality = "low (Orb)"
        self.frame_interval = "10"
        self.projection = "spherical"
        self.focal_ratio = "0.5"
        self.transpose_images = False
        self.clahe_clip_limit = 1.0
        self.clahe_tile_grid_size = 8
        self.start_image = "1"
        self.num_images = "All"
        self.available_images = 0
        self.input_path = None

# InputManager class to handle input selection and image loading
class InputManager:
    def __init__(self, config):
        self.config = config

    def select_input(self):
        if self.config.input_type == "images":
            self.config.input_path = filedialog.askdirectory(title="Select Image Folder")
            if self.config.input_path:
                image_paths = glob.glob(os.path.join(self.config.input_path, "*.jpg")) + glob.glob(os.path.join(self.config.input_path, "*.png"))
                self.config.available_images = len(image_paths)
                logging.info(f"Selected folder: {self.config.input_path} ({self.config.available_images} images)")
        else:
            self.config.input_path = filedialog.askopenfilename(title="Select Video File", 
                                                                filetypes=[("Video files", "*.mp4 *.avi *.mov")])
            if self.config.input_path:
                cap = cv2.VideoCapture(self.config.input_path)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                interval = int(self.config.frame_interval) if self.config.frame_interval.isdigit() else 10
                self.config.available_images = frame_count // interval
                cap.release()
                logging.info(f"Selected video: {self.config.input_path} (~{self.config.available_images} frames)")
        return self.config.input_path

    def load_images(self, max_size=400):
        if self.config.input_type == "images":
            return self._load_folder_images(max_size)
        else:
            return self._extract_video_frames(max_size)

    def _load_folder_images(self, max_size):
        image_paths = sorted(glob.glob(os.path.join(self.config.input_path, "*.jpg")) + 
                             glob.glob(os.path.join(self.config.input_path, "*.png")))
        start_idx = int(self.config.start_image) - 1
        num_images = None if self.config.num_images.lower() == "all" else int(self.config.num_images)
        image_paths = image_paths[start_idx:start_idx+num_images] if num_images is not None else image_paths[start_idx:]
        for path in image_paths:
            img = cv2.imread(path)
            if img is not None:
                yield img

    def _extract_video_frames(self, max_size):
        cap = cv2.VideoCapture(self.config.input_path)
        interval = int(self.config.frame_interval)
        start_idx = int(self.config.start_image)
        num_images = None if self.config.num_images.lower() == "all" else int(self.config.num_images)
        frame_idx = 0
        extracted_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1
            if frame_idx < start_idx:
                continue
            if frame_idx % interval == 0:
                if num_images is not None and extracted_count >= num_images:
                    break
                yield frame
                extracted_count += 1
        cap.release()

# ImageProcessor class for image resizing, warping, and normalization
class ImageProcessor:
    def resize_image(self, img, max_size=400):
        h, w = img.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        return img

    def warp_to_cylindrical(self, image, f):
        h, w = image.shape[:2]
        xcenter, ycenter = w // 2, h // 2
        warped = np.zeros_like(image)
        for y in range(h):
            for x in range(w):
                theta = (x - xcenter) / f
                h_prime = (y - ycenter) / f
                x_new = int(f * np.tan(theta) + xcenter)
                y_new = int(f * h_prime / np.sqrt(np.tan(theta)**2 + 1) + ycenter)
                if 0 <= x_new < w and 0 <= y_new < h:
                    warped[y_new, x_new] = image[y, x]
        return warped

    def normalize_image(self, gray, apply_clahe=True):
        if apply_clahe:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(gray)
        return cv2.equalizeHist(gray)

# Stitcher class for panorama stitching logic
class Stitcher:
    def __init__(self, config):
        self.config = config

    def estimate_focal_length(self, images):
        # Placeholder for focal length estimation
        return float(self.config.focal_ratio) * 1000

    def stitch_images(self, images, is_preview=False):
        processor = ImageProcessor()
        focal_length = self.estimate_focal_length(images)
        processed_images = []
        for img in images:
            img = processor.resize_image(img)
            if self.config.projection == "cylindrical":
                img = processor.warp_to_cylindrical(img, focal_length)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            norm = processor.normalize_image(gray)
            processed_images.append(cv2.cvtColor(norm, cv2.COLOR_GRAY2BGR))
        
        stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
        status, pano = stitcher.stitch(processed_images)
        if status == cv2.Stitcher_OK:
            return pano
        else:
            logging.error(f"Stitching failed with status: {status}")
            return None

# UIManager class for handling the Tkinter UI
class UIManager:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.popup_window = None
        self.popup_canvas = None
        self.popup_photo = None
        self.status_var = tk.StringVar(value="Ready")
        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Input Type:").grid(row=0, column=0, sticky=tk.W)
        input_type = ttk.Combobox(frame, values=["images", "video"], textvariable=tk.StringVar(value=self.config.input_type))
        input_type.grid(row=0, column=1, sticky=tk.W)
        input_type.bind("<<ComboboxSelected>>", lambda e: setattr(self.config, "input_type", input_type.get()))

        ttk.Button(frame, text="Select Input", command=self.root.controller.on_select_input).grid(row=1, column=0, columnspan=2, pady=5)

        ttk.Label(frame, text="Status:").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(frame, textvariable=self.status_var).grid(row=2, column=1, sticky=tk.W)

        ttk.Button(frame, text="Preview", command=self.root.controller.on_start_preview).grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Stitch", command=self.root.controller.on_start_stitching).grid(row=3, column=1, pady=5)
        ttk.Button(frame, text="Save", command=self.root.controller.on_save_pano).grid(row=4, column=0, columnspan=2, pady=5)

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def display_pano(self, pano):
        if self.popup_window and self.popup_window.winfo_exists():
            self.popup_window.destroy()
        
        self.popup_window = tk.Toplevel(self.root)
        self.popup_window.title("Panorama Preview")
        img = Image.fromarray(cv2.cvtColor(pano, cv2.COLOR_BGR2RGB))
        self.popup_photo = ImageTk.PhotoImage(img)
        self.popup_canvas = tk.Canvas(self.popup_window, width=img.width, height=img.height)
        self.popup_canvas.pack()
        self.popup_canvas.create_image(0, 0, anchor=tk.NW, image=self.popup_photo)

    def close_popup(self):
        if self.popup_window and self.popup_window.winfo_exists():
            self.popup_window.destroy()
            self.popup_window = None

# PanoramaController class to coordinate user actions
class PanoramaController:
    def __init__(self, root):
        self.config = Config()
        self.input_manager = InputManager(self.config)
        self.image_processor = ImageProcessor()
        self.stitcher = Stitcher(self.config)
        self.ui_manager = UIManager(root, self.config)
        self.root = root
        self.root.controller = self  # Attach controller to root for button callbacks

    def on_select_input(self):
        if self.input_manager.select_input():
            self.ui_manager.update_status(f"Input selected: {self.config.input_path}")
        else:
            self.ui_manager.update_status("No input selected")

    def on_start_preview(self):
        threading.Thread(target=self._preview_thread, daemon=True).start()

    def _preview_thread(self):
        self.ui_manager.update_status("Generating preview...")
        images = list(self.input_manager.load_images())
        if not images:
            self.ui_manager.update_status("No images loaded")
            return
        pano = self.stitcher.stitch_images(images, is_preview=True)
        if pano is not None:
            self.ui_manager.display_pano(pano)
            self.ui_manager.update_status("Preview ready")
        else:
            self.ui_manager.update_status("Preview failed")

    def on_start_stitching(self):
        threading.Thread(target=self._stitch_thread, daemon=True).start()

    def _stitch_thread(self):
        self.ui_manager.update_status("Stitching panorama...")
        images = list(self.input_manager.load_images())
        if not images:
            self.ui_manager.update_status("No images loaded")
            return
        pano = self.stitcher.stitch_images(images)
        if pano is not None:
            self.ui_manager.display_pano(pano)
            self.ui_manager.update_status("Stitching completed")
        else:
            self.ui_manager.update_status("Stitching failed")

    def on_save_pano(self):
        if not self.ui_manager.popup_canvas:
            messagebox.showwarning("Warning", "No panorama to save!")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg")])
        if file_path:
            pano = self.stitcher.stitch_images(list(self.input_manager.load_images()))
            if pano is not None:
                cv2.imwrite(file_path, pano)
                self.ui_manager.update_status(f"Saved to {file_path}")
            else:
                self.ui_manager.update_status("Save failed")

# Main application entry point
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Panorama Stitcher")
    controller = PanoramaController(root)
    root.mainloop()
