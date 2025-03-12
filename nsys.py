import os, json, tkinter, tkinter.ttk, tkinter.messagebox, tkinter.scrolledtext, traceback, hashlib, importlib, time;
global root;
root=tkinter.Tk()
def show_error(self, *args):
    log("GAYer")
    log(traceback.format_exception(*args))
    raise args[0](args[1])
# but this works too
tkinter.Tk.report_callback_exception = show_error
logwindow = root
logwindow.protocol("WM_DELETE_WINDOW", exit)
logwindow.title("NovaOS Logs")
logwindow.geometry("400x400")
logtext = tkinter.scrolledtext.ScrolledText(logwindow)
logtext.config(state=tkinter.DISABLED)
logtext.pack()
tkinter.ttk.Button(logwindow, text = "Exit", command=exit).pack()
_sysStatus = 0
_sysUser = "";
_config = {}

def log(text=""):
    logtext.config(state=tkinter.NORMAL)
    logtext.insert(tkinter.INSERT, str(text)+"\n")
    print(text)
    logtext.config(state=tkinter.DISABLED)

class UserNotFoundError(Exception):
    pass
class AuthenticationError(Exception):
    pass
with open("config.json") as _f:
    _config = json.load(_f)
    print(_config)
def getsysinfo():
    return f'{os.uname().sysname} {os.uname().nodename} {os.uname().release} {os.uname().version} {os.uname().machine}';

def listapplications():
    applications = []
    for a in next(os.walk('applications'))[1]:
        if(not(a.startswith("__"))):
            applications.append(a)
            
    return applications;

class sysState:
    def get():
        return _sysStatus;
    def set(state: int):
        _sysStatus = state;
        return _sysStatus;
    def Unknown():
        return 0;
    def Booting():
        return 1;
    def Booted():
        return 2;
    def awaitLogin():
        return 3;
    def sysAuthenticated():
        return 4;
    def poweringDown():
        return 5;
    def stateNames():
        return ["Unkown", "Booted", "Awaiting Login", "Logged in", "Power down requested"]
    def stateDescriptions():
        return ["State unset.", "Waiting for first profile to authenticate", "Logged in to "+_sysUser, "A shutdown has been requested."]

class Users():
    def list():
        return _config.get("users")
    def getAllNames():
        tempUL = _config.get("users")
        return [*tempUL.keys()]
    def exec(username: str, passhash: str, program, attributes: list = []):
        return 0;
    def systemProfileInt():
        return 0;
    def adminProfileInt():
        return 1;
    def regularProfileInt():
        return 2;
    def guestProfileInt():
        return 3;
    def profileTypeNames():
        return ["Godmode", "Admin", "Regular", "Guest"]
def refresh():
    try:
        with open("config.json") as _f:
            _config = json.load("config.json")
        return True
    except:
        return False
class Session():
    def __new__(cls):
        instance = super(Session, cls).__new__(cls)
        return instance
    
    def showAuthPopup(cls, minPriv:int=3, username:str=False, appfolder:str=False):
        loginwindow = tkinter.Tk()
        loginwindow.title("Authentication Required")
        if(appfolder):
            tkinter.ttk.Label(loginwindow,text=str(appfolder)+" requested rasied session permissions to "+Users.profileTypeNames()[minPriv]+".\nEnter your credentials to proceed.", font=("TkDefaultFont Bold", "15")).pack()
        else:
            tkinter.ttk.Label(loginwindow, text="Please Log In.", font=("TkDefaultFont Bold", "15")).pack()
            
        tkinter.ttk.Label(loginwindow, text="Username").pack()
        unamebox = tkinter.Entry(loginwindow)
        if(username):
            unamebox.insert(0, username)
        unamebox.pack()
        passbox = tkinter.Entry(loginwindow)
        al=tkinter.Listbox(loginwindow)
        def reloadAL(ev):
            al.delete(0, tkinter.END)
            if unamebox.get() in Users.getAllNames():
                accessLvl = _config.get("users").get(unamebox.get()).get("kind")
                print(accessLvl)
                i = 0;
                levels = Users.profileTypeNames()
                for l in levels:
                    print("gae")
                    print(i)
                    print(accessLvl)
                    if i >= accessLvl:
                        print(l)
                        print("GaYY")
                        print(i)
                        al.insert(i,l);
                    i+=1;
        unamebox.bind("<KeyRelease>", reloadAL)
        tkinter.ttk.Label(loginwindow, text="Password").pack()
        passbox.pack()
        tkinter.ttk.Label(loginwindow, text="Access Level").pack()
        levels = Users.profileTypeNames()[slice(minPriv+1)]
        log(levels)
        log(minPriv)
        i=1
        al.selection_set(0)
        for e in levels:
            al.insert(i, e)
            i +=1;
        al.pack()
        def handlelogin():
            try:
                uname =unamebox.get()
                passw = hashlib.md5(passbox.get().encode("ascii")).hexdigest()
                try:
                    sestype = Users.profileTypeNames().index(al.get(tkinter.ACTIVE))
                    print("sestype")
                    print(al.get(tkinter.ACTIVE))
                    loginwindow.destroy()
                    loginwindow.quit()
                    cls.Authenticate(username=uname,passhash=passw, sessionType=sestype);
                    log(cls.user)
                    log(cls.type)
                    return cls;
                except ValueError:
                    tkinter.tkinter.ttk.Button.showerror("Missing value: Access Level","Pick an Access Level.")
            except Exception as e:
                tkinter.tkinter.ttk.Button.showerror("Authentication Error ("+type(e).__name__+")", e)
                print(traceback.format_exception(e))
                # loginwindow.destroy()
                # loginwindow.quit()
                cls.showAuthPopup(minPriv, username, appfolder)
            log(cls)
        tkinter.ttk.Button(loginwindow, text="Authenticate", command=handlelogin).pack()
        loginwindow.mainloop()
        return cls;
        
        
    def Authenticate(instance, username: str, passhash: str, sessionType: int=3):
        userlist = Users.getAllNames();
        print(userlist)
            
        if username in userlist:
            user = _config.get("users").get(username)
            print(user)
            if username in userlist:
                if user.get("pass") == passhash:
                    if user.get("kind") <= sessionType:
                        instance.user = username;
                        instance.type = sessionType;
                        log(instance.user)
                        log(instance.type)
                        return instance;
                    else:
                        raise AuthenticationError("User "+username+" is not of required permission level ("+str(sessionType)+"/"+Users.profileTypeNames()[sessionType]+") or higher. User has permission level "+str(user.get("kind"))+ " (" +Users.profileTypeNames()[user.get("kind")]+")")
                else:
                        raise AuthenticationError("Authentication error, please try again (password)")
        else:
            raise UserNotFoundError("User " + username + " not found, please try again (user)");
    def exec(cls, program, appfolder:str, attributes: str=""):
        log("gay!")
        if cls.user == None or cls.type == None:
            raise AuthenticationError("what")
        try:
            program({"user": cls.user, "type": cls.type,"appfolder":appfolder}, attributes)
        except PermissionError as e:
            log("GAYYYYYY")
            if(type(e) == PermissionError):
                log("gay")
                output = ""
                log(str(e.args[0]))
                args = json.loads(str(e.args[0]))
                log(args)
                output += (args.get("session").get("appfolder") + " exited unexpectedly due to a permission defficiency. You are currently logged in as an " + Users.profileTypeNames()[cls.type] + " user. The executable reuqests a " + Users.profileTypeNames()[args.get("requiredLevel")] + " user at minimum.")
                output += ("\n\nThe executable said: " + args.get("message"))
                if tkinter.tkinter.ttk.Button.askyesno("Permission error!", output):
                    appsession = Session()
                    appsession.showAuthPopup(minPriv=int(args.get("requiredLevel")),username=args.get("session").get("user"),appfolder=args.get("session").get("appfolder"))
                    capp = importlib.import_module("applications."+args.get("session").get("appfolder"), args.get("session").get("appfolder")).self;                        
                    appsession.exec(capp.exec, appfolder=args.get("session").get("appfolder"))
                    
def fadeInWin(root):
    try:
        root._animT
    except AttributeError:
        root._animT = 0
        root.lift()
    if(root._animT < 0.05):
        root.lift()
    if root._animT < 198:
        root._animT = root._animT + 0.01
        if root._animT < 100:
            root.wm_attributes('-alpha',root._animT)
        root._Tjob = root.after(5,lambda:fadeInWin(root))
    else:
        root.after_cancel(root._animT)