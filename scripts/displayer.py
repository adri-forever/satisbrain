import ttkthemes, tktooltip
import tkinter as tk
from tkinter import ttk

import brain

### Classes ###
class AutocompleteCombobox(ttk.Combobox):
    """
    Autocomplete from:
    https://mail.python.org/pipermail/tkinter-discuss/2012-January/003041.html
    """
    def set_completion_list(self, completion_list):
            """Use our completion list as our drop down selection menu, arrows move through menu."""
            self._completion_list = sorted(completion_list, key=str.lower) # Work with a sorted list
            self._hits = []
            self._hit_index = 0
            self.position = 0
            self.bind('<KeyRelease>', self.handle_keyrelease)
            self['values'] = self._completion_list  # Setup our popup menu

    def autocomplete(self, delta=0):
            """autocomplete the Combobox, delta may be 0/1/-1 to cycle through possible hits"""
            if delta: # need to delete selection otherwise we would fix the current position
                    self.delete(self.position, tk.END)
            else: # set position to end so selection starts where textentry ended
                    self.position = len(self.get())
            # collect hits
            _hits = []
            for element in self._completion_list:
                    if element.lower().startswith(self.get().lower()): # Match case insensitively
                            _hits.append(element)
            # if we have a new hit list, keep this in mind
            if _hits != self._hits:
                    self._hit_index = 0
                    self._hits=_hits
            # only allow cycling if we are in a known hit list
            if _hits == self._hits and self._hits:
                    self._hit_index = (self._hit_index + delta) % len(self._hits)
            # now finally perform the auto completion
            if self._hits:
                    self.delete(0,tk.END)
                    self.insert(0,self._hits[self._hit_index])
                    self.select_range(self.position,tk.END)

    def handle_keyrelease(self, event):
            """event handler for the keyrelease event on this widget"""
            if event.keysym == "BackSpace":
                    self.delete(self.index(tk.INSERT), tk.END)
                    self.position = self.index(tk.END)
            if event.keysym == "Left":
                    if self.position < self.index(tk.END): # delete the selection
                            self.delete(self.position, tk.END)
                    else:
                            self.position = self.position-1 # delete one character
                            self.delete(self.position, tk.END)
            if event.keysym == "Right":
                    self.position = self.index(tk.END) # go to end (no selection)
            if len(event.keysym) == 1:
                    self.autocomplete()
            # No need for up/down, we'll jump to the popup
            # list at the position of the autocompletion
            
class Window(tk.Tk):
    
    tabcount = 0
    
    def __init__(self):
        super().__init__()
        
        self.title('Satisbrain ALPHA')
        #set icon
        self.geometry('720x480')
        
        # self.setup_style()
        
        self.topbuttonbar = TopButtonBar(self)
        self.topbuttonbar.pack(fill='x')
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
    
    def newtab(self):
        #Keep track of tabs by ID
        self.tabcount += 1
        
        #Names
        tabname = f'tab_{self.tabcount}'
        tabname_d = f'Plan {self.tabcount}'
        # print(f'{tabname=}')
        
        #Create the tab
        setattr(self.notebook, tabname, ComputingFrame(self.notebook))
        newtab: ComputingFrame = getattr(self.notebook, tabname)
        newtab.pack(fill='both', expand=True)
        
        #Assign it to the notebook and select it
        self.notebook.add(newtab, text=tabname_d)
        self.notebook.select(newtab)
    
    def setup_style(self):
        """
        imitate satisfactory UI:
        background: black
        menu: dark gray
        tab: dark gray
        selected tab gray
        selected button: orange
        hovered button: gray
        text: white
        """
        self.style = ttk.Style(self)
        
        print(self.style.theme_names())
        self.style.theme_use('clam')
        
        self.style.configure('TButton', relief='flat', foreground='white', background='black', activebackground='orange',
                             highlightbackground = 'dark gray')
        
class TopButtonBar(ttk.Frame):
    
    def __init__(self, master: Window):
        super().__init__(master)
        
        self.new_btn = ttk.Button(self, text='New', command=self.newtab)
        self.new_btn.pack(side='left')
        
        self.btn_tooltip = tktooltip.ToolTip(self.new_btn, msg='Create new plan', delay=.5)
    
    def newtab(self):
        self.master.newtab()

class ComputingFrame(tk.Canvas):
    """
    """
    
    def __init__(self, master: ttk.Notebook):
        super().__init__(master, highlightthickness=0)
        
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.yview)
        self.scrollbar.pack(side='right', fill='y')
        
        self.configure(yscrollcommand=self.scrollbar.set)
        self.bind('<Configure>', lambda e: self.after(1, self.scroller))
        
        self.innerframe = ttk.Frame(self)
        
        self.create_window((0,0), window=self.innerframe, anchor='nw')
        
        # for i in range(20):
        #     ttk.Button(self.innerframe, text=f'button {i}').pack(pady=5)
        self.box_0 = ItemContainer(self)
        self.box_0.pack(padx=10, pady=10, anchor='nw')

    def scroller(self, event: tk.Event = None):
        if str(self) == self.master.select():
            self.configure(scrollregion=self.bbox('all'))
        
class ItemContainer(ttk.Frame):
    
    def __init__(self, master):
        super().__init__(master)
        
        ipads = {'ipadx': 0, 'ipady': 0}
        pads = {'padx': 10, 'pady': 10}
        
        #Header
        self.header = tk.Frame(self, background='dark gray')
        self.header.pack(fill='x', **ipads)
        
        self.itemvar = tk.StringVar(self, value='Title long enough that i wish to unalive')
        self.title = ttk.Entry(self.header, textvariable=self.itemvar, state='readonly')
        self.title.pack(**pads)
        
        self.body = tk.Frame(self, background='black')
        self.body.pack(fill='both', **ipads)
        
        self.content = ttk.Label(self.body, text='Body')
        self.content.pack(**pads)
        self.content1 = ttk.Label(self.body, text='Body')
        self.content1.pack(**pads)
        self.content2 = ttk.Label(self.body, text='Body')
        self.content2.pack(**pads)
        
        
### Functions ###

def main():
    window = Window()
    window.mainloop()
    
    print('Mainloop interrupted. Closing')
    
if __name__=='__main__':
    main()