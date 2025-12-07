import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from applications import basicapplib

win = None
im = None
imgf = 0
s = 250

# Create application instance first
self = basicapplib.Application(app_folder="com.example.helloworld")

# Create image preprocessor with correct path
ip = basicapplib.ImagePreprocessor([f"Anim/Try2/{i}.bmp" for i in range(119)], target_height=s, target_width=s)

def onFrameDraw(win2, frameCount):
    global win, im, imgf
    if win is not None and im is not None:
        # Get current frame image
        current_image = ip.getCurrentFrameImage()
        if current_image is not None:
            im.set({"image": current_image})
        ip.advanceFrameCount()
        imgf += 1
        if imgf >= 119:
            # ip.clearAllCaches()
            ip.setFrameCount(0)
            imgf = 0
def oip(imPath,imCompletedCount,imTotalCount):
    win.set(title="Loading ("+str(imCompletedCount+1)+"/"+str(imTotalCount)+")")
def main(session, args=[]):
    print("Hello World application loaded")
    global win, im, s
    win = self.ui(geo=(s,s), clearFrames=False, drawAlways=False)
    win.set(title="Loading...")
    im = win.Image(height=s, width=s)
    #Cache all images for smooth playback
    ip.cacheAllImages(waitForCompletion=True,onImageProcessed=oip)  # Preprocess all images
    print("Images preprocessed")
    win.set(clearFrames=False)
    win.set(drawAlways=True)
    win.set(title="Playing")
    im.set({"image": None})
    win.hookEvent("onFrameStart", onFrameDraw)
self.setScript(kind="main", program=main)