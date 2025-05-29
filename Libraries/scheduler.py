import time
import Libraries.nsys as nsys
import importlib.util
import os

class Scheduler:
    def __init__(self):
        self.scheduled_apps = {}  # Dictionary to keep track of scheduled apps
        self.running = False
        self.last_tick_time = time.time()
        self.interval = 1.0  # Default interval in seconds
    
    def register_app(self, app_id, app_instance):
        """
        Register a scheduled application with the scheduler
        """
        if app_id in self.scheduled_apps:
            nsys.log(f"App {app_id} already registered in scheduler")
            return False
        
        self.scheduled_apps[app_id] = {
            "app": app_instance,
            "active": False,
            "last_tick": time.time()
        }
        nsys.log(f"Registered scheduled app: {app_id}")
        return True
    
    def unregister_app(self, app_id):
        """
        Remove a scheduled application from the scheduler
        """
        if app_id in self.scheduled_apps:
            app_info = self.scheduled_apps[app_id]
            if app_info["active"]:
                # Stop the app before unregistering
                app_info["app"].stop()
            
            del self.scheduled_apps[app_id]
            nsys.log(f"Unregistered scheduled app: {app_id}")
            return True
        return False
    
    def start_app(self, app_id):
        """
        Start a scheduled application
        """
        if app_id in self.scheduled_apps:
            app_info = self.scheduled_apps[app_id]
            if not app_info["active"]:
                try:
                    app_info["app"].start()
                    app_info["active"] = True
                    app_info["last_tick"] = time.time()
                    nsys.log(f"Started scheduled app: {app_id}")
                    return True
                except Exception as e:
                    nsys.log(f"Error starting app {app_id}: {e}")
                    return False
            return True  # Already active
        return False
    
    def stop_app(self, app_id):
        """
        Stop a scheduled application
        """
        if app_id in self.scheduled_apps:
            app_info = self.scheduled_apps[app_id]
            if app_info["active"]:
                try:
                    app_info["app"].stop()
                    app_info["active"] = False
                    nsys.log(f"Stopped scheduled app: {app_id}")
                    return True
                except Exception as e:
                    nsys.log(f"Error stopping app {app_id}: {e}")
                    return False
            return True  # Already inactive
        return False
    def start(self):
        """
        Start the scheduler
        """
        if not self.running:
            self.running = True
            self.last_tick_time = time.time()
            nsys.log("Scheduler started")
            return True
        return False
    
    def stop(self):
        """
        Stop the scheduler
        """
        if self.running:
            self.running = False
            
            # Stop all running scheduled apps
            for app_id, app_info in self.scheduled_apps.items():
                if app_info["active"]:
                    try:
                        app_info["app"].stop()
                        app_info["active"] = False
                    except Exception as e:
                        nsys.log(f"Error stopping app {app_id} during scheduler shutdown: {e}")
            
            nsys.log("Scheduler stopped")
            return True
        return False
    def process_tick(self):
        """
        Process a single tick for all active scheduled apps
        This should be called from the main event loop regularly
        """
        if not self.running:
            return
            
        current_time = time.time()
        
        # Check if enough time has passed since the last tick
        if current_time - self.last_tick_time >= self.interval:
            self.last_tick_time = current_time
            
            for app_id, app_info in list(self.scheduled_apps.items()):
                if app_info["active"]:
                    try:
                        print(f"Ticking scheduled app: {app_id}")
                        # Execute the tick function for each active app
                        app_info["app"].tick()
                        app_info["last_tick"] = current_time
                    except Exception as e:
                        nsys.log(f"Error in scheduled app {app_id} tick: {e}")
    
    def list_scheduled_apps(self):
        """
        Get a list of all registered scheduled apps and their status
        """
        apps_list = []
        for app_id, app_info in self.scheduled_apps.items():
            apps_list.append({
                "id": app_id,
                "name": app_info["app"].name if hasattr(app_info["app"], "name") else app_id,
                "active": app_info["active"],
                "last_tick": app_info["last_tick"]
            })
        return apps_list

# Create a global scheduler instance
scheduler = Scheduler()
