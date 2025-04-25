import tkinter.messagebox
import os, tkinter, tkinter.ttk, json, nsys, random, string, platform;
global Application;
class Application():
    def __new__(cls, name: str = "", description: str = "", package: str = "", version: str = "", developer: str = "", developer_website: str = "", developer_email: str = ""):
        instance = super(Application, cls).__new__(cls)
        instance.name = name
        instance.description = description
        instance.package = package
        instance.version = version
        instance.developer = developer
        instance.developer_web = developer_website
        instance.developer_mail = developer_email
        instance.windows = []
        instance.con = _con(instance)
        instance.sys = _sys(instance)
        instance.power = _power(instance)
        instance.generators = _generators()
        instance.fs = _fs(instance)
        return instance;
    def setScript(self, kind: str, program):
        if(kind == "main"):
            self.program = program;
    def exec(self, session, args):
        self.program(session, args=[])
    def ui(cls):
        win = uiDoNotUse(cls)
        cls.windows.append(win);
        return win;
    def requestLevelRaise(self,session, level: int=1, message: str="No message provided"):
        raise PermissionError(json.dumps({"message": message, "requiredLevel":level, "session": session}))

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
class _fs:
    def __new__(cls, parent):
        inst = super(_fs, cls).__new__(cls)
        inst.parent = parent;
        return inst;
    def list(self, path):
        return os.listdir(path)
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
                
            
class uiDoNotUse:
    def __new__(cls, parent):
        instance = super(uiDoNotUse, cls).__new__(cls)
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
        instance._tk.protocol("WM_DELETE_WINDOW", on_closing)
        instance.elements=[]
        return instance;
    def onWindowClose(cls, ev):
        cls._ocev=ev;
        return cls;
    def uiApploop(cls): # used for platforms where a loop is required for keepalive
        cls._tk.mainloop()
    def Label(cls, text="Unset Value", size=12):
        el = uiElementsDoNotUse.Label(cls, text, size)
        cls.elements.append(el)
        return el;
    def basicAsk(cls,prompt):
        from tkinter.simpledialog import askstring;
        return askstring("Dialog for: "+cls.parent.name, prompt)  
class uiElementsDoNotUse:
    class Label():
        def __new__(cls, parent, text="idiot, you did not set", size=12):
            instance = super(uiElementsDoNotUse.Label, cls).__new__(cls)
            instance.tkel = tkinter.ttk.Label(parent._tk, text=text, font=('Comic Neue', size))
            instance.tkel.pack()
            return instance;
        def set(cls, parameters):
            cls.tkel.configure(**parameters)
            return cls
class _generators:
    def num(min, max):
        return random.randrange(min, max, 2);
    def str(len):
       return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(len)) 
class _UIel:
        def __new__(cls, parent, type, parameters):
            print()