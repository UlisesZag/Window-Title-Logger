import win32gui
import win32process
import psutil
import ctypes

import time
import datetime
import atexit
import sys
import os

from PIL import Image
import pystray
import threading

from tkinter.messagebox import showinfo

script_dir = os.path.dirname(os.path.realpath(__file__))

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

proc_name = ""

def get_process_id_by_name(process_name):
    proc_pids = []

    for proc in psutil.process_iter():
        if process_name in proc.name():
            proc_pids.append(proc.pid)

    return proc_pids

def get_hwnds_for_pid(pid):
    def callback(hwnd, hwnds):
        #if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)

        if found_pid == pid:
            hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds 

def get_window_title_by_handle(hwnd):
    length = GetWindowTextLength(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    GetWindowText(hwnd, buff, length + 1)
    return buff.value

def get_proc_handle(proc_name):
    pids = get_process_id_by_name(proc_name)

    for i in pids:
        hwnds = get_hwnds_for_pid(i)
        for hwnd in hwnds:
            if IsWindowVisible(hwnd):
                return hwnd

def file_append_line(path, string):
    with open(path, "a") as file:
        file.write(string)

def log_message(path, string):
    try:
        print(string)
        file_append_line(path, string+"\n")
    except PermissionError:
        print(f"ERROR: Permission denied for file {path}. Make sure the program has the correct permissions. Try running as admin.")

class App:
    def main(self):
        self.stop_flag = False
        self.log_started = False
        self.stray = True

        if len(sys.argv) == 1:
            proc_name = input("Process name to log: ")
        else:
            proc_name = sys.argv[1]
            print("Process to log: ",proc_name)
        
        #Crea el icono
        if self.stray:
            self.sticon = SystemTrayIcon()
            self.sticon.setup_system_tray(
                cancel_func=self.cancel_logging,
                process_logging = proc_name
                )

        atexit.register(self.exit_handler)

        print()
        self.log_loop(proc_name)

    #Bucle de logeo
    def log_loop(self, proc_name):
        log_file_path = script_dir + "/" + proc_name+".log"
        last_title = ""
        
        #Espera a que el programa arranque
        print("Waiting for the process to start...")
        seconds = 30
        while seconds > 0:
            proc_handle = get_proc_handle(proc_name)
            t = get_window_title_by_handle(proc_handle)
            if proc_handle != None and t != None:
                break
        
            #Si lo cancelan deja de esperar al proceso
            if self.stop_flag:
                seconds = -1
                break
            
            time.sleep(0.25)
            seconds -= 0.25
        
        #Si seconds es 0 quiere decir timeout, no encontro el programa y sale sin esperar.
        if seconds <= 0:
            print("Timeout. Exiting...")
            return
        
        self.log_started = True
        log_message(log_file_path, f"--- Log started for process {proc_name}, at {datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")} ---")

        #Bucle principal donde registra los titulos
        while True:
            # Flag para cancelar el logger desde el systray
            if self.stop_flag:
                break

            proc_handle = get_proc_handle(proc_name)
            
            #Si es none quiere decir que el proceso logueado se termino de ejecutar. Entonces cierra el bucle
            if proc_handle == None:
                break

            proc_title = get_window_title_by_handle(proc_handle)
            if last_title != proc_title:
                log_message(log_file_path, f"[{datetime.datetime.now().strftime("%d/%m/%Y %I:%M%p")}] "+proc_title)
                last_title = proc_title
            
            time.sleep(0.25)
        
        #Fin del programa.
        log_message(log_file_path,f"--- Process {proc_name} finished, at {datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")} ---")

        if self.stray:
            showinfo("El creador de PySTray es puto.", "Por favor, terminar de cerrar el logger desde el icono en la barra de tareas")
        else:
            showinfo("WTLogger: Terminado", f"El proceso WTLogger que registaba el proceso \"{proc_name}\" ha finalizado.")

    #Manejador de cerrar el programa
    def exit_handler(self):
        #Fin del programa.
        if self.log_started:
            log_message(proc_name+".log", f"--- Logger terminated, at {datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")} ---")
        
        self.sticon.stop_system_tray()
    
    def cancel_logging(self):
        self.stop_flag = True

class SystemTrayIcon():
    def __init__(self):
        self.thread = None
        self.icon_stop_flag = threading.Event()

    def setup_system_tray(self, cancel_func=None, process_logging="PROCESS LOGGING"):
        self.thread = SystemTrayThread(
            cancel_func=cancel_func, 
            process_logging=process_logging,
            icon_stop_flag=self.icon_stop_flag)
        self.thread.start()
    
    def stop_system_tray(self):
        self.thread.stop_icon()

class SystemTrayThread(threading.Thread):
    def __init__(self, cancel_func=None, process_logging="PROCESS LOGGING", icon_stop_flag=None):
        super().__init__()
        self.cancel_func = cancel_func
        self.process_logging = process_logging
        self.icon_stop_flag = icon_stop_flag

    def run(self):
        image = Image.open("strayico.ico")
        menu = (pystray.MenuItem(f'Process logging: {self.process_logging}',  None),
                pystray.MenuItem(f'Open log file', None),
                pystray.MenuItem('End logging',self.cancel_logging))
        self.icon = pystray.Icon("Window Title Logger", image, "Window Title Logger", menu)
        self.icon.run(setup=self.icon_loop)
    
    def icon_loop(self, icon):
        icon.visible = True
    
    def stop_icon(self):
        self.icon.stop()

    def cancel_logging(self):
        self.icon.stop()
        self.cancel_func()

if __name__ == '__main__':
    app = App()
    app.main()
    
