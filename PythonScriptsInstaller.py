#!/usr/bin/env python
'''
Joan's x-plane Python Plugins Net installer

Copyright (C) 2012-2015 Joan Perez i Cauhe
---
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''
import Tkinter as tk
import tkFileDialog
import threading
import ttk
import time

import json
import urllib
import ssl
import tempfile
import platform
from zipfile import ZipFile
from shutil import move, rmtree, copytree, copy
from time import sleep
import tempfile
import ssl

import tkFont
import sys
import os

VERSION = '1.2'

class XPScriptsUpdater:
    ''' Process script updates
    '''
    UPDATE_URL='http://x-plane.joanpc.com/plugins/updater_json/OSX/' + VERSION

    updates = []
    update_types = ['zip', 'direct']

    def __init__(self, xplanedir, plugin = False):
        self.xplanedir = xplanedir
        self.processing = False
        self.printStatus = False
        self.downloadProgress = False
        self.errors = 0
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
            self.printStatus(' ok.', 'bold', False)

            return True

        elif update['update_type'] == 'zip':
            zipfile = dpath + '/._xpjpcUPDATE.zip'
            # Download update

            if not self.download(update['update_url'], zipfile):
                return False

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
            self.printStatus(' ok.', 'bold', newline = False)

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
                    self.printStatus('ERROR: %s%s' % (sys.exc_info()[0], sys.exc_info()[1]), 'error')
                    self.errors += 1
                    return False
        return True

    def download(self, url, path):

        self.printStatus('Downloading: \n%s' % url)
        try:
            urllib.urlretrieve(url, path, reporthook = self.downloadProgress, context=ssl._create_unverified_context())
        except:
            self.printStatus('ERROR: %s%s' % (sys.exc_info()[0], sys.exc_info()[1]), 'error')
            self.errors += 1
            return False
        self.printStatus(' ok.', 'bold', newline = False)

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
            res = urllib.urlopen(self.UPDATE_URL, context=ssl._create_unverified_context())
        except:
            self.errors += 1
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
        self.disableCertVerify()

        self.updates = False
        self.printStatus('Checking the net for available scripts:', newline = False)
        self.threadDo(self.findUpdates, None)
        self.printStatus(' ok.', 'bold', newline = False)
        self.checkPython()
        self.printStatus('Please select which plugins to install and your x-plane folder.')

        if self.updates:
            self.createUpdatesWidgets(self.updates_frame)
        else:
            self.printStatus('ERROR: downloading updates.\nThis installer needs an internet connection.\nCheck your network connection and try again.', 'error')
            self.installButton.config(text = 'Quit', command = self.close)

    def track(self, errors):
        try:
            urllib.urlopen('http://analytics.joanpc.com/piwik.php?action_name=win_install&idsite=4&rec=1&send_image=0&url=http://x-plane.joanpc.com/OSXInstaller/install/%s/errors/%d' %
        VERSION, errors, context=ssl._create_unverified_context())
        except:
            pass

    def checkPython(self):

        if sys.platform.lower() == 'darwin':
            major, minor = platform.mac_ver()[0].split('.')[:2]
            if int(major) == 10 and int(minor) < 7:
                self.printStatus('WARNING: Your osx version doesn\'t ship with a 2.7 python installation.', 'warning')
                self.printStatus('Download and isntall Python 2.7 from http://www.python.com.', 'warning')
                return False
            else:
                self.printStatus('Your OSX version comes with Python 2.7 installed.', 'bold')
                return True
        elif sys.platform.lower() == 'win32':
            # Windows
            pass


    def sslContext(self, purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None, cadata=None):
        return ssl.create_default_context(cafile = 'certs.pem')

    def disableCertVerify(self):
        ssl._create_default_https_context  = self.sslContext

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
            self.printStatus('ERROR: No updates available', 'error')


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

        self.progress = tk.IntVar()
        self.progressbar = ttk.Progressbar(self, variable = self.progress)
        self.progressbar.pack(fill = 'both')

        self.updater.downloadProgress = self.downloadProgress

        frame = tk.Frame(self)
        frame.pack(fill = 'x')

        self.statusScroll = tk.Scrollbar(frame)
        self.statusScroll.pack(side = 'right', fill = 'y')

        self.status = tk.Text(frame, height = 8, padx = 5, pady = 5,
            state = 'disabled', bg = '#fff', yscrollcommand = self.statusScroll.set)
        self.status.tag_config("error", foreground="red")
        self.status.tag_config('warning', foreground='DarkOrange3')
        self.status.tag_config("bold", foreground="#006600")
        self.status.pack(side = 'left', fill = 'both')

        self.statusScroll.config(command = self.status.yview)

    def downloadProgress(self, count, blockSize, totalSize):
        self.progress.set( count * blockSize * 100 / totalSize )

    def selectXplaneFolder(self):
        if not self.processing:
            self.xp_path = tkFileDialog.askdirectory(title = 'Pick a folder', initialdir = '/')
            if self.xp_path:
                self.printStatus('Selected X-Plane folder:\n%s' % (self.xp_path))
            else:
                self.printStatus('No folder selected.', 'error')

    def printStatus(self, message, tag = None, newline = True):
        nl = ''
        if newline:
            nl = "\n"

        self.status.config(state='normal')
        self.status.insert('end', nl + message, tag)
        self.status.see('end')
        self.status.config(state='disabled')

        #self.statusCaption.set('%s%s%s' % (self.statusCaption.get(), nl, message))

    def threadDo(self, task, args):
        # Run a task on a thread while updating.
        # Python interface install
        window = self.winfo_toplevel()

        th = threading.Thread(target = task, args = [args])
        th.start()
        while th.is_alive():
            window.update()
            th.join(0.001)

    def close(self):
        if self.processing:
            self.printStatus('Still working, please wait', 'error')
        else:
            self.winfo_toplevel().destroy()

    def doInstalls(self):

        if not self.xp_path:
            self.printStatus('ERROR: No X-Plane folder selected.', 'error')
            return
        else:
            self.updater.xplanedir = self.xp_path

        if not self.updater.checkPaths():
            self.printStatus('ERROR: Accessing x-plane folder.', 'error')
            return

        if self.processing:
            self.printStatus('Processing, please wait.')
            return

        self.processing = True

        if self.installPythonInteface.get():

            self.printStatus('--\nInstalling %s' % 'Python Interface: ', 'bold')
            self.threadDo(self.updater.installPlugin, ['url'])
            self.printStatus('Installation Completed.', 'bold')

        for sid, install in self.installChecks.iteritems():
            if install.get():

                self.progress.set(0)
                self.progressbar.start(1000)
                self.printStatus('--\nInstalling %s: ' % (self.updates[sid]['name']))
                self.threadDo(self.updater.update, self.updates[sid])
                self.printStatus('Installation Completed.', 'bold')
                self.progressbar.stop()
                self.progress.set(100)
                self.winfo_toplevel().update()

        self.printStatus('-- \nALL installations COMPLETED.', 'bold')
        if self.updater.errors:
            self.printStatus('%d ERRORS during installation.' % (self.updater.errors), 'error')
        self.printStatus('-- \nThis installer is in development:\nPlease report your experience to x-plane@joanpc.com')
        self.processing = False
        self.track(self.updater.errors)
        self.installButton.config(text = 'Quit', command = self.close)

app = Application()
root = app.winfo_toplevel()
app.master.title('X-Plane Python Scripts Net Installer %s' % (VERSION))
root.protocol("WM_DELETE_WINDOW", app.close)
root.resizable(0,0)
root.call('wm', 'attributes', '.', '-topmost', True)
root.after_idle(root.call, 'wm', 'attributes', '.', '-topmost', False)
app.mainloop()
