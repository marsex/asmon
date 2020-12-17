import gc
import esp
import camera
import _thread 
import usocket as socket
import json
import ujson
import time
from time import sleep
from machine import Pin
from structure import urequests, wifi, machine_data, asmon_sys, color, cam
import uerrno  
from structure import urequests as requests
th = _thread.start_new_thread

import uasyncio as asyncio

red = ("\033[1;31;40m")
green = ("\033[1;32;40m")
yellow = ("\033[1;33;40m")
blue = ("\033[1;34;40m")
normal = ("\033[0;37;40m")

# esp.osdebug(False)
esp.osdebug(True)

h={
'POST': """POST /$req HTTP/1.1
Host: 127.0.0.1:9515
Content-Type: $type
Content-Length: """
}

hdr = {
    'POST': """POST /snap HTTP/1.1
Host: 127.0.0.1:9515
Content-Type: image/jpeg
Content-Length: """
}

json_command = {}
def clean_up(cs):
    cs.close()  # flash buffer and close socket
    del cs
    gc.collect()


def frame_gen():
    while True:
        buf = camera.capture()
        yield buf
        del buf
        gc.collect()

async def cli(sc):     
    print(color.yellow()+'\n Starting CAM_SYSTEM:')
    while True:      
        s = socket.socket()
        try:
            s.connect(("marstv.softether.net" , 8081))
            img = next(pic)  
            s.send(b'%s %d\r\n\r\n' % (hdr['POST'], len(img)))
            s.send(img)
            s.send(b'\r\n')
            result = s.recv(12)
            while (len(result) > 0):
                #print(result)
                #print('\ngot result')
                break
        except Exception as e:
            ee = str(e)
            if ee != '':
                print('cam error: '+ ee)    
        s.close()  # flash buffer and close socket
        gc.collect()
        sleep(.1)
        
def tcam(sc):     
    print(color.yellow()+'\n Starting CAM_SYSTEM:')
    while True:      
        s = socket.socket()
        s.setblocking(False)
        try:
            while True:
                try:
                    print('connecting')
                    s.connect(("asmon.com.ar" , 8081))
                except OSError as e:
                    if str(e) == "127":
                        print('connected')
                        break
                sleep(0.2)
            
            img = next(pic)  
            s.sendall(b'%s %d\r\n\r\n' % (hdr['POST'], len(img)))
            s.sendall(img)
            s.sendall(b'\r\n')
            result = s.recv(2000)
            while (len(result) > 0):
                #print(result)
                print('\ngot result')
                break
        except Exception as e:
            ee = str(e)
            if ee != '':
                print('cam error: '+ ee)    
        s.close()  # flash buffer and close socket
        gc.collect()
        sleep(.1)

def start_com(address):
    global json_command
    print(color.yellow()+'\n Starting DATA_SYSTEM:')
    while True: 
        try:
            client_socket = socket.socket()
            client_socket.setblocking(False)

            try:    
                client_socket.connect(address)
            except OSError as error:
              if error.args[0] not in [uerrno.EINPROGRESS, uerrno.ETIMEDOUT]:
                print(color.red()+'**** Error connecting ****', error, color.normal())
            
            try:
                POST(client_socket, 'esp_data/dev_cam01', 'json',machine_data.get())         
                while True:
                    res = str(client_socket.recv(2000))
                    if res.find('200 OK') != -1:
                        command = str(res)[str(res).find('\\r\\n\\r\\n')+len('\\r\\n\\r\\n'):len(str(res))-1]
                        new_json_command = ujson.loads(command)
                        if json_command != new_json_command:
                            json_command = new_json_command
                            print(json_command)
                    break    
            except OSError as error:
                if error.args[0] not in [uerrno.EINPROGRESS, uerrno.ETIMEDOUT]:
                    print(color.red()+'\t\t\t**** ERROR writing ****\n\t\t\t', error, color.normal())

            client_socket.close()  # flash buffer and close socket
            del client_socket
            gc.collect()
        except OSError as error:
            print(color.red()+'\t\t\t**** ERROR creating socket ****\n\t\t\t', error, color.normal())
        sleep(.1)


def POST(s, req, type, data):
    size = 0
    if type == 'json':
        type = 'application/json'
        data = json.dumps(data)
        size = len(data)
        data = data.encode()
        header = h['POST'].replace('$req',req).replace('$type',type)

    s.send(b'%s %d\r\n\r\n' % (header, size))
    s.send(data)
    s.send(b'\r\n')
    
cr = cam.start()
if not cr:
    print("Camera not ready. Can't continue!")
else:
    pic = cam.frame_gen()
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
    
    # host, port = ['marstv.softether.net','8080'] #server_list[0].split(':')
    # address = socket.getaddrinfo(host, port)[0][-1]
    # print(address)
    # th(start_com, (address,))
    th(tcam,('asd',))
    #ath = asyncio.get_event_loop()
    
    #ath.create_task(cli('t'))
    #ath.run_forever()
    #asmon_sys.start()