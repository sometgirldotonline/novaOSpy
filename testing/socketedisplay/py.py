import socket
import threading
import time
import numpy as np
import math
from PIL import Image

HOST = '127.0.0.1'
FRAME_PORT = 6000
BACKCHANNEL_PORT = 6001

WIDTH, HEIGHT = 64, 64
resolution_lock = threading.Lock()  # Add lock for resolution changes

t = 0.0
stop_event = threading.Event()  # Event to signal threads to stop

def render_animated_gradient():
    global t
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    height, width, _ = frame.shape  # Correctly extract height (Y) and width (X)

    # Use NumPy's vectorised operations to calculate the gradient
    x = np.arange(width)  # Array of x-coordinates (horizontal axis)
    y = np.arange(height)[:, None]  # Array of y-coordinates (vertical axis, as a column vector)

    # Calculate the gradient for each colour channel
    frame[:, :, 0] = (x + t) % 256  # Red channel changes with x (horizontal) and frame
    frame[:, :, 1] = (y + t) % 256  # Green channel changes with y (vertical) and frame
    frame[:, :, 2] = (x + y + t) % 256  # Blue channel changes with x, y, and frame
    t += 0.1  # Increment time for animation effect
    return frame


def generate_frameOLD(width, height, t):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            r = int(127 * (1 + math.sin(x * 0.1 + t)))
            g = int(127 * (1 + math.sin(y * 0.1 + t)))
            b = int(127 * (1 + math.sin((x + y) * 0.05 + t)))
            frame[y, x] = (r, g, b)
    return frame, t + 0.1   


def generate_frame():
    # Random RGB frame for testing
    data = np.random.randint(0, 256, (HEIGHT, WIDTH, 3), dtype=np.uint8)
    return data

def send_frames():
    global t
    while not stop_event.is_set():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((HOST, FRAME_PORT))
                print("🟢 Connected to C# frame receiver")

                while not stop_event.is_set():
                    with resolution_lock:  # Ensure consistent resolution during frame generation
                        current_width, current_height = WIDTH, HEIGHT
                        frame = render_animated_gradient()
                    
                    frame_bytes = frame.tobytes()
                    
                    # Send the frame size first
                    size_bytes = f"{current_width} {current_height}\n".encode('utf-8')
                    s.sendall(size_bytes)
                    s.sendall(frame_bytes)
                    
                    print(f"📤 Sending frame: {current_width}x{current_height}, {len(frame_bytes)} bytes")
                    time.sleep(1 / 10)  # 10 FPS for debugging
        except (socket.timeout, ConnectionRefusedError):
            if stop_event.is_set():
                break
            print("🔴 Frame sender error: Retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"🔴 Frame sender error: {e}")
            time.sleep(2)

def listen_backchannel():
    global WIDTH, HEIGHT
    while not stop_event.is_set():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((HOST, BACKCHANNEL_PORT))
                print("🟢 Backchannel connected")
                
                s.settimeout(0.1)
                buffer = ""
                
                while not stop_event.is_set():
                    try:
                        data = s.recv(1024).decode('utf-8')
                        if not data:
                            print("🔴 Backchannel connection closed by server")
                            break
                        
                        buffer += data
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            if line:
                                print(f"💬 From C#: {line}")
                                
                                if line == "exit":
                                    print("🔴 Exiting backchannel listener")
                                    return
                                
                                if line.startswith("NewRes"):
                                    try:
                                        _, width, height = line.split()
                                        new_width, new_height = int(width), int(height)
                                        
                                        with resolution_lock:  # Synchronize resolution change
                                            WIDTH, HEIGHT = new_width, new_height
                                        
                                        print(f"🔄 New resolution: {WIDTH}x{HEIGHT}")
                                        time.sleep(0.1)  # Brief pause to let frame sender catch up
                                    except ValueError as e:
                                        print(f"🔴 Error parsing resolution: {e}")
                                
                                # Send keep-alive response
                                try:
                                    s.send(b"keep-alive\n")
                                except:
                                    break  # Connection lost
                    
                    except socket.timeout:
                        # Send periodic keep-alive
                        try:
                            s.send(b"keep-alive\n")
                        except:
                            break  # Connection lost
                        continue
                    except Exception as e:
                        print(f"🔴 Backchannel read error: {e}")
                        break
                        
        except (socket.timeout, ConnectionRefusedError) as e:
            if stop_event.is_set():
                break
            print(f"🔴 Backchannel connection error: {e}. Retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"🔴 Unexpected backchannel error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    try:
        threading.Thread(target=send_frames, daemon=True).start()
        threading.Thread(target=listen_backchannel, daemon=True).start()
        while not stop_event.is_set():
            time.sleep(0.1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("🔴 Terminating...")
        stop_event.set()