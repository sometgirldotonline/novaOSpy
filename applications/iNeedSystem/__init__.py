from .. import basicapplib;
def main(session, args=[]):
    if(session.get("type") > 0):
        self.requestLevelRaise(session=session,level=0,message="This app needs System permission (0) or lower, but the authenticated user ("+session.get("user")+") only has permission level "+str(session.get("type")))
    else:
        win = self.ui()
        label = win.Label()
        label.set({"text":"Welcome, you have the correct permissions!"})
self = basicapplib.Application(name="iNeedSystem")
self.setScript(kind="main", program=main)
