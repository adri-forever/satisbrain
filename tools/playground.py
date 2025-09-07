from airium import Airium
import tkinter as tk, sys
from tkinter import filedialog

a = Airium()

a('<!DOCTYPE html>')
with a.html():
    with a.head():
        a.meta(content='width=device-width, initial-scale=1', name='viewport')
        with a.style():
            a('body {\n\tbackground-color: #333;\n}\n\nh1 {\n\tcolor: white;\n\tfont-family: "Segoe UI", sans-serif;\n\t\n}\n\ntable {\n\tpadding: 5px 0 5px;\n}\n\ntd, th {\n\tpadding: 1px 5px;\n}\n\nth, td {\n  border: 1px solid #444;\n}\n\n.collapsible {\n\tbackground-color: #555;\n\tcolor: white;\n\tcursor: pointer;\n\tpadding: 10px;\n\twidth: 100%;\n\tborder: none;\n\ttext-align: left;\n\toutline: none;\n\tfont-size: 16px;\n\tfont-family: "Segoe UI", sans-serif;\n}\n\n.collapsible:hover {\n\tbackground-color: #FA9649;\n}\n.active {\n\tbackground-color: #777;\n}\n\n.content {\n\tcolor: white;\n\tpadding: 0 18px;\n\tdisplay: none;\n\toverflow: hidden;\n\tbackground-color: #333;\n\tfont-family: "Segoe UI", sans-serif;\n}\n\n.high {\n\tcolor: #FA9649\n}')
    with a.body():
        a.h1(_t='Production plan:')
        a.button(klass='collapsible', type='button', _t='Tier 1')
        with a.div(klass='content'):
            a.button(klass='collapsible', type='button', _t='Uranium Fuel Rod : Uranium Fuel Rod (default)')
            with a.div(klass='content'):
                with a.p():
                    a('Produced in:')
                    a.b(_t='Manufacturer')
                with a.p():
                    a('Production rate:')
                    a.b(_t='.4 /min')
                with a.p():
                    a('Required amount of machines:')
                    a.b(_t='25')
                    a('(total rate:')
                    a.b(_t='10 /min')
                    a(')')
                a.p(_t='Ingredients:')
        a.button(klass='collapsible', type='button', _t='Tier 2')
        with a.div(klass='content'):
            a.button(klass='collapsible', type='button', _t='Electromagnetic control rod')
            with a.div(klass='content'):
                with a.table():
                    with a.tr():
                        a.th()
                        a.th(_t='Rate (/min)')
                        a.th(_t='Total (/min)')
                        a.th()
                        a.th(_t='Produced in')
                        a.th(_t='Amount')
                    with a.tr():
                        a.td(_t='Electromagnetic Control Rod')
                        a.td(_t='4')
                        with a.td(klass='high'):
                            a('40')
                            with a.td():
                                a.td(_t='Assembler')
                                a.td(_t='10')
                    with a.tr():
                        a.th(_t='Ingredients')
                    with a.tr():
                        a.td(_t='Stator')
                        a.td(_t='3')
                        a.td(klass='high', _t='30')
                    with a.tr():
                        a.td(_t='AI Limiter')
                        a.td(_t='4')
                        a.td(klass='high', _t='40')
            a.button(klass='collapsible', type='button', _t='Encased Industrial Beam')
            with a.div(klass='content'):
                a.p(_t='Recipe here')
        a.button(klass='collapsible', type='button', _t='Base resources')
        with a.div(klass='content'):
            with a.table():
                with a.tr():
                    a.td(_t='Water')
                    with a.td():
                        a.b(_t='600 /min')
                with a.tr():
                    with a.tr():
                        a.td(_t='Sulfur')
                        with a.td():
                            a.b(_t='600 /min')
                    with a.tr():
                        with a.tr():
                            a.td(_t='Iron Ore')
                            with a.td():
                                a.b(_t='480 /min')
                        with a.tr():
                            with a.tr():
                                a.td(_t='Copper Ore')
                                with a.td():
                                    a.b(_t='360 /min')
        with a.script():
            a('var coll = document.getElementsByClassName("collapsible");\nvar i;\n\nfor (i = 0; i < coll.length; i++) {\n\tcoll[i].addEventListener("click", function() {\n\t\tthis.classList.toggle("active");\n\t\tvar content = this.nextElementSibling;\n\t\tif (content.style.display === "block") {\n\t\t\tcontent.style.display = "none";\n\t\t} else {\n\t\tcontent.style.display = "block";\n\t\t}\n\t});\n}')


if __name__ == '__main__':
    
    root = tk.Tk()
    
    filetypes = [('HTML', '*.html')]
    initialdir = '.\\output'
    initialfile = 'report.html'
    title = 'Save plan as'
    
    command= lambda: filedialog.asksaveasfilename(filetypes=filetypes, initialdir=initialdir, initialfile=initialfile, title=title)
    
    btn = tk.Button(text='here', command=command)
    btn.pack()
    
    root.mainloop()