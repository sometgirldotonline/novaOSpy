import struct, time, sys, json, os
previous_bmps = {}
resized_bmps = {}
def read_bmp_rgb_array(filename, target_width=None, target_height=None, cachedOnly=False):
    # Check if the raw BMP data is cached
    s_overall = time.time()
    cache_key = (filename)
    if cachedOnly:
        # If cachedOnly is True, return None if not found in cache, check filename only
        if cache_key not in previous_bmps:
            print(f"Image {filename} not found in cache.")
            return None
    cache_key = (filename, target_width, target_height)
    if cache_key in resized_bmps:
        return resized_bmps[cache_key]
    # Check if the raw BMP data is already cached for the image without resizing
    s_conv = time.time()
    if filename in previous_bmps:
        return previous_bmps[filename]
    print(filename)
    with open(filename, "rb") as f:
        data = f.read()  # Read the entire file into memory

    # Parse BMP header
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<I", data, 18)[0]
    height = struct.unpack_from("<I", data, 22)[0]
    bpp = struct.unpack_from("<H", data, 28)[0]

    if bpp != 24:
        raise ValueError("Only 24-bit BMPs are supported.")

    # Calculate row size (including padding)
    row_size = (width * 3 + 3) & ~3

    # Extract pixel data
    raw_pixels = [None] * height
    for y in range(height):
        row_start = pixel_offset + y * row_size
        row_end = row_start + width * 3
        row = [
            (data[i + 2], data[i + 1], data[i])  # Convert BGR to RGB
            for i in range(row_start, row_end, 3)
        ]
        raw_pixels[height - y - 1] = row  # Flip vertically

    # Cache the raw image for future conversions
    previous_bmps[filename] = raw_pixels
    print(f"Converted: {time.time() - s_conv}")

    # Skip resize if dimensions match or are not provided
    if not target_width or not target_height or (target_width == width and target_height == height):
        resized_bmps[cache_key] = raw_pixels
        return raw_pixels

    # Resize logic
    resized = []
    s_resize = time.time()
    # If scaling down, we skip pixels
    if target_width < width or target_height < height:
        for y in range(target_height):
            src_y = int(y * height / target_height)
            row = []
            for x in range(target_width):
                src_x = int(x * width / target_width)
                row.append(raw_pixels[src_y][src_x])
            resized.append(row)
    
    else:
        # If scaling up, we interpolate by duplicating pixels via mapping, not manually
        for y in range(target_height):
            src_y = int(y * height / target_height)
            row = []
            for x in range(target_width):
                src_x = int(x * width / target_width)
                row.append(raw_pixels[src_y][src_x])
            resized.append(row)
    print(f"Resized: {time.time() - s_resize}")
    print(f"Overall: {time.time() - s_overall}")

    # Cache the resized image for future requests
    cache_key = (filename, target_width, target_height)
    resized_bmps[cache_key] = resized
    return resized

for img in os.listdir("ImageIn"):
    item_path = os.path.join("ImageIn", img)
    if os.path.isfile(item_path):
        print(f"Processing {img}")
        with open(f"ImageOut/{img.split(".")[0]}.pybmp", "w") as f:
            f.write(f"image = {read_bmp_rgb_array(item_path)}")
        

    
