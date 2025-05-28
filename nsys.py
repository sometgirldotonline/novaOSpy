import sys
args = sys.argv
if __name__ == "__main__":
    print("Do not run this script! You should run the system python file (__main__.py) instead.")
    sys.exit()
import os, json, tkinter, tkinter.ttk, tkinter.messagebox, tkinter.scrolledtext, traceback, hashlib, importlib, time, platform

global root
root = tkinter.Tk()

def show_error(self, *args):
    log("Error occurred", level=1)
    print(traceback.format_exception(*args))
    try:
        raise args[0](args[1])
    except:
        print(args)
    if sysState.testMode == sysState.get():
        exit()


tkinter.Tk.report_callback_exception = show_error

logwindow = root
logwindow.protocol("WM_DELETE_WINDOW", exit)
logwindow.title("NovaOS Logs")
logwindow.geometry("400x400")
logtext = tkinter.scrolledtext.ScrolledText(logwindow)
logtext.config(state=tkinter.DISABLED)
logtext.pack()
tkinter.ttk.Button(logwindow, text="Exit", command=exit).pack()

_sysStatus = 0
_sysUser = ""
_config = {}

def log(text="", level=0):
    """
    Logs messages based on the logLevel set in config.json.
    Levels:
    0: Notice, 1: Error, 2: Devel, -1: None
    """
    global _config
    logLevel = _config.get("logLevel", 0)
    if logLevel == -1 or level > logLevel:
        return
    logtext.config(state=tkinter.NORMAL)
    logtext.insert(tkinter.INSERT, str(text) + "\n")
    print(text)
    logtext.config(state=tkinter.DISABLED)

class UserNotFoundError(Exception):
    pass

class AuthenticationError(Exception):
    pass

with open("config.json") as _f:
    _config = json.load(_f)

def getsysinfo():
    un = platform.uname()
    return f'{un.system} {un.node} {un.release} {un.version} {un.machine}'

def listapplications():
    applications = []
    for a in next(os.walk('applications'))[1]:
        if not a.startswith("__"):
            applications.append(a)
    return applications

class sysState:
    def get():
        return _sysStatus

    def set(state: int):
        global _sysStatus
        _sysStatus = state
        return _sysStatus

    def Unknown():
        return 0

    def Booting():
        return 1

    def Booted():
        return 2

    def awaitLogin():
        return 3

    def sysAuthenticated():
        return 4
    def poweringDown():
        return 5
    def testMode():
        return 6
    def stateNames():
        return ["Unknown", "Booting", "Booted", "Awaiting Login", "Authenticated", "Powering Down", "TEST MODE"]
    def stateDescriptions():
        return ["State unset.", "Booting", "Booted", "Waiting for first profile to authenticate", "Logged in to " + _sysUser, "A shutdown has been requested.", "TEST MODE. DO NOT USE THIS IN PRODUCTION."]

class Users:
    def list():
        return _config.get("users")

    def getAllNames():
        tempUL = _config.get("users")
        return [*tempUL.keys()]

    def exec(username: str, passhash: str, program, attributes: list = []):
        return 0

    def systemProfileInt():
        return 0

    def adminProfileInt():
        return 1

    def regularProfileInt():
        return 2

    def guestProfileInt():
        return 3

    def profileTypeNames():
        return ["Godmode", "Admin", "Regular", "Guest"]

def refresh():
    try:
        with open("config.json") as _f:
            global _config
            _config = json.load(_f)
        return True
    except:
        return False

