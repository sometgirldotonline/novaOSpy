from applications import basicapplib;
win = None
im = None
imgf = 0
def onFrameDraw(win2, frameCount):
    global win, im, imgf
    if win is not None and im is not None:
        # ip.clearPreviousFrames()
        im.set({"bitmap": ip.getCurrentFrameImage()})
        # ip.cacheAheadImages(ahead=20)  # Cache ahead to ensure smooth playback
        ip.advanceFrameCount()
        imgf += 1
        if imgf >= 120:
            # ip.clearAllCaches()
            ip.setFrameCount(0)
            imgf = 0
def main(session, args=[]):
    print("Hello World application loaded")
    global win, im
    win = self.ui(geo=(s,s), clearFrames=True, drawAlways=False)
    im = win.Image(height=s, width=s, path="luke.bmp")
    win.set(title="Loading...")
    # self.preprocessImages([f"anim/Try2/{i}.bmp" for i in range(120)], waitForCompletion=True, height=s, width=s)
    # ip.cacheAheadImages(ahead=20, waitForCompletion=True)  # Preprocess and cache images ahead
    ip.cacheAllImages(waitForCompletion=True)  # Preprocess all images
    print("Images preprocessed")
    win.set(clearFrames=False)
    win.set(drawAlways=True)
    win.set(title="Playing")
    # im.set({"cachedOnly": True})
    win.hookEvent("onFrameStart", onFrameDraw)
import os
s = 250
ip = basicapplib.ImagePreprocessor([f"anim/Try2/{i}.bmp" for i in range(120)], target_height=s, target_width=s)
self = basicapplib.Application(app_folder="com.example.helloworld")
self.setScript(kind="main", program=main)