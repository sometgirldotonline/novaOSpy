print("Hello World application loaded")
from applications import basicapplib;
from Libraries.nsys import id
import time, math, time
win = None
im = None
imgf = 0
def onFrameDraw(win2, frameCount):
    global win, im, imgf
    if win is not None and im is not None:
        im.set({"path": f"anim/Try2/{imgf}.bmp"})
        imgf += 1
        if imgf >= 120:  # 50 because we have 50 images from 00 to 49
            imgf = 0
        # win.nUiObject["indexbak"] = "balls"
        # win.nUiObject["cbak"] = "balls"
def main(session, args=[]):
    s = 250
    global win, im
    win = self.ui(geo=(s,s), clearFrames=True, drawAlways=False)
    im = win.Image(height=s, width=s, path="luke.bmp")
    win.set(title="Loading...")
    self.preprocessImages([f"anim/Try2/{i}.bmp" for i in range(120)], waitForCompletion=True, height=s, width=s)
    print("Images preprocessed")
    win.set(clearFrames=False)
    win.set(drawAlways=True)
    win.set(title="Playing")
    im.set({"cachedOnly": True})
    win.hookEvent("onFrameStart", onFrameDraw)
    # txt = win.Label()
import os
self = basicapplib.Application(app_folder=os.path.dirname(os.path.realpath(__file__)))
self.setScript(kind="main", program=main)