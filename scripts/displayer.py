import tkinter as tk
from tkinter import ttk

### Classes ###

class Window(tk.Tk):
    
    tabcount = 0
    
    def __init__(self):
        super().__init__()
        
        self.title('Satisbrain ALPHA')
        #set icon
        self.geometry('720x480')
        
        self.topbuttonbar = TopButtonBar(self)
        self.topbuttonbar.pack(fill='x')
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
    
    def newtab(self):
        self.tabcount += 1
        
        tabname = f'tab_{self.tabcount}'
        print(f'{tabname=}')
        tabname_d = f'Plan {self.tabcount}'
        setattr(self.notebook, tabname, ComputingFrame(self.notebook))
        newtab: ComputingFrame = getattr(self.notebook, tabname)
        newtab.pack(fill='both', expand=True)
        self.notebook.add(newtab, text=tabname_d)
        self.notebook.select(newtab)
        
        
class TopButtonBar(ttk.Frame):
    
    def __init__(self, master: Window):
        super().__init__(master)
        
        self.new_btn = ttk.Button(self, text='New', command=self.newtab)
        self.new_btn.pack(side='left')
    
    def newtab(self):
        self.master.newtab()

class ComputingFrame(tk.Canvas):
    """
    Crashing on change tab:
    probably because of scrollbar -> verify if still crashing without scrollbar
        -> it is
    
    if so
    try different function for <Configure> (only do if current tab is self, and maybe with an after at 1ms or whatever)
    try different scrollbar at all if that exists
    """
    
    def __init__(self, master: ttk.Notebook):
        super().__init__(master, background='black')
        
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.yview)
        self.scrollbar.pack(side='right', fill='y')
        
        self.configure(yscrollcommand=self.scrollbar.set)
        self.bind('<Configure>', lambda e: self.after(1, self.scroller))
        
        self.innerframe = ttk.Frame(self)
        
        self.create_window((0,0), window=self.innerframe, anchor='nw')
        
        for i in range(20):
            ttk.Button(self.innerframe, text=f'button {i}').pack(pady=5)

    def scroller(self, event: tk.Event = None):
        if str(self) == self.master.select():
            self.configure(scrollregion=self.bbox('all'))
        
### Functions ###

def main():
    window = Window()
    window.mainloop()
    
    print('Mainloop interrupted. Closing')
    
if __name__=='__main__':
    main()