'''
PI_CSV_logger Script

Logs dataref values in a csv file

If you have problems opening the csv file try opening it with LibreOffice/OpenOffice, msexcel is a pain with csv files.
Select UTF-8 encoding and ; (semicolon) as separator.

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

from XPLMDefs import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *
from XPLMPlanes import *
from SandyBarbourUtilities import *
from PythonScriptMessaging import *
from XPLMPlugin import *
from XPLMMenus import *
from datetime import *

import ConfigParser
from os import path, makedirs

CONF_FILENAME = 'CSV_logger.ini'
ACF_CONF_FILENAME = CONF_FILENAME
VERSION = "1.0"

class PythonInterface:
    def XPluginStart(self):
        self.Name = "CSV_logger - " + VERSION
        self.Sig = "csvlogger.joanpc.PI"
        self.Desc = "simple CSV Logger script"
        
        self.separator = ','
        self.sys_path = ""
        self.logfile = False
        self.sys_path = XPLMGetSystemPath(self.sys_path)
        
        self.samplerate = 0.5
        
        self.hcols = []
        self.cols = []
        
        self.outpath = self.sys_path + 'Output/CSV_logger'
        self.loggin = False
        self.autostart = False
        
        # floop
        self.floop = self.floopCallback
        XPLMRegisterFlightLoopCallback(self, self.floop, 0, 0)
        
        # Main menu
        self.Cmenu1 = self.mmenuCallback1
        self.mPluginItem = XPLMAppendMenuItem(XPLMFindPluginsMenu(), 'CSV Logger', 0, 1)
        self.mMain = XPLMCreateMenu(self, 'CSV Logger', XPLMFindPluginsMenu(), self.mPluginItem, self.Cmenu1, 0)
        self.mToggle = XPLMAppendMenuItem(self.mMain, 'Start', False, 1)
        # rate menu
        self.Cmenu2 = self.mmenuCallback2
        self.mRateItem = XPLMAppendMenuItem(self.mMain, 'rate:     ', False, 1)
        self.mRate = XPLMCreateMenu(self, 'rate: ' + str(self.samplerate) , self.mMain, self.mRateItem, self.Cmenu2, 0)
        self.mr5m  = XPLMAppendMenuItem(self.mRate, '5min', 5*60*1000, 1)
        self.mr1m  = XPLMAppendMenuItem(self.mRate, '1min', 60*1000, 1)
        self.mr10s = XPLMAppendMenuItem(self.mRate, '10s', 10*1000, 1)
        self.mr1s  = XPLMAppendMenuItem(self.mRate, '1s', 1000, 1)
        self.mr1ms = XPLMAppendMenuItem(self.mRate, '100ms', 100, 1)
        
        self.getConfig(True)
        
        return self.Name, self.Sig, self.Desc
    
    def mmenuCallback1(self, menuRef, menuItem):
        # Start/Stop menuitem
        if menuItem == 0:
            if self.loggin:
                self.autostart = False
                self.stop()
            else:
                self.autostart = True
                self.start()
                    
    def mmenuCallback2(self, menuRef, menuItem):
        # Samplerate menu
        self.samplerate = menuItem * 0.001
        XPLMSetMenuItemName(self.mMain, self.mRateItem, 'rate: ' + str(self.samplerate) + 's', 1)  

    def XPluginStop(self):
        self.stop()
        XPLMUnregisterFlightLoopCallback(self, self.floop, 0)
        XPLMDestroyMenu(self, self.mRate)
        XPLMDestroyMenu(self, self.mMain)
        pass
        
    def XPluginEnable(self):
        return 1
    
    def XPluginDisable(self):
        pass
    
    def getConfig(self, startup = True):

        self.hcols = []
        self.cols = []
        
        config = ConfigParser.RawConfigParser(False)
        
        # Load only the main config on startup
        if (startup):
            config.read(self.sys_path + 'Resources/plugins/PythonScripts/' + CONF_FILENAME)
        else:
            # Try to load the aircraft config or reset the main conf
            plane, plane_path = XPLMGetNthAircraftModel(0)
            if (not config.read(plane_path[:-4] + ACF_CONF_FILENAME)):
                if (not config.read(plane_path[:-len(plane)] + CONF_FILENAME)):
                    config.read(self.sys_path + 'Resources/plugins/PythonScripts/' + CONF_FILENAME)
                    
        for section in config.sections():            
            #print("[" + section + "]", 2)
            if (section == "DATA"):
                for item in config.items(section):
                    # get col names and datarefs
                    # print item
                    dref = EasyDref(item[1])
                    if dref.isarray:
                        self.hcols.extend([item[0] + str(i) for i in range(dref.index, dref.last + 1)])
                    else:
                        self.hcols.append(item[0])
                    self.cols.append(dref)
            if (section == 'CONFIG'):
                for item in config.items(section):
                    # print item
                    if item[0] == 'samplerate':
                        self.samplerate = float(item[1])
                        XPLMSetMenuItemName(self.mMain, self.mRateItem, 'rate: ' + str(self.samplerate) + 's', 1)
                    if item[0] == 'separator':
                        self.separator = item[1]
                    if item[0] == 'autostart':
                        self.autostart = item[1].lower() in ('true', 'yes', 'y', '1')
                        print 'autostart', self.autostart
    
    def clearConfig(self):
        pass
    
    def start(self):
        # Open a new file and enable floop
        XPLMSetMenuItemName(self.mMain, self.mToggle, 'stop', 1)
        XPLMSetFlightLoopCallbackInterval(self, self.floop, self.samplerate, 0, 0)
        self.loggin = True
    
    def stop(self):
        # stop floop and close logfile
        XPLMSetMenuItemName(self.mMain, self.mToggle, 'start', 1)
        XPLMSetFlightLoopCallbackInterval(self, self.floop, 0, 0, 0)
        if self.logfile:
            self.logfile.close()
            self.logfile = False
        self.loggin = False

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        if (inFromWho == XPLM_PLUGIN_XPLANE and inParam == XPLM_PLUGIN_XPLANE):
            
            # On plane load
            if (inMessage == XPLM_MSG_PLANE_LOADED ):
                self.stop()
                self.clearConfig()
                self.getConfig()
                if (self.autostart):
                    self.start()
            
            # On airport load
            if (inMessage == XPLM_MSG_AIRPORT_LOADED):
                self.stop()
                if (self.autostart):
                    self.start()
    
    def floopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        '''
        Floop Callback
        gets all the data and prints it to file
        '''
        output = []
        
        if not self.logfile:
            if not path.exists(self.outpath):
                makedirs(self.outpath)
            
            plane, plane_path = XPLMGetNthAircraftModel(0)
            logname = plane[:-4].upper() + '_' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.csv'
            self.logfile = open(self.outpath + '/' + logname, 'w')
            self.logfile.write(self.separator.join(self.hcols) + '\n')
        
        for item in self.cols:
            if item.isarray:
                output.extend(['{0:-f}'.format(value) for value in item.value])
            else:
                output.append('{0:-f}'.format(item.value))
        
        #print self.separator.join(output)
        self.logfile.write(self.separator.join(output) + '\n')
        
        return self.samplerate
    
class EasyDref:    
    '''
    Easy Dataref access
    
    Copyright (C) 2011  Joan Perez i Cauhe
    '''
    def __init__(self, dataref, type = "float"):
        # Clear dataref
        dataref = dataref.strip()
        self.isarray, dref = False, False
        
        if ('"' in dataref):
            dref = dataref.split('"')[1]
            dataref = dataref[dataref.rfind('"')+1:]
        
        if ('(' in dataref):
            # Detect embedded type, and strip it from dataref
            type = dataref[dataref.find('(')+1:dataref.find(')')]
            dataref = dataref[:dataref.find('(')] + dataref[dataref.find(')')+1:]
        
        if ('[' in dataref):
            # We have an array
            self.isarray = True
            range = dataref[dataref.find('[')+1:dataref.find(']')].split(':')
            dataref = dataref[:dataref.find('[')]
            if (len(range) < 2):
                range.append(range[0])
            
            self.initArrayDref(range[0], range[1], type)
            
        elif (type == "int"):
            self.dr_get = XPLMGetDatai
            self.dr_set = XPLMSetDatai
            self.cast = int
        elif (type == "float"):
            self.dr_get = XPLMGetDataf
            self.dr_set = XPLMSetDataf
            self.cast = float  
        elif (type == "double"):
            self.dr_get = XPLMGetDatad
            self.dr_set = XPLMSetDatad
            self.cast = float
        else:
            print "ERROR: invalid DataRef type", type
        
        if dref: dataref = dref
        self.DataRef = XPLMFindDataRef(dataref)
        if self.DataRef == False:
            print "Can't find " + dataref + " DataRef"
    
    def initArrayDref(self, first, last, type):
        self.index = int(first)
        self.count = int(last) - int(first) +1
        self.last = int(last)
        
        if (type == "int"):
            self.rget = XPLMGetDatavi
            self.rset = XPLMSetDatavi
            self.cast = int
        elif (type == "float"):
            self.rget = XPLMGetDatavf
            self.rset = XPLMSetDatavf
            self.cast = float  
        elif (type == "bit"):
            self.rget = XPLMGetDatab
            self.rset = XPLMSetDatab
            self.cast = float
        else:
            print "ERROR: invalid DataRef type", type
        pass

    def set(self, value):
        if (self.isarray):
            self.rset(self.DataRef, value, self.index, len(value))
        else:
            self.dr_set(self.DataRef, self.cast(value))
            
    def get(self):
        if (self.isarray):
            list = []
            self.rget(self.DataRef, list, self.index, self.count)
            return list
        else:
            return self.dr_get(self.DataRef)
        
    def __getattr__(self, name):
        if name == 'value':
            return self.get()
        else:
            raise AttributeError
    
    def __setattr__(self, name, value):
        if name == 'value':
            self.set(value)
        else:
            self.__dict__[name] = value