import tktooltip, re, platform, webbrowser, copy
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Literal

import brain

"""
This is the ugly tkinter version
"""

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
            
class ScrollFrame(tk.Frame):
    """
    Source:
    https://gist.github.com/mp035/9f2027c3ef9172264532fcd6262f3b01
    """
    def __init__(self, parent):
        super().__init__(parent) # create a frame (self)

        self.canvas = tk.Canvas(self, borderwidth=0, background="#333")          #place canvas on self
        self.innerframe = tk.Frame(self.canvas, background="#333")                    #place a frame on the canvas, this frame will hold the child widgets 
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview) #place a scrollbar on self 
        self.canvas.configure(yscrollcommand=self.vsb.set)                          #attach scrollbar action to scroll of canvas

        self.vsb.pack(side="right", fill="y")                                       #pack scrollbar to right of self
        self.canvas.pack(side="left", fill="both", expand=True)                     #pack canvas to left of self and expand to fil
        self.canvas_window = self.canvas.create_window((4,4), window=self.innerframe, anchor="nw",            #add view port frame to canvas
                                  tags="self.innerframe")

        self.innerframe.bind("<Configure>", self.onFrameConfigure)                       #bind an event whenever the size of the innerframe frame changes.
        self.canvas.bind("<Configure>", self.onCanvasConfigure)                       #bind an event whenever the size of the canvas frame changes.
            
        self.innerframe.bind('<Enter>', self.onEnter)                                 # bind wheel events when the cursor enters the control
        self.innerframe.bind('<Leave>', self.onLeave)                                 # unbind wheel events when the cursorl leaves the control

        self.onFrameConfigure(None)                                                 #perform an initial stretch on render, otherwise the scroll region has a tiny border until the first resize

    def onFrameConfigure(self, event):                                              
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))                 #whenever the size of the frame changes, alter the scroll region respectively.

    def onCanvasConfigure(self, event):
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width = canvas_width)            #whenever the size of the canvas changes alter the window region respectively.

    def onMouseWheel(self, event):                                                  # cross platform scroll wheel event
        if platform.system() == 'Windows':
            self.canvas.yview_scroll(int(-1* (event.delta/120)), "units")
        elif platform.system() == 'Darwin':
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll( -1, "units" )
            elif event.num == 5:
                self.canvas.yview_scroll( 1, "units" )
    
    def onEnter(self, event):                                                       # bind wheel events when the cursor enters the control
        if platform.system() == 'Linux':
            self.canvas.bind_all("<Button-4>", self.onMouseWheel)
            self.canvas.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)

    def onLeave(self, event):                                                       # unbind wheel events when the cursorl leaves the control
        if platform.system() == 'Linux':
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")
                
class ScrollingFrame(tk.Canvas):
    """
    sucks ass
    """
    notebook: ttk.Notebook
    
    def __init__(self, master, notebook):
        super().__init__(master, highlightthickness=0)
        self.notebook = notebook
        
        self.innerframe = ttk.Frame(self)
        
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.yview)
        self.scrollbar.pack(side='right', fill='y')
        
        self.configure(yscrollcommand=self.scrollbar.set)
        self.bind('<Configure>', lambda e: self.after(1, self.scroller))
        
        # self.innerframe.pack(fill='both', expand=True)
        
        self.create_window((0,0), window=self.innerframe, anchor='nw')

    def scroller(self, event: tk.Event = None):
        if str(self) == self.notebook.select():
            self.configure(scrollregion=self.bbox('all'))
            
class Window(tk.Tk):
    
    tabcount = 0
    
    def __init__(self):
        super().__init__()
        
        self.title('Satisbrain')
        #set icon
        self.geometry('720x480')
        
        icon = tk.PhotoImage(file='resource\\image\\satisbrain.png')
        self.wm_iconphoto(False, icon)
        
        self.setup_style()
        
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
        
        font = "Segoe UI"
        fontsize = 11
        
        print(self.style.theme_names())
        self.style.theme_use('clam')
        
        self.style.configure('TNotebook', relief='flat', background='#333', foreground='white')
        
        self.style.configure('TFrame', relief='flat', background='#333')
        self.style.configure('light.TFrame', relief='flat', background='#555')
        
        self.style.configure('TLabel', relief='flat', background='#333', foreground='white', font=(font, fontsize))
        self.style.configure('high.TLabel', relief='flat', background='#555', foreground='white', font=(font, fontsize+2, 'bold'))
        
        self.style.configure('TButton', relief='flat', foreground='white', background='#555', activebackground='#FA9649',
                             highlightbackground = '#FA9649')
        
