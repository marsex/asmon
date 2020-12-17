import gc
import esp
import camera
import _thread 
import usocket as socket
import json
import time
from time import sleep
from machine import Pin
from structure import urequests, wifi, machine_data, asmon_sys, color, cam
import uerrno
from structure import urequests as requests
th = _thread.start_new_thread

red = ("\033[1;31;40m")
green = ("\033[1;32;40m")
yellow = ("\033[1;33;40m")
blue = ("\033[1;34;40m")
normal = ("\033[0;37;40m")

cr = cam.start()
if not cr:
    print("Camera not ready. Can't continue!")
else:
    # setup networking
    wifi.start()
    sleep(1)
    wifi.set_credentials('1255,12551255')
    credentials_state, cred_ssid, cred_psw = wifi.get_credentials()

    while credentials_state == False:
        print('Getting credentials...')
        credentials_state, cred_ssid, cred_psw = wifi.get_credentials()
        sleep(1)
        pass

    sleep(1)

    wifi_connected = wifi.connect(cred_ssid, cred_psw)

    while wifi_connected == False:
        print("WIFI not ready. Wait...")
        sleep(2)
        pass

    print(green+'Connection successful\n'+normal)
    print("Up Up and Away!")
    sleep(2)
    asmon_sys.start()