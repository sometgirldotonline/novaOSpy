import pygame
import sdl
import numpy as np
from font_array import charmap as CHARACTER_MAP
from threading import Thread
ls = (0,0)

class SurfaceDriver:
    def __init__(self, width=800, height=600, title="NovaOS BMP SurfaceDriver Window", callback=None):
        """
        Initialise the SurfaceDriver.

        :param width: Width of the window.
        :param height: Height of the window.
        :param title: Title of the window.
        :param callback: A function to update the pixel data.
        """
        pygame.init()
        self.width = width
        self.height = height
        self.title = title
        self.callback = callback

        # Set up the display
        self.screen = pygame.display.set_mode((self.width, self.height),pygame.RESIZABLE)
        pygame.display.set_caption(self.title)

        # Create a numpy array for raw pixel data (RGB format)
        # Fix: pygame expects (width, height, 3) not (height, width, 3)
        self.pixel_data = np.zeros((self.width, self.height, 3), dtype=np.uint8)

        # Running state
        self.running = True

        # Clock for limiting frame rate
        self.clock = pygame.time.Clock()

    def fill_screen(self, colour=(255, 255, 255)):
        """
        Overwrite the entire screen with a specific colour.

        :param colour: A tuple representing the RGB colour (e.g., (255, 0, 0) for red).
        """
        self.pixel_data[:, :] = colour

    def run(self):
        """
        Main loop for the SurfaceDriver.
        """
        global ls
        frame = 0  # Frame counter for animation
        while self.running:
            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False  # Fix: was True, should be False
                    sdl.stop_event.set()  # Signal SDL threads to stop
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    # Always allocate pixel_data as (height, width, 3)
                    pygame.display.update()
                    self.pixel_data = np.zeros((self.width, self.height, 3), dtype=np.uint8)  # Correct NumPy order: (height, width, 3)
                    # If a callback is provided, use it to update the pixel data
                    if self.callback:
                        # Note: we pass width and height in the conventional order (width first, then height)
                        self.callback(self.pixel_data, frame)                # If a callback is provided, use it to update the pixel data

            # Get events from the sdl.py - call only once per loop
            event = sdl.get_event()
            if event is not None:
                print(f"Processing event: {event}")
                
                if event.get("event") == "resize":
                    print("Socket resize event:", event["width"], "x", event["height"])
                    self.width, self.height = event["width"], event["height"]
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    # Fix: correct dimensions for pygame
                    self.pixel_data = np.zeros((self.width, self.height, 3), dtype=np.uint8)
                
                # Clear the event after processing
                sdl.clear_event()
            if ls != (self.width, self.height):
                ls = (self.width, self.height);
            # If a callback is provided, use it to update the pixel data
            if self.callback:
                self.callback(self.pixel_data, frame)


            # Create a surface from the pixel data
            surface = pygame.surfarray.make_surface(self.pixel_data)

            # Blit the surface to the screen and update the display
            self.screen.blit(surface, (0, 0))
            pygame.display.flip()

            # Increment the frame counter
            frame += 1

            # Send the current frame to SDL socket
            # Resize pixel_data to match SDL dimensions if needed
            # if self.pixel_data.shape[:2] != (sdl.HEIGHT, sdl.WIDTH):
            #     # Simple nearest neighbor resize for demonstration
            #     import cv2
            #     resized_frame = cv2.resize(self.pixel_data, (sdl.WIDTH, sdl.HEIGHT))
            #     sdl.send_frame(resized_frame)
            # else:
            Thread(target=sdl.send_frame,args=[self.pixel_data.copy()],daemon=True).start()
            # Limit the frame rate to 60 FPS
            self.clock.tick(60)

        pygame.quit()


def render_animated_gradient(pixel_data, frame):
    """
    Render a gradient that dynamically fills the screen based on the current dimensions of pixel_data.
    """
    # Fix: pygame uses (width, height, 3) format
    width, height, _ = pixel_data.shape

    # Create a more visible gradient pattern
    for x in range(width):
        for y in range(height):
            # Create a more dramatic gradient that's easy to see
            r = int((x / width * 255 + frame) % 256)
            g = int((y / height * 255 + frame) % 256)  
            b = int(((x + y) / (width + height) * 255 + frame) % 256)
            pixel_data[x, y] = (r, g, b)
    
    # Debug: Print some pixel values
    # if frame % 60 == 0:  # Every second at 60fps
    #     print(f"🎨 Gradient sample: pixel_data[10,10] = {pixel_data[10,10] if width > 10 and height > 10 else 'N/A'}")

