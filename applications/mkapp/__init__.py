from .. import basicapplib;
self = basicapplib.Application(name="App Creator", description="Creates a boilerplate code for a NovaOS Pyapplication", package="win.novafurry.os.pkgmake", version="0.0.1", developer="NovaOS Contributors", developer_website="https://git.novafurry.win/os/app-pkgmake", developer_email="os.app.pkgmake@novafurry.win")
def main(session, args=[]):
    ui = self.ui()
    self.con.write("==== Application Creator ====");
    name = ui.basicAsk("Name your app: ")
    pkg = ui.basicAsk("Enter the package id (ex: com.you.app): ") 
    version = "0.0.0"
    description = ui.basicAsk("Describe your app: ")
    dev = ui.basicAsk("Your name: ")
    web = ui.basicAsk("Your website: ")
    mail = ui.basicAsk("Your email: ")
    fs = self.fs;
    self.con.write(fs.list("."))
self.setScript("main", main)
