'''
process_info.py
Module used to get other processes information, more specifically their window title.
Its based on this answer from stackoverflow: https://stackoverflow.com/questions/70618975/python-get-windowtitle-from-process-id-or-process-name
'''

import win32gui
import win32process
import psutil
import ctypes

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

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