class TopButtonBar(ttk.Frame):
    
    def __init__(self, master: Window):
        super().__init__(master)
        
        self.new_btn = ttk.Button(self, text='New', command=self.newtab)
        self.new_btn.pack(side='left')
        
        self.btn_tooltip = tktooltip.ToolTip(self.new_btn, msg='Create new plan', delay=.5)
    
    def newtab(self):
        self.master.newtab()

class ComputingFrame(ttk.Frame):
    """
    """
    
    target_item: str = ''
    qty: float = 0
    recipes: dict[str: str] = {}
    base_resources: set[str] = copy.deepcopy(brain.data_baseresources)
    production_plan: dict = {}
    
    pads = {'padx': 5, 'pady': 5}

    def __init__(self, master: ttk.Notebook):
        super().__init__(master)
        
        self.header = ttk.Frame(self)
        self.header.pack(fill='x')
        
        self.item_picker = ItemPicker(self.header, self)
        self.item_picker.pack(side='left', anchor='nw', **self.pads)
        
        self.resource_manager = BaseResourceManager(self.header, self)
        self.resource_manager.pack(side='left', anchor='nw', **self.pads)
        
        self.genrep_btn = ttk.Button(self.header, text='Generate report', command=self.generate_report)
        self.genrep_btn.pack(side='right', **self.pads)
        
        self.plan_frame = ScrollFrame(self)
        self.plan_frame.pack(fill='both', expand=True)
        
    def submit_item(self, target_item: str, qty: float):
        confirm = True
        if self.target_item and target_item!=self.target_item:
            confirm = messagebox.askokcancel('Base item change', 'This action will reset the plan. All choices will be lost. Continue ?')
        
        if not confirm:
            return
        else:
            self.target_item = target_item
            self.qty = qty
            # print(target_item, qty)
            
            self.build_plan()
    
    def manage_base_resources(self, item: str, action: Literal['add', 'remove'] = 'add'):
        """
        Allow to change what items are considered base resources or not in current production plan
        """
        if action=='add' and item not in self.base_resources:
            self.base_resources.add(item)
        elif action=='remove' and item in self.base_resources:
            self.base_resources.remove(item)
        elif action not in ['add', 'remove']:
            print(f'Could not interpret action "{action}". Instruction ignored')
        
        self.build_plan()
        self.resource_manager.update_tree()
    
    def set_item_recipe(self, item: str, recipe: str):
        self.recipes[item] = recipe
        
        self.build_plan()
        
    def build_plan(self):
        self.production_plan, self.recipes = brain.get_production_plan(self.target_item, self.qty,
                                                                       self.recipes, self.base_resources)
        print('Plan built')
        
        self.display_plan()
    
    def display_plan(self):
        for child in self.plan_frame.innerframe.winfo_children():
            child.destroy()
        
        pplan = self.production_plan
        
        for tier in pplan.values():
            if 'itemtorec' in tier:
                separator = ttk.Separator(self.plan_frame.innerframe)
                separator.pack(fill='x')
                
                left_items = tier['itemtorec'].keys()
                
                if left_items:
                    for i, item in enumerate(left_items):
                        # Every n recipe, create a new line
                        if i%5==0:
                            line = ttk.Frame(self.plan_frame.innerframe)
                            line.pack(fill='x')
                        
                        recipebox = RecipePicker(line, self, item)
                        recipebox.pack(side='left', anchor='n', **self.pads)

    def generate_report(self):
        filetypes = [('HTML', '*.html')]
        initialdir = '.\\output'
        title = 'Save plan as'

        initialfile = f'Production_plan_{brain.data_items[self.target_item]['slug']}.html'
        
        path = filedialog.asksaveasfilename(filetypes=filetypes, initialdir=initialdir, initialfile=initialfile, title=title)
        
        brain.generate_html(self.production_plan, path)
        
        webbrowser.open(path)       

