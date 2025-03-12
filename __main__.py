import nsys, json, importlib, hashlib, tkinter, tkinter.ttk, time;
nsys.log("Booting NovaOS basic example implementation")
nsys.log("NovaOS 0.0.0 booting on " + nsys.getsysinfo())
nsys.sysState.set(nsys.sysState.Booting)
def picker(applications):
    try:
        aid = int(input("Choose app to execute (number): "))
        return aid        
    except:
        nsys.log('Please enter a number')
        return picker(applications)
global applications;
applications = [];
systemSession = nsys.Session();
  
def launcher(session, args):
    shouldExitOnClose = True;
    applicationFolders = nsys.listapplications()
    i = 1
    # time.sleep(1)            
    root=tkinter.Tk()
    root.protocol("WM_DELETE_WINDOW", exit)
    tkinter.ttk.Label(root, text="NovaOS Launcher Example", font=('Comic Neue Bold', 25)).pack()
    root.title("NovaOS Launcher Example")
    for appfolder in applicationFolders:
        if(not(appfolder.startswith("__"))):
            capp = importlib.import_module("applications."+appfolder, appfolder).self;
            gay = json.dumps(session)
            gay = gay.replace("}",", \"appfolder\":\""+appfolder+"\"}")
            exec("tkinter.ttk.Button(root, text='"+capp.name+"', command=lambda: systemSession.exec(applications["+str(i-1)+"].exec, appfolder='"+appfolder+"')).pack()")
            applications.append(capp)
        i +=1;
    tkinter.ttk.Button(root, text="Reauthenticate Session", command=systemSession.showAuthPopup).pack()
    # nsys.fadeInWin(root)
    root.mainloop()
def authloop():
    try:
        nsys.sysState.set(nsys.sysState.awaitLogin)
        try:
            # systemSession.Authenticate("system", passhash=hashlib.md5(b"Password").hexdigest(), sessionType=3)
            systemSession.showAuthPopup()
            systemSession.exec(launcher, appfolder="")
        except Exception as e:
            nsys.log(e.args)
            # authloop()
    except(KeyboardInterrupt):
        nsys.log()
        nsys.log("Exiting.")
authloop()