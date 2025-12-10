# import tkinter.messagebox
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED, as_completed
# import tkinter.scrolledtext
import os, json, Libraries.nsys as nsys, random, string, platform;
from permissions import PermissionSubsystem;
# import threading;
from Libraries.nsys import windows;
import time
from Libraries.nsys import sysUI;
import numpy as np
import struct
import hashlib
# from __main__ import resized_bmps, previous_bmps;
psys = PermissionSubsystem();
global Application;
# Initialize cache dictionaries for raw BMP data and resized images
resizedBmpsCache = {}
wholeBmpsCache = {}
def md5_hash_file(file_path, chunk_size=8192):
    """
    Generate an MD5 hash for a file.

    :param file_path: Path to the file to hash.
    :param chunk_size: Size of chunks to read from the file (default: 8192 bytes).
    :return: MD5 hash of the file as a hexadecimal string.
    """
    # Create an MD5 hash object
    md5 = hashlib.md5()
    
    # Open the file in binary mode and read it in chunks
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    
    # Return the hexadecimal digest
    return md5.hexdigest()
def rgb_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
def rgb565_to_rgb888(rgb565):
    # Extract red, green, and blue components
    r = (rgb565 >> 11) & 0x1F
    g = (rgb565 >> 5) & 0x3F
    b = rgb565 & 0x1F

    # Scale back to 8 bits
    r = (r << 3) | (r >> 2)
    g = (g << 2) | (g >> 4)
    b = (b << 3) | (b >> 2)

    return r, g, b
def read_bmp_rgb_array(filename, target_width=None, target_height=None, cachedOnly=False, imagesObject=None):
    # Check if the raw BMP data is cached
    global resizedBmpsCache, wholeBmpsCache
    if filename is None or not os.path.exists(filename):
        return np.zeros((target_height, target_width, 3), dtype=np.uint8) if target_width and target_height else np.zeros((100, 100, 3), dtype=np.uint8)
    cache_key = md5_hash_file(filename)
    if cachedOnly:
        # If cachedOnly is True, return None if not found in cache, check filename only
        if cache_key not in wholeBmpsCache:
            print(f"Image {filename} not found in cache.")
            return None
    cache_key = (md5_hash_file(filename), target_width, target_height)
    if cache_key in resizedBmpsCache:
        return resizedBmpsCache[cache_key]
    # Check if the raw BMP data is already cached for the image without resizing
    with open(filename, "rb") as f:
        data = f.read()  # Read the entire file into memory
    if md5_hash_file(filename) in wholeBmpsCache:
        print("Using initial cache")
        raw_pixels = wholeBmpsCache[md5_hash_file(filename)]
        width = len(wholeBmpsCache[md5_hash_file(filename)][0])
        height = len(wholeBmpsCache[md5_hash_file(filename)])
    else:
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
        wholeBmpsCache[md5_hash_file(filename)] = raw_pixels

    # Skip resize if dimensions match or are not provided
    if not target_width or not target_height or (target_width == width and target_height == height):
        # resized_bmps[cache_key] = raw_pixels
        return raw_pixels
    # Resize logic
    resized = []
    for y in range(target_height):
        src_y = int(y * height / target_height)
        row = []
        for x in range(target_width):
            src_x = int(x * width / target_width)
            row.append(raw_pixels[src_y][src_x])
        resized.append(row)


    # Cache the resized image for future requests
    cache_key = (md5_hash_file(filename), target_width, target_height)
    resizedBmpsCache[cache_key] = resized
    return resized

