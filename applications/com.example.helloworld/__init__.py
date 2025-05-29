print("Hello World application loaded")
from applications import basicapplib;
from Libraries.nsys import id
import time, math
win = None
im = None
imgf = 0
def onFrameDraw(win2, frameCount):
    global win, im, imgf
    if win is not None and im is not None:
        im.set({"path": f"anim/{imgf:03d}.bmp"})
        imgf += 1
        if imgf >= 120:  # 50 because we have 50 images from 00 to 49
            imgf = 0
def main(session, args=[]):
    global win, im
    win = self.ui(geo=(500,500), clearFrames=True, drawAlways=False)
    win.set(title="Loading...")
    self.preprocessImages([f"anim/{i:03d}.bmp" for i in range(120)], waitForCompletion=False)
    print("Images preprocessed")
    win.set(clearFrames=False)
    win.set(drawAlways=True)
    win.set(title="Playing")
    im = win.Image(height=300, width=300, path="")
    im.set({"cachedOnly": True})
    win.hookEvent("onFrameStart", onFrameDraw)
    # txt = win.Label()
import os
self = basicapplib.Application(app_folder=os.path.dirname(os.path.realpath(__file__)))
self.setScript(kind="main", program=main)