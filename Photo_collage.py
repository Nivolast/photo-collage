import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import math
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk
import time

def read_settings(settings_file="settings.txt"):
    """
    Read settings from a configuration file.
    
    Parameters:
    settings_file (str): Path to the settings file
    
    Returns:
    dict: Dictionary containing the settings
    """
    # Default settings
    settings = {
        "number": "6",
        "photos_directory": "photos",  # Default to a subdirectory called 'photos'
        "width": 1600,
        "height": 900,
        "text": "Years Anniversary",
        "refresh_interval": 5,
        "fullscreen": True  # Added fullscreen setting with default as True
    }
    
    # Try to read settings from file
    try:
        with open(settings_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert numeric values
                        if key in ["width", "height", "refresh_interval"]:
                            settings[key] = int(value)
                        elif key == "fullscreen":
                            settings[key] = value.lower() == "true"
                        else:
                            settings[key] = value
                    except ValueError:
                        print(f"Warning: Ignoring invalid setting line: {line}")
        print(f"Settings loaded from {settings_file}")
    except FileNotFoundError:
        print(f"Settings file {settings_file} not found. Using defaults.")
        # Create a default settings file for future use
        try:
            with open(settings_file, 'w') as f:
                f.write("# Photo Collage Settings\n")
                f.write("# Edit these settings to customize your collage\n\n")
                for key, value in settings.items():
                    f.write(f"{key}={value}\n")
            print(f"Created default settings file: {settings_file}")
        except Exception as e:
            print(f"Error creating default settings file: {e}")
    except Exception as e:
        print(f"Error reading settings: {e}")
    
    return settings

class PhotoCollageApp:
    def __init__(self, root, number, photos_directory, width=1200, height=800, text=None, refresh_interval=5, fullscreen=False):
        """
        Initialize the photo collage application.
        
        Parameters:
        root: Tkinter root window
        number (str): The number to create as a collage
        photos_directory (str): Directory containing photos to use
        width (int): Width of the output image
        height (int): Height of the output image
        text (str): Optional text to add below the number
        refresh_interval (int): Time in seconds between refreshes
        fullscreen (bool): Whether to display in fullscreen mode
        """
        self.root = root
        self.root.title(f"Photo Collage {number} Years Anniversary")
        
        self.number = number
        self.photos_directory = photos_directory
        self.width = width
        self.height = height
        self.text = text
        self.refresh_interval = refresh_interval * 1000  # Convert to milliseconds
        self.fullscreen = fullscreen
        
        # Set fullscreen mode
        if self.fullscreen:
            self.root.attributes('-fullscreen', True)
            # Bind Escape key to exit fullscreen
            self.root.bind("<Escape>", self.toggle_fullscreen)
        
        # Create a frame to hold the image
        self.frame = ttk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a label to display the image
        self.image_label = ttk.Label(self.frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Generate initial collage
        self.update_collage()
        
        # Setup periodic refresh
        self.root.after(self.refresh_interval, self.refresh_collage)
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        return "break"  # Prevents the event from propagating further
    
    def refresh_collage(self):
        """Refresh the collage at regular intervals"""
        self.update_collage()
        self.status_var.set(f"Updated: {time.strftime('%H:%M:%S')} - Regular refresh")
        
        # Schedule next refresh
        self.root.after(self.refresh_interval, self.refresh_collage)
    
    def update_collage(self):
        """Create and display a new photo collage"""
        self.status_var.set("Generating collage...")
        self.root.update()
        
        # Create the collage
        collage = create_number_photo_collage(
            self.number, 
            self.photos_directory, 
            self.width, 
            self.height, 
            self.text,
            return_image=True
        )
        
        # Convert to PhotoImage and display
        self.photo = ImageTk.PhotoImage(collage)
        self.image_label.config(image=self.photo)
        
        self.status_var.set(f"Updated: {time.strftime('%H:%M:%S')}")


def get_cell_size_multiplier(num_images):
    """
    Get the appropriate cell size multiplier based on the number of images.
    
    Parameters:
    num_images (int): Number of images in the directory
    
    Returns:
    float: Cell size multiplier
    """
    # Define the mapping between number of images and cell size multiplier
    # Format: [num_images, multiplier]
    image_to_cell_ratio = [
        [0, 0.04],
        [2, 0.04],
        [8, 0.02],
        [12, 0.02],
        [28, 0.02],
        [52, 0.02],
        [88, 0.02],
        [200, 0.01]
    ]
    
    # If fewer than the minimum images
    if num_images <= image_to_cell_ratio[0][0]:
        return image_to_cell_ratio[0][1]
    
    # If more than the maximum images
    if num_images >= image_to_cell_ratio[-1][0]:
        return image_to_cell_ratio[-1][1]
    
    # Find the appropriate interval and interpolate
    for i in range(len(image_to_cell_ratio) - 1):
        lower_bound = image_to_cell_ratio[i]
        upper_bound = image_to_cell_ratio[i + 1]
        
        if lower_bound[0] <= num_images < upper_bound[0]:
            # Linear interpolation
            ratio = (num_images - lower_bound[0]) / (upper_bound[0] - lower_bound[0])
            multiplier = lower_bound[1] + ratio * (upper_bound[1] - lower_bound[1])
            return multiplier
    
    # Fallback to a default value
    return 0.05


def create_number_photo_collage(number, photos_directory, width=1200, height=800, text=None, return_image=False):
    """
    Create a number-shaped photo collage.
    
    Parameters:
    number (str): The number or text to create as a collage
    photos_directory (str): Directory containing photos to use
    width (int): Width of the output image
    height (int): Height of the output image
    text (str): Optional text to add below the number
    return_image (bool): If True, return the PIL Image object instead of displaying it
    
    Returns:
    PIL.Image.Image: The collage image if return_image is True
    """
    # Create a blank white image
    collage = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(collage)
    
    # Create mask for the number shape
    mask = Image.new('L', (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    
    # Choose a font and size for the number
    try:
        font = ImageFont.truetype("arial.ttf", int(height * 1.0))
    except IOError:
        font = ImageFont.load_default()
    
    # Draw the number as a mask
    if hasattr(font, "getsize"):
        text_width, text_height = font.getsize(number)
    else:
        # For newer Pillow versions
        bbox = font.getbbox(number)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    
    position = ((width - text_width) // 2, (height - text_height) // 2 - int(height * 0.225))
    mask_draw.text(position, number, fill=255, font=font)
    
    # Get list of all photos in the directory
    photo_files = [os.path.join(photos_directory, f) for f in os.listdir(photos_directory) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not photo_files:
        raise ValueError("No photos found in the specified directory")
    
    # Count the number of images
    num_images = len(photo_files)
    
    # Get the cell size multiplier based on the number of images
    cell_size_multiplier = get_cell_size_multiplier(num_images)
    
    # Calculate the cell size for the grid
    cell_size = int(min(width, height) * cell_size_multiplier)
    
    # Print information about cell size adjustment
    print(f"Number of images: {num_images}")
    print(f"Cell size multiplier: {cell_size_multiplier}")
    print(f"Cell size: {cell_size}")
    
    cols = width // cell_size
    rows = height // cell_size
    
    # For each cell in the grid
    for row in range(rows):
        for col in range(cols):
            x = col * cell_size
            y = row * cell_size
            
            # Check if this cell is within the number shape
            points_in_mask = 0
            samples = 5
            for sx in range(samples):
                for sy in range(samples):
                    sample_x = x + (cell_size * sx) // samples
                    sample_y = y + (cell_size * sy) // samples
                    if sample_x < width and sample_y < height:
                        if mask.getpixel((sample_x, sample_y)) > 0:
                            points_in_mask += 1
            
            # If most points are in the mask, place a photo here
            if points_in_mask > (samples * samples) // 2:
                # Choose a random photo
                photo_path = random.choice(photo_files)
                try:
                    photo = Image.open(photo_path)
                    
                    # Resize and crop to fit the cell
                    photo = resize_and_crop_improved(photo, (cell_size, cell_size))
                    
                    # Paste the photo into the collage
                    collage.paste(photo, (x, y))
                except Exception as e:
                    print(f"Error processing {photo_path}: {e}")
    
    # Add text if provided
    if text:
        try:
            text_font = ImageFont.truetype("arial.ttf", int(height * 0.05))
        except IOError:
            text_font = ImageFont.load_default()
        
        # Using the same method for text size calculation    
        if hasattr(text_font, "getsize"):
            text_width, text_height = text_font.getsize(text)
        else:
            # For newer Pillow versions
            bbox = text_font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
        text_position = ((width - text_width) // 2, height - text_height - 75)
        draw.text(text_position, text, fill=(0, 0, 0), font=text_font)
    
    # Save the final collage  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    output_file="6_years_anniversary_collage_16k.png"
    collage.save(output_file)

    if return_image:
        return collage
    else:
        collage.show()
        return None


def resize_and_crop_improved(image, size):
    """
    Improved version that better handles different aspect ratios.
    Resize and crop an image to fit the specified size without leaving empty spaces.
    
    Parameters:
    image (PIL.Image): The input image
    size (tuple): The target size (width, height)
    
    Returns:
    PIL.Image: The resized and cropped image
    """
    # Convert to RGB if image has transparency or is in a different mode
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Calculate aspect ratios
    target_width, target_height = size
    target_ratio = target_width / target_height
    img_width, img_height = image.size
    img_ratio = img_width / img_height
    
    # Determine which dimension to fit
    if img_ratio > target_ratio:
        # Image is wider than the target ratio - fit height and crop width
        scale_factor = target_height / img_height
        new_width = int(img_width * scale_factor)
        new_height = target_height
        resized = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Crop to fit width
        left = (resized.width - target_width) // 2
        right = left + target_width
        top = 0
        bottom = target_height
        cropped = resized.crop((left, top, right, bottom))
    else:
        # Image is taller than the target ratio - fit width and crop height
        scale_factor = target_width / img_width
        new_width = target_width
        new_height = int(img_height * scale_factor)
        resized = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Crop to fit height
        left = 0
        right = target_width
        top = (resized.height - target_height) // 2
        bottom = top + target_height
        cropped = resized.crop((left, top, right, bottom))
    
    return cropped


# Example usage
if __name__ == "__main__":
    # Read settings from file
    settings = read_settings()
    
    # Create Tkinter root
    root = tk.Tk()
    
    # We don't need to manually set window dimensions for fullscreen,
    # but we keep these calculations for non-fullscreen mode
    window_width = settings["width"]
    window_height = settings["height"]  # Add a little extra for the status bar
    
    # Center the window on screen (will be used if not in fullscreen)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    
    # Set window position (this will be used if fullscreen is toggled off)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    # Create the application with settings
    app = PhotoCollageApp(
        root=root,
        number=settings["number"],
        photos_directory=settings["photos_directory"],
        width=settings["width"],
        height=settings["height"]-40,
        text=settings["text"],
        refresh_interval=settings["refresh_interval"],
        fullscreen=settings.get("fullscreen", True)  # Default to True if not specified
    )
    
    # Start the application
    root.mainloop()