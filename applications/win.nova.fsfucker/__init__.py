from applications import basicapplib;
def main(session, args=[]):
    fs = self.fs()
    if(type(fs) == PermissionError):
        if(fs.args[0].get("permGranted") == False):
            print("yae")
            self.requestPermission("novaos.FileSystem", ["READ"])
    else:
        print("oh fuck me")
    fs = self.fs()
    print(type(fs))
import os
self = basicapplib.Application(app_folder=os.path.dirname(os.path.realpath(__file__)))
self.setScript(kind="main", program=main)
