'''
Joanpc X-Plane Python Scripts update plugin

Copyright (C) 2011  Joan Perez i Cauhe
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

VERSION = '1.0'
UPDATE_URL='https://raw.github.com/joanpc/joan-s-x-plane-python-scripts/master/versions.json'

import json
import urllib
import tempfile
import os
from zipfile import ZipFile
from shutil import move, rmtree, copytree, copy

class XPScriptsUpdater:
    ''' Process script updates
    '''
    updates = []
    
    def __init__(self, xplanedir, plugin = False):
        self.xplanedir = xplanedir
        pass
    
    def versionFromName(self, name):
        n = name.rfind('-')
        if n:
            return name[n+1:].strip()
        else:
            return 'na'
    
    def listScripts(self):
        ''' List Xplane Python Scripts
        '''
        nscripts = PI_CountScripts()
        scripts = {}
        for i in range(nscripts):
            sid = PI_GetNthScript(i)
            name, signature, description = PI_GetScriptInfo(sid)
            # Try to get version from the name
            version = self.versionFromName(name)
            scripts[signature] = {'name': name, 'version': version, 'description': description}
            
        return scripts
    
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
        print update
        
        if not os.path.exists(dpath):
            os.mkdir(dpath)
        
        if update['update_type'] == 'direct' and update['update_filename']:
            urllib.urlretrieve(update['update_url'], dpath + '/'  +  update['update_filename'])
            copy(dpath + '/'  +  update['update_filename'], installpath + '/'  +  update['update_filename'])            
            print dpath + '/'  +  update['update_filename'], installpath + '/'  +  update['update_filename']
            
        elif update['update_type'] == 'zip':
            zipfile = dpath + '/._xpjpcUPDATE.zip'
            # Download update
            urllib.urlretrieve(update['update_url'], zipfile)
            zip = ZipFile(zipfile, 'r')
            
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
    
    def findUpdates(self, signature = False, version = False):
        if signature and version:
            scripts = {signature: {'version' : version}}
        else:
            scripts = self.listScripts()
        
        res = urllib.urlopen(UPDATE_URL)
        #res = open('./versions.json', 'r')
        versions = json.load(res)
        updates = {}
        for signature, data in versions.iteritems():
            updates[signature] = data
            if signature in scripts:
                # Script installed
                if data['version'] != scripts[signature]['version']:
                    action = 'update'
                else:
                    action = 'na'
                current_ver =  scripts[signature]['version']   
            else:
                # Not installed
                action = 'install'
                current_ver = 'na'
            updates[signature]['action'] = action
            updates[signature]['current_version'] = current_ver
        return updates
        
    
'''
X-Plane Plugin
'''
from XPLMDefs import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *
from XPLMPlanes import *
from XPLMNavigation import *
from SandyBarbourUtilities import *
from PythonScriptMessaging import *
from XPLMPlugin import *
from XPLMMenus import *
from XPWidgetDefs import *
from XPWidgets import *
from XPStandardWidgets import *

class PythonInterface:

    def XPluginStart(self):
        self.Name = "Joan's Scripts Updater - " + VERSION
        self.Sig = "ScriptUpdater.joanpc.PI"
        self.Desc = "Script Updater tool"
        
        self.window = False
        
        self.path = ""
        self.path = XPLMGetSystemPath(self.path)
        
        # Create a updater instance
        self.updater = XPScriptsUpdater(self.path)
        
        # Main menu
        self.Cmenu = self.mmenuCallback
        self.mPluginItem = XPLMAppendMenuItem(XPLMFindPluginsMenu(), 'Script Updater', 0, 1)
        self.mMain = XPLMCreateMenu(self, 'Script Updater', XPLMFindPluginsMenu(), self.mPluginItem, self.Cmenu, 0)
        self.mCheckUpdates = XPLMAppendMenuItem(self.mMain, 'Check Updates', False, 1)
        
        return self.Name, self.Sig, self.Desc
    
    def XPluginStop(self):
        XPLMDestroyMenu(self, self.mMain)
        if (self.window):
            XPDestroyWidget(self, self.WindowWidget, 1)
        pass
        
    def XPluginEnable(self):
        return 1
    
    def XPluginDisable(self):
        pass
    
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass
        
    def mmenuCallback(self, menuRef, menuItem):
        if menuItem == self.mCheckUpdates:
            self.updates = self.updater.findUpdates()
            if (not self.window):
                self.CreateWindow(221, 640, 420, 90)
                self.window = True
            else:
                if(not XPIsWidgetVisible(self.WindowWidget)):
                    XPSetWidgetDescriptor(self.statusCaption, '')
                    XPShowWidget(self.WindowWidget)

    def CreateWindow(self, x, y, w, h):
        x2 = x + w + 80
        y2 = y - h - len(self.updates) * 26 -20
        Buffer = "Joan's Xplane Scripts Installer/Updater"
        
        # Create the Main Widget window
        self.WindowWidget = XPCreateWidget(x, y, x2, y2, 1, Buffer, 1,    0, xpWidgetClass_MainWindow)
        
        # Add Close Box decorations to the Main Widget
        XPSetWidgetProperty(self.WindowWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        
        # Config Sub Window, style
        subw = XPCreateWidget(x + 10, y-30, x2 - 10, y2 + 40, 1, "" ,  0,self.WindowWidget , xpWidgetClass_SubWindow)
        XPSetWidgetProperty(subw, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)
        
        y -= 38
        x += 40
        
        # Help caption
        XPCreateWidget(x, y, x+180, y-20, 1, 'Script Name', 0, self.WindowWidget, xpWidgetClass_Caption)
        XPCreateWidget(x +180, y, x2, y-20, 1, 'Ver. avail.', 0, self.WindowWidget, xpWidgetClass_Caption)
        XPCreateWidget(x +240, y, x2, y-20, 1, 'Ver. inst.', 0, self.WindowWidget, xpWidgetClass_Caption)
        
        self.buttons = {}
        y -=28
        
        for sid, data in self.updates.iteritems():
            button = False
            XPCreateWidget(x, y, x+180, y-20, 1, data['name'], 0, self.WindowWidget, xpWidgetClass_Caption)
            XPCreateWidget(x +180, y, x2, y-20, 1, data['version'], 0, self.WindowWidget, xpWidgetClass_Caption)
            XPCreateWidget(x +240, y, x2, y-20, 1, data['current_version'], 0, self.WindowWidget, xpWidgetClass_Caption)
            
            # Update/Install buttons
            if data['action'] == "install" or data['action'] == "update":
                button = XPCreateWidget(x+310, y, x+400, y-20, 1, data['action'], 0, self.WindowWidget, xpWidgetClass_Button)
            else:
                XPCreateWidget(x + 310, y, x+400, y-20, 1, 'up to date', 0, self.WindowWidget, xpWidgetClass_Caption)
            if button:
                # Store script signature related to the buttons
                XPSetWidgetProperty(button, xpProperty_ButtonType, xpPushButton)
                self.buttons[button] = sid
                
            y -=26
        # Status caption
        y -= 10
        self.statusCaption = XPCreateWidget(x, y, x+400, y-20, 1, 'Ready to update', 0, self.WindowWidget, xpWidgetClass_Caption)
        self.reloadButton = XPCreateWidget(x+310, y, x+400, y-20, 0, 'reload plugins', 0, self.WindowWidget, xpWidgetClass_Button)
        
        # Register our widget handler
        self.WindowHandlerrCB = self.WindowHandler
        XPAddWidgetCallback(self, self.WindowWidget, self.WindowHandlerrCB)
        

    def WindowHandler(self, inMessage, inWidget, inParam1, inParam2):
        if (inMessage == xpMessage_CloseButtonPushed):
            if (self.window):
                #XPHideWidget(self.WindowWidget)
                XPDestroyWidget(self, self.WindowWidget, 1)
                self.window = False
            return 1

        # Handle any button pushes
        if (inMessage == xpMsg_PushButtonPressed):    
            if inParam1 in self.buttons:
                # Install/Update action
                XPHideWidget(inParam1)
                XPSetWidgetDescriptor(self.statusCaption, 'Updating: ' + self.buttons[inParam1] + ' please wait..')
                XPShowWidget(self.reloadButton)
                self.updater.update(self.updates[self.buttons[inParam1]])
                XPSetWidgetDescriptor(self.statusCaption, 'Update suceeded, reload plugins')
                return 1
            elif inParam1 == self.reloadButton:
                XPLMReloadPlugins()   
                return 1
        return 0