import pyinotify

wm = pyinotify.WatchManager()  # Watch Manager
mask = (
    pyinotify.IN_DELETE
    | pyinotify.IN_CREATE
    | pyinotify.IN_MODIFY
    | pyinotify.IN_MOVED_FROM
    | pyinotify.IN_MOVED_TO
    | pyinotify.IN_MOVE_SELF
    | pyinotify.IN_DELETE_SELF
)  # watched events


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print("Creating:", event.pathname)

    def process_IN_DELETE(self, event):
        print("Removing:", event.pathname)

    def process_IN_MODIFY(self, event):
        print("Modifying:", event.pathname)

    def process_IN_MOVED_FROM(self, event):
        print("Moved From:", event.pathname)

    def process_IN_MOVED_TO(self, event):
        print("Moved To:", event.pathname)

    def process_IN_MOVE_SELF(self, event):
        print("Moving Self:", event.pathname)

    def process_IN_DELETE_SELF(self, event):
        print("Deleting Self:", event.pathname)


handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)

# watch Hyperledger and HOME
from os.path import expanduser

home = expanduser("~")
dirs = ["/etc/hyperledger/", "/var/hyperledger/", home]
for dir in dirs:
    print("Add watcher to", dir)
    wdd = wm.add_watch(dir, mask, rec=True, auto_add=True)

notifier.loop()
