'''
Weight & Fuel: Profiles and Set by numbers

Allows storing the current Weight and Fuel in profiles and provides 
a dialog for setting W&F by numbers (no imprecise sliders) 

Can be easily modified to story any kind of dataref into profiles.

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
from XPWidgetDefs import *
from XPWidgets import *
from XPStandardWidgets import *
from os import path
import cPickle

# False constants
VERSION='0.2'
PRESETS_FILE='WFprofiles.wfp'
HELP_CAPTION='Profile name: '

# Conversion rates
LB2KG=0.45359237
KG2LB=2.20462262

# Uncomment the following line switch to the great metric system.
#LB2KG, KG2LB = 1,1

#
# Datarefs to store 
#
# Modify the following dict to add more datarefs to store in your profiles
#
DATAREFS = {
            'Payload':      'sim/flightmodel/weight/m_fixed',
            'Fuel tanks':   'sim/flightmodel/weight/m_fuel[0:9]',
            'jettison':     'sim/flightmodel/weight/m_jettison',
            'JATO':         'sim/flightmodel/misc/jato_left'
            }

class PythonInterface:
    def XPluginStart(self):
        self.Name = "WFpresets - " + VERSION
        self.Sig = "WFpresets.joanpc.PI"
        self.Desc = "Weight and fuel profiles"
        
        # Array of presets
        self.presets = []
        self.presetFile = False
        
        self.window, self.fuelWindow = False, False
        
        self.Mmenu = self.mainMenuCB
        self.Lmenu = self.loadMenuCB
        self.Dmenu = self.deleteMenuCB
        
        self.mPluginItem = XPLMAppendMenuItem(XPLMFindPluginsMenu(), 'W & Fuel Profiles', 0, 1)
        self.mMain = XPLMCreateMenu(self, 'W & Fuel Profiles', XPLMFindPluginsMenu(), self.mPluginItem, self.Mmenu, 0)
        
        # Load/Delete Menu
        self.mLoadItem = XPLMAppendMenuItem(self.mMain, 'Load profile', 0, 1)
        self.mLoad = XPLMCreateMenu(self, 'Load preset', self.mMain, self.mLoadItem, self.Lmenu, 0)
        
        self.mDeleteItem = XPLMAppendMenuItem(self.mMain, 'Delete profile', 0, 1)
        self.mDelete = XPLMCreateMenu(self, 'Delete preset', self.mMain, self.mDeleteItem, self.Dmenu, 0)
        
        # Save menu item
        self.mSave =  XPLMAppendMenuItem(self.mMain, 'New profile', 0, 1)
        
        # Set fuel by numbers
        self.mSetFuel =  XPLMAppendMenuItem(self.mMain, 'Set W & Fuel by numbers', 1, 1)
        
        self.values = {}
        
        # Init datarefs
        for key in DATAREFS: self.values[key] = EasyDref(DATAREFS[key])
        
        # Init fuel datarefs 
        self.fuel = self.values['Fuel tanks']
        self.drPayLoad = self.values['Payload']
        self.drNFuelTanks = EasyDref('sim/aircraft/overflow/acf_num_tanks(int)')
        
        return self.Name, self.Sig, self.Desc
    
    def float(self, string):
        # try to convert to float or return 0
        try: 
            val = float(string)
        except ValueError:
            val = 0.0
        return val
    
    def rebuildMenu(self, setDefault = False):
        XPLMClearAllMenuItems(self.mLoad)
        XPLMClearAllMenuItems(self.mDelete)
        
        for i in range(len(self.presets)):
            name = self.presets[i]['name']
            # Load default
            if setDefault and self.presets[i]['default']:
                self.LoadPreset(i)
            XPLMAppendMenuItem(self.mLoad, name , i, 1)
            XPLMAppendMenuItem(self.mDelete, 'delete: ' + name, i, 1)
        pass
    
    def XPluginStop(self):
        XPLMDestroyMenu(self, self.mMain)
        pass
        
    def XPluginEnable(self):
        return 1
    
    def XPluginDisable(self):
        pass
    
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        if (inFromWho == XPLM_PLUGIN_XPLANE):
            if (inFromWho == XPLM_PLUGIN_XPLANE and inParam == XPLM_PLUGIN_XPLANE):
                # Destroy fuel window
                if self.fuelWindow:
                    XPDestroyWidget(self, self.FuelWindowWidget, 1)
                    self.fuelWindow = False
            # On plane load
            if (inParam == XPLM_PLUGIN_XPLANE and inMessage == XPLM_MSG_AIRPORT_LOADED ): # On aircraft change
                plane, plane_path = XPLMGetNthAircraftModel(0)
                self.presets = []
                self.presetFile = plane_path[:-len(plane)] + PRESETS_FILE
                if path.lexists(self.presetFile):
                    self.LoadPresetFile(self.presetFile)
                self.rebuildMenu(True)
    
    def SavePresetFile(self, filename):
        f = open(filename, 'w')
        cPickle.dump(self.presets, f)
        f.close()
    
    def LoadPresetFile(self, filename):
        f = open(filename, 'r')
        self.presets = cPickle.load(f)
        f.close()
    
    def SavePreset(self, presetName, default = False):
        if self.presetFile:
            if default:
                for preset in self.presets:
                    preset['default'] = False
            
            data = {}        
            for key in self.values:
                data[key] = self.values[key].value
                
            self.presets.append({'name': presetName, 'default': default, 'data': data})
            self.SavePresetFile(self.presetFile)
            self.rebuildMenu()
    
    def LoadPreset(self, npreset):
        data = self.presets[npreset]['data']
        
        for key in data:
            if key in self.values:
                self.values[key].value = data[key]
            
    def DeletePreset(self, npreset):
        if self.presetFile:
            self.presets.pop(npreset)
            self.SavePresetFile(self.presetFile)
            self.rebuildMenu()
    
    def mainMenuCB(self, menuRef, menuItem):
        # Save menu
        if menuItem == 0:
            if (not self.window):
                 self.CreateWindow(221, 640, 220, 90)
                 self.window = True
            
            elif (not XPIsWidgetVisible(self.WindowWidget)):
                  XPShowWidget(self.WindowWidget)
                  XPSetKeyboardFocus(self.nameInput)
        
        if menuItem == 1:
            if (not self.fuelWindow):
                 self.CreateFuelWindow(221, 640, 220, 105)
                 self.fuelWindow = True
            
            elif (not XPIsWidgetVisible(self.FuelWindowWidget)):
                  XPShowWidget(self.FuelWindowWidget)
                  self.FuelWindowUpdate()
                  #XPSetKeyboardFocus(self.nameInput)
                  
            
    def loadMenuCB(self, menuRef, menuItem):
        self.LoadPreset(menuItem)
    
    def deleteMenuCB(self, menuref, menuItem):
        self.DeletePreset(menuItem)

    def CreateWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Buffer = "New weight and fuel Profile"
        
        # Create the Main Widget window
        self.WindowWidget = XPCreateWidget(x, y, x2, y2, 1, Buffer, 1,0 , xpWidgetClass_MainWindow)
        
        # Add Close Box decorations to the Main Widget
        XPSetWidgetProperty(self.WindowWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        
        # Help caption
        HelpCaption = XPCreateWidget(x+20, y-10, x+150, y-52, 1, HELP_CAPTION, 0, self.WindowWidget, xpWidgetClass_Caption)
        
        # Save preset button
        self.SaveButton = XPCreateWidget(x+160, y-40, x+200, y-62, 1, "Save", 0, self.WindowWidget, xpWidgetClass_Button)
        XPSetWidgetProperty(self.SaveButton, xpProperty_ButtonType, xpPushButton)
        
        # Route input
        self.nameInput = XPCreateWidget(x+20, y-40, x+150, y-62, 1, "", 0, self.WindowWidget, xpWidgetClass_TextField)
        XPSetWidgetProperty(self.nameInput, xpProperty_TextFieldType, xpTextEntryField)
        XPSetWidgetProperty(self.nameInput, xpProperty_Enabled, 1)
        
        # Default checkbox
        self.defaultCheck = XPCreateWidget(x+20, y-60, x+30, y-82, 1, "", 0, self.WindowWidget, xpWidgetClass_Button)
        XPSetWidgetProperty(self.defaultCheck, xpProperty_ButtonType, xpRadioButton)
        XPSetWidgetProperty(self.defaultCheck, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
        
        # Checkbox caption
        XPCreateWidget(x+30, y-60, x+120, y-82, 1, 'default: (load on startup)', 0, self.WindowWidget, xpWidgetClass_Caption)
        
        # Register our widget handler
        self.WindowHandlerrCB = self.WindowHandler
        XPAddWidgetCallback(self, self.WindowWidget, self.WindowHandlerrCB)
        
        # set focus
        XPSetKeyboardFocus(self.nameInput)
        pass
    
    def CreateFuelWindow(self, x, y, w, h):
        # Get number of fuel tanks
        self.nFuelTanks = self.drNFuelTanks.value
        
        x2 = x + w
        y2 = y - h - self.nFuelTanks * 20 
        Buffer = "Set Weight Fuel by numbers"
        
        # Create the Main Widget window
        self.FuelWindowWidget = XPCreateWidget(x, y, x2, y2, 1, Buffer, 1,0 , xpWidgetClass_MainWindow)
        
        # Add Close Box decorations to the Main Widget
        XPSetWidgetProperty(self.FuelWindowWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        
        XPCreateWidget(x+15, y-46, x+35, y-54, 1, 'Payload', 0, self.FuelWindowWidget, xpWidgetClass_Caption)
        self.payLoadInput = XPCreateWidget(x+60, y-40, x+190, y-62, 1, "", 0, self.FuelWindowWidget, xpWidgetClass_TextField)
        XPSetWidgetProperty(self.payLoadInput, xpProperty_TextFieldType, xpTextEntryField)
        XPSetWidgetProperty(self.payLoadInput, xpProperty_Enabled, 1)
        y -= 25
        
        self.tankInput = []
         
        for i in range(self.nFuelTanks):
            XPCreateWidget(x+20, y-46, x+40, y-54, 1, 'Tank ' + str(i+1), 0, self.FuelWindowWidget, xpWidgetClass_Caption)
            tankInput = XPCreateWidget(x+60, y-40, x+190, y-62, 1, "", 0, self.FuelWindowWidget, xpWidgetClass_TextField)
            XPSetWidgetProperty(tankInput, xpProperty_TextFieldType, xpTextEntryField)
            XPSetWidgetProperty(tankInput, xpProperty_Enabled, 1)
            y -= 20
            self.tankInput.append(tankInput)
        
        self.FuelWindowUpdate()
        
        # Save button
        self.FuelSaveButton = XPCreateWidget(x+160, y-50, x+200, y-62, 1, "Save", 0, self.FuelWindowWidget, xpWidgetClass_Button)
        XPSetWidgetProperty(self.FuelSaveButton, xpProperty_ButtonType, xpPushButton)
        
        # Register our widget handler
        self.FuelWindowHandlerCB = self.FuelWindowHandler
        XPAddWidgetCallback(self, self.FuelWindowWidget, self.FuelWindowHandlerCB)
        
        
    def FuelWindowUpdate(self):
        fuelTanks = self.fuel.value
        
        XPSetWidgetDescriptor(self.payLoadInput, "%.0f" % (self.drPayLoad.value * KG2LB))
        
        for i in range(self.nFuelTanks):
            XPSetWidgetDescriptor(self.tankInput[i], "%.0f" % (fuelTanks[i] * KG2LB))
        pass
    
    def FuelWindowHandler(self, inMessage, inWidget, inParam1, inParam2):
        if (inMessage == xpMessage_CloseButtonPushed):
            if (self.fuelWindow):
                XPHideWidget(self.FuelWindowWidget)
            return 1

        # Handle any button pushes
        if (inMessage == xpMsg_PushButtonPressed):

            if (inParam1 == self.FuelSaveButton):
                buff = []
                XPGetWidgetDescriptor(self.payLoadInput, buff, 256)
                self.drPayLoad.value = self.float(buff[0]) * LB2KG
                
                data = []
                for i in range(self.nFuelTanks):
                    buff = []
                    XPGetWidgetDescriptor(self.tankInput[i], buff, 256)
                    data.append(self.float(buff[0]) * LB2KG)
                self.fuel.value = data
                return 1
        return 0

    def WindowHandler(self, inMessage, inWidget, inParam1, inParam2):
        if (inMessage == xpMessage_CloseButtonPushed):
            if (self.window):
                XPHideWidget(self.WindowWidget)
            return 1

        # Handle any button pushes
        if (inMessage == xpMsg_PushButtonPressed):

            if (inParam1 == self.SaveButton):
                #XPSetWidgetDescriptor(self.errorCaption, '')
                buff = []
                XPGetWidgetDescriptor(self.nameInput, buff, 256)
                default = XPGetWidgetProperty(self.defaultCheck, xpProperty_ButtonState, None)
                name = buff[0]
                if len(name) > 1:
                    XPHideWidget(self.WindowWidget)
                    self.SavePreset(name, default)
                    XPSetWidgetDescriptor(self.nameInput, '')
                    XPSetWidgetProperty(self.defaultCheck, xpProperty_ButtonState, 0)
                return 1
        return 0

'''

Includes

'''
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