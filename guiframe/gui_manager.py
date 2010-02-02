"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee

How-to build an application using guiframe:

 1- Write a main application script along the lines of dummyapp.py
 2- Write a config script along the lines of config.py, and name it local_config.py
 3- Write your plug-ins and place them in a directory called "perspectives".
     - Look at local_perspectives/plotting for an example of a plug-in.
     - A plug-in should define a class called Plugin. See abstract class below.

"""
#TODO: rewrite the status bar monstrosity

import wx
import wx.aui
import os, sys
import xml
try:
    # Try to find a local config
    import imp
    path = os.getcwd()
    if(os.path.isfile("%s/%s.py" % (path, 'local_config'))) or \
      (os.path.isfile("%s/%s.pyc" % (path, 'local_config'))):
            fObj, path, descr = imp.find_module('local_config', [path])
            config = imp.load_module('local_config', fObj, path, descr)  
    else:
        # Try simply importing local_config
        import local_config as config
except:
    # Didn't find local config, load the default 
    import config
    
from sans.guicomm.events import EVT_STATUS
from sans.guicomm.events import EVT_NEW_PLOT,EVT_SLICER_PARS_UPDATE

import warnings
warnings.simplefilter("ignore")

import logging

class Plugin:
    """
        This class defines the interface for a Plugin class
        that can be used by the gui_manager.
        
        Plug-ins should be placed in a sub-directory called "perspectives".
        For example, a plug-in called Foo should be place in "perspectives/Foo".
        That directory contains at least two files:
            perspectives/Foo/__init.py contains two lines:
            
                PLUGIN_ID = "Foo plug-in 1.0"
                from Foo import *
                
            perspectives/Foo/Foo.py contains the definition of the Plugin
            class for the Foo plug-in. The interface of that Plugin class
            should follow the interface of the class you are looking at.
            
        See dummyapp.py for a plugin example.
    """
    
    def __init__(self, name="Test_plugin"):
        """
            Abstract class for gui_manager Plugins.
        """
        ## Plug-in name. It will appear on the application menu.
        self.sub_menu = name     
        
        ## Reference to the parent window. Filled by get_panels() below.
        self.parent = None
        
        ## List of panels that you would like to open in AUI windows
        #  for your plug-in. This defines your plug-in "perspective"
        self.perspective = []
        
        
    def populate_menu(self, id, parent):
        """
            Create and return the list of application menu
            items for the plug-in. 
            
            @param id: deprecated. Un-used.
            @param parent: parent window
            @return: plug-in menu
        """
        return []
    
    def get_panels(self, parent):
        """
            Create and return the list of wx.Panels for your plug-in.
            Define the plug-in perspective.
            
            Panels should inherit from DefaultPanel defined below,
            or should present the same interface. They must define
            "window_caption" and "window_name".
            
            @param parent: parent window
            @return: list of panels
        """
        ## Save a reference to the parent
        self.parent = parent
        
        # Return the list of panels
        return []
    
    def get_tools(self):
        """
            Returns a set of menu entries for tools
        """
        return []
        
    
    def get_context_menu(self, graph=None):
        """
            This method is optional.
        
            When the context menu of a plot is rendered, the 
            get_context_menu method will be called to give you a 
            chance to add a menu item to the context menu.
            
            A ref to a Graph object is passed so that you can
            investigate the plot content and decide whether you
            need to add items to the context menu.  
            
            This method returns a list of menu items.
            Each item is itself a list defining the text to 
            appear in the menu, a tool-tip help text, and a
            call-back method.
            
            @param graph: the Graph object to which we attach the context menu
            @return: a list of menu items with call-back function
        """
        return []
    
    def get_perspective(self):
        """
            Get the list of panel names for this perspective
        """
        return self.perspective
    
    def on_perspective(self, event):
        """
            Call back function for the perspective menu item.
            We notify the parent window that the perspective
            has changed.
            @param event: menu event
        """
        self.parent.set_perspective(self.perspective)
    
    def post_init(self):
        """
            Post initialization call back to close the loose ends
        """
        pass


class ViewerFrame(wx.Frame):
    """
        Main application frame
    """
    def __init__(self, parent, id, title, window_height=300, window_width=300):
        """
            Initialize the Frame object
        """
        from local_perspectives.plotting import plotting
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, size=(window_width, window_height))
        # Preferred window size
        self._window_height = window_height
        self._window_width  = window_width
        
        # Logging info
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='sans_app.log',
                    filemode='w')        
        path = os.path.dirname(__file__)
        temp_path= os.path.join(path,'images')
        ico_file = os.path.join(temp_path,'ball.ico')
        if os.path.isfile(ico_file):
            self.SetIcon(wx.Icon(ico_file, wx.BITMAP_TYPE_ICO))
        else:
            temp_path= os.path.join(os.getcwd(),'images')
            ico_file = os.path.join(temp_path,'ball.ico')
            if os.path.isfile(ico_file):
                self.SetIcon(wx.Icon(ico_file, wx.BITMAP_TYPE_ICO))
        
        ## Application manager
        self.app_manager = None
        
        ## Find plug-ins
        # Modify this so that we can specify the directory to look into
        self.plugins =[]
        self.plugins.append(plotting.Plugin())
        self.plugins += self._find_plugins()
      
        ## List of panels
        self.panels = {}

        ## Next available ID for wx gui events 
        #TODO:  No longer used - remove all calls to this 
        self.next_id = 20000

        # Default locations
        self._default_save_location = os.getcwd()        

        # Welcome panel
        self.defaultPanel = None

        # Check for update
        self._check_update(None)
        ## maximum number of opened files' paths to store
        self.n_maxfileopen =  2
        ## number of file open
        self.n_fileOpen=0
        ## list of path of open files 
        self.filePathList=[]
        ## list of open file with name form menu
        #self._saveOpenData()
        ## Dictionary of open file where keys are filename  and values are number of copy of data plotted
        ## using the same loaded file 
        self.indice_load_data={}
        # Register the close event so it calls our own method
        wx.EVT_CLOSE(self, self._onClose)
        # Register to status events
        self.Bind(EVT_STATUS, self._on_status_event)
    
        
    def build_gui(self):
        # Set up the layout
        self._setup_layout()
        
        # Set up the menu
        self._setup_menus()
        
        #self.Fit()
        
        self._check_update(None)
             
    def _setup_layout(self):
        """
            Set up the layout
        """
        # Status bar
        from statusbar import MyStatusBar
        self.sb = MyStatusBar(self,wx.ID_ANY)
        self.SetStatusBar(self.sb)

        # Add panel
        self._mgr = wx.aui.AuiManager(self)
        self._mgr.SetDockSizeConstraint(0.5, 0.5) 
        
        # Load panels
        self._load_panels()
        
        self._mgr.Update()

    def add_perspective(self, plugin):
        """
            Add a perspective if it doesn't already
            exist.
        """
        is_loaded = False
        for item in self.plugins:
             if plugin.__class__==item.__class__:
                 print "Plugin %s already loaded" % plugin.__class__.__name__
                 is_loaded = True
                 
        if not is_loaded:
            self.plugins.append(plugin)
      
    def _find_plugins(self, dir="perspectives"):
        """
            Find available perspective plug-ins
            @param dir: directory in which to look for plug-ins
            @return: list of plug-ins
        """
        import imp
        
        plugins = []
        # Go through files in panels directory
        try:
            list = os.listdir(dir)
            ## the default panel is the panel is the last plugin added
            for item in list:
                toks = os.path.splitext(os.path.basename(item))
                name = None
                if not toks[0] == '__init__':
                    
                    if toks[1]=='.py' or toks[1]=='':
                        name = toks[0]
                
                    path = [os.path.abspath(dir)]
                    file = None
                    try:
                        if toks[1]=='':
                            mod_path = '.'.join([dir, name])
                            module = __import__(mod_path, globals(), locals(), [name])
                        else:
                            (file, path, info) = imp.find_module(name, path)
                            module = imp.load_module( name, file, item, info )
                        if hasattr(module, "PLUGIN_ID"):
                            try:
                                plugins.append(module.Plugin())
                                logging.info("Found plug-in: %s" % module.PLUGIN_ID)
                            except:
                                config.printEVT("Error accessing PluginPanel in %s\n  %s" % (name, sys.exc_value))
                        
                    except:
                        print sys.exc_value
                        logging.error("ViewerFrame._find_plugins: %s" % sys.exc_value)
                    finally:
                        if not file==None:
                            file.close()
        except:
            # Should raise and catch at a higher level and display error on status bar
            pass   
        return plugins
    
    def set_welcome_panel(self, panel_class):
        """
           Sets the default panel as the given welcome panel 
           @param panel_class: class of the welcome panel to be instantiated
        """
        self.defaultPanel    = panel_class(self, -1, style=wx.RAISED_BORDER)
        self.defaultPanel.set_manager(manager=self.app_manager)
      
    def _load_panels(self):
        """
            Load all panels in the panels directory
        """
        
        # Look for plug-in panels
        panels = []    
        for item in self.plugins:
            if hasattr(item, "get_panels"):
                ps = item.get_panels(self)
                panels.extend(ps)

        # Show a default panel with some help information
        # It also sets the size of the application windows
        #TODO: Use this for slpash screen
        if self.defaultPanel is None:
            self.defaultPanel    = DefaultPanel(self, -1, style=wx.RAISED_BORDER)
            
        self.panels["default"] = self.defaultPanel
        
        self._mgr.AddPane(self.defaultPanel, wx.aui.AuiPaneInfo().
                              Name("default").
                              CenterPane().
                              # This is where we set the size of the application window
                              BestSize(wx.Size(self._window_width, self._window_height)).
                              #MinSize(wx.Size(self._window_width, self._window_height)).
                              Show())
     

        # Add the panels to the AUI manager
        for panel_class in panels:
            p = panel_class
            id = wx.NewId()
            
            # Check whether we need to put this panel
            # in the center pane
            if hasattr(p, "CENTER_PANE"):
                if p.CENTER_PANE:
                    self.panels[str(id)] = p
                    self._mgr.AddPane(p, wx.aui.AuiPaneInfo().
                                          Name(p.window_name).Caption(p.window_caption).
                                          CenterPane().
                                          #BestSize(wx.Size(550,600)).
                                          #MinSize(wx.Size(500,500)).
                                          Hide())
            else:
                self.panels[str(id)] = p
                self._mgr.AddPane(p, wx.aui.AuiPaneInfo().
                                  Name(p.window_name).Caption(p.window_caption).
                                  Right().
                                  Dock().
                                  TopDockable().
                                  BottomDockable().
                                  LeftDockable().
                                  RightDockable().
                                  MinimizeButton().
                                  Hide())
                                  #BestSize(wx.Size(550,600)))
                                  #MinSize(wx.Size(500,500)))                 
                
        
    def get_context_menu(self, graph=None):
        """
            Get the context menu items made available 
            by the different plug-ins. 
            This function is used by the plotting module
        """
        menu_list = []
        for item in self.plugins:
            if hasattr(item, "get_context_menu"):
                menu_list.extend(item.get_context_menu(graph))
            
        return menu_list
        
    def popup_panel(self, p):
        """
            Add a panel object to the AUI manager
            @param p: panel object to add to the AUI manager
            @return: ID of the event associated with the new panel [int]
        """
        
        ID = wx.NewId()
        self.panels[str(ID)] = p
        
        count = 0
        for item in self.panels:
            if self.panels[item].window_name.startswith(p.window_name): 
                count += 1
        
        windowname = p.window_name
        caption = p.window_caption
        
        if count>0:
            windowname += str(count+1)
            caption += (' '+str(count))
          
        p.window_name = windowname
        p.window_caption = caption
            
        self._mgr.AddPane(p, wx.aui.AuiPaneInfo().
                          Name(windowname).Caption(caption).
                          Floatable().
                          #Float().
                          Right().
                          Dock().
                          TopDockable().
                          BottomDockable().
                          LeftDockable().
                          RightDockable().
                          MinimizeButton().
                          #Hide().
                          #Show().
                          Resizable(True).
                          # Use a large best size to make sure the AUI manager
                          # takes all the available space
                          BestSize(wx.Size(400,400)))
        pane = self._mgr.GetPane(windowname)
        self._mgr.MaximizePane(pane)
        self._mgr.RestoreMaximizedPane()
        
        
        # Register for showing/hiding the panel
        
        wx.EVT_MENU(self, ID, self._on_view)
        
        self._mgr.Update()
        return ID
        
    def _setup_menus(self):
        """
            Set up the application menus
        """
        # Menu
        menubar = wx.MenuBar()
        
        # File menu
        self.filemenu = wx.Menu()
        
        id = wx.NewId()
        self.filemenu.Append(id, '&Open', 'Open a file')
        wx.EVT_MENU(self, id, self._on_open)
        #self.filemenu.AppendSeparator()
        
        id = wx.NewId()
        self.filemenu.Append(id,'&Quit', 'Exit') 
        wx.EVT_MENU(self, id, self.Close)
        
        # Add sub menus
        menubar.Append(self.filemenu,  '&File')
        
        # Plot menu
        # Attach a menu item for each panel in our
        # panel list that also appears in a plug-in.
        # TODO: clean this up. We should just identify
        # plug-in panels and add them all.
        
        # Only add the panel menu if there is more than two panels
        n_panels = 0
        for plug in self.plugins:
            pers = plug.get_perspective()
            if len(pers)>0:
                n_panels += 1
       
        if n_panels>2:
            viewmenu = wx.Menu()
            for plug in self.plugins:
                plugmenu = wx.Menu()
                pers = plug.get_perspective()
                if len(pers)>0:
                    for item in self.panels:
                        if item == 'default':
                            continue
                        panel = self.panels[item]
                        if panel.window_name in pers:
                            plugmenu.Append(int(item), panel.window_caption, "Show %s window" % panel.window_caption)
                           
                            wx.EVT_MENU(self, int(item), self._on_view)
                    
                    viewmenu.AppendMenu(wx.NewId(), plug.sub_menu, plugmenu, plug.sub_menu)
            menubar.Append(viewmenu, '&Panel')

        # Perspective
        # Attach a menu item for each defined perspective.
        # Only add the perspective menu if there are more than one perspectives
        n_perspectives = 0
        for plug in self.plugins:
            if len(plug.get_perspective()) > 0:
                n_perspectives += 1
        
        if n_perspectives>1:
            p_menu = wx.Menu()
            for plug in self.plugins:
                if len(plug.get_perspective()) > 0:
                    id = wx.NewId()
                    p_menu.Append(id, plug.sub_menu, "Switch to %s perspective" % plug.sub_menu)
                    wx.EVT_MENU(self, id, plug.on_perspective)
            menubar.Append(p_menu,   '&Perspective')
 
        # Tools menu
        # Go through plug-ins and find tools to populate the tools menu
        toolsmenu = None
        for item in self.plugins:
            if hasattr(item, "get_tools"):
                for tool in item.get_tools():
                    # Only create a menu if we have at least one tool
                    if toolsmenu is None:
                        toolsmenu = wx.Menu()
                    id = wx.NewId()
                    
                    toolsmenu.Append(id, tool[0], tool[1])
                    wx.EVT_MENU(self, id, tool[2])
        if toolsmenu is not None:
            menubar.Append(toolsmenu, '&Tools')
 
        # Help menu
        helpmenu = wx.Menu()
        # add the welcome panel menu item
        if self.defaultPanel is not None:
            id = wx.NewId()
            helpmenu.Append(id,'&Welcome', '')
            helpmenu.AppendSeparator()
            wx.EVT_MENU(self, id, self.show_welcome_panel)
        
        # Look for help item in plug-ins 
        for item in self.plugins:
            if hasattr(item, "help"):
                id = wx.NewId()
                helpmenu.Append(id,'&%s help' % item.sub_menu, '')
                wx.EVT_MENU(self, id, item.help)
        
        if config._do_aboutbox:
            id = wx.NewId()
            helpmenu.Append(id,'&About', 'Software information')
            wx.EVT_MENU(self, id, self._onAbout)
        id = wx.NewId()
        helpmenu.Append(id,'&Check for update', 'Check for the latest version of %s' % config.__appname__)
        wx.EVT_MENU(self, id, self._check_update)
        
        
        
        
        # Look for plug-in menus
        # Add available plug-in sub-menus. 
        for item in self.plugins:
            if hasattr(item, "populate_menu"):
                for (self.next_id, menu, name) in item.populate_menu(self.next_id, self):
                    menubar.Append(menu, name)
                   

        menubar.Append(helpmenu, '&Help')
         
        self.SetMenuBar(menubar)
        
        
        
    def _on_status_event(self, evt):
        """
            Display status message
        """
        #self.sb.clear_gauge( msg="")
        mythread=None
        mytype= None
        if hasattr(evt, "curr_thread"):
            mythread= evt.curr_thread
        if hasattr(evt, "type"):
            mytype= evt.type
        self.sb.set_status( type=mytype,msg=str(evt.status),thread=mythread)
       

        
    def _on_view(self, evt):
        """
            A panel was selected to be shown. If it's not already
            shown, display it.
            @param evt: menu event
        """
        self.show_panel(evt.GetId())
        
    def on_close_welcome_panel(self ):
        """
            Close the welcome panel
        """
        if self.defaultPanel is None:
            return 
        self._mgr.GetPane(self.panels["default"].window_name).Hide()
        self._mgr.Update()
       
        
    def show_welcome_panel(self, event):
        """    
            Display the welcome panel
        """
        if self.defaultPanel is None:
            return 
        for id in self.panels.keys():
            if self._mgr.GetPane(self.panels[id].window_name).IsShown():
                self._mgr.GetPane(self.panels[id].window_name).Hide()
        # Show default panel
        if not self._mgr.GetPane(self.panels["default"].window_name).IsShown():
            self._mgr.GetPane(self.panels["default"].window_name).Show()
        
        self._mgr.Update()
        
    def show_panel(self, uid):
        """
            Shows the panel with the given id
            @param uid: unique ID number of the panel to show
        """
        ID = str(uid)
        config.printEVT("show_panel: %s" % ID)
        if ID in self.panels.keys():
            if not self._mgr.GetPane(self.panels[ID].window_name).IsShown():
                self._mgr.GetPane(self.panels[ID].window_name).Show()
                # Hide default panel
                self._mgr.GetPane(self.panels["default"].window_name).Hide()
            
                
            self._mgr.Update()
   
    def _on_open(self, event):
   
        from data_loader import plot_data
        path = self.choose_file()

        if path ==None:
            return
        if path and os.path.isfile(path):
            plot_data(self, path)
           
        
        
    def _onClose(self, event):
        """
            Store info to retrieve in xml before closing the application
        """
        try:
            doc = xml.dom.minidom.Document()
            main_node = doc.createElement("file Path")
            
            doc.appendChild(main_node)
        
            for item in self.filePathList:
                id, menuitem_name , path, title = item
                pt1 = doc.createElement("File")
                pt1.setAttribute("name", menuitem_name)
                pt2 = doc.createElement("path")
                pt2.appendChild(doc.createTextNode(str(path)))
                pt1.appendChild(pt2)
                pt3 = doc.createElement("title")
                pt3.appendChild(doc.createTextNode(str(title)))
                pt1.appendChild(pt3)
                
                main_node.appendChild(pt1)
                
               
            fd = open("fileOpened.xml",'w')
            fd.write(doc.toprettyxml())
            fd.close()
        except:
            pass
        
        import sys
        wx.Exit()
        sys.exit()
                   
                   
    def Close(self, event=None):
        """
            Quit the application
        """
        import sys
        wx.Frame.Close(self)
        wx.Exit()
        sys.exit()

  
    def _check_update(self, event=None): 
        """
            Check with the deployment server whether a new version
            of the application is available.
            A thread is started for the connecting with the server. The thread calls
            a call-back method when the current version number has been obtained.
        """
        if hasattr(config, "__update_URL__"):
            import version
            checker = version.VersionThread(config.__update_URL__, self._process_version, baggage=event==None)
            checker.start()  
    
    def _process_version(self, version, standalone=True):
        """
            Call-back method for the process of checking for updates.
            This methods is called by a VersionThread object once the current
            version number has been obtained. If the check is being done in the
            background, the user will not be notified unless there's an update.
            
            @param version: version string
            @param standalone: True of the update is being checked in the background, False otherwise.
        """
        try:
            if cmp(version, config.__version__)>0:
                self.SetStatusText("Version %s is available! See the Help menu to download it." % version)
                if not standalone:
                    import webbrowser
                    webbrowser.open(config.__download_page__)
            else:
                if not standalone:
                    self.SetStatusText("You have the latest version of %s" % config.__appname__)
        except:
            logging.error("guiframe: could not get latest application version number\n  %s" % sys.exc_value)
            if not standalone:
                self.SetStatusText("Could not connect to the application server. Please try again later.")
                    
        
    def _onAbout(self, evt):
        """
            Pop up the about dialog
            @param evt: menu event
        """
        if config._do_aboutbox:
            import aboutbox 
            dialog = aboutbox.DialogAbout(None, -1, "")
            dialog.ShowModal()            
            
    def _onreloaFile(self, event):  
        """
            load a data previously opened 
        """
        from data_loader import plot_data
        for item in self.filePathList:
            id, menuitem_name , path, title = item
            if id == event.GetId():
                if path and os.path.isfile(path):
                    plot_data(self, path)
                    break
            
        
    def set_manager(self, manager):
        """
            Sets the application manager for this frame
            @param manager: frame manager
        """
        self.app_manager = manager
        
    def post_init(self):
        """
            This initialization method is called after the GUI 
            has been created and all plug-ins loaded. It calls
            the post_init() method of each plug-in (if it exists)
            so that final initialization can be done.
        """
        for item in self.plugins:
            if hasattr(item, "post_init"):
                item.post_init()
        
    def set_perspective(self, panels):
        """
            Sets the perspective of the GUI.
            Opens all the panels in the list, and closes
            all the others.
            
            @param panels: list of panels
        """
        for item in self.panels:
            # Check whether this is a sticky panel
            if hasattr(self.panels[item], "ALWAYS_ON"):
                if self.panels[item].ALWAYS_ON:
                    continue 
            
            if self.panels[item].window_name in panels:
                if not self._mgr.GetPane(self.panels[item].window_name).IsShown():
                    self._mgr.GetPane(self.panels[item].window_name).Show()
            else:
                if self._mgr.GetPane(self.panels[item].window_name).IsShown():
                    self._mgr.GetPane(self.panels[item].window_name).Hide()
    
        self._mgr.Update()
        
    def choose_file(self, path=None):
        """ 
            Functionality that belongs elsewhere
            Should add a hook to specify the preferred file type/extension.
        """
        #TODO: clean this up
        from data_loader import choose_data_file
        
        # Choose a file path
        if path==None:
            path = choose_data_file(self, self._default_save_location)
            
        if not path==None:
            try:
                self._default_save_location = os.path.dirname(path)
               
                #self.n_fileOpen += 1
                if self.n_fileOpen==1:
                    pos= self.filemenu.GetMenuItemCount()-1
                    #self.filemenu.InsertSeparator(pos )
               
                id = wx.NewId()
                filename= os.path.basename(path)
                dir= os.path.split(self._default_save_location)[1]
                title= str(os.path.join(dir,filename )) 
                menuitem_name = str(self.n_fileOpen)+". "+ title
                position= self.filemenu.GetMenuItemCount()-2
                #self.filemenu.Insert(id=id, pos= position,text=menuitem_name,help=str(path) ) 
                #self.filePathList.append(( id, menuitem_name, path, title))
                #wx.EVT_MENU(self, id, self._onreloaFile)
                
                ## construct menu item for open file
                if self.n_fileOpen == self.n_maxfileopen +1:
                    ## reach the maximun number of path to store
                    self.n_fileOpen = 0
                    id, menuitem_name , path, title = self.filePathList[0]
                    self.filemenu.Delete(id)
                    self.filePathList.pop(0)
                    for item in self.filePathList:
                        id, menuitem_name , path, title = item
                        self.n_fileOpen += 1
                        label = str(self.n_fileOpen)+". "+ title
                        #self.filemenu.FindItemById(id).SetItemLabel(label)
                        
                          
            except:
                raise
                #pass
        return path
    
    def load_ascii_1D(self, path):
        from data_loader import load_ascii_1D
        return load_ascii_1D(path)
                  
class DefaultPanel(wx.Panel):
    """
        Defines the API for a panels to work with
        the GUI manager
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "default"
    ## Name to appear on the window title bar
    window_caption = "Welcome panel"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True

  
# Toy application to test this Frame
class ViewApp(wx.App):
    def OnInit(self):
        #from gui_manager import ViewerFrame
        self.frame = ViewerFrame(None, -1, config.__appname__)    
        self.frame.Show(True)

        if hasattr(self.frame, 'special'):
            self.frame.special.SetCurrent()
        self.SetTopWindow(self.frame)
        return True
    
    def set_manager(self, manager):
        """
            Sets a reference to the application manager
            of the GUI manager (Frame) 
        """
        self.frame.set_manager(manager)
        
    def build_gui(self):
        """
            Build the GUI
        """
        self.frame.build_gui()
        self.frame.post_init()
        
    def set_welcome_panel(self, panel_class):
        """
            Set the welcome panel
            @param panel_class: class of the welcome panel to be instantiated
        """
        self.frame.set_welcome_panel(panel_class)
        
    def add_perspective(self, perspective):
        """
            Manually add a perspective to the application GUI
        """
        self.frame.add_perspective(perspective)
        

if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()              