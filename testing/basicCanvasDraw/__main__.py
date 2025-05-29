import pygame
import numpy as np
from font_array import charmap as CHARACTER_MAP

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
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption(self.title)

        # Create a numpy array for raw pixel data (RGB format)
        self.pixel_data = np.zeros((self.height, self.width, 3), dtype=np.uint8)

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
        frame = 0  # Frame counter for animation
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    # Handle window resizing
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.pixel_data = np.zeros((event.w, event.h, 3), dtype=np.uint8)

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

            # Limit the frame rate to 60 FPS
            self.clock.tick(60)

        pygame.quit()


def render_animated_gradient(pixel_data, frame):
    """
    Render a gradient that dynamically fills the screen based on the current dimensions of pixel_data.
    :param pixel_data: The numpy array representing the pixel data.
    :param frame: The current frame number (used for animation).
    """
    height, width, _ = pixel_data.shape  # Correctly extract height (Y) and width (X)

    # Use NumPy's vectorised operations to calculate the gradient
    x = np.arange(width)  # Array of x-coordinates (horizontal axis)
    y = np.arange(height)[:, None]  # Array of y-coordinates (vertical axis, as a column vector)

    # Calculate the gradient for each colour channel
    pixel_data[:, :, 0] = (x + frame) % 256  # Red channel changes with x (horizontal) and frame
    pixel_data[:, :, 1] = (y + frame) % 256  # Green channel changes with y (vertical) and frame
    pixel_data[:, :, 2] = (x + y + frame) % 256  # Blue channel changes with x, y, and frame
