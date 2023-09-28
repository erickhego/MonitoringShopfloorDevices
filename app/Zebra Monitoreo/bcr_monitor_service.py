#!/usr/bin/env python

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import Zebra_Monitor

class bcr_monitor_Service(win32serviceutil.ServiceFramework):
    _svc_name_ = 'BCR_monitor_Service'
    _svc_display_name_ = 'BCR_monitor_Service'
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(120)

    def SvcStop(self):
        Zebra_Monitor.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, 'Hi'))
        
        self.main()
    
    def main(self):
        Zebra_Monitor.run()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(bcr_monitor_Service)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(bcr_monitor_Service)