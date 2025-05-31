import xml.etree.ElementTree as ET
import os
import json
# import tkinter;
class PermissionSubsystem:
    def __init__(self, xml_file="apps.xml"):
        self.xml_file = xml_file
        self.applications = {}
        self.load_permissions()
        self.sync_with_meta_jsons()
        # list all applications in the XML file

    def load_permissions(self):
        """Load application data and permissions from the XML file."""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            for app in root.findall("application"):
                app_id = app.get("id")
                name = app.find("name").text
                description = app.find("description").text
                permissions = {}
                for perm in app.find("permissions").findall("permission"):
                    perm_name = perm.get("name")
                    perm_value = perm.text if perm.text else True
                    permissions[perm_name] = perm_value
                self.applications[app_id] = {
                    "name": name,
                    "description": description,
                    "permissions": permissions,
                    "version": app.get("version"),
                    "developer": app.get("developer"),
                    "developer_web": app.get("developer_web"),
                    "developer_mail": app.get("developer_mail")
                }
        except FileNotFoundError:
            print(f"XML file '{self.xml_file}' not found. Creating a new one.")
            self.create_empty_xml()

    def create_empty_xml(self):
        """Create an empty XML file if none exists."""
        root = ET.Element("applications")
        tree = ET.ElementTree(root)
        tree.write(self.xml_file)

    def sync_with_meta_jsons(self):
        """Ensure all meta.json values are reflected in the XML."""
        apps_dir = "applications"
        tree = ET.parse(self.xml_file)
        root = tree.getroot()

        for app_folder in os.listdir(apps_dir):
            app_path = os.path.join(apps_dir, app_folder)
            meta_path = os.path.join(app_path, "meta.json")

            if os.path.isdir(app_path) and os.path.exists(meta_path):
                with open(meta_path, "r") as meta_file:
                    meta_data = json.load(meta_file)
                    app_id = meta_data.get("id")
                    print(app_id)
                    # Check if the app already exists in the XML
                    app_element = root.find(f"application[@id='{app_id}']")
                    if app_element is None:
                        # Add new application to XML
                        app_element = ET.SubElement(root, "application", id=app_id)
                        ET.SubElement(app_element, "name").text = meta_data.get("name", "")
                        ET.SubElement(app_element, "description").text = meta_data.get("description", "")
                        ET.SubElement(app_element, "version").text = meta_data.get("version", "")
                        ET.SubElement(app_element, "developer").text = meta_data.get("developer", "")
                        ET.SubElement(app_element, "developer_web").text = meta_data.get("developer_website", "")
                        ET.SubElement(app_element, "developer_mail").text = meta_data.get("developer_email", "")
                        ET.SubElement(app_element, "permissions")
                    else:
                        # Update existing application in XML
                        app_element.find("name").text = meta_data.get("name", "")
                        app_element.find("description").text = meta_data.get("description", "")
                        app_element.find("version").text = meta_data.get("version", "")
                        app_element.find("developer").text = meta_data.get("developer", "")
                        app_element.find("developer_web").text = meta_data.get("developer_website", "")
                        app_element.find("developer_mail").text = meta_data.get("developer_email", "")

        # Save changes to the XML file
        tree.write(self.xml_file)

    def get_permissions(self, app_id):
        """Retrieve permissions for a specific application."""
        return self.applications.get(app_id, {}).get("permissions", {})

    def list_applications(self):
        """List all registered applications."""
        apps = []
        i = 0;
        for app_id, data in self.applications.items():
            apps.append(data)
            apps[i]["id"] = app_id
            i=i+1;
        return apps;
    def add_application(self, app_id, name, description, version, developer, developer_web, developer_mail):
        """Add a new application to the XML file."""
        tree = ET.parse(self.xml_file)
        root = tree.getroot()

        # Check if the application already exists
        if root.find(f"application[@id='{app_id}']") is not None:
            raise ValueError(f"Application with ID '{app_id}' already exists.")

        # Create a new application element
        app_element = ET.SubElement(root, "application", id=app_id)
        ET.SubElement(app_element, "name").text = name
        ET.SubElement(app_element, "description").text = description
        ET.SubElement(app_element, "version").text = version
        ET.SubElement(app_element, "developer").text = developer
        ET.SubElement(app_element, "developer_web").text = developer_web
        ET.SubElement(app_element, "developer_mail").text = developer_mail

        # Add permissions
        ET.SubElement(app_element, "permissions")

        # Save the updated XML file
        tree.write(self.xml_file)

        # Update the in-memory data
        self.applications[app_id] = {
            "name": name,
            "description": description,
            "version": version,
            "developer": developer,
            "developer_web": developer_web,
            "developer_mail": developer_mail
        }

    def check_permission(self, app_id, permission):
        """Check if an application has a specific permission."""
        app_permissions = self.get_permissions(app_id)
        return app_permissions.get(permission, False)
    def grant_permission(self, app_id, permission, data=[]):
        """
        Function to grant a permission (add it to the applications file)
        data is an array of data lines for the permission
        if the permission already exists check if theres any new datas to add, and add them
        """
        tree = ET.parse(self.xml_file)
        root = tree.getroot()

        app_element = root.find(f".//application[@id='{app_id}']")
        if app_element is None:
            raise ValueError(f"Application with ID '{app_id}' not found.")

        permissions_element = app_element.find("permissions")
        if permissions_element is None:
            # Should not happen if sync_with_meta_jsons ran, but handle defensively
            permissions_element = ET.SubElement(app_element, "permissions")

        permission_element = permissions_element.find(f"permission[@name='{permission}']")

        new_data_str = "\n".join(map(str, data)) if data else None

        if permission_element is not None:
            # Permission already exists
            if new_data_str:
                existing_data = permission_element.text if permission_element.text else ""
                # Append new data if it's not already present (simple check)
                if new_data_str not in existing_data:
                     permission_element.text = f"{existing_data}\n{new_data_str}".strip()
            # If no new data, and element exists, it's already granted (implicitly True)
        else:
            # Permission does not exist, create it
            permission_element = ET.SubElement(permissions_element, "permission", name=permission)
            if new_data_str:
                permission_element.text = new_data_str
            # If no data, leave text empty (load_permissions interprets as True)


        # Save the updated XML file
        tree.write(self.xml_file)

        # Update the in-memory data
        if app_id in self.applications:
             perm_value = permission_element.text if permission_element.text else True
             self.applications[app_id]["permissions"][permission] = perm_value
        else:
             # This case might indicate an inconsistency, but reload for safety
             self.load_permissions() # Reload to reflect changes if app wasn't in memory
    def revoke_permission(self, app_id, permission, data=[]):
        """
        Revoke a permission. If data is empty- remove the whole permission- if a data is specified, remove that specific data
        """
        tree = ET.parse(self.xml_file)
        root = tree.getroot()

        app_element = root.find(f".//application[@id='{app_id}']")
        if app_element is None:
            # App not found, nothing to revoke
            print(f"Warning: Application with ID '{app_id}' not found for revoking permission.")
            return

        permissions_element = app_element.find("permissions")
        if permissions_element is None:
            # App has no permissions element, nothing to revoke
            print(f"Warning: Application '{app_id}' has no permissions element.")
            return

        permission_element = permissions_element.find(f"permission[@name='{permission}']")
        if permission_element is None:
            # Permission not found for this app, nothing to revoke
            print(f"Warning: Permission '{permission}' not found for application '{app_id}'.")
            return

        permission_revoked = False
        if not data:
            # No specific data provided, remove the entire permission
            permissions_element.remove(permission_element)
            permission_revoked = True
            print(f"Revoked permission '{permission}' entirely for app '{app_id}'.")
        else:
            # Specific data provided, remove only those lines
            if permission_element.text:
                existing_data_lines = permission_element.text.strip().split('\n')
                data_to_remove_str = [str(d) for d in data]
                remaining_data_lines = [line for line in existing_data_lines if line not in data_to_remove_str]

                if len(remaining_data_lines) < len(existing_data_lines):
                    if not remaining_data_lines:
                        # All data lines were removed, remove the permission element itself
                        permissions_element.remove(permission_element)
                        permission_revoked = True
                        print(f"Removed all data for permission '{permission}', revoking entirely for app '{app_id}'.")
                    else:
                        # Update the text with remaining data
                        permission_element.text = "\n".join(remaining_data_lines)
                        print(f"Removed specific data from permission '{permission}' for app '{app_id}'.")
                else:
                    print(f"Specified data not found within permission '{permission}' for app '{app_id}'.")
            else:
                # Permission exists but has no text data, cannot remove specific data
                 print(f"Warning: Permission '{permission}' for app '{app_id}' has no data to remove specific items from.")


        # Save the updated XML file
        tree.write(self.xml_file)

        # Update the in-memory data
        if app_id in self.applications and permission in self.applications[app_id]["permissions"]:
            if permission_revoked:
                del self.applications[app_id]["permissions"][permission]
            elif not data: # Should be caught by permission_revoked, but double check
                 del self.applications[app_id]["permissions"][permission]
            elif permission_element is not None and permission_element.text is not None: # Check if element still exists and has text
                 self.applications[app_id]["permissions"][permission] = permission_element.text
            elif permission_element is not None and permission_element.text is None: # Element exists but no text (implicitly True)
                 self.applications[app_id]["permissions"][permission] = True
            # else: permission was removed, already handled by del

        # Optional: Reload if state seems inconsistent, though direct update is preferred
        # self.load_permissions()
    def uninstallApp(self, app_id):
        return "Not Implemented"        