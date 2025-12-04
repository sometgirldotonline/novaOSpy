import socket
import threading
import time
import numpy as np

# Configuration
HOST = '127.0.0.1'
FRAME_PORT = 6000
WIDTH, HEIGHT = 64, 64
FRAME = None
LASTEVENT = None
stop_event = threading.Event()
t = 0.0

# Event API
def get_event():
    global LASTEVENT
    return LASTEVENT

def clear_event():
    global LASTEVENT
    LASTEVENT = None

# Frame generation
def render_animated_gradient():
    global t
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    x = np.arange(WIDTH)
    y = np.arange(HEIGHT)[:, None]
    frame[:, :, 0] = (x + t) % 256
    frame[:, :, 1] = (y + t) % 256
    frame[:, :, 2] = (x + y + t) % 256
    t += 0.1
    return frame

def generate_frame():
    return np.random.randint(0, 256, (HEIGHT, WIDTH, 3), dtype=np.uint8)

# Frame injection API
def send_frame(frame):
    global FRAME, WIDTH, HEIGHT
    FRAME = frame
    HEIGHT = frame.shape[0]
    WIDTH = frame.shape[1]

# Frame sender thread
def send_frames():
    global FRAME, WIDTH, HEIGHT
    while not stop_event.is_set():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((HOST, FRAME_PORT))
                print("🟢 Connected to C# frame receiver")
                s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)

                frame_count = 0
                last_frame_data = None

                while not stop_event.is_set():
                    try:
                        frame = FRAME
                        if frame is None:
                            time.sleep(0.01)
                            continue

#                        if frame_count > 11 and last_frame_data is not None:
#                            same_pixels_mask = np.all(frame == last_frame_data, axis=-1)
#                            frame = np.where(same_pixels_mask[..., None], 0, frame)

                        last_frame_data = frame.copy()

                        actual_height, actual_width, _ = frame.shape
                        frame_bytes = np.ascontiguousarray(frame).tobytes()
                        size_msg = f"frameSize {actual_width} {actual_height}\n".encode('utf-8')
                        s.sendall(size_msg + frame_bytes)

                        frame_count += 1
                        time.sleep(0.05)
                    except Exception:
                        continue
        except Exception:
            time.sleep(2)

# Command listener
def command_listener(event_handler, host='127.0.0.1', port=6001):
    """
    Listens for commands from the C# client and calls event_handler(command, args).
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    print(f"[Command] Listening for commands on {host}:{port}")

    def handle_client(conn):
        with conn:
            buffer = b""
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.decode("utf-8").strip()
                    if line:
                        parts = line.split()
                        command = parts[0]
                        args = parts[1:]
                        event_handler(command, args)

    def accept_loop():
        while True:
            conn, _ = server.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

    threading.Thread(target=accept_loop, daemon=True).start()

# Example event handler function
def handle_command(command, args):
    global LASTEVENT
    if command == "resolution" and len(args) == 2:
        width, height = map(int, args)
        print(f"[Command] Change resolution to {width}x{height}")
        # TODO: trigger your SDL resize logic here
        # e.g., set a flag or call a function in your main loop
        try:
            LASTEVENT = {"event": "resize", "width": width, "height": width}
            print(f"🔄 New resolution: {width}x{width}")
        except ValueError as e:
            print(f"🔴 Error parsing resolution: {e}")
                                

    elif command == "mouse" and len(args) == 2:
        x, y = map(int, args)
        print(f"[Command] Mouse event at {x},{y}")
    else:
        print(f"[Command] Unknown command: {command} {args}")

# Start sender thread on import
threading.Thread(target=send_frames, daemon=True).start()
print("🟢 SDL sender thread started")

# Start command listener
command_listener(handle_command)
