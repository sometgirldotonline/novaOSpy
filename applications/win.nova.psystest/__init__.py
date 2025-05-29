from applications import basicapplib;
import os
def main(session, args=[]):
    win = self.ui((500,500))
    win.Label().set({"text": "Psys Test"})
    log = win.scrolledtext()
    log2 = win.scrolledtext()
    refreshbtn = win.btn("Refresh")
    def refresh():
        log.set({"text": str(self.getPermissions())})
        log2.set({"text":f"""Type {session.type}
User: {session.user}
Parent: {session.parent}
Parent Type: {session.parent.type}
Parent User: {session.parent.user}"""})
    refresh()
    def reqraise(v):
        session.showAuthPopup(minPriv=int(v))
        refresh()
    refreshbtn.setOnClick(command=refresh)
    requestbtn = win.btn("Request")
    reqRevokebtn = win.btn("Request revoke")
    reqLvLraise = win.btn("Raise Level")
    requestbtn.setOnClick(command=lambda:win.basicAsk("Enter Pn", callback=self.requestPermission))
    reqRevokebtn.setOnClick(command=lambda:win.basicAsk("Enter Pn", callback=self.revokePermission))
    reqLvLraise.setOnClick(command=lambda:win.basicAsk("enter lv from 0-3", callback=reqraise))
self = basicapplib.Application(app_folder=os.path.dirname(os.path.realpath(__file__)))
self.setScript(kind="main", program=main)