class Application():
    # type is one of "basic" or "scheduled"
    def __new__(cls, app_folder=os.path.dirname(os.path.realpath(__file__)), type="basic"):
        if type not in ["basic", "scheduled"]:
            raise ValueError("Invalid application type. Must be 'basic' or 'scheduled'.")
        cls.type = type
        cls.running = False
        if app_folder is None:
            raise ValueError("app_folder must be provided, there is no way to get the current app folder")
        if not app_folder.startswith("/"):
            app_folder = os.path.join("applications/", app_folder)
        elif app_folder.startswith("#"):
            app_folder = os.path.join(os.getcwd(), app_folder)
        else:
            app_folder = os.path.join(os.getcwd(), app_folder[1:])
        if not os.path.exists(app_folder):
            raise FileNotFoundError(f"'{app_folder}' does not exist.")
        if not os.path.isdir(app_folder):
            raise NotADirectoryError(f"'{app_folder}' is not a directory.")
        if not os.path.exists(os.path.join(app_folder, "meta.json")):
            raise FileNotFoundError(f"meta.json not found in '{app_folder}'.")
        # if path does not start with /, add the current working directory, if we start with a # it means system applications folder
        
        instance = super(Application, cls).__new__(cls)
        instance.folder = app_folder

        # Load metadata from meta.json
        meta_path = os.path.join(app_folder, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as meta_file:
                meta_data = json.load(meta_file)
                instance.name = meta_data.get("name", "")
                instance.description = meta_data.get("description", "")
                instance.package = meta_data.get("id", "")
                instance.version = meta_data.get("version", "")
                instance.developer = meta_data.get("developer", "")
                instance.developer_web = meta_data.get("developer_website", "")
                instance.developer_mail = meta_data.get("developer_email", "")
        else:
            raise FileNotFoundError(f"meta.json not found in {app_folder}")
        instance.running = False
        instance.windows = []
        instance.con = _con(instance)
        instance.sys = _sys(instance)
        instance.power = _power(instance)
        instance.generators = _generators()
        instance.thread = None
        instance.apps = _apps(instance)
        return instance;


    def preprocessImages(self, image_paths, waitForCompletion=False, onComplete=None, height=None, width=None, imagesObject=None, onImageProcessed=None):
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit tasks to the executor
            futures = {
                executor.submit(read_bmp_rgb_array, path, target_width=width, target_height=height, imagesObject=imagesObject): path
                for path in image_paths
            }
            completedImages = 0
            totalImages = len(image_paths)
            # Process tasks as they complete
            if waitForCompletion:
                for future in as_completed(futures):
                    try:
                        result = future.result()  # Ensures the task is complete and raises exceptions if any
                        if onImageProcessed != None:
                            onImageProcessed(image_paths[completedImages], completedImages, totalImages)
                        completedImages+=1;
                    except Exception as e:
                        print(f"Error processing image {futures[future]}: {e}")
                if onComplete:
                    onComplete()
            else:
                # If not waiting for completion, tasks will run in the background
                pass
    def setScript(self, kind: str, program):
        if(kind == "main"):
            self.program = program;
        elif(kind == "start"):
            self.startScript = program;
        elif(kind == "stop"):
            self.stopScript = program;
    def start(self):
        self.running = True
        if hasattr(self, "startScript"):
            self.startScript(self)
    def stop(self):
        self.running = False
        if hasattr(self, "stopScript"):
            self.stopScript(self)
        if self.thread != None:
            self.thread.terminate()
    def exec(self, session, args):
        global windows
        self.session = session
        global resized_bmps, previous_bmps
        resized_bmps = {}
        previous_bmps = {}
        if hasattr(self, "program") & (self.type == "basic"):
            self.program(session, args)
        elif hasattr(self, "startScript") and self.type == "scheduled":
            # throw an error because scheduled apps are launched differently
            return {"error": "Scheduled apps cannot be launched with exec()", "reason":"ScheduledApp"}
        else:
            return {"error": "No script set for this application", "reason":"NoScript"}
    def exitApp(self):
        global resized_bmps, previous_bmps, windows
        # self.thread.terminate()
        # For every window, unbind any events
        for win in self.windows:
            win.nUiObject = None
            if hasattr(win, "ofsprog"):
                try:
                    win.ofsprog = None
                except Exception as e:
                    nsys.log(f"Error unbinding ofsprog for window {win.title}: {e}")
        self.session.exit()
        
        for win in self.windows:
            windows.__delitem__(win.index)
            self.windows.remove(win)
        if self.type == "basic":
            if nsys.sysState.get() == nsys.sysState.testMode:
                exit()
        elif self.type == "scheduled":
            if hasattr(self, "stopScript"):
                self.stop()
        else:
            raise TypeError("Invalid application type. Must be 'basic' or 'scheduled'.")
        self = None
        del self
    def ui(cls, geo=(200, 200), pos=(0, 0), colour=(220, 220, 220), title="", drawAlways=False, clearFrames=True):
        win = _ui(cls, geo=geo, pos=pos, colour=colour,title=title,drawAlways=drawAlways,clearFrames=clearFrames)
        cls.windows.append(win);
        windows.append(win.updateJSON())
        return win;
    def fs(cls):
        diderror = False
        if not psys.check_permission(cls.package, permission="novaos.FileSystem") in ["READ", "WRITE", "READWRITE"]:
            diderror = True
            return PermissionError({"type": "PermissionError", "permGranted": False, "message": "EPerm, Filesystem Permissions not granted"})
        # if not hasattr(cls, "fs") & (not diderror):
            cls.fs = _fs(cls)
        return _fs(cls);
    def requestPermission(self,permission, data=[]):
        if permission == None:
            raise TypeError("Expected 'String' type not 'None' Type.")
        if tkinter.messagebox.askyesno("Permission Controller",f"Allow {self.name} to use permission: {permission}?"):
            psys.grant_permission(self.package, permission=permission, data=data)
            return True;
        else:
            return False;

    def revokePermission(self,permission, data=[]):
        if permission == None:
            raise TypeError("Expected 'String' type not 'None' Type.")
        if tkinter.messagebox.askyesno("Permission Controller",f"Revoke {self.name} permission: {permission}?"):
            psys.revoke_permission(self.package, permission=permission, data=data)
            return True;
        else:
            return False;
    def getPermissions(self):
        return psys.get_permissions(self.package)
    def checkPermission(self, permission):
        if permission == None:
            raise TypeError("Expected 'String' type not 'None' Type.")
        return psys.check_permission(self.package, permission=permission)
    def getLogs(self):
        return "Not Implemented, track the logs urself dummy"
    def getInfo(self):
            meta_path = os.path.join(self.folder, "meta.json")
            with open(meta_path, "r") as meta_file:
                return json.load(meta_file)
    def checkUpdate(self):
        return "Not Implemented"
    def requestUpdate(self):
        return "Not Implemented"
    def uninstall(self):
        return psys.uninstallApp(self.id)

class ImagePreprocessor():
    def __init__(self, image_paths, target_width=None, target_height=None):
        global resizedBmpsCache, wholeBmpsCache
        self.image_paths = image_paths
        self.target_width = target_width
        self.target_height = target_height
        self.myBitmaps = {}
        self.currentFrame = 0
        print("BMPs Cached to ram: "+str(len(wholeBmpsCache)+len(resizedBmpsCache)))
    def _preprocessor(self, filename, target_width=None, target_height=None, cachedOnly=False, imagesObject=None):
        # Check if the raw BMP data is cached
        #print("Caching "+filename)
        global wholeBmpsCache;
        global resizedBmpsCache;
        resized_bmps = resizedBmpsCache
        previous_bmps = wholeBmpsCache
        cache_key = md5_hash_file(filename)
        if cachedOnly:
            # If cachedOnly is True, return None if not found in cache, check filename only
            if cache_key not in previous_bmps:
                print(f"Image {filename} not found in cache.")
                return None
        if cache_key in previous_bmps:
             return previous_bmps[cache_key]
        cache_key = (md5_hash_file(filename), target_width, target_height)
        if cache_key in resized_bmps:
            return resized_bmps[cache_key]
        # Check if the raw BMP data is already cached for the image without resizing
        with open(filename, "rb") as f:
            data = f.read()  # Read the entire file into memory
        if md5_hash_file(filename) in previous_bmps:
            print("Using initial cache")
            raw_pixels = previous_bmps[md5_hash_file(filename)]
            width = len(previous_bmps[md5_hash_file(filename)][0])
            height = len(previous_bmps[md5_hash_file(filename)])
        else:
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
            wholeBmpsCache[md5_hash_file(filename)] = np.array(raw_pixels)

        # Skip resize if dimensions match or are not provided
        if not target_width or not target_height or (target_width == width and target_height == height):
            # resized_bmps[cache_key] = raw_pixels
            return raw_pixels
        # Resize logic
        resized = []
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
        # Cache the resized image for future requests
        cache_key = (md5_hash_file(filename), target_width, target_height)
        resized_bmps[cache_key] = np.array(resized)
        self.myBitmaps[cache_key] = resized
        return resized

    def clearNFirstImages(self, n):
        # Clear the first n Images from both caches, set to None rather than deleting to keep indexing
        if n < 0 or n > len(self.image_paths):
            raise ValueError("n must be between 0 and the number of images in image_paths.")
        for i in range(n):
            path = self.image_paths[i]
            cache_key = (md5_hash_file(path), self.target_width, self.target_height)
            if cache_key in self.resized_bmps:
                self.resized_bmps[cache_key] = None
            if path in self.previous_bmps:
                self.previous_bmps[path] = None
    def clearPreviousFrames(self):
        # Clear all frames before the current frame, from both caches, set to None rather than deleting to keep indexing
        for i in range(self.currentFrame):
            path = self.image_paths[i]
            cache_key = (md5_hash_file(path), self.target_width, self.target_height)
            if cache_key in self.resized_bmps:
                self.resized_bmps[cache_key] = None
            if path in self.previous_bmps:
                self.previous_bmps[path] = None
    def cacheAheadImages(self, ahead=10, waitForCompletion=False):
        # Cache n images ahead of the current frame
        if self.currentFrame + ahead >= len(self.image_paths):
            ahead = len(self.image_paths) - self.currentFrame - 1
        for i in range(self.currentFrame, self.currentFrame + ahead):
            path = self.image_paths[i]
            executor = ThreadPoolExecutor()
            futures = [executor.submit(self._preprocessor, path, target_width=self.target_width, target_height=self.target_height) for path in self.image_paths]
            if waitForCompletion:
                for future in futures:
                    future.result()  # ensures completion    def cacheOneFrameAhead(self):
        # Cache the next frame image
        if self.currentFrame + 1 < len(self.image_paths):
            path = self.image_paths[self.currentFrame + 1]
            self._preprocessor(path, target_width=self.target_width, target_height=self.target_height)
        else:
            print("No more frames to cache ahead.")

    def cacheFrame(self, frame):
        # Cache a specific frame image
        if frame < len(self.image_paths):
            path = self.image_paths[frame]
            self._preprocessor(path, target_width=self.target_width, target_height=self.target_height)
        else:
            print(f"Frame {frame} is out of range. Total frames: {len(self.image_paths)}")
    
    def clearAllCaches(self):
        # Clear both caches
        self.resized_bmps = {}
        self.previous_bmps = {}
        print("All caches cleared.")
    
    def cacheAllImages(self, waitForCompletion=False, onImageProcessed=None, onComplete=None):
        # Cache all images in the image_paths list
        image_paths = self.image_paths
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit tasks to the executor
            futures = {
                executor.submit(self._preprocessor, path, target_width=self.target_width, target_height=self.target_height): path
                for path in image_paths
            }
            completedImages = 0
            totalImages = len(image_paths)
            # Process tasks as they complete
            if waitForCompletion:
                for future in as_completed(futures):
                    try:
                        result = future.result()  # Ensures the task is complete and raises exceptions if any
                        if onImageProcessed:
                            onImageProcessed(image_paths[completedImages], completedImages, totalImages)
                        completedImages+=1;
                    except Exception as e:
                        print(f"Error processing image {futures[future]}: {e}")
                if onComplete:
                    onComplete()
            else:
                # If not waiting for completion, tasks will run in the background
                pass
            global resizedBmpsCache, wholeBmpsCache
            print(len(resizedBmpsCache))
            print(len(wholeBmpsCache))
            print(len(self.myBitmaps))

    def advanceFrameCount(self):
        # Increment the current frame count
        if self.currentFrame < len(self.image_paths) - 1:
            self.currentFrame += 1
        else:
            print("Already at the last frame.")
    def setFrameCount(self, frame):
        # Set the current frame count to a specific value
        if 0 <= frame < len(self.image_paths):
            self.currentFrame = frame
            print(f"Set current frame to {self.currentFrame}.")
        else:
            print(f"Frame {frame} is out of range. Total frames: {len(self.image_paths)}")
    def getCurrentFrameCount(self):
        # Get the current frame count
        return self.currentFrame
    def getCurrentFrameImage(self):
        # Get the image for the current frame from the cache
        if 0 <= self.currentFrame < len(self.image_paths):
            # print(self.resized_bmps.get((self.image_paths[self.currentFrame], self.target_width, self.target_height)))
            # print(self.myBitmaps)
            return self.myBitmaps.get((md5_hash_file(self.image_paths[self.currentFrame]), self.target_width, self.target_height))
        else:
            print("Current frame is out of range.")
            return None
    def getFrameImage(self, frame):
        # Get the image for a specific frame from the cache
        if 0 <= frame < len(self.image_paths):
            return self.myBitmaps.get((self.image_paths[frame], self.target_width, self.target_height))

class _generators:
    def num(min, max):
        return random.randrange(min, max, 2);
    def str(len):
       return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(len)) 