def draw_hello(pixel_data, frame):
    """
    Draw "Hello" as pixels on the screen, with line wrapping and support for missing characters.
    """
    # Remove this line to preserve previous frame data:
    # pixel_data[:, :] = (50, 50, 50)  # Dark gray background
    
    # Add the animated gradient (this will overwrite the entire frame)
    render_animated_gradient(pixel_data, frame)
    
    # Add some bright test pixels to make sure something is visible
    width, height, _ = pixel_data.shape
    if width > 50 and height > 50:
        # Draw a bright white square in the corner
        pixel_data[10:30, 10:30] = (255, 255, 255)
        # Draw a bright red square
        pixel_data[40:60, 10:30] = (255, 0, 0)
        # Draw a bright green square  
        pixel_data[10:30, 40:60] = (0, 255, 0)
        # Draw a bright blue square
        pixel_data[40:60, 40:60] = (0, 0, 255)

    # Debug output
    # if frame % 60 == 0:
    #     print(f"🖼️  Frame {frame}: Drawing on {width}x{height} canvas")
    #     print(f"🎯 Test squares: white={pixel_data[20,20]}, red={pixel_data[50,20]}")

# Add a new function that only draws on specific areas without clearing
def draw_selective(pixel_data, frame):
    """
    Draw only specific elements without clearing the background.
    """
    width, height, _ = pixel_data.shape
    
    # Only draw moving elements, leaving background intact
    if width > 100 and height > 100:
        # Moving white dot
        dot_x = int((frame * 2) % (width - 20)) + 10
        dot_y = int((frame * 1.5) % (height - 20)) + 10
        
        # Clear previous dot position by restoring gradient
        if frame > 0:
            prev_x = int(((frame - 1) * 2) % (width - 20)) + 10
            prev_y = int(((frame - 1) * 1.5) % (height - 20)) + 10
            for dx in range(-5, 6):
                for dy in range(-5, 6):
                    if 0 <= prev_x + dx < width and 0 <= prev_y + dy < height:
                        # Restore gradient at previous position
                        x, y = prev_x + dx, prev_y + dy
                        r = int((x / width * 255 + frame) % 256)
                        g = int((y / height * 255 + frame) % 256)  
                        b = int(((x + y) / (width + height) * 255 + frame) % 256)
                        pixel_data[x, y] = (r, g, b)
        
        # Draw new dot
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                if dx*dx + dy*dy <= 25 and 0 <= dot_x + dx < width and 0 <= dot_y + dy < height:
                    pixel_data[dot_x + dx, dot_y + dy] = (255, 255, 255)

def draw_hello_no_background(pixel_data, frame):
    """
    Draw without clearing background - preserves previous frame.
    """
    # Don't clear the background - comment out this line:
    # pixel_data[:, :] = (50, 50, 50)  # Dark gray background
    
    # The gradient will still overwrite the entire frame
    render_animated_gradient(pixel_data, frame)
    
    # Add some bright test pixels on top
    width, height, _ = pixel_data.shape
    if width > 50 and height > 50:
        # Draw test squares on top of gradient
        pixel_data[10:30, 10:30] = (255, 255, 255)
        pixel_data[40:60, 10:30] = (255, 0, 0)
        pixel_data[10:30, 40:60] = (0, 255, 0)
        pixel_data[40:60, 40:60] = (0, 0, 255)

# For truly preserving previous frames, use this approach:
def draw_overlay_only(pixel_data, frame):
    """
    Only draw specific overlay elements, preserving background.
    """
    width, height, _ = pixel_data.shape
    
    # Only draw small moving elements without touching the rest
    if width > 100 and height > 100:
        # Animated text position
        text_x = int((frame * 0.5) % (width - 100)) + 50
        text_y = height // 2
        
        # Draw a simple moving text indicator
        for i in range(20):
            for j in range(5):
                if text_x + i < width and text_y + j < height:
                    pixel_data[text_x + i, text_y + j] = (255, 255, 255)

def red_screen(pixel_data, frame):
    """
    Fill the screen with a red colour.
    """
    pixel_data[:, :] = (255, 0, 0)  # Fill with red

# Example usage
if __name__ == "__main__":
    # Use the overlay-only version to preserve previous frames
    driver = SurfaceDriver(width=400, height=300, callback=draw_hello)
    driver.run()