from applications import basicapplib;
import os
def main(session, args=[]):
    win = self.ui()
    win.Label().set({"text": "Psys Test"})
    log = win.scrolledtext()
    log2 = win.scrolledtext()
    refreshbtn = win.btn("Refresh")
    def refresh():
        log.set({"text": self.getPermissions()})
        log2.set({"text":f"""Type {session.type}
User: {session.user}
Parent: {session.parent}
Parent Type: {session.parent.type}
Parent User: {session.parent.user}"""})
    refresh()
    def reqraise():
        session.showAuthPopup(minPriv=win.basicAskint("enter lv from 0-3"))
        refresh()
    refreshbtn.setOnClick(command=refresh)
    requestbtn = win.btn("Request")
    reqRevokebtn = win.btn("Request revoke")
    reqLvLraise = win.btn("Raise Level")
    requestbtn.setOnClick(command=lambda:self.requestPermission(win.basicAsk("Enter Pn")))
    reqRevokebtn.setOnClick(command=lambda:self.revokePermission(win.basicAsk("Enter Pn")))
    reqLvLraise.setOnClick(command=reqraise)
self = basicapplib.Application(app_folder=os.path.dirname(os.path.realpath(__file__)))
self.setScript(kind="main", program=main)
