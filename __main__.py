import nsys, json, importlib.util, hashlib, tkinter, tkinter.ttk, time;
from permissions import PermissionSubsystem
import scheduler
systemVersion = "0.0.1"
nsys.log(f"NovaOS {systemVersion} booting on " + nsys.getsysinfo())
nsys.sysState.set(nsys.sysState.Booting)
nsys.log("state set to Booting")
nsys.log("Loading permissions subsystem")
permissions = PermissionSubsystem()
nsys.log("Permissions subsystem loaded")
nsys.log("Starting scheduler")
scheduler.scheduler.start()
nsys.log("Scheduler started")

# Ensure no duplicate enumeration of applications
registered_apps = permissions.list_applications()
if len(registered_apps) == 0:
    for af in nsys.listapplications():
        print(af)
        if not af.startswith("__"):
            try:
                with open(f"applications/{af}/meta.json") as f:
                    data = json.load(f)
                    permissions.add_application(af, data["name"], data["description"], data["version"], data["developer"], data["developer_website"], data["developer_email"])
            except Exception as e:
                nsys.log(f"Error reading meta.json in {af}: {e}")
                continue

nsys.log("Permissions subsystem initialized")   
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
    shouldExitOnClose = True
    root = tkinter.Toplevel()
    root.protocol("WM_DELETE_WINDOW", exit)
    tkinter.ttk.Label(root, text="NovaOS Launcher Example", font=('Comic Neue Bold', 25)).pack()
    root.title("NovaOS Launcher Example")

    # Add Scheduler Manager frame
    scheduler_frame = tkinter.ttk.LabelFrame(root, text="Scheduled Apps")
    scheduler_frame.pack(fill="x", padx=5, pady=5)

    # Function to refresh scheduled apps list
    def refresh_scheduled_apps():
        for widget in scheduler_frame.winfo_children():
            widget.destroy()
        
        scheduled_apps = scheduler.scheduler.list_scheduled_apps()
        if not scheduled_apps:
            tkinter.ttk.Label(scheduler_frame, text="No scheduled apps registered").pack()
        else:
            for app in scheduled_apps:
                app_frame = tkinter.Frame(scheduler_frame)
                app_frame.pack(fill="x", padx=2, pady=2)
                
                status = "Active" if app["active"] else "Inactive"
                tkinter.ttk.Label(app_frame, text=f"{app['name']} - {status}").pack(side="left")
                
                if app["active"]:
                    tkinter.ttk.Button(app_frame, text="Stop", 
                        command=lambda app_id=app["id"]: scheduler.scheduler.stop_app(app_id) or refresh_scheduled_apps()
                    ).pack(side="right")
                else:
                    tkinter.ttk.Button(app_frame, text="Start", 
                        command=lambda app_id=app["id"]: scheduler.scheduler.start_app(app_id) or refresh_scheduled_apps()
                    ).pack(side="right")

    # Add refresh button for scheduled apps
    tkinter.ttk.Button(scheduler_frame, text="Refresh", command=refresh_scheduled_apps).pack(anchor="e")
    refresh_scheduled_apps()

    # Main apps frame
    apps_frame = tkinter.ttk.LabelFrame(root, text="Applications")
    apps_frame.pack(fill="x", padx=5, pady=5)

    registered_apps = permissions.list_applications()
    for app in registered_apps:
        print(app)
        app_id = app['id']
        app_name = app['name']
        print(f'{app_id}: {app_name}')
        
        # Create new frame for the app and buttons
        app_frame = tkinter.Frame(apps_frame)
        app_frame.pack(fill="x", padx=2, pady=2)
        
        tkinter.ttk.Label(app_frame, text=app_name).pack(side="left")
        
        # Function to load and check if app is a scheduled app
        def load_app_info(app_id):
            try:
                app_spec = importlib.util.spec_from_file_location(
                    name=app_id.replace(".", ""),
                    location=f"./applications/{app_id}/__init__.py"
                )
                app_module = importlib.util.module_from_spec(app_spec)
                app_spec.loader.exec_module(app_module)
                return app_module.self
            except Exception as e:
                nsys.log(f"Error loading app info for {app_id}: {e}")
                return None
        
        app_instance = load_app_info(app_id)
        
        # Check if this is a scheduled app
        is_scheduled = hasattr(app_instance, 'type') and app_instance.type == "scheduled"
        
        def launch_app(app_id=app_id):
            # Only launch basic apps via AppSession
            app_instance = load_app_info(app_id)
            if hasattr(app_instance, 'type') and app_instance.type == "scheduled":
                # Register with scheduler if needed
                if app_id not in [app["id"] for app in scheduler.scheduler.list_scheduled_apps()]:
                    scheduler.scheduler.register_app(app_id, app_instance)
                    refresh_scheduled_apps()
                else:
                    nsys.log(f"App {app_id} already registered with scheduler")
            else:
                # Launch basic apps normally
                app_ses = nsys.AppSession(app_id, session)
                app_ses.exec()

        # Create button based on app type
        if is_scheduled:
            tkinter.ttk.Button(app_frame, text="Register", command=launch_app).pack(side="right")
        else:
            tkinter.ttk.Button(app_frame, text="Launch", command=launch_app).pack(side="right")

    tkinter.ttk.Button(root, text="Reauthenticate Session", command=systemSession.showAuthPopup).pack()
    arg = args.split(", ")
    if(arg[0] == "test"):
        app_id = arg[1]
        app_instance = load_app_info(app_id)
        
        if hasattr(app_instance, 'type') and app_instance.type == "scheduled":
            # Register with scheduler if needed
            scheduler.scheduler.register_app(app_id, app_instance)
            scheduler.scheduler.start_app(app_id)
            refresh_scheduled_apps()
        else:
            # Launch basic apps normally
            app_ses = nsys.AppSession(app_id, session)
            app_ses.exec()
    
    # root.mainloop()

def authloop():
    try:
        nsys.sysState.set(nsys.sysState.awaitLogin)
        try:
            # systemSession.Authenticate("system", passhash=hashlib.md5(b"password").hexdigest(), sessionType=3)
            # time.sleep(1)
            systemSession.showAuthPopup()
            systemSession.exec(launcher, appfolder="")
        except Exception as e:
            nsys.log(e.args)
            # authloop()
    except(KeyboardInterrupt):
        nsys.log()
        nsys.log("Exiting.")
# check for arguments
print(nsys.args)
if len(nsys.args) > 1:
    if nsys.args[1] == "test":
        nsys.log("Starting test mode. Module: " + nsys.args[2])
        
        # Set the system state to Test Mode (6)
        nsys.sysState.set(nsys.sysState.testMode)
        # Log in automatically as "test" user, password "test", session type 3
        systemSession.Authenticate("test", passhash=hashlib.md5(b"test").hexdigest(), sessionType=3)
        print(systemSession)
        time.sleep(1)
        systemSession.exec(launcher, appfolder="", arguments="test, "+nsys.args[2])
    else:
        authloop()
else:
    authloop()