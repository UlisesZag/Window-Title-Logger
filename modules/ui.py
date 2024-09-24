import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo

import sys
import psutil
import notifypy
import os

import modules.process_info as proc_info
import modules.configfile as configfile

class ProcessSelectGUI(tk.Tk):
    def __init__(self, log_loop_func=None, logs_folder_func=None, script_dir=""):
        super().__init__()
        self.log_loop_func = log_loop_func
        self.proc_var = tk.StringVar(value="")
        self.logs_folder_func = logs_folder_func
        self.script_dir = script_dir
        self.icon_path = script_dir+"/strayico.ico"
    
        #Construimos la UI
        self.title("Window Title Logger")
        self.iconbitmap(default=self.icon_path)

        #Menu bar
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        self.options_menu = tk.Menu(self.menubar, tearoff=False)
        self.options_menu.add_command(label='Open logs folder',command=self.logs_folder)
        self.options_menu.add_command(label="Preferences", command=self.show_config)
        self.options_menu.add_command(label='About', command=self.about)

        self.menubar.add_cascade(label="Options",menu=self.options_menu)

        #Frame
        self.select_frame = ttk.Labelframe(self, text="Process Selection")
        self.select_frame.pack(expand=True, fill="both", padx=10, pady=5, ipadx=5, ipady=5)
        self.columnconfigure(0, weight=1)
        self.select_frame.columnconfigure(0, weight=1)
        self.select_frame.columnconfigure(1, weight=3)
        #Label
        self.select_label = ttk.Label(self.select_frame, text="Process to log: ")
        self.select_label.grid(column=0, row=0, sticky=tk.E)
        #Selector de procesos
        self.select_combobox = ttk.Combobox(self.select_frame, textvariable=self.proc_var, values=(1,2,3), state="readonly")
        self.select_combobox.grid(column=1, row=0, sticky=tk.EW)
        self.bind("<1>", lambda e: self.update_processes_options())

        #Boton de logear
        self.log_button = ttk.Button(self.select_frame, text="Start logging", command=self.log)
        self.log_button.grid(column=0, row=1, columnspan=2, sticky=tk.NSEW)

        self.update_processes_options()

    def log(self):
        if self.proc_var.get() != "":
            self.log_loop_func(self.proc_var.get())
    
    def update_processes_options(self):
        procs = []
        for i in psutil.process_iter():
            if proc_info.is_visible_by_id(i.pid):
                procs.append(i.name())

        self.select_combobox["values"] = procs
    
    def logs_folder(self):
        self.logs_folder_func()
    
    def show_config(self):
        config_window = ConfigGUI(self, self.script_dir)
        config_window.grab_set()

    def about(self):
        showinfo("About", 
'''Window Title Logger v0.1
Github: https://github.com/UlisesZag/Window-Title-Logger
Licence: MIT
'''
)
        
class ConfigGUI(tk.Toplevel):
    def __init__(self, root, script_dir):
        super().__init__(root)

        self.title("Settings")

        self.script_dir = script_dir

        self.config = configfile.load_config(script_dir+"/config.json")

        self.t_scan_interval_var = tk.DoubleVar(value=float(self.config["log_time_interval"]))
        self.p_scan_interval_var = tk.DoubleVar(value=float(self.config["wait_time_interval"]))

        self.frame = ttk.Labelframe(self, text="Configuration")
        self.frame.pack(padx=5, pady=5, ipadx=2.5, ipady=2.5)

        self.title_scan_interval_label = ttk.Label(self.frame, text="Title Scan Interval (seconds): ")
        self.title_scan_interval_label.grid(column=0, row=0)

        self.title_scan_interval_spinbox = ttk.Spinbox(
                                                    self.frame, 
                                                    from_=0.1, 
                                                    to=10, 
                                                    textvariable=self.t_scan_interval_var, 
                                                    values= [x/100 for x in range(1,1000)],
                                                    wrap=True
                                                )
        self.title_scan_interval_spinbox.grid(column=1, row=0)

        self.process_scan_interval_label = ttk.Label(self.frame, text="Process Scan Interval (seconds): ")
        self.process_scan_interval_label.grid(column=0, row=1)

        self.process_scan_interval_label = ttk.Spinbox(
                                                    self.frame, 
                                                    from_=0.1, 
                                                    to=10, 
                                                    textvariable=self.p_scan_interval_var, 
                                                    values= [x/100 for x in range(1,1000)],
                                                    wrap=True
                                                )
        self.process_scan_interval_label.grid(column=1, row=1)

        self.save_button = ttk.Button(self, text="Save settings", command=self.save_config)
        self.save_button.pack(padx=5, pady=5, expand=True, fill="both")
    
    def save_config(self):
        self.config["log_time_interval"] = self.t_scan_interval_var.get()
        self.config["wait_time_interval"] = self.p_scan_interval_var.get()

        configfile.save_config(self.script_dir+"/config.json", self.config)
        showinfo("", "Settings saved correctly.")
        
#Toast notification
def send_toast(title, message, icon_path):
    notification = notifypy.Notify()
    notification.title = title
    notification.message = message
    notification.application_name = 'Window Title Logger'
    notification.icon = icon_path

    notification.send()