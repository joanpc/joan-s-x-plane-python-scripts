'''
Fast Plan

If you don't have time to make your own flight-plans and program the x-plane FMC...
You should try this tool.

Just enter your departure and destination airports and FastPlan will find a route using 
http://rfinder.asalink.net/free/ and program your FMC.

Limitations:
Routes with more than 100 points doesn't fit the x-plane FMC.
FastPlan doesn't plan ascend and descent, Vertical Navigation it's on your hands. No SID/STAR.
You need an internet connection :)

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
from XPLMNavigation import *
from SandyBarbourUtilities import *
from PythonScriptMessaging import *
from XPLMPlugin import *
from XPLMMenus import *
from XPWidgetDefs import *
from XPWidgets import *
from XPStandardWidgets import *
import urllib2, urllib
import re
import os
import datetime

import threading
import Queue

# False constants
VERSION = "0.7"
RFIND_URL = "http://rfinder.asalink.net/free/autoroute_rtx.php"
NAVAID_TYPES = xplm_Nav_Airport + xplm_Nav_NDB + xplm_Nav_VOR + xplm_Nav_Fix + xplm_Nav_DME
AIRAC='1501'
HELP_CAPTION= 'Enter desired Origin and destination airport. ex: LEBL LEBB'
MAX_FMS_ENTRIES=100
XP_DB_MATCH_PRECISION=0.1
UFMC_PLANS_PATH='Resources/plugins/FJCC_FMC/FlightPlans'

class threadJob:
    '''
    Creates threaded job
    '''
    q = Queue.Queue()
    cyclewait = 0.5
    flightloops = []
    timeLimit = 45
    
    def __init__(self, plugin, job, args, callback):
        self.plugin = plugin
        self.job = job
        self.args = args
        self.callback = callback
        self.q = Queue.Queue()
        self.floop = self.floopCallback

        self.timer = 0

        self.floop = self.floopCallback
        XPLMRegisterFlightLoopCallback(self.plugin, self.floop, -1, 0)
        self.__class__.flightloops.append(self.floop)

        self.t = threading.Thread(target = self.run, args = ())
        self.t.start()
        
    def run(self):
        ret = self.job(*self.args)
        self.q.put(ret)
        
    def floopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        self.timer += elapsedMe
        if self.timer > self.timeLimit:
            self.callback(False)
            return 0
        if not self.q.empty():
            self.callback(self.q.get())
            return 0
        return self.cyclewait
    
    def clean(self):
        for floop in self.__class__.flightloops:
            XPLMUnregisterFlightLoopCallback(self.plugin, floop, 0)

class rfind:
    @classmethod
    def RouteFind(self, orig, destination, maxalt = 'FL330', minalt = 'FL330', ufmc = False):
        # Get current airac
        today = datetime.date.today()
        cycle = int(today.strftime('%j'))/28
        year = today.strftime('%y')
        AIRAC = "%s%02d" % (year, cycle)
        
        # query params
        params = urllib.urlencode({
        'dbid':      AIRAC,
        'ic1':       '',
        'ic2':       '',
        'id1':       orig,
        'id2':       destination,
        'k':         '832309203',
        'lvl':       'B',
        'maxalt':     maxalt,
        'minalt':     minalt,
        'nats':       'R',
        'rnav':       'Y',
        'usesid':     'Y',
        'usestar':    'Y',
        })
        
        # Server Connection
        res = urllib2.urlopen(RFIND_URL, params)
        # quick parse
        # TODO handle aiport not found
        file = res.readlines()
        it = iter(file)
        
        navpoints = []
        response = []
        
        # Parse route with arways
        for line in it:
            if '<tt>' in line[:5]:
                for i in re.findall('<b>([^<]*)<\/b> *([^< ]*)', line):
                    fix, way = i
                    navpoints.append(fix)
                    if not way in ['SID', 'STAR', '']:
                        navpoints.append(way)
                
                response.append(navpoints[:])
        
        # Parse fix route
        navpoints = []
        it = iter(file)
        rec = False
        
        for line in it:
            if '</pre>' in line:
                break
            if rec:
                m = re.search("([^ ]*) *([^ ]*) *([0-9]*) *([0-9]*)[^N|S]*([^ ]+)[^E|W]*([^ ]+) *", line)
                lat = m.group(5)
                lon = m.group(6)
                
                shift = 0
                if m.group(4): shift = 1
                heading = m.group(2 + shift)
                lat = float(lat[1:3]) + float(lat[8:10])/60 + float(lat[11:16])/3600
                lon = float(lon[1:4]) + float(lon[9:11])/60 + float(lon[12:17])/3600
                if m.group(5)[0] == 'S': lat *= -1
                if m.group(6)[0] == 'W': lon *= -1
                
                navpoints.append((m.group(1), lat, lon, heading))
            if ('<pre>' in line):
                rec = True
                        
        response.append(navpoints)
        return response
    
    @classmethod
    def clearFMS(self):
        # FIXME: -1 ?
        # Set destination
        XPLMSetDestinationFMSEntry(0)
        XPLMSetDisplayedFMSEntry(0)
        for i in range(0, XPLMCountFMSEntries(), -1):
            XPLMClearFMSEntry(i)
    @classmethod
    def CompressRoute(self, route):
        last = 'None'
        comp_route = []
        for i in range(len(route)):
            if last == route[i][3]:
                comp_route.pop()
            comp_route.append(route[i])
            last = route[i][3]
        return comp_route
    @classmethod
    def SaveUfmcPlan(self, path, plan):
        orig, dest = plan.pop(0), plan.pop(-1)
        star = 'DCT\n'
        if plan[0] == 'DCT': start = ''
        if plan[-1] == 'DCT': plan.pop(-1)
        
        fname = path + '/' + orig + dest + '.ufmc'
        f = open(fname , 'w')
        f.write(orig + '\n' + dest + '\n' + star + '\n'.join(plan) + '\n99\n\n')
        f.close()

    @classmethod
    def NavaidsToXplane(self, navaids):
        i = 0
        rfind.clearFMS()
        for navaid in navaids:
            id, lat, lon, hdn = navaid
            nref = XPLMFindNavAid(None, id, lat, lon, None, NAVAID_TYPES)
            if nref != XPLM_NAV_NOT_FOUND:
                xlat, xlon, outID = [], [], []
                # check if is the correct navaid by id and proximiy
                XPLMGetNavAidInfo(nref, None, xlat, xlon, None, None, None, outID, None, None)
                # Debug
                #print '--'
                #print outID
                #print lat, xlat[0], lon, xlon[0]
                #print abs(xlat[0] - lat), abs(xlon[0] -lon)

                if outID[0] != id or abs(xlat[0] - lat) > XP_DB_MATCH_PRECISION or abs(xlon[0] -lon) > XP_DB_MATCH_PRECISION:
                    XPLMSetFMSEntryLatLon(i, lat, lon, 0)
                else:  
                    XPLMSetFMSEntryInfo(i, nref, 0)        
                i += 1
            else:
                #add point manually
                XPLMSetFMSEntryLatLon(i, lat, lon, 0)
                i += 1
                pass
        # Set destination
        XPLMSetDestinationFMSEntry(0)
        XPLMSetDisplayedFMSEntry(0)

    @classmethod
    def copyToClipboard(self, text):
        from Tkinter import Tk
        w = Tk()
        w.withdraw()
        w.clipboard_clear()
        w.clipboard_append(text)
        w.destroy()

class PythonInterface:
    def XPluginStart(self):
        self.Name = "FastPlan - " + VERSION
        self.Sig = "FastPlan.joanpc.PI"
        self.Desc = "FastPlant rfinder FMC tool"
        
        self.window = False
        self.th = False
        
        self.ufmcPlansPath = False
        path = ""
        path = XPLMGetSystemPath(path)
        path += UFMC_PLANS_PATH
        # Disabled UFMC Support
        #if os.path.exists(path):
        #    self.ufmcPlansPath = path
        
        # Main menu
        self.Cmenu = self.mmenuCallback
        self.mPluginItem = XPLMAppendMenuItem(XPLMFindPluginsMenu(), 'Fast Plan FMC', 0, 1)
        self.mMain = XPLMCreateMenu(self, 'Fast Plan FMC', XPLMFindPluginsMenu(), self.mPluginItem, self.Cmenu, 0)
        self.mNewPlan = XPLMAppendMenuItem(self.mMain, 'New plan', False, 1)
        
        return self.Name, self.Sig, self.Desc
    
    def XPluginStop(self):
        XPLMDestroyMenu(self, self.mMain)
        if (self.window):
            XPDestroyWidget(self, self.WindowWidget, 1)
        
        if self.th:
            self.th.clean()
        
    def XPluginEnable(self):
        return 1
    
    def XPluginDisable(self):
        pass
    
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass
        
    def mmenuCallback(self, menuRef, menuItem):
        # Start/Stop menuitem
        if menuItem == self.mNewPlan:
            if (not self.window):
                self.CreateWindow(221, 640, 420, 90)
                self.window = True
            else:
                if(not XPIsWidgetVisible(self.WindowWidget)):
                    XPSetWidgetDescriptor(self.errorCaption, '')
                    XPShowWidget(self.WindowWidget)
            # Set nearest aiport
            #nref = XPLMFindNavAid('', '', False, False, False, xplm_Nav_Airport)
            #if nref: 
            #    airport = []
            #    # check if is the correct navaid by id and proximiy
            #    XPLMGetNavAidInfo(nref, None, None, None, None, None, None, airport, None, None)
            #    XPSetWidgetDescriptor(self.routeInput, airport[0] + ' ')
            # set focus
            XPSetKeyboardFocus(self.routeInput)

    def CreateWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h - 100
        Buffer = "Fast Plan to FMS"
        
        # Create the Main Widget window
        self.WindowWidget = XPCreateWidget(x, y, x2, y2, 1, Buffer, 1,    0, xpWidgetClass_MainWindow)
        
        # Config Sub Window, style
        subw = XPCreateWidget(x+10, y-30, x2-20 + 10, y2+40 -25, 1, "" ,  0,self.WindowWidget , xpWidgetClass_SubWindow)
        XPSetWidgetProperty(subw, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)
        x += 25
        y -= 20
        
        # Add Close Box decorations to the Main Widget
        XPSetWidgetProperty(self.WindowWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        
        # Help caption
        HelpCaption = XPCreateWidget(x+20, y-10, x+300, y-52, 1, HELP_CAPTION, 0, self.WindowWidget, xpWidgetClass_Caption)
        
        # find route button
        self.RouteButton = XPCreateWidget(x2 - 220, y-50, x2-140, y-72, 1, "To XP FMC", 0, self.WindowWidget, xpWidgetClass_Button)

        x2 = 0
        self.UfmcButton = False
        # UFMC button
        if (self.ufmcPlansPath):
            # find route button
            self.UfmcButton = XPCreateWidget(x2 - 220, y-50, x2-140, y-72, 1, "To UFMC", 0, self.WindowWidget, xpWidgetClass_Button)
            x2 = -100

        XPSetWidgetProperty(self.RouteButton, xpProperty_ButtonType, xpPushButton)
        
        # Route input
        self.routeInput = XPCreateWidget(x+20, y-50, x+160, y-72, 1, "", 0, self.WindowWidget, xpWidgetClass_TextField)
        XPSetWidgetProperty(self.routeInput, xpProperty_TextFieldType, xpTextEntryField)
        XPSetWidgetProperty(self.routeInput, xpProperty_Enabled, 1)
        
        y -= 40
        # Help caption
        XPCreateWidget(x+20, y-50, x+300, y-72, 1, "Route output:", 0, self.WindowWidget, xpWidgetClass_Caption)
        # Route output
        self.routeOutput = XPCreateWidget(x+20, y-70, x+360, y-92, 1, "", 0, self.WindowWidget, xpWidgetClass_TextField)
        XPSetWidgetProperty(self.routeOutput, xpProperty_TextFieldType, xpTextEntryField)
        XPSetWidgetProperty(self.routeOutput, xpProperty_Enabled, 1)
        
        y -= 20
        
        # Error caption
        self.errorCaption = XPCreateWidget(x+20, y-70, x+300, y-90, 1, '', 0, self.WindowWidget, xpWidgetClass_Caption)
        
        # Register our widget handler
        self.WindowHandlerrCB = self.WindowHandler
        XPAddWidgetCallback(self, self.WindowWidget, self.WindowHandlerrCB)
        
        # set focus
        XPSetKeyboardFocus(self.routeInput)
        pass

    def WindowHandler(self, inMessage, inWidget, inParam1, inParam2):
        if (inMessage == xpMessage_CloseButtonPushed):
            if (self.window):
                XPHideWidget(self.WindowWidget)
            return 1

        # Handle any button pushes
        if (inMessage == xpMsg_PushButtonPressed):

            XPSetWidgetDescriptor(self.errorCaption, '')
            buff = []
            XPGetWidgetDescriptor(self.routeInput, buff, 256)
            param = buff[0].split(' ')
                
            if (inParam1 == self.RouteButton):
                if len(param) > 1:

                    XPSetWidgetDescriptor(self.errorCaption, 'Loading route from the net.')
                    XPSetWidgetProperty(self.RouteButton, xpProperty_Enabled, 0)
                    
                    self.th = threadJob(self, rfind.RouteFind, (param[0], param[1]), self.rfindCallback)
                    
                return 1
            if (inParam1 == self.UfmcButton):
                if len(param) > 1:
                    XPHideWidget(self.WindowWidget)
                    route, troute = rfind.RouteFind(param[0], param[1], ufmc = True)
                    if len(route) > 1:
                        rfind.SaveUfmcPlan(self.ufmcPlansPath, route)
                    else:
                        XPSetWidgetDescriptor(self.errorCaption, 'ERROR: route not found.')
                        XPShowWidget(self.WindowWidget)
                        XPSetKeyboardFocus(self.routeInput)
                return 1    
                
        return 0
        
    def rfindCallback(self, args):
        
        XPSetWidgetProperty(self.RouteButton, xpProperty_Enabled, 1)
        
        if not args:
            XPSetWidgetDescriptor(self.errorCaption, 'Failed.')
            return 0
        
        XPSetWidgetDescriptor(self.errorCaption, 'Route loaded.')
        
        uroute, route = args
        nfix = len(route)
        if 1 < nfix <= MAX_FMS_ENTRIES:
            rfind.NavaidsToXplane(route)
            #rfind.copyToClipboard(' '.join(uroute))
            #XPSetWidgetDescriptor(self.errorCaption, 'Route copied to clipboard')
            XPSetWidgetDescriptor(self.routeOutput, ' '.join(uroute))
        else:
            route = rfind.CompressRoute(route)
            if nfix > 1 and len(route) < MAX_FMS_ENTRIES:
                rfind.NavaidsToXplane(route)
            else:
                XPSetWidgetDescriptor(self.errorCaption, 'ERROR: route not found or too large to fit on the FMS')
                XPShowWidget(self.WindowWidget)
                XPSetKeyboardFocus(self.routeInput)