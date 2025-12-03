from applications import basicapplib;
from Drivers.surfaceDriverSdlPyg import overlayfb
import time
showRect = False
# Define a function to run every frame
def ofd(win2, framecount):
    global overlayfb, showRect
    # Check if it's time to toggle the variable
    if framecount % 20 == 0:
        showRect = not showRect
    if showRect:
        overlayfb[0:10,0:10] = (255,0,0)
    

def main(session, args=[]):
    win = self.ui(drawAlways=True)
    self.con.write(self.windows)
    win.Label().set({"text": "Authenticated as: "+session.user});
    win.Label().set({"text": "Session type: "+str(session.type)});
    st = time.time()
    self.preprocessImages(["anim/037.bmp"], waitForCompletion=True, height=498, width=498)
    print(time.time() - st)
    win.hookEvent("onFrameStart", ofd)
import os
self = basicapplib.Application(app_folder="win.nova.st")
self.setScript(kind="main", program=main)
