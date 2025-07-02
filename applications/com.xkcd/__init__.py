from applications import basicapplib;
import requests;
import subprocess;
def main(session, args=[]):
    win = self.ui(geo=(500,520), title="xkcd Viewer",drawAlways=True, clearFrames=False)
    # Request the latest xkcd comic
    response = requests.get("https://xkcd.com/info.0.json")
    if response.status_code == 200:
        comic_data = response.json()
        comic_title = comic_data['title']
        comic_img_url = comic_data['img']
        win.set(title=f"xkcd #{comic_data['num']}: {comic_title}")
        # Download the comic image
        img_response = requests.get(comic_img_url)
        if img_response.status_code == 200:
            with open("xkcd.bmp", "wb") as f:
                f.write(img_response.content)
            res = subprocess.run(["convert", "xkcd.bmp", "--depth", "24", "-define", "bmp:format=rgb565", "xkcd_565.bmp"])
            print(res)
            win.Image("xkcd_565.bmp", width=490, height=400)
            win.Label(f"{comic_data['alt']}")
            win.set(drawAlways=True, clearFrames=False)
        else:
            win.Label("Failed to load xkcd comic image.")
        # Convert comic image to a 24 Bit RGB 565 BMP Image using "convert" command
    else:
        win.Label("Failed to load xkcd comic.")
import os
print(__file__, os.path.dirname(os.path.realpath(__file__)), os.path.realpath(__file__))
self = basicapplib.Application(app_folder="com.xkcd")
self.setScript(kind="main", program=main)