class _apps:
    def __new__(cls,parent):
        global psys;
        inst = super(_apps, cls).__new__(cls)
        inst.parent = parent;
        return inst;
    def listApplications(self):
        return psys.list_applications()
un = platform.uname();
class _sys:
    def __new__(cls, parent):
        inst = super(_sys, cls).__new__(cls)
        inst.parent = parent;
        return inst;
    platform = {
            "string": f'{un.system} {un.node} {un.release} {un.version} {un.machine}',
            "hostplatform": un.system,
            "architecture": un.machine,
        }
    def getSystemStateInt(cls):
        return nsys.sysState.get()
class _fs:
    def __new__(cls, parent):
        inst = super(_fs, cls).__new__(cls)
        inst.parent = parent;
        return inst;
    def list(self, path):
        return os.listdir(path)
    # write and reads should support both text and binary files
    def write(self, path, data, mode="w"):
        with open(path, mode) as f:
            f.write(data)
    def read(self, path, mode="r"):
        with open(path, mode) as f:
            return f.read()
    def exists(self, path):
        return os.path.exists(path)
    def createDirectory(self, path):
        try:
            os.mkdir(path)
            return True
        except FileExistsError:
            return False
    def delete(self, path):
        try:
            os.remove(path)
            return True
        except FileNotFoundError:
            return False
    def move(self, src, dst):
        try:
            os.rename(src, dst)
            return True
        except FileNotFoundError:
            return False
    def copy(self, src, dst):
        try:
            import shutil
            shutil.copy(src, dst)
            return True
        except FileNotFoundError:
            return False
    def getFileInfo(self, path):
        try:
            import os.path
            return os.path.getsize(path), os.path.getmtime(path), os.path.getctime(path)
        except FileNotFoundError:
            return None, None, None
