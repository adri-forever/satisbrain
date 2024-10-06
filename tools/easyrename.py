import tkinter as tk
import os, sys, shutil
from tkinter import ttk

# Get the path of the current directory (main_directory)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to folder_one
parent_folder = os.path.join(current_dir, '..')
# folder_one_path = os.path.join(current_dir, '..', 'scripts')

# Add folder_one to the system path
sys.path.append(parent_folder)

# from scripts import displayer
from scripts import brain

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
    
    def __init__(self):
        super().__init__()
        
        self.title('Image renamer')
        icon = tk.PhotoImage(file='resource\\image\\satisbrain.png')
        self.wm_iconphoto(False, icon)
        
        # Load data
        self.itemdict = {value['name']: key for key, value in brain.data_items.items()}
        
        self.oldpath = 'tools\\raw_images\\'
        self.newpath = 'tools\\processed_images\\'
        
        if not os.path.exists(self.oldpath):
            os.mkdir(self.newpath) #prepare folder for new images
        self.images = os.listdir(self.oldpath) #find images
        
        self.index = 0
        self.NoOfIm = len(self.images)
        
        # UI elements
        pads = {'padx': 5, 'pady': 5}
        
        self.titlevar = tk.StringVar(self, 'No item selected')
        self.image_title = tk.Label(self, textvariable=self.titlevar)
        self.image_title.pack()
        
        # self.image = tk.PhotoImage(file='tools\\raw_images\\A.I. Limiter.png')
        self.image_label = tk.Label(self)
        self.image_label.pack()
        
        self.controls = tk.Frame(self, bg='black')
        self.controls.pack(fill='x')
        
        self.prev_btn = tk.Button(self.controls, text='Previous', command=self.previous_img)
        self.prev_btn.pack(side='left', **pads)
        
        self.autocomplete = AutocompleteCombobox(self.controls)
        self.autocomplete.pack(side='left', **pads)
        self.autocomplete.set_completion_list(self.itemdict.keys())
        
        self.ok_btn = tk.Button(self.controls, text='Ok', command=self.rename_image)
        self.ok_btn.pack(side='left', **pads)
        
        self.next_btn = tk.Button(self.controls, text='Next', command=self.change_image)
        self.next_btn.pack(side='left', **pads)
        
        self.change_image(0)
    
    def previous_img(self):
        self.change_image(-1)
    
    def change_image(self, increment = 1):
        self.index += increment
        self.index %= self.NoOfIm
        
        self.image = tk.PhotoImage(file=os.path.join(self.oldpath, self.images[self.index]))
        self.image_label.configure(image=self.image)
        self.titlevar.set(self.images[self.index])
        
        # print(self.index, self.images[self.index])

    def rename_image(self):
        name = ''
        selected = self.autocomplete.get()
        
        if selected in self.itemdict:
                name = self.itemdict[selected]
        else:
                print(f'Error in selection, could not handle "{selected}"')
                return
        
        source = os.path.join(self.oldpath, self.images[self.index])
        destination = os.path.join(self.newpath, name+'.png')
        
        shutil.copy(source, destination)

        del self.images[0]
        self.NoOfIm = len(self.images)
        
        self.change_image(0) # reload to change image

window = Window()
window.mainloop()