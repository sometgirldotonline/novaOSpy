from applications import basicapplib;
from Drivers.surfaceDriverSdlPyg import overlayfb
import time
from pathlib import Path
showRect = False
# Define a function to run every frame
def ofd(win2, framecount):
    global overlayfb, showRect
    # Check if it's time to toggle the variable
    if framecount % 20 == 0:
        showRect = not showRect
    if showRect:
        overlayfb[0:10,0:10] = (255,0,0)
    
mdheadings = [
    {
        "fmt": "###",
        "mult": 1.3
    },
        {
        "fmt": "##",
        "mult": 1.5
    },
        {
        "fmt": "#",
        "mult": 1.8
    },
]
    

def main(session, args=[]):
    print(os.path.join(Path(__file__).parent.parent.parent.absolute(), "readme.md"))
    win = self.ui(drawAlways=False, title="Readme", geo=(640,480))
    with open(os.path.join(Path(__file__).parent.parent.parent.absolute(), "readme.md"), 'r') as rdme:
        for line in rdme.readlines():
            multi = 1
            for fmt in mdheadings:
                if line.lstrip().startswith(fmt["fmt"]) and multi == 1:
                    multi = fmt["mult"]
                    line = line.replace(fmt["fmt"],"",1)
                    line = line.replace("<br>","")
            print(f"Printing: {line} with {multi}")
            win.Label(text=line,size=12*multi)
    win.Label().set({"text": "Session type: "+str(session.type)});
import os
self = basicapplib.Application(app_folder="online.sometgirl.readmereader")
self.setScript(kind="main", program=main)