def draw_hello(pixel_data, frame):
    """
    Draw "Hello" as pixels on the screen, with line wrapping and support for missing characters.
    """
    # Clear the screen
    pixel_data[:, :] = (0, 0, 0)
    render_animated_gradient(pixel_data=pixel_data, frame=frame)
    # Define the character map
    CHARACTER_MAP1 = {
        'H': [
            "1001",
            "1001",
            "1111",
            "1001",
            "1001",
        ],
        'e': [
            "111",
            "100",
            "111",
            "100",
            "111",
        ],
        'l': [
            "1",
            "1",
            "1",
            "1",
            "1",
        ],
        'o': [
            "1111",
            "1001",
            "1001",
            "1001",
            "1111",
        ],
        ' ': [
            "0",
            "0",
            "0",
            "0",
            "0",
        ],
        'z': [
            "11010",
            "11001",
            "00001",
            "11001",
            "11010",
        ],
        'missing': [
            "11111",
            "10001",
            "10101",
            "10001",
            "11111",
        ]
    }
    CHARACTER_MAP2 = {
        'A': [
            "0100",
            "1010",
            "1110",
            "1010",
            "1010",
        ],
        'B': [
            "1110",
            "1010",
            "1100",
            "1010",
            "1110",
        ],
        'C': [
            "110",
            "100",
            "100",
            "100",
            "110",
        ],
        'D': [
            "1100",
            "1010",
            "1010",
            "1010",
            "1100",
        ],
        'E': [
            "1110",
            "1000",
            "1100",
            "1000",
            "1110",
        ],
        'F': [
            "1110",
            "1000",
            "1100",
            "1000",
            "1000",
        ],
        'G': [
            "1110",
            "1000",
            "1010",
            "1010",
            "1100",
        ],
        'H': [
            "1010",
            "1010",
            "1110",
            "1010",
            "1010",
        ],
        'I': [
            "10",
            "10",
            "10",
            "10",
            "10",
        ],
        'J': [
            "010",
            "010",
            "010",
            "010",
            "100",
        ],
        'K': [
            "1010",
            "1010",
            "1100",
            "1010",
            "1010",
        ],
        'L': [
            "100",
            "100",
            "100",
            "100",
            "110",
        ],
        'M': [
            "11010",
            "10101",
            "10101",
            "10101",
            "10101",
        ],
        'N': [
            "1100",
            "1010",
            "1010",
            "1010",
            "1010",
        ],
        'O': [
            "1110",
            "1010",
            "1010",
            "1010",
            "1110",
        ],
        'P': [
            "1110",
            "1010",
            "1110",
            "1000",
            "1000",
        ],
        'Q': [
            "1110",
            "1010",
            "1010",
            "1010",
            "1010",
            "0100",
        ],
        'R': [
            "1110",
            "1010",
            "1100",
            "1010",
            "1010",
        ],
        'S': [
            "1110",
            "1000",
            "1110",
            "0010",
            "1110",
        ],
        'T': [
            "1110",
            "0100",
            "0100",
            "0100",
            "0100",
        ],
        'U': [
            "1010",
            "1010",
            "1010",
            "1010",
            "1110",
        ],
        'V': [
            "1010",
            "1010",
            "1010",
            "1010",
            "0100",
        ],
        'W': [
            "10101",
            "10101",
            "10101",
            "10101",
            "01010",
        ],
        'X': [
            "1010",
            "1010",
            "0100",
            "1010",
            "1010",
        ],
        'Y': [
            "1010",
            "1010",
            "1010",
            "0100",
            "0100",
        ],
        'Z': [
            "1110",
            "0010",
            "0100",
            "1000",
            "1110",
        ],
        'a': [
            "0110",
            "1010",
            "1010",
            "0110",
        ],
        'b': [
            "1000",
            "1100",
            "1010",
            "1010",
            "1100",
        ],
        'c': [
            "0110",
            "1000",
            "1000",
            "0110",
        ],
        'd': [
            "0010",
            "0110",
            "1010",
            "1010",
            "0110",
        ],
        'e': [
            "0100",
            "1010",
            "1110",
            "1000",
            "0100",
        ],
        'f': [
            "010",
            "100",
            "110",
            "100",
            "100",
        ],
        'g': [
            "0110",
            "1010",
            "1010",
            "0010",
            "1110",
        ],
        'h': [
            "1000",
            "1100",
            "1010",
            "1010",
            "1010",
        ],
        'i': [
            "10",
            "00",
            "10",
            "10",
            "10",
        ],
        'j': [
            "010",
            "000",
            "010",
            "010",
            "010",
            "100",
        ],
        'k': [
            "1000",
            "1010",
            "1100",
            "1010",
            "1010",
        ],
        'l': [
            "10",
            "10",
            "10",
            "10",
            "10",
        ],
        'm': [
            "11010",
            "10101",
            "10101",
            "10101",
        ],
        'n': [
            "1100",
            "1010",
            "1010",
            "1010",
        ],
        'o': [
            "0100",
            "1010",
            "1010",
            "0100",
        ],
        'p': [
            "1100",
            "1010",
            "1010",
            "1100",
            "1000",
        ],
        'q': [
            "0110",
            "1010",
            "1010",
            "0110",
            "0010",
        ],
        'r': [
            "110",
            "100",
            "100",
            "100",
        ],
        's': [
            "1110",
            "1000",
            "0010",
            "1110",
        ],
        't': [
            "100",
            "110",
            "100",
            "100",
            "110",
        ],
        'u': [
            "1010",
            "1010",
            "1010",
            "0110",
        ],
        'v': [
            "1010",
            "1010",
            "1010",
            "0100",
        ],
        'w': [
            "10101",
            "10101",
            "10101",
            "01010",
        ],
        'x': [
            "1010",
            "0100",
            "0100",
            "1010",
        ],
        'y': [
            "1010",
            "1010",
            "1010",
            "0100",
            "1000",
        ],
        'z': [
            "11010",
            "00100",
            "01000",
            "10110",
        ],
        ' ': [
            "0",
            "0",
            "0",
            "0",
            "0",
        ],
    }

    # Text to draw
    pixel_multiplier = 1 # Scale factor for each pixel
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz"
    x, y = 10, 10  # Starting position
    spacing = 2  # Spacing between characters
    colour = (255, 255, 255)  # Colour of the text
    max_char_height = 5
    for char in CHARACTER_MAP:
        if len(char) > max_char_height:
            max_char_height = len(char)*pixel_multiplier
    max_char_height+=max_char_height+5;
    # Starting cursor position
    cursor_x = x
    cursor_y = y

    # Iterate through each character in the text
    for char in text:
        if char in CHARACTER_MAP:
            char_pixels = CHARACTER_MAP[char]
        else:
            char_pixels = CHARACTER_MAP['missing']
        # Check if the character will exceed the screen width
        char_width = len(char_pixels[0]) * pixel_multiplier + spacing * pixel_multiplier
        if cursor_x + char_width > pixel_data.shape[0]:
            # Wrap to the next line
            cursor_x = x
            cursor_y += max_char_height * pixel_multiplier  # Move down by the height of a character

        # Draw the character
        for row_index, row in enumerate(char_pixels):
            for col_index, pixel in enumerate(row):
                if pixel == "1":
                    # Scale the pixel horizontally and vertically
                    for dy in range(pixel_multiplier):
                        for dx in range(pixel_multiplier):
                            # Check boundaries before writing
                            if (
                                cursor_y + row_index * pixel_multiplier + dy < pixel_data.shape[1]
                                and cursor_x + col_index * pixel_multiplier + dx < pixel_data.shape[0]
                            ):
                                pixel_data[
                                    cursor_x + col_index * pixel_multiplier + dx,
                                    cursor_y + row_index * pixel_multiplier + dy,
                                ] = colour

        # Move the cursor to the right for the next character
        cursor_x += len(char_pixels[0]) * pixel_multiplier + spacing * pixel_multiplier
# Example usage
if __name__ == "__main__":
    # Create and run the SurfaceDriver
    driver = SurfaceDriver(callback=draw_hello)
    driver.run()