class _con:
    def __new__ (cls, parent):
        inst = super(_con, cls).__new__(cls)
        inst.parent = parent;
        return inst;
    def write(cls, text):
        nsys.log(cls.parent.name+": "+str(text))
    def read(cls, prompt):
        return input(cls.parent.name+": "+str(prompt) + "> ")
class _power:
        def __new__ (cls, parent):
            inst = super(_power, cls).__new__(cls)
            inst.parent = parent;
            return inst;
        def poweroff(cls):
            # Display prompt asking user if they want to power down
            if tkinter.messagebox.askyesno("Dialog for: "+str(cls.parent.name), str(cls.parent.name) + " would like to turn off the device. Would you like to continue?"):
                print("Exiting.")
                nsys.pwrmgr.poweroff()
                return True
            else:
                return False;
        def reboot(cls):
            if tkinter.messagebox.askyesno("Dialog for: "+str(cls.parent.name), str(cls.parent.name) + " would like to reboot the device. Would you like to continue?"):
                print("Rebooting")
                # tkinter.Tk.quit()
                nsys.pwrmgr.reboot()
                return True
            else: 
                return False;
          
def exitAppIfNoWin(app, window):
    app.windows.remove(window)
    print(len(app.windows))
    #windows.remove(window)
    if len(app.windows) == 0:
        app.exitApp()
class _ui:
    def __new__(cls, parent, geo=(200, 200), pos=(0, 0), colour=(220, 220, 220), title="", drawAlways=False, clearFrames=True):
        print("Creating window for: " + parent.package)
        instance = super(_ui, cls).__new__(cls)

        # Set window properties
        instance.title = title if title else parent.package
        instance.geo = geo
        instance.pos = pos
        instance.colour = colour
        instance.components = []
        instance.parent = parent
        instance.dirty = True
        # JSON representation of the window
        instance.nUiObject = {
            "title": instance.title,
            "pos": instance.pos,
            "geo": instance.geo,
            "colour": instance.colour,
            "clearFrames": clearFrames,
            "stamp": time.time(),
            "drawAlways": drawAlways,
            "components": [],
            "onCloseFunc": lambda: exitAppIfNoWin(parent, instance),
            "onFrameStart": instance.onFrameStart,  # Placeholder for onFrameStart event
        }
        def iDoNothing(a,b):
            return
        instance.ofsprog = iDoNothing
        return instance
    # framedraw function
    def set(self, geo=None, pos=None, colour=None, title=None, drawAlways=None, clearFrames=None):
        self.dirty = True
        # Update the window's properties in the JSON
        if geo is not None:
            self.nUiObject["geo"] = geo
        if pos is not None:
            self.nUiObject["pos"] = pos
        if colour is not None:
            self.nUiObject["colour"] = colour
        if title is not None:
            self.nUiObject["title"] = title
        if drawAlways is not None:
            self.nUiObject["drawAlways"] = drawAlways
        if clearFrames is not None:
            self.nUiObject["clearFrames"] = clearFrames
    def onFrameStart(self, fc):
        # if our window (self) has a onFrameStart function, call it
        try:
            self.ofsprog(self, fc)
            self.dirty = True
        except Exception as e:
            nsys.log(f"Error in onFrameStart: {e}")
        # update our window's json (use the stamp to find) in the systems windows array- DO NOT CHANGE THE STAMP, USE UPDATEJSON TO GET THE JSON OBJECT THEN COMMIT IT TO THE SYSTEM's WINDOWS ARRAY
        # Update the window in the global windows list
        if self.dirty:
            for i, win in enumerate(windows):
                if win.get("stamp") == self.nUiObject["stamp"]:
                    windows[i] = self.updateJSON()
            self.dirty = False
    def Label(self, text="Unset Value", size=12, colour=(0, 0, 0)):
        self.dirty = True
        # Add a label component to the JSON
        element_id = len(self.nUiObject["components"])
        self.nUiObject["components"].append({
            "type": "text",
            "text": str(text),
            "pixel_multiplier": size/12,
            "colour": colour
        })

        # Return a template object to allow further updates
        return uiElTemplate(self, element_id)

    def Input(self, value="", size=12, colour=(0, 0, 0), bg=(255, 255, 255), border=(0, 0, 0), geo=(300, 20)):
        self.dirty = True
        # Add an input box component to the JSON
        element_id = len(self.nUiObject["components"])
        self.nUiObject["components"].append({
            "type": "input",
            "value": str(value),
            "size": size,
            "colour": colour,
            "bg": bg,
            "border": border,
            "geo": geo
        })

        # Return a template object to allow further updates
        return uiElTemplate(self, element_id)
    def hookEvent(self, event, callback):
        self.dirty = True
        # first event is onFrameStart
        if event == "onFrameStart":
            # add callback to the windows JSON so it can be called when the frame starts
            self.ofsprog = callback
            # synchronize the callback with the system UI
        print(f"Hooking event '{event}' with callback {callback} for window: {self.parent.package}")

    def Image(self, path="luke.bmp", width=None, height=None, cachedOnly=False):
        self.dirty = True
        element_id = len(self.nUiObject["components"])
        bmparray = None
        if path == "" or path is None:
            # set bmparray to an empty numpy array of the specified height and width with colour (0, 0, 0)
            if height is None or width is None:
                height = 100
                width = 100
            bmparray = np.zeros((height, width, 3), dtype=np.uint8)
        else:
            bmparray = read_bmp_rgb_array(path, width, height, cachedOnly=cachedOnly)
        self.nUiObject["components"].append({
            "type": "image",
            "width": width,
            "height": height,
            "image": bmparray,
            "cachedOnly": cachedOnly,
        })
        return uiElTemplate(self, element_id)

    def scrolledtext(self, text="Unset Value", size=12, colour=(0, 0, 0)):
        self.dirty = True
        # Proxy scrolled text to a label in the JSON
        element_id = len(self.nUiObject["components"])
        self.nUiObject["components"].append({
            "type": "text",  # Proxy as a label
            "text": str(text),
            "size": size,
            "colour": colour
        })

        # Return a template object to allow further updates
        return uiElTemplate(self, element_id)

    def btn(self, text="Unset Value", size=12, colour=(100, 100, 150), bg=(190, 190, 190), border=(0, 0, 0)):
        self.dirty = True
        # Add a button component to the JSON
        element_id = len(self.nUiObject["components"])
        self.nUiObject["components"].append({
            "type": "button",
            "text": str(text),
            "size": size,
            "colour": colour,
            "bg": bg,
            "border": border
        })

        # Return a template object to allow further updates
        return uiElTemplate(self, element_id)

    def updateJSON(self):
        # Return the current JSON representation of the window
        return self.nUiObject

    def basicAsk(cls, prompt="Enter a value:", default_value="", callback=None):
        cls.dirty = True
        # Create a new dialog window in the JSON
        global windows
        dialog_id = len(windows)
        dialog_json = {
            "type": "dialog",
            "title": "Input Dialog",
            "prompt": prompt,
            "value": default_value,
            "geo": (300, 150),  # Default size for the dialog
            "pos": (200, 200),  # Default position for the dialog
            "colour": (250, 250, 250),
            "components": [
                {
                    "type": "text",
                    "text": prompt,
                    "colour": (0, 0, 0)  # Default text colour
                },
                {
                    "type": "input",
                    "value": default_value,
                    "colour": (0, 0, 0),  # Default text colour
                    "geo": (300, 20),
                    "bg": (255, 255, 255),  # Default background colour
                    "border": (0, 0, 0)  # Default border colour
                },
                {
                    "type": "button",
                    "text": "OK",
                    "colour": (100, 100, 150),
                    "bg": (190, 190, 190),
                    "border": (0, 0, 0),
                    "on_click": None  # Placeholder for the button's click event
                }
            ]
        }
        windows.append(dialog_json)

        # Assign the on_click function to the "OK" button
        def runCallback():
            windows.pop(dialog_id, None)
            if callable(callback):
                callback(sysUI[dialog_id]["components"][1]["value"])

        windows[dialog_id]["components"][2]["on_click"] = runCallback
    def messageBox(cls, prompt="Enter a value:", callback=None):
        cls.dirty = True
        # Create a new dialog window in the JSON
        global windows
        dialog_id = len(windows)
        dialog_json = {
            "type": "dialog",
            "title": "Message",
            "prompt": prompt,
            "geo": (300, 150),  # Default size for the dialog
            "pos": (200, 200),  # Default position for the dialog
            "colour": (250, 250, 250),
            "components": [
                {
                    "type": "text",
                    "text": prompt,
                    "colour": (0, 0, 0)  # Default text colour
                },
                {
                    "type": "button",
                    "text": "OK",
                    "colour": (100, 100, 150),
                    "bg": (190, 190, 190),
                    "border": (0, 0, 0),
                    "on_click": None  # Placeholder for the button's click event
                }
            ]
        }
        windows.append(dialog_json)

        # Assign the on_click function to the "OK" button
        def runCallback():
            windows.pop(dialog_id, None)
            if callable(callback):
                callback()

        windows[dialog_id]["components"][2]["on_click"] = runCallback


class uiElTemplate:
    def __init__(self, parent, element_id):
        self.parent = parent
        self.element_id = element_id

    def set(self, parameters):
        self.parent.dirty = True
        # Update the element's properties in the JSON
        for key, value in parameters.items():
            if self.parent.nUiObject["components"][self.element_id]["type"] == "image" and key == "path":
                if value == "" or value is None:
                    arr = np.zeros((self.parent.nUiObject["components"][self.element_id]["height"], self.parent.nUiObject["components"][self.element_id]["width"], 3), dtype=np.uint8)
                    self.parent.nUiObject["components"][self.element_id]["image"] = arr
                else:
                    arr = read_bmp_rgb_array(value, self.parent.nUiObject["components"][self.element_id]["width"], self.parent.nUiObject["components"][self.element_id]["height"], cachedOnly=self.parent.nUiObject["components"][self.element_id].get("cachedOnly", False))
                    if type(arr) != type(None):
                        self.parent.nUiObject["components"][self.element_id]["image"] = arr
            elif self.parent.nUiObject["components"][self.element_id]["type"] == "image" and key == "bitmap":
                if value is not None:
                    self.parent.nUiObject["components"][self.element_id]["image"] = value
            else:
                self.parent.nUiObject["components"][self.element_id][key] = value
        return self

    def get(self, parameter):
        # Retrieve the element's property from the JSON
        return self.parent.nUiObject["components"][self.element_id].get(parameter)
    def setOnClick(self, command):
        self.parent.dirty = True
        self.parent.nUiObject["components"][self.element_id]["on_click"] = command