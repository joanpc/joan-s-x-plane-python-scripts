#!/usr/bin/env python
import Tkinter as tk
import tkFileDialog
import threading
import time

import json
import urllib
import tempfile
import os
from zipfile import ZipFile
from shutil import move, rmtree, copytree, copy
from time import sleep
import tempfile

import tkFont

class XPScriptsUpdater:
    ''' Process script updates
    '''
    VERSION = '0.1'
    UPDATE_URL='http://x-plane.joanpc.com/plugins/updater_json/OSX/' + VERSION

    updates = []
    update_types = ['zip', 'direct']

    def __init__(self, xplanedir, plugin = False):
        self.xplanedir = xplanedir
        self.processing = False
        self.printStatus = False
        pass

    def tcopy(self, src, dst):
        ''' Recursive overwrite
        '''
        for path in os.listdir(src):
            spath = src + '/' + path
            if os.path.isdir(spath):
                if os.path.exists(dst + '/' + path):
                    rmtree(dst + '/' + path)
                os.mkdir(dst + '/' + path)
                self.tcopy(spath, dst + '/' + path)
            elif not os.path.islink(spath):
                copy(spath, dst)

    def update(self, update):
        dpath = self.xplanedir + '/Resources/Downloads'
        installpath = self.xplanedir + '/Resources/plugins/PythonScripts'

        if not os.path.exists(dpath):
            os.mkdir(dpath)

        if update['update_type'] == 'direct' and update['update_filename']:


            if not self.download(update['update_url'], dpath + '/' + update['update_filename']):
                return False

            self.printStatus('Installing files:')
            copy(dpath + '/'  +  update['update_filename'], installpath + '/'  +  update['update_filename'])
            self.printStatus('.', False)

            return True

        elif update['update_type'] == 'zip':
            zipfile = dpath + '/._xpjpcUPDATE.zip'
            # Download update

            self.printStatus('Downloading: \n%s' % update['update_url'])
            try:
                urllib.urlretrieve(update['update_url'], zipfile)
            except:
                self.printStatus('ERROR: ')
                return False
            self.printStatus('.', False)

            zip = ZipFile(zipfile, 'r')

            self.printStatus('Unpacking: %s' % update['name'])
            # Check zip file
            if not zip.testzip():
                # Unzip
                unzipdir = dpath + '/' + zip.namelist()[0]
                zip.extractall(dpath)
                zip.close()
                # Move files
                self.tcopy(unzipdir, installpath)
                rmtree(unzipdir)
                os.remove(zipfile)
            self.printStatus('.', False)

            return True

    def checkPaths(self):

        if not os.path.exists(self.xplanedir):
            return False

        paths = ['Resources', 'Resources/Downloads', 'Resources/plugins', 'Resources/plugins/PythonScripts']

        for path in paths:
            path = '%s/%s' % (self.xplanedir, path)
            if not os.path.exists(path):
                try:
                    os.mkdir(path)
                except:
                    return False
        return True

    def download(self, url, path):

        self.printStatus('Downloading: \n%s' % url)
        try:
            urllib.urlretrieve(url, path)
        except:
            self.printStatus(' ERROR!')
            return False
        self.printStatus('.', False)

        return path


    def installPlugin(self, url):
        url = 'http://www.xpluginsdk.org/downloads/latest/Python27/PythonInterface.zip'

        dpath = self.xplanedir + '/Resources/Downloads'
        installpath = self.xplanedir + '/Resources/plugins'

        zipfile = dpath + '/PythonInterface.zip'

        # Download update
        if not self.download(url, zipfile):
            return False

        zip = ZipFile(zipfile, 'r')

        # Check zip file
        if not zip.testzip():
            # Unzip
            zip.extractall(installpath)
            zip.close()

    def findUpdates(self, signature = False, version = False):

        try:
            res = urllib.urlopen(self.UPDATE_URL)
        except:
            return False

        if not res:
            return False

        versions = json.load(res)
        updates = {}
        for signature, data in versions.iteritems():
            updates[signature] = data

            # Not installed
            if data['update_type'] in self.update_types:
                action = 'install'
            else:
                action = 'Update installer first'
            current_ver = 'na'
            updates[signature]['action'] = action
            updates[signature]['current_version'] = current_ver
        return updates