def showAuthPopup(cls, minPriv: int = 3, username: str = False, appfolder: str = False):
        loginwindow = tkinter.Tk()
        loginwindow.title("Authentication Required")
        if appfolder:
            tkinter.ttk.Label(loginwindow, text=str(appfolder) + " requested raised session permissions to " + Users.profileTypeNames()[minPriv] + ".\nEnter your credentials to proceed.", font=("TkDefaultFont Bold", "15")).pack()
        else:
            tkinter.ttk.Label(loginwindow, text="Please Log In.", font=("TkDefaultFont Bold", "15")).pack()

        tkinter.ttk.Label(loginwindow, text="Username").pack()
        unamebox = tkinter.Entry(loginwindow)
        if username:
            unamebox.insert(0, username)
        unamebox.pack()
        passbox = tkinter.Entry(loginwindow)
        al = tkinter.Listbox(loginwindow)

        def reloadAL(ev):
            al.delete(0, tkinter.END)
            if unamebox.get() in Users.getAllNames():
                accessLvl = _config.get("users").get(unamebox.get()).get("kind")
                i = 0
                levels = Users.profileTypeNames()
                for l in levels:
                    if i >= accessLvl:
                        al.insert(i, l)
                    i += 1

        unamebox.bind("<KeyRelease>", reloadAL)
        tkinter.ttk.Label(loginwindow, text="Password").pack()
        passbox.pack()
        tkinter.ttk.Label(loginwindow, text="Access Level").pack()
        levels = Users.profileTypeNames()[slice(minPriv + 1)]
        i = 1
        al.selection_set(0)
        for e in levels:
            al.insert(i, e)
            i += 1
        al.pack()

        def handlelogin():
            try:
                uname = unamebox.get()
                passw = hashlib.md5(passbox.get().encode("ascii")).hexdigest()
                try:
                    sestype = Users.profileTypeNames().index(al.get(tkinter.ACTIVE))
                    loginwindow.destroy()
                    loginwindow.quit()
                    cls.Authenticate(username=uname, passhash=passw, sessionType=sestype)
                    log(f"User {cls.user} authenticated with session type {cls.type}", level=0)
                    return cls
                except ValueError:
                    tkinter.messagebox.showerror("Missing value: Access Level", "Pick an Access Level.")
            except Exception as e:
                tkinter.messagebox.showerror("Authentication Error (" + type(e).__name__ + ")", e)
                cls.showAuthPopup(minPriv, username, appfolder)

        tkinter.ttk.Button(loginwindow, text="Authenticate", command=handlelogin).pack()
        loginwindow.mainloop()
        return cls

class Session:
    def __new__(cls):
        instance = super(Session, cls).__new__(cls)
        return instance
    def showAuthPopup(cls, minPriv: int = 3, username: str = False, appfolder: str = False):
        showAuthPopup(cls, minPriv=minPriv, username=username, appfolder=appfolder)
    def Authenticate(instance, username: str, passhash: str, sessionType: int = 3):
        userlist = Users.getAllNames()
        if username in userlist:
            user = _config.get("users").get(username)
            if user.get("pass") == passhash:
                if user.get("kind") <= sessionType:
                    instance.user = username
                    instance.type = sessionType
                    return instance
                else:
                    raise AuthenticationError(f"User {username} is not of required permission level ({sessionType}/{Users.profileTypeNames()[sessionType]}) or higher. User has permission level {user.get('kind')} ({Users.profileTypeNames()[user.get('kind')]})")
            else:
                raise AuthenticationError("Authentication error, please try again (password)")
        else:
            raise UserNotFoundError(f"User {username} not found, please try again (user)")

    def exec(cls, program, appfolder: str, arguments: str = ""):
        print("Executing " + program.__name__ + " with arguments: " + str(arguments))
        if cls.user is None or cls.type is None:
            raise AuthenticationError("Session not authenticated")
        print("Running " + program.__name__ + " with arguments: " + str(arguments) + " and appfolder: " + str(appfolder) + " as user: " + str(cls.user) + " with type: " + str(cls.type))
        try:
            program(cls, arguments)
        except Exception as e:
            if(type(e) == PermissionError):
                print("Running " + program.__name__ + " failed with PermissionError: " + str(e))
                args = json.loads(str(e.args[0]))
                output = (f"{args.get('session').get('appfolder')} exited unexpectedly due to a permission deficiency. "
                        f"You are currently logged in as a {Users.profileTypeNames()[cls.type]} user. "
                        f"The executable requests a {Users.profileTypeNames()[args.get('requiredLevel')]} user at minimum.\n\n"
                        f"The executable said: {args.get('message')}")
                if tkinter.messagebox.askyesno("Permission error!", output):
                    appsession = Session()
                    appsession.showAuthPopup(minPriv=int(args.get("requiredLevel")), username=args.get("session").get("user"), appfolder=args.get("session").get("appfolder"))
                    capp = importlib.import_module("applications." + args.get("session").get("appfolder"), args.get("session").get("appfolder")).self
                    appsession.exec(capp.exec, appfolder=args.get("session").get("appfolder"))
            else:
                # Throw the error to the console like normal
                raise e
        # if program ends in test mode, exit the system


class AppSession:
    def __new__(cls, appfolder, parent):
        instance = super(AppSession, cls).__new__(cls)
        instance.appfolder = appfolder
        instance.parent = parent
        if parent != None:
            instance.user = parent.user
            instance.type = parent.type
        return instance

    def showAuthPopup(self, minPriv: int = 3):
        showAuthPopup(self, minPriv=minPriv, username=self.parent.user, appfolder=self.appfolder)
        

    def Authenticate(self, username: str, passhash: str, sessionType: int = 3):
        userlist = Users.getAllNames()
        if username in userlist:
            user = _config.get("users").get(username)
            if user.get("pass") == passhash:
                if user.get("kind") <= sessionType:
                    self.user = username
                    self.type = sessionType
                    return self
                else:
                    raise AuthenticationError(f"User {username} is not of required permission level ({sessionType}/{Users.profileTypeNames()[sessionType]}) or higher. User has permission level {user.get('kind')} ({Users.profileTypeNames()[user.get('kind')]})")
            else:
                raise AuthenticationError("Authentication error, please try again (password)")
        else:
            raise UserNotFoundError(f"User {username} not found, please try again (user)")

    def exec(cls, arguments: str = ""):
        appfolder = cls.appfolder
        print("Executing " + appfolder + " with arguments: " + str(arguments))
        if cls.user is None or cls.type is None:
            raise AuthenticationError("Session not authenticated")
        print("Running " + appfolder + " with arguments: " + str(arguments) + " and appfolder: " + str(appfolder) + " as user: " + str(cls.user) + " with type: " + str(cls.type))
        try:
            # program({"user": cls.user, "type": cls.type, "appfolder": appfolder}, arguments)
            app_spec = importlib.util.spec_from_file_location(name=appfolder.replace(".",""), location=f"./applications/{appfolder}/__init__.py")
            app_module = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_module)
            app_instance = app_module.self
            app_instance.exec(cls, arguments)
        except PermissionError as e:
            print("Running " + appfolder +  " failed with PermissionError: " + str(e))
            args = json.loads(str(e.args[0]))
            output = (f"{args.get('session').get('appfolder')} exited unexpectedly due to a permission deficiency. "
                      f"You are currently logged in as a {Users.profileTypeNames()[cls.type]} user. "
                      f"The executable requests a {Users.profileTypeNames()[args.get('requiredLevel')]} user at minimum.\n\n"
                      f"The executable said: {args.get('message')}")
            if tkinter.messagebox.askyesno("Permission error!", output):
                showAuthPopup(cls=cls,minPriv=int(args.get("requiredLevel")), username=args.get("session").get("user"), appfolder=args.get("session").get("appfolder"))
                # capp = importlib.import_module("applications." + args.get("session").get("appfolder"), args.get("session").get("appfolder")).self
                # appsession.exec(capp.exec, appfolder=args.get("session").get("appfolder"))


def requestAppPermRaise(args):
    print(args.get("session"))
    output = (f"{args.get('session').appfolder} exited unexpectedly due to a permission deficiency. "
                f"You are currently logged in as a {Users.profileTypeNames()[args.get("session").type]} user. "
                f"The executable requests a {Users.profileTypeNames()[args.get('requiredLevel')]} user at minimum.\n\n"
                f"The executable said: {args.get('message')}")
    if tkinter.messagebox.askyesno("Permission error!", output):
        appsession = AppSession(args.get("session").appfolder, args.get("session"))
        appsession.showAuthPopup(minPriv=int(args.get("requiredLevel")))
        print(args)
        app_id = args.get("session").appfolder
        # app_spec = importlib.util.spec_from_file_location(name=app_id.replace(".",""), location=f"./applications/{app_id}/__init__.py")
        # app_module = importlib.util.module_from_spec(app_spec)
        # app_spec.loader.exec_module(app_module)
        # app_instance = app_module.self
        appsession.exec()
        # appsession.exec(app_instance.exec, appfolder=app_id)
                
def fadeInWin(root):
    try:
        root._animT
    except AttributeError:
        root._animT = 0
        root.lift()
    if root._animT < 0.05:
        root.lift()
    if root._animT < 198:
        root._animT = root._animT + 0.01
        if root._animT < 100:
            root.wm_attributes('-alpha', root._animT)
        root._Tjob = root.after(5, lambda: fadeInWin(root))
    else:
        root.after_cancel(root._animT)

class pwrmgr:
    def poweroff():
        exit()

    def reboot():
        python = sys.executable
        print("Please manually relaunch NovaOS. Auto-Relaunch is not supported in this environment. NOTE FOR IMPLEMENTERS: DO NOT LEAVE THIS NOTE, REPLACE IT WITH THE METHOD OF REBOOTING FOR YOUR PLATFORM")
        exit()