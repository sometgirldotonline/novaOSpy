print("Schedule Tester application loaded")
from applications import basicapplib;
def tick(app):
    print("Tick from Schedule Tester")
    
def start(app):
    print("Schedule Tester started")
    
def stop(app):
    print("Schedule Tester stopped")
    
import os
self = basicapplib.Application(app_folder=os.path.dirname(os.path.realpath(__file__)), type="scheduled")
self.setScript(kind="tick", program=tick)
self.setScript(kind="start", program=start)
self.setScript(kind="stop", program=stop)