class Application(tk.Frame):

    message = 'Those are my Open Source x-plane plugin projects. They require \n'
    message += 'a Python 2.7 installation in your system and Sandy Barbour\'s \n'
    message += 'X-Plane Python Interface.'

    def __init__(self, master=None):

        self.xp_path = None

        tk.Frame.__init__(self, master)
        self.pack(padx = 10, pady= 10, fill='both', expand=1)

        self.updater = XPScriptsUpdater(self.xp_path)

        self.updater.printStatus = self.printStatus
        self.processing = False
        self.createWidgets()

        self.updates = False
        self.printStatus('Checking the net for available scripts.')
        self.threadDo(self.findUpdates, None)
        self.printStatus('done.')

        if self.updates:
            self.createUpdatesWidgets(self.updates_frame)
        else:
            self.printStatus('ERROR: downloading updates\nCheck yout internet connection and try again.')

    def findUpdates(self, ignoreme):
        self.updates = self.updater.findUpdates()

    def createUpdatesWidgets(self, frame):

        row = 0
        tk.Label(frame, text = 'Sandy Barbour\'s Python Interface (required)').grid(row = row, column = 0, sticky = "W")
        self.installPythonInteface = tk.IntVar()
        check = tk.Checkbutton(frame, variable = self.installPythonInteface)
        check.select()
        check.grid(row = row, column = 1)

        row += 1

        if self.updates:
            for sid, data in self.updates.iteritems():
                tk.Label(frame, text = data['name']).grid(row = row, column = 0, sticky = "W")

                self.installChecks[sid] = tk.IntVar()
                check = tk.Checkbutton(frame, variable = self.installChecks[sid])
                check.grid(row = row, column = 1)
                check.select()
                row += 1

        else:
            self.printStatus('No updates available')


    def separator(self, frame):
        # Separator
        tk.Frame(frame, height = 10 ).pack(fill = 'x')
        tk.Frame(frame, height = 1, bg = '#000').pack(fill = 'x')


    def createWidgets(self):

        self.installChecks = {}
        self.labels = {}

        tk.Label(self, text = self.message, font = ('monospace', 14),
            height = 3, pady = 4, anchor = 'sw', justify = tk.LEFT, width = 60).pack(fill = 'x')

        self.separator(self)

        self.updates_frame = tk.Frame(self, padx = 4)
        self.updates_frame.pack(fill = 'x')

        self.separator(self)

        frame = tk.Frame(self)
        frame.pack(fill = 'x', pady = 10)

        self.xpFolderButton = tk.Button(frame, text='Select X-Plane folder',
            command = self.selectXplaneFolder)
        self.xpFolderButton.pack(side = 'left')

        self.installButton = tk.Button(frame, text='Install',
            command=self.doInstalls)
        self.installButton.pack(side = 'right')

        self.statusCaption = tk.StringVar()
        tk.Label(self, textvariable = self.statusCaption, font = ('monospace'),
            height = 8, anchor = 'sw', justify = tk.LEFT, width = 60,
            padx = 5, pady = 5, bg = '#fff').pack(fill = 'x')
        self.printStatus('Please, select your X-Plane folder.')

        #print row
        #self.quitButton = tk.Button(self, text='Exit',
        #    command=self.quit)
        #self.quitButton.grid(row = row, column = 1, columnspan = 1, sticky = 'W')

    def selectXplaneFolder(self):
        if not self.processing:
            self.xp_path = tkFileDialog.askdirectory(title = 'Pick a folder', initialdir = '/')
            if self.xp_path:
                self.printStatus('Selected X-Plane folder:\n %s' % (self.xp_path))
            else:
                self.printStatus('No folder selected.')

    def printStatus(self, message, newline = True):
        nl = ''
        if newline:
            nl = "\n"

        self.statusCaption.set('%s%s%s' % (self.statusCaption.get(), nl, message))

    def threadDo(self, task, args):
        # Run a task on a thread while updating.
        # Python interface install
        window = self.winfo_toplevel()

        th = threading.Thread(target = task, args = [args])
        th.start()
        while th.is_alive():
            window.update()
            time.sleep(0.001)

    def doInstalls(self):

        if not self.xp_path:
            self.printStatus('ERROR: No X-Plane folder selected.')
            return
        else:
            self.updater.xplanedir = self.xp_path

        if not self.updater.checkPaths():
            self.printStatus('ERROR: Accessing x-plane folder.')
            return

        if self.processing:
            self.printStatus('Processing, please wait.')
            return

        self.processing = True

        if self.installPythonInteface.get():
            self.printStatus('Installing %s' % 'Python Interface: ')
            self.threadDo(self.updater.installPlugin, ['url'])
            self.printStatus('Completed.', None)

        for sid, install in self.installChecks.iteritems():
            if install.get():

                self.printStatus('Installing %s: ' % (self.updates[sid]['name']))
                self.threadDo(self.updater.update, self.updates[sid])
                self.printStatus(' Done.', False)

                self.winfo_toplevel().update()

        self.printStatus('ALL installations COMPLETED.')
        self.processing = False

app = Application()
app.master.title('X-Plane Python Scripts Net Installer')
app.mainloop()
