from applications import basicapplib;
def main(session, args=[]):
    print(session.type)
    print(session.user)
    print(session.parent.type)
    print(session.parent.user)
    if(session.type > 0):
        # self.requestLevelRaise(session=session,level=0,message="This app needs System permission (0) or lower, but the authenticated user ("+session.user+") only has permission level "+str(session.type))
        session.showAuthPopup(minPriv=0)
    else:
        win = self.ui()
        label = win.Label()
        label.set({"text":"Welcome, you have the correct permissions!"})
import os
self = basicapplib.Application(app_folder=os.path.dirname(os.path.realpath(__file__)))

self.setScript(kind="main", program=main)
