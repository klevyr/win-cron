import win32serviceutil
import win32service
import win32event
import os, sys
import subprocess

class CrontabService(win32serviceutil.ServiceFramework):
    _svc_name_ = "PyCrontab Service"
    _svc_display_name_ = "Crontab Service"
    _svc_description_ = "Servicio para administrar los trabajos de post-capp"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.process:
            self.process.terminate()

    def SvcDoRun(self):
        os.chdir("D:\\com\\jupyter\\tools\\crontab")
        self.process = subprocess.Popen(["crontab.py", "crontab.txt"], shell=True)
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        self.process.wait()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(CrontabService)