class ItemPicker(ttk.Frame):

    computingframe: ComputingFrame

    def __init__(self, master, computingframe: ComputingFrame):
        super().__init__(master, relief='solid')
        
        self.computingframe = computingframe

        self.itemdict = {item_data['name']: item for item, item_data in brain.data_items.items() if item not in self.computingframe.base_resources}
        self.itemlist = list(self.itemdict.keys())

        ipads = {'ipadx': 0, 'ipady': 0}
        pads = {'padx': 2, 'pady': 2}
            
        self.item_label = ttk.Label(self, text='Select item:')
        self.item_label.pack(side='left', **pads)

        self.item_box = AutocompleteCombobox(self, width=25)
        self.item_box.set_completion_list(self.itemlist)
        self.item_box.pack(side='left', **pads)
        
        vcmd = (self.register(self.qty_validate),
            '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.qty_box = ttk.Entry(self, validate='key', validatecommand=vcmd, width=5)
        self.qty_box.pack(side='left', **pads)
        
        self.rate_label = ttk.Label(self, text='/min')
        self.rate_label.pack(side='left', **pads)

        self.submit_btn = ttk.Button(self, text='OK', command=self.submit_item)
        self.submit_btn.pack(side='left', **pads)
    
    def qty_validate(self, action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name):
        regex = re.compile(r"(\+|\-)?[0-9.]*$")
        result = regex.match(value_if_allowed)
        result = (value_if_allowed == ""
                or (value_if_allowed.count('+') <= 1
                    and value_if_allowed.count('-') <= 1
                    and value_if_allowed.count('.') <= 1
                    and result is not None
                    and result.group(0) != ""))
        return result
    
    def submit_item(self):
        selected_item = self.item_box.get()
        selected_qty = self.qty_box.get()
        
        show_error = False
        err_title = ''
        err_msg = ''
        
        if not selected_item:
            show_error = True
            err_title, err_msg = 'No item selected', 'Please select an item to continue'
        elif not selected_qty:
            show_error = True
            err_title, err_msg = 'No given quantity', 'Please enter a rate (item/min) to continue'
        elif selected_item not in self.itemdict:
            show_error = True
            err_title, err_msg = 'Item name not found', 'Please select an item in the list'
        
        if show_error:
            messagebox.showerror(err_title, err_msg)
        else:
            target_item = self.itemdict[selected_item]
            target_qty = float(selected_qty)
            self.computingframe.submit_item(target_item, target_qty)

class BaseResourceManager(ttk.Frame):
    computingframe: ComputingFrame

    def __init__(self, master, computingframe: ComputingFrame):
        super().__init__(master)
        
        self.computingframe = computingframe

        ipads = {'ipadx': 0, 'ipady': 0}
        pads = {'padx': 2, 'pady': 2}
        
        self.rowconfigure(0, weight=0, pad=2)
        self.rowconfigure(1, weight=0, pad=2)
        self.columnconfigure(0, weight=0, pad=2)
        self.columnconfigure(1, weight=0, pad=2)
        
        self.label = ttk.Label(self, text='Base resources\n(will be taken as input)',)
        self.label.grid(row=0, column=1)

        self.resourcebox = tk.Listbox(self, height=5)
        self.resourcebox.grid(row=0, column=0, rowspan=2)
        self.update_tree()
        
        self.remove_btn = ttk.Button(self, text='Remove', command=self.remove_resource)
        self.remove_btn.grid(row=1, column=1, sticky='w')
    
    def update_tree(self):
        self.itemdict = dict(sorted({brain.data_items[item]['name']: item for item in self.computingframe.base_resources}.items()))
        
        self.resourcebox.delete(0,'end')
        
        for item in self.itemdict:
            self.resourcebox.insert('end', item)
    
    def remove_resource(self):
        selection = self.resourcebox.curselection()
        resource = self.itemdict[self.resourcebox.get(selection[0])]
        
        self.computingframe.manage_base_resources(resource, 'remove')
        
        # self.update_tree()

class RecipePicker(ttk.Frame):
    
    computingframe: ComputingFrame
    
    def __init__(self, master, computingframe, item: str):
        super().__init__(master, relief='solid')
        self.computingframe = computingframe
        self.item = item

        self.recipedict = {brain.data_recipes[recipe]['name']: recipe for recipe in brain.data_itemtorecipes[item]}
        self.recipelist = list(self.recipedict.keys())
        self.recipelist.append('Set as input')

        ipads = {'ipadx': 0, 'ipady': 0}
        pads = {'padx': 10, 'pady': 10}
        
        #Header
        self.header = ttk.Frame(self, style='light.TFrame')
        self.header.pack(fill='x', **ipads)

        self.item_box = ttk.Label(self.header, text=brain.data_items[item]['name'], style='high.TLabel')
        self.item_box.pack(side='left', **pads)
        
        if item in self.computingframe.recipes:
            default = self.computingframe.recipes[item]
        else:
            default = brain.select_recipe(item)
        
        self.recipe_box = ttk.Combobox(self.header, values=self.recipelist, state='readonly')
        self.recipe_box.set(brain.data_recipes[default]['name'])
        self.recipe_box.pack(side='left', **pads)
        self.recipe_box.bind('<<ComboboxSelected>>', self.change_recipe)
        
        body = ttk.Frame(self)
        body.pack(fill='both', **ipads)
        
        recipe_data = brain.data_recipes[default]
        ncol = 3
        nprod = len(recipe_data['products'])
        ningr = len(recipe_data['ingredients'])
        nlin = 3 + nprod + ningr
        #lines: empty + 'Product' + products + 'Ingredient' + ingredients
        
        for n in range(ncol):
            body.columnconfigure(n, weight=0, pad=2)
        for n in range(nlin):
            body.rowconfigure(n, weight=0, pad=2)
        
        kwargs = {'sticky': 'news'}
        
        #labels
        ratelabel = ttk.Label(body, text='Rate (/min)')
        ratelabel.grid(row=0, column=1, **kwargs)
        prodlabel = ttk.Label(body, text='Products')
        prodlabel.grid(row=1, column=0, **kwargs)
        ingrlabel = ttk.Label(body, text='Ingredients')
        ingrlabel.grid(row=2+nprod, column=0, **kwargs)
        producedinlabel = ttk.Label(body, text='Produced in')
        producedinlabel.grid(row=0, column=2, **kwargs)
        
        #products
        for i, product in enumerate(recipe_data['products']):
            prodnamelabel = ttk.Label(body, text=brain.data_items[product['item']]['name'])
            prodnamelabel.grid(row=i+2, column=0, **kwargs)
            
            rate = 60 * product['amount'] / recipe_data['time']
            prdratelabel = ttk.Label(body, text=rate)
            prdratelabel.grid(row=i+2, column=1, **kwargs)
            
        #ingredients
        for i, ingredient in enumerate(recipe_data['ingredients']):
            ingrnamelabel = ttk.Label(body, text=brain.data_items[ingredient['item']]['name'])
            ingrnamelabel.grid(row=i+3+nprod, column=0, **kwargs)
            
            rate = 60 * ingredient['amount'] / recipe_data['time']
            ingrratelabel = ttk.Label(body, text=rate)
            ingrratelabel.grid(row=i+3+nprod, column=1, **kwargs)
        
        #producedin
        machine = brain.data_buildings[recipe_data['producedIn'][0]]['name']
        machinelabel = ttk.Label(body, text=machine)
        machinelabel.grid(row=1, column=2, **kwargs)
    
    def change_recipe(self, event: tk.Event = None):
        boxchoice = self.recipe_box.get()
        
        if boxchoice=='Set as input':
            self.computingframe.manage_base_resources(self.item, 'add')
        elif boxchoice in self.recipedict:
            self.computingframe.set_item_recipe(self.item, self.recipedict[self.recipe_box.get()])
        else:
            print(f'Error: {boxchoice} not recognized as a valid option')
        
### Functions ###

def main():
    window = Window()
    window.mainloop()
    
    print('Mainloop interrupted. Closing')
    
if __name__=='__main__':
    main()