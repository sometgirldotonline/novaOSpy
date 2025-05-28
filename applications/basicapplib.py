import tkinter.messagebox
import tkinter.scrolledtext
import os, tkinter, tkinter.ttk, json, nsys, random, string, platform;
from permissions import PermissionSubsystem;
import threading;
psys = PermissionSubsystem();
global Application;
class Application():
    # type is one of "basic" or "scheduled"
    def __new__(cls, app_folder=os.path.dirname(os.path.realpath(__file__)), type="basic"):
        if type not in ["basic", "scheduled"]:
            raise ValueError("Invalid application type. Must be 'basic' or 'scheduled'.")
        cls.type = type
        cls.running = False
        if app_folder is None:
            raise ValueError("app_folder must be provided, there is no way to get the current app folder")
        if not app_folder.startswith("/"):
            app_folder = os.path.join("applications/", app_folder)
        elif app_folder.startswith("#"):
            app_folder = os.path.join(os.getcwd(), app_folder)
        else:
            app_folder = os.path.join(os.getcwd(), app_folder[1:])
        if not os.path.exists(app_folder):
            raise FileNotFoundError(f"'{app_folder}' does not exist.")
        if not os.path.isdir(app_folder):
            raise NotADirectoryError(f"'{app_folder}' is not a directory.")
        if not os.path.exists(os.path.join(app_folder, "meta.json")):
            raise FileNotFoundError(f"meta.json not found in '{app_folder}'.")
        # if path does not start with /, add the current working directory, if we start with a # it means system applications folder
        
        instance = super(Application, cls).__new__(cls)
        instance.folder = app_folder

        # Load metadata from meta.json
        meta_path = os.path.join(app_folder, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as meta_file:
                meta_data = json.load(meta_file)
                instance.name = meta_data.get("name", "")
                instance.description = meta_data.get("description", "")
                instance.package = meta_data.get("id", "")
                instance.version = meta_data.get("version", "")
                instance.developer = meta_data.get("developer", "")
                instance.developer_web = meta_data.get("developer_website", "")
                instance.developer_mail = meta_data.get("developer_email", "")
        else:
            raise FileNotFoundError(f"meta.json not found in {app_folder}")

        instance.windows = []
        instance.con = _con(instance)
        instance.sys = _sys(instance)
        instance.power = _power(instance)
        instance.generators = _generators()
        instance.apps = _apps(instance)
        return instance;

    def setScript(self, kind: str, program):
        if(kind == "main"):
            self.program = program;
        elif(kind == "start"):
            self.startScript = program;
        elif(kind == "stop"):
            self.stopScript = program;
        elif(kind == "tick"):
            self.tickScript = program;
    def tick(self):
        self.tickScript(self)
    def start(self):
        if hasattr(self, "startScript"):
            self.startScript(self)
        self.running = True
    def stop(self):
        if hasattr(self, "stopScript"):
            self.stopScript(self)
        self.running = False
    def exec(self, session, args):
        if hasattr(self, "program") & (self.type == "basic"):
            self.program(session, args)
        elif hasattr(self, "startScript") & self.type == "scheduled":
            # throw an error because scheduled apps are launched differently
            return {"error": "Scheduled apps cannot be launched with exec()", "reason":"ScheduledApp"}
        else:
            return {"error": "No script set for this application", "reason":"NoScript"}
    def exitApp(self):
        if self.type == "basic":
            if hasattr(self, '_tk'):
                self._tk.destroy()
            if nsys.sysState.get() == nsys.sysState.testMode:
                exit()
        elif self.type == "scheduled":
            if hasattr(self, "stopScript"):
                self.stop()
        else:
            raise TypeError("Invalid application type. Must be 'basic' or 'scheduled'.")
    def ui(cls):
        win = _ui(cls)
        cls.windows.append(win);
        return win;
    def fs(cls):
        diderror = False
        if not psys.check_permission(cls.package, permission="novaos.FileSystem") in ["READ", "WRITE", "READWRITE"]:
            diderror = True
            return PermissionError({"type": "PermissionError", "permGranted": False, "message": "EPerm, Filesystem Permissions not granted"})
        # if not hasattr(cls, "fs") & (not diderror):
            cls.fs = _fs(cls)
        return _fs(cls);
    # def requestLevelRaise(self,session, level: int=1, message: str="No message provided"):
    #     # raise PermissionError(json.dumps({"message": message, "requiredLevel":level, "session": session}))
    #     nsys.requestAppPermRaise({"message": message, "requiredLevel":level, "session": session})
    #     self.exitApp()
    def requestPermission(self,permission, data=[]):
        if permission == None:
            raise TypeError("Expected 'String' type not 'None' Type.")
        if tkinter.messagebox.askyesno("Permission Controller",f"Allow {self.name} to use permission: {permission}?"):
            psys.grant_permission(self.package, permission=permission, data=data)
            return True;
        else:
            return False;

    def revokePermission(self,permission, data=[]):
        if permission == None:
            raise TypeError("Expected 'String' type not 'None' Type.")
        if tkinter.messagebox.askyesno("Permission Controller",f"Revoke {self.name} permission: {permission}?"):
            psys.revoke_permission(self.package, permission=permission, data=data)
            return True;
        else:
            return False;
    def getPermissions(self):
        return psys.get_permissions(self.package)
    def checkPermission(self, permission):
        if permission == None:
            raise TypeError("Expected 'String' type not 'None' Type.")
        return psys.check_permission(self.package, permission=permission)
    def getLogs(self):
        return "Not Implemented, track the logs urself dummy"
    def getInfo(self):
            meta_path = os.path.join(self.folder, "meta.json")
            with open(meta_path, "r") as meta_file:
                return json.load(meta_file)
    def checkUpdate(self):
        return "Not Implemented"
    def requestUpdate(self):
        return "Not Implemented"
    def uninstall(self):
        return psys.uninstallApp(self.id)


class _apps:
    def __new__(cls,parent):
        global psys;
        inst = super(_apps, cls).__new__(cls)
        inst.parent = parent;
        return inst;
    def listApplications(self):
        return psys.list_applications()
un = platform.uname();
class _sys:
    def __new__(cls, parent):
        inst = super(_sys, cls).__new__(cls)
        inst.parent = parent;
        return inst;
    platform = {
            "string": f'{un.system} {un.node} {un.release} {un.version} {un.machine}',
            "hostplatform": un.system,
            "architecture": un.machine,
        }
    def getSystemStateInt(cls):
        return nsys.sysState.get()
class _fs:
    def __new__(cls, parent):
        inst = super(_fs, cls).__new__(cls)
        inst.parent = parent;
        return inst;
    def list(self, path):
        return os.listdir(path)
    # write and reads should support both text and binary files
    def write(self, path, data, mode="w"):
        with open(path, mode) as f:
            f.write(data)
    def read(self, path, mode="r"):
        with open(path, mode) as f:
            return f.read()
    def exists(self, path):
        return os.path.exists(path)
    def createDirectory(self, path):
        try:
            os.mkdir(path)
            return True
        except FileExistsError:
            return False
    def delete(self, path):
        try:
            os.remove(path)
            return True
        except FileNotFoundError:
            return False
    def move(self, src, dst):
        try:
            os.rename(src, dst)
            return True
        except FileNotFoundError:
            return False
    def copy(self, src, dst):
        try:
            import shutil
            shutil.copy(src, dst)
            return True
        except FileNotFoundError:
            return False
    def getFileInfo(self, path):
        try:
            import os.path
            return os.path.getsize(path), os.path.getmtime(path), os.path.getctime(path)
        except FileNotFoundError:
            return None, None, None
class _con:
    def __new__ (cls, parent):
        inst = super(_con, cls).__new__(cls)
        inst.parent = parent;
        return inst;
    def write(cls, text):
        nsys.log(cls.parent.name+": "+str(text))
    def read(cls, prompt):
        return input(cls.parent.name+": "+str(prompt) + "> ")
class _power:
        def __new__ (cls, parent):
            inst = super(_power, cls).__new__(cls)
            inst.parent = parent;
            return inst;
        def poweroff(cls):
            # Display prompt asking user if they want to power down
            if tkinter.messagebox.askyesno("Dialog for: "+str(cls.parent.name), str(cls.parent.name) + " would like to turn off the device. Would you like to continue?"):
                print("Exiting.")
                nsys.pwrmgr.poweroff()
                return True
            else:
                return False;
        def reboot(cls):
            if tkinter.messagebox.askyesno("Dialog for: "+str(cls.parent.name), str(cls.parent.name) + " would like to reboot the device. Would you like to continue?"):
                print("Rebooting")
                # tkinter.Tk.quit()
                nsys.pwrmgr.reboot()
                return True
            else: 
                return False;
          

class uiElTemplate:
    def set(cls, parameters):
        cls.tkel.configure(**parameters)
        return cls
    def get(cls, parameter):
        return cls.tkel.cget(parameter)
class _ui:
    def __new__(cls, parent):
        print("Creating window for: " + parent.name)
        instance = super(_ui, cls).__new__(cls)
        # check if tkinter is already running with an existing window
        instance._tk = tkinter.Toplevel()
        instance.name = "Window for: " + parent.name
        instance._tk.title(instance.name)
        instance.parent = parent
        instance._ocev = False;
        def balClose():
            nsys.log(parent.name+"(basicapplib): "+str(parent.windows))
            index = list.index(parent.windows, instance)
            instance._tk.destroy()
            list.remove(parent.windows, instance)
            nsys.log(parent.name+"(basicapplib): "+str(parent.windows))
        def on_closing():
            if instance._ocev != False:
                if instance._ocev(instance): # must return a truthy value to continue!
                    balClose()
            else:
                balClose()
            if nsys.sysState.testMode == nsys.sysState.get():
                exit()
        instance._tk.protocol("WM_DELETE_WINDOW", on_closing)
        instance.elements=[]
        instance._tk.after(300, instance._tk.focus_force)
        return instance;

    def onWindowClose(cls, ev):
        cls._ocev=ev;
        return cls;
    def uiApploop(cls): # used for platforms where a loop is required for keepalive
        cls._tk.mainloop()
    def Label(cls, text="Unset Value", size=12):
        el = _uiElLabel(cls, text, size)
        cls.elements.append(el)
        return el;
    def scrolledtext(cls, text="Unset Value", size=12):
        el = _uiElSt(cls, text, size)
        cls.elements.append(el)
        return el;
    def btn(cls, text="Unset Value", size=12):
        el = _uiElBtn(cls,text,size)
        cls.elements.append(el)
        return el;
    def basicAsk(cls,prompt):
        from tkinter.simpledialog import askstring;
        return askstring("Dialog for: "+cls.parent.name, prompt)  
    def basicAskint(cls,prompt):
        from tkinter.simpledialog import askinteger
        return askinteger("Dialog For: "+cls.parent.name, prompt)
    

class _uiElLabel(uiElTemplate):
        def __new__(cls, parent, text="idiot, you did not set", size=12):
            instance = super(_uiElLabel, cls).__new__(cls)
            instance.tkel = tkinter.ttk.Label(parent._tk, text=text, font=('sans-serif', size))
            instance.tkel.pack()
            return instance;
class _uiElSt(uiElTemplate):
    def __new__(cls, parent, text="Idiot", size=12):
        instance = super(_uiElSt, cls).__new__(cls)
        instance.tkel = tkinter.scrolledtext.ScrolledText(parent._tk, font=('sans-serif', size))
        instance.tkel.insert("1.0", text)  # Insert new text
        instance.tkel.pack()
        return instance
    def set(cls, parameters):
        print(parameters)
        for p in parameters:
            if(p == "text"):
                cls.tkel.delete("1.0", "end")  # Delete existing text
                cls.tkel.insert("1.0", parameters[p])  # Insert new text
            else:
                cls.tkel.configure({p:parameters[p]})
        return cls
    def get(cls, parameter):
        if(parameter == "text"):
            return cls.tkel.get("1.0", "end-1c")
        else:
            return cls.tkel.cget(parameter)
class _uiElBtn(uiElTemplate):
    def __new__(cls, parent, text="Idiot", size=12):
        instance = super(_uiElBtn, cls).__new__(cls)
        instance.tkel = tkinter.Button(parent._tk, text=text, font=("sans-serif", size))
        instance.tkel.pack()
        return instance
    def setOnClick(cls, command=lambda: print("Wheres the bind fool")):
        cls.tkel.config(command=command)
        return cls;
class _generators:
    def num(min, max):
        return random.randrange(min, max, 2);
    def str(len):
       return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(len)) 
class _UIel:
        def __new__(cls, parent, type, parameters):
            print()