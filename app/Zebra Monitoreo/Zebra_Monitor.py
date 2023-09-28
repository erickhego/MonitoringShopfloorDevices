#!/usr/bin/env python
import psutil
import subprocess
import signal
import datetime
import os
import time
import re
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

current_dir = r'C:\Users\PC\WORKSPACE\COMPAS\MONITOREO\app\Zebra Monitoreo'


break_flag = False
restart_flag = False
process_id = 0

class MyEventHandler(FileSystemEventHandler):
    def __init__(self, log):
        self.log_file = log
        super().__init__()

    def on_modified(self, event):
        print(event.src_path, "Modificado")
        print(self.log_file)

        try:
            # time.sleep(0.1)
            with open(current_dir + "\\IoTConnector\\logs\\" + self.log_file) as log:
                    log_lines = log.readlines()
                    last_update = log_lines[-1]
                    event = re.search(r"EVENT:(\w*\s\w*|\w*)", last_update)
                    # print(event.group(1))
                    # print('+++' + log_lines[-1])

                    if event:
                        with open(current_dir + r'\bcr_status.json', 'w') as status:
                            data = ''
                            status.writelines(data)
                            status.close()
                        if event.group(1) == 'DEVICE ATTACHED':
                            with open(current_dir + r'\bcr_status.json', 'w') as status:
                                bcr_data = {'BCR' : 'IDLE'}
                                json.dump(bcr_data, status, indent=1)
                        elif event.group(1) == 'DEVICE DETACHED':
                            with open(current_dir + r'\bcr_status.json', 'w') as status:
                                bcr_data = {'BCR' : 'DOWN'}
                                json.dump(bcr_data, status, indent=1)
                        elif event.group(1) == 'BATTERY':
                            with open(current_dir + r'\bcr_status.json', 'w') as status:
                                battery_info = re.search(r"(Charge = (\d*)).*(ChargingStatus = (\w*\s\w*|\w*)).*(BatteryHealthPercentage = (\d*))", last_update)
                                bcr_data = {'BCR' : 'IDLE',
                                            'CHARGE' : battery_info.group(2),
                                            'CHARGING STATUS' : battery_info.group(4),
                                            'BATTERY HEALTH PERCENTAGE' : battery_info.group(6)}
                                json.dump(bcr_data, status, indent=1)
                        else:
                            pass
                    log.close()
        except:
            pass

def check_IoT_process():
    '''This function checks if IoTConnector is running and returns True or False respectively.'''
    for p in psutil.process_iter():
        if p.name() == 'IoTConnector.exe':
            IoT = True
            return IoT
        else:
            IoT = False
    return IoT

def run_IoT_process():
    '''Excecutes IoTConnector'''
    global process_id
    process = subprocess.Popen([current_dir + "\\IoTConnector\\IoTConnector.exe"])
    process_id = process.pid
    
def stop_IoT_process():
    try:
        global process_id
        os.kill(process_id,signal.SIGTERM)
    except:
        pass

def modify_xml(current_date):
    '''Replaces the date if the log file of currently day isn't in the log directory'''
    new_string = '                    <property key="log_file_name" value="iotConnector_' + current_date + '.log" />\n'
    # Open the XML config file and replace the name of the file the current date
    with open(current_dir + "\\IoTConnector\\IoTConnector-Config.xml", 'r') as xml_config:
        data = xml_config.readlines()
        data[11] = new_string
    # Write the modified line on the config file. 
    with open(current_dir + "\\IoTConnector\\IoTConnector-Config.xml", 'w') as xml_conf_date:
        xml_conf_date.writelines(data)
        xml_conf_date.close()

def check_len_log(log_file):
    with open(current_dir + "\\IoTConnector\\logs\\" + log_file) as log:
        log_lines = log.readlines()
        len_log_lines = len(log_lines)
        log.close()
        return len_log_lines

def create_day_log(observer):
    time.sleep(1)
    # Obtain the current date
    current_date = str(datetime.date.today())
    # print(current_date)
    # Concatenate the Preffix name + current date
    log_file = 'iotConnector_' + current_date + '.log'
    log_dir = current_dir + "\IoTConnector\logs"
    # check if exists the log file of the current day
    log_files_list = os.listdir(r'{}'.format(log_dir))
    # If it doesn't exist, then modify the XML, so when the IoTConnector runs create new log file with the current date
    if log_file not in log_files_list:
        print('Modificando XML')
        modify_xml(current_date = current_date)
        stop_IoT_process()
        run_IoT_process()
        restart(observer)
        
    return log_file
            
def restart(observer):
    global restart_flag
    print('restarting...')
    observer.stop()
    restart_flag = True
    run()

def stop():
    global break_flag
    stop_IoT_process()
    break_flag = True
    

def run():
    observer = Observer() 
    log_file = create_day_log(observer)
    observer.schedule(MyEventHandler(log_file), current_dir + "\\IoTConnector\\logs\\", recursive = False)
    observer.start()

    while(True):
        log_file = create_day_log(observer)
        # print(log_file)

        # check if IoTConnector is running
        iot = check_IoT_process()
        # If not is running, then run
        if iot == False:
            print('Starting process')
            run_IoT_process()
            time.sleep(3)

        global restart_flag
        if restart_flag:
            restart_flag = False
            run()
            break

        global break_flag
        if break_flag:
            break

        time.sleep(0.1)
        with open(current_dir + "\\IoTConnector\\logs\\" + log_file , 'r') as log:
            pass
        log.close()
        observer.join(1)

            
if __name__ == '__main__':
    run()