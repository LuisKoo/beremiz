#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2016 - 2017: Andrey Skvortsov <andrej.skvortzov@gmail.com>
#
# See COPYING file for copyrights details.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.



import os, sys, getopt
import time
import __builtin__

class BeremizIDELauncher:
    def __init__(self):
        self.updateinfo_url = None
        self.extensions = []
        self.app_dir = os.path.dirname(os.path.realpath(__file__))
        self.projectOpen = None
        self.buildpath = None
        self.splash = None
        self.splashPath = self.Bpath("images", "splash.png")

    def Bpath(self, *args):
        return os.path.join(self.app_dir,*args)

    def ShowSplashScreen(self):
        from wx.lib.agw.advancedsplash import AdvancedSplash
        bmp = wx.Image(self.splashPath).ConvertToBitmap()
        self.splash = AdvancedSplash(None, bitmap=bmp)

        # process all events
        # even the events generated by splash themself during showing
        if wx.Platform == '__WXMSW__':
            self.splash.Show()
            self.splash.ProcessEvent(wx.PaintEvent())
        else:
            for i in range(0,30):
                wx.Yield()
                time.sleep(0.01);


    def Usage(self):
        print "Usage:"
        print "%s [Options] [Projectpath] [Buildpath]"%sys.argv[0]        
        print ""
        print "Supported options:"
        print "-h --help                    Print this help"
        print "-u --updatecheck URL         Retrieve update information by checking URL"
        print "-e --extend PathToExtension  Extend IDE functionality by loading at start additional extensions"
        print ""
        print ""        

    def SetCmdOptions(self):
        self.shortCmdOpts = "hu:e:"
        self.longCmdOpts = ["help", "updatecheck=", "extend="]

    def ProcessOption(self, o, a):
        if o in ("-h", "--help"):
            self.Usage()
            sys.exit()
        if o in ("-u", "--updatecheck"):
            self.updateinfo_url = a
        if o in ("-e", "--extend"):
            self.extensions.append(a)

    def ProcessCommandLineArgs(self):
        self.SetCmdOptions()
        try:
            opts, args = getopt.getopt(sys.argv[1:], self.shortCmdOpts, self.longCmdOpts)
        except getopt.GetoptError:
            # print help information and exit:
            self.Usage()
            sys.exit(2)

        for o, a in opts:
            self.ProcessOption(o, a)

        if len(args) > 2:
            self.Usage()
            sys.exit()

        elif len(args) == 1:
            self.projectOpen = args[0]
            self.buildpath = None
        elif len(args) == 2:
            self.projectOpen = args[0]
            self.buildpath = args[1]

    def CreateApplication(self):
        if os.path.exists("BEREMIZ_DEBUG"):
            __builtin__.__dict__["BMZ_DBG"] = True
        else :
            __builtin__.__dict__["BMZ_DBG"] = False

        global wxversion, wx
        import wxversion
        wxversion.select(['2.8', '3.0'])
        import wx

        if wx.VERSION >= (3, 0, 0):
            self.app = wx.App(redirect=BMZ_DBG)
        else:
            self.app = wx.PySimpleApp(redirect=BMZ_DBG)

        self.app.SetAppName('beremiz')
        if wx.VERSION < (3, 0, 0):
            wx.InitAllImageHandlers()

        self.ShowSplashScreen()
        self.BackgroundInitialization()
        self.app.MainLoop()

    def BackgroundInitialization(self):
        self.InitI18n()
        self.CheckUpdates()
        self.LoadExtensions()
        self.ImportModules()
        self.InstallExceptionHandler()
        self.ShowUI()

    def InitI18n(self):
        from util.misc import InstallLocalRessources
        InstallLocalRessources(self.app_dir)

    def LoadExtensions(self):
        for extfilename in self.extensions:
            from util.TranslationCatalogs import AddCatalog
            from util.BitmapLibrary import AddBitmapFolder
            extension_folder = os.path.split(os.path.realpath(extfilename))[0]
            sys.path.append(extension_folder)
            AddCatalog(os.path.join(extension_folder, "locale"))
            AddBitmapFolder(os.path.join(extension_folder, "images"))
            execfile(extfilename, locals())

    def CheckUpdates(self):
        if self.updateinfo_url is not None:
            updateinfo = _("Fetching %s") % self.updateinfo_url

            def updateinfoproc():
                global updateinfo
                try :
                    import urllib2
                    updateinfo = urllib2.urlopen(self.updateinfo_url,None).read()
                except :
                    updateinfo = _("update info unavailable.")

            from threading import Thread
            self.splash.SetText(text=updateinfo)
            updateinfoThread = Thread(target=updateinfoproc)
            updateinfoThread.start()
            updateinfoThread.join(2)
            self.splash.SetText(text=updateinfo)

    def ImportModules(self):
        global BeremizIDE
        import BeremizIDE

    def InstallExceptionHandler(self):
        import version
        import tempfile
        logpath = tempfile.gettempdir()+os.sep+'Beremiz'
        BeremizIDE.AddExceptHook(logpath,version.app_version)

    def ShowUI(self):
        self.frame = BeremizIDE.Beremiz(None, self.projectOpen, self.buildpath)
        if self.splash:
            self.splash.Close()
        self.frame.Show()

    def Start(self):
        self.ProcessCommandLineArgs()
        self.CreateApplication()

if __name__ == '__main__':
    beremiz = BeremizIDELauncher()
    beremiz.Start()
