from PIL import Image

def bmp_to_array(bmp_path, char_name):
    # Open the BMP image
    img = Image.open(bmp_path)
    
    # Ensure the image is in black-and-white mode (1-bit per pixel)
    img = img.convert("1")
    
    # Get the pixel data
    pixels = img.load()
    width, height = img.size
    
    # Create the array for the character
    char_array = []
    
    for y in range(height):
        row = ""
        for x in range(width):
            # Add '1' for black pixels and '0' for white pixels
            row += "1" if pixels[x, y] == 0 else "0"
        char_array.append(row)
    
    # Format the result as a dictionary
    result = {
        char_name: char_array
    }
    
    return result

# Example usage
import sys
bmp_path = sys.argv[1]  # Replace with the path to your BMP file
char_name = sys.argv[1]     # Replace with the character name
result = bmp_to_array(bmp_path, char_name)

# Print the result
print(f"{char_name}: [")
for row in result[char_name]:
    print(f'    "{row}",')
print("]")
