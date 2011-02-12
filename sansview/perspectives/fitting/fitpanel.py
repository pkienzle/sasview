
import numpy
import string 
import wx
import wx.aui

from sans.guiframe.panel_base import PanelBase
from sans.guiframe.events import PanelOnFocusEvent
import basepage

_BOX_WIDTH = 80


class PageInfo(object):
    """
    this class contains the minimum numbers of data members
    a fitpage or model page need to be initialized.
    """
    data = None
    model =  None
    manager = None
    event_owner= None
    model_list_box = None
    name = None
    ## Internal name for the AUI manager
    window_name = "Page"
    ## Title to appear on top of the window
    window_caption = "Page"
    #type of page can be real data , theory 1D or therory2D
    type = "Data"
    def __init__(self, model=None, data=None, manager=None,
                  event_owner=None, model_list_box=None, name=None):
        """
        Initialize data members
        """
        self.data = data
        self.model= model
        self._manager= manager
        self.event_owner= event_owner
        self.model_list_box = model_list_box
        self.name=None
        self.window_name = "Page"
        self.window_caption = "Page"
        self.type = "Data"
        
class FitPanel(wx.aui.AuiNotebook, PanelBase):    

    """
    FitPanel class contains fields allowing to fit  models and  data
    
    :note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.
       
    """
    ## Internal name for the AUI manager
    window_name = "Fit panel"
    ## Title to appear on top of the window
    window_caption = "Fit Panel "
    CENTER_PANE = True
    
    def __init__(self, parent, *args, **kwargs):
        """
        """
        wx.aui.AuiNotebook.__init__(self, parent, -1,
                    style= wx.aui.AUI_NB_WINDOWLIST_BUTTON|
                    wx.aui.AUI_NB_DEFAULT_STYLE|
                    wx.CLIP_CHILDREN)
        PanelBase.__init__(self, parent)
    
        self._manager = None
        self.parent = parent
        self.event_owner = None
        
        pageClosedEvent = wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_close_page)
       
        #dictionary of miodel {model class name, model class}
        self.model_list_box = {}
        ## save the title of the last page tab added
        self.fit_page_name = {}
        ## list of existing fit page
        self.opened_pages = {}
        #page of simultaneous fit 
        self.sim_page = None
        ## get the state of a page
        self.Bind(basepage.EVT_PAGE_INFO, self._onGetstate)
        self.Bind(basepage.EVT_PREVIOUS_STATE, self._onUndo)
        self.Bind(basepage.EVT_NEXT_STATE, self._onRedo)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_page_changing)
       
        #add default pages
        self.add_default_pages()
     
        # increment number for model name
        self.count = 0
        #updating the panel
        self.Update()
        self.Center()
        
    def on_page_changing(self, event):
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            wx.PostEvent(self.parent, PanelOnFocusEvent(panel=selected_page))
    def on_set_focus(self, event):
        """
        """
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            wx.PostEvent(self.parent, PanelOnFocusEvent(panel=selected_page))
        
    def get_data(self):
        """
        get the data in the current page
        """
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            return selected_page.get_data()
    
    def get_state(self):
        """
         return the state of the current selected page
        """
        pos = self.GetSelection()
        if pos != -1:
            selected_page = self.GetPage(pos)
            return selected_page.get_state()
    
    def add_default_pages(self):
        """
        Add default pages such as a hint page and an empty fit page
        """
        #add default page
        from hint_fitpage import HintFitPage
        self.hint_page = HintFitPage(self) 
        self.AddPage(page=self.hint_page, caption="Hint")
        self.hint_page.set_manager(self._manager)
        #Add the first fit page
        self.add_empty_page()

    
    def close_all(self):
        """
        remove all pages, used when a svs file is opened
        """
        
        #get number of pages
        nop = self.GetPageCount()
        #use while-loop, for-loop will not do the job well.
        while (nop>0):
            #delete the first page until no page exists
            page = self.GetPage(0)
            if self._manager.parent.panel_on_focus == page:
                self._manager.parent.panel_on_focus = None
            self._close_helper(selected_page=page)
            self.DeletePage(0)
            nop = nop - 1
            
        ## save the title of the last page tab added
        self.fit_page_name = {}
        ## list of existing fit page
        self.opened_pages = {}  
         
    def set_state(self, state):
        """
        Restore state of the panel
        """
        page_is_opened = False
        if state is not None:
            page_info = self.get_page_info(data=state.data)
            for name, panel in self.opened_pages.values():
                #Don't return any panel is the exact same page is created
                if name == page_info.window_name:
                    # the page is still opened
                    panel.reset_page(state=state)
                    panel.save_current_state() 
                    page_is_opened = True
            if not page_is_opened:
                panel = self.add_fit_page(data=state.data)
                # add data associated to the page created
                if panel is not None:  
                    self._manager.store_page(page=panel, data=state.data)
                    panel.reset_page(state=state)
                    panel.save_current_state()
                    
    def clear_panel(self):
        """
        Clear and close all panels, used by guimanager
        """
       
        #close all panels only when svs file opened
        self.close_all()
        self._manager.mypanels = []
        
                       
    def on_close_page(self, event=None):
        """
        close page and remove all references to the closed page
        """
        nbr_page = self.GetPageCount()
        if nbr_page == 1:
           
            event.Veto()
            return 
        selected_page = self.GetPage(self.GetSelection())
        self._close_helper(selected_page=selected_page)
        
    def close_page_with_data(self, deleted_data):
        """
        close a fit page when its data is completely remove from the graph
        """
        if deleted_data is None:
            return
        for index in range(self.GetPageCount()):
            selected_page = self.GetPage(index) 
            if hasattr(selected_page,"get_data"):
                data = selected_page.get_data()
                
                if data is None:
                    #the fitpanel exists and only the initial fit page is open 
                    #with no selected data
                    return
                if data.name == deleted_data.name:
                    self._close_helper(selected_page)
                    self.DeletePage(index)
                    break
        
    def set_manager(self, manager):
        """
        set panel manager
        
        :param manager: instance of plugin fitting
        
        """
        self._manager = manager
        for pos in range(self.GetPageCount()):
            page = self.GetPage(pos)
            if page is not None:
                page.set_manager(self._manager)

        
    def set_owner(self,owner):
        """ 
        set and owner for fitpanel
        
        :param owner: the class responsible of plotting
        
        """
        self.event_owner = owner
    
    def set_model_list(self, dict):
         """ 
         copy a dictionary of model into its own dictionary
         
         :param dict: dictionnary made of model name as key and model class
             as value
         """
         self.model_list_box = dict
        
    def get_current_page(self):
        """
        :return: the current page selected
        
        """
        return self.GetPage(self.GetSelection() )
    
    def add_sim_page(self):
        """
        Add the simultaneous fit page
        """
        from simfitpage import SimultaneousFitPage
        page_finder= self._manager.get_page_finder()
        self.sim_page = SimultaneousFitPage(self,page_finder=page_finder, id=-1)
        
        self.AddPage(self.sim_page,caption="Simultaneous Fit",select=True)
        self.sim_page.set_manager(self._manager)
        return self.sim_page
        
    def get_page_info(self, data=None):
        """
        fill information required to add a page in the fit panel
        """
        name = "Fit Page"
        type = 'empty'
        if data is not None:
            if data.is_data:
                name = data.name 
                type = 'Data'
            else:
                if data.__class__.__name__ == "Data2D":
                    name = 'Model 2D Fit'
                    type = 'Theory2D'
                else:
                    name = 'Model 1D Fit'
                    type = 'Theory1D'
        page_info = PageInfo(data=data, name=name)
        page_info.event_owner = self.event_owner 
        page_info.manager = self._manager
        page_info.window_name = name
        page_info.window_caption = name
        page_info.type = type
        return page_info
   
    def add_empty_page(self):
        """
        add an empty page
        """
        page_info = self.get_page_info()
        from fitpage import FitPage
        panel = FitPage(parent=self, page_info=page_info)
        panel.set_manager(self._manager)
        self.AddPage(page=panel, caption=page_info.window_name, select=True)
        self.opened_pages[page_info.type] = [page_info.window_name, panel]
        return panel 
    
    def add_page(self, page_info):
        """
        add a new page
        """
        from fitpage import FitPage
        panel = FitPage(parent=self, page_info=page_info)
        panel.set_manager(self._manager)
        self.AddPage(page=panel, caption=page_info.window_name, select=True)
        index = self.GetPageIndex(panel)
        self.change_page_content(data=page_info.data, index=index)
        return panel
    
    def change_page_content(self, data, index):
        """
        replace the contains of an existing page
        """
        page_info = self.get_page_info(data=data)
        self.SetPageText(index, page_info.window_name)
        panel = self.GetPage(index)
        panel.set_data(data)
        if panel.model_list_box is None or len(panel.model_list_box) == 0: 
            page_info.model_list_box = self.model_list_box.get_list()
            panel.populate_box(dict=page_info.model_list_box)
            panel.initialize_combox()
        panel.set_page_info(page_info=page_info)
        self.opened_pages[page_info.type] = [page_info.window_name, panel]
        return panel
    
    def replace_page(self, index, page_info, type):
        """
        replace an existing page
        """
        self.DeletePage(index)
        del self.opened_pages[type]
        return self.add_page(page_info=page_info)
        
    def add_fit_page(self, data, reset=False):
        """ 
        Add a fitting page on the notebook contained by fitpanel
        
        :param data: data to fit
        
        :return panel : page just added for further used. is used by fitting module
        
        """
        if data is None:
            return None
        page_info = self.get_page_info(data=data)
        type = page_info.type
        npages = len(self.opened_pages.keys())
        #check if only and empty page is opened
        if len(self.opened_pages.keys()) > 0:
            first_page_type = self.opened_pages.keys()[0]
            if npages == 1 and first_page_type in ['empty']:
                #replace the first empty page
                name, panel = self.opened_pages[first_page_type]
                index = self.GetPageIndex(panel)
                panel = self.change_page_content(data=data, index=index)
                del self.opened_pages[first_page_type]
                return panel
        if type in self.opened_pages.keys():
            #this type of page is already created but it is a theory
            # meaning the same page is just to fit different data
            if not type.lower() in ['data']:
                #delete the previous theory page and add a new one
                name, panel = self.opened_pages[type]
                #self._manager.reset_plot_panel(panel.get_data())
                #delete the existing page and replace it
                index = self.GetPageIndex(panel)
                panel = self.replace_page(index=index, page_info=page_info, type=type)
                return panel 
            else:
                for name, panel in self.opened_pages.values():
                    #Don't return any panel is the exact same page is created
                    if name == page_info.window_name:
                        return None
                    else:
                        panel = self.add_page(page_info=page_info)
                        return panel        
        else:
            #a new type of page is created
            panel = self.add_page(page_info=page_info)
            return panel
        
    def  _onGetstate(self, event):
        """
        copy the state of a page
        """
        page= event.page
        if page.window_name in self.fit_page_name:
            self.fit_page_name[page.window_name].appendItem(page.createMemento()) 
            
    def _onUndo(self, event ):
        """
        return the previous state of a given page is available
        """
        page = event.page 
        if page.window_name in self.fit_page_name:
            if self.fit_page_name[page.window_name].getCurrentPosition()==0:
                state = None
            else:
                state = self.fit_page_name[page.window_name].getPreviousItem()
                page._redo.Enable(True)
            page.reset_page(state)
        
    def _onRedo(self, event): 
        """
        return the next state available
        """       
        page = event.page 
        if page.window_name in self.fit_page_name:
            length= len(self.fit_page_name[page.window_name])
            if self.fit_page_name[page.window_name].getCurrentPosition()== length -1:
                state = None
                page._redo.Enable(False)
                page._redo.Enable(True)
            else:
                state = self.fit_page_name[page.window_name].getNextItem()
            page.reset_page(state)  
                 
    def _close_helper(self, selected_page):
        """
        Delete the given page from the notebook
        """
        #remove hint page
        if selected_page == self.hint_page:
            return
        ## removing sim_page
        if selected_page == self.sim_page :
            self._manager.sim_page=None 
            return
        
        ## closing other pages
        state = selected_page.createMemento()
        page_name = selected_page.window_name
        page_finder = self._manager.get_page_finder() 
        fitproblem = None
        ## removing fit page
        data = selected_page.get_data()
        #Don' t remove plot for 2D
        flag = True
        if data.__class__.__name__ == 'Data2D':
            flag = False
        if selected_page in page_finder:
            #Delete the name of the page into the list of open page
            for type, list in self.opened_pages.iteritems():
                #Don't return any panel is the exact same page is created
                name = str(list[0])
                if flag and selected_page.window_name == name:
                    if type.lower() in ['theory1d', 'theory2d']:
                        self._manager.remove_plot(selected_page, theory=True)
                    else:
                        self._manager.remove_plot(selected_page, theory=False)
                    break 
            del page_finder[selected_page]
        ##remove the check box link to the model name of this page (selected_page)
        try:
            self.sim_page.draw_page()
        except:
            ## that page is already deleted no need to remove check box on
            ##non existing page
            pass
                
        #Delete the name of the page into the list of open page
        for type, list in self.opened_pages.iteritems():
            #Don't return any panel is the exact same page is created
            name = str(list[0])
            if selected_page.window_name == name:
                del self.opened_pages[type]
                break 
     
  