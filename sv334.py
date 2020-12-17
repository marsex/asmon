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
from structure import urequests, wifi, machine_data, asmon_sys  , color, cam
import uerrno  
from structure import urequests as requests
th = _thread.start_new_thread


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

def cli(sc):     
    while True:
    
        print('Check com_socket')
        com_state = sget('com')
        while com_state != 'socket_closed':
            com_state = sget('com')
            sleep(.05)
            pass

        sset('cam','creating_socket')           
        s = socket.socket()
        try:
            
            #s.setblocking(0)
            s.connect(("asmon.com.ar" , 8081))
        #    s.sendall(b"GET /connect/espcam/hola HTTP/1.1\r\nHost: feelfree.softether.net\r\nAccept: application/json\r\n\r\n")
            
            img = next(pic)
            
            s.send(b'%s %d\r\n\r\n' % (hdr['POST'], len(img)))
            s.send(img)
            s.send(b'\r\n')
            result = s.recv(12)
            while (len(result) > 0):
                #print(result)
                #print('\ngot result')
                break
            sset('cam','svgot_img')
        except Exception as e:
            ee = str(e)
            if ee != '':
                print('cam error: '+ ee)

        #print('bye')
        s.close()  # flash buffer and close socket
        #del s
        gc.collect()
        
        sset('cam','socket_closed')
        time.sleep(1)
        
def start_com(address):
    global json_command
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
                    sleep(.2)
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
        
        
def start_cam(address):
    while True:
        com_state = sget('com')
        if com_state == 'socket_closed':
            sset('cam','busy')
            try:
                client_socket = socket.socket()
                th(timeout,(client_socket,5))
                try:    
                    client_socket.connect(address)
                except OSError as error:
                  if error.args[0] not in [uerrno.EINPROGRESS, uerrno.ETIMEDOUT]:
                    print(color.red()+'**** Error connecting  CAM ****', error,color.normal())
                img = next(pic)
                try:
                    POST(client_socket, 'snap/dev_cam01', 'img',img) 
                    while True:
                        res = str(client_socket.recv(2000))
                        #if res.find('200 OK') != -1:
                            #print(res)
                        break    
                except OSError as error:
                    if error.args[0] not in [uerrno.EINPROGRESS, uerrno.ETIMEDOUT]:
                        print(color.red()+'\t\t\t**** ERROR writing CAM  ****\n\t\t\t', error,color.normal())

                client_socket.close()  # flash buffer and close socket
                del client_socket
                gc.collect()
            except OSError as error:
                print(color.red()+'\t\t\t**** ERROR creating CAM socket ****\n\t\t\t', error, color.normal())
        sset('cam','socket_closed')
        sleep(.2)

def timeout(s,time):
    timeout_count = 0
    while True:
        timeout_count = timeout_count + 1
        if timeout_count > time:
            break
        sleep(.1)
    s.close()
    del s
    gc.collect()
    #print(color.red() + 'TIME OUT' + color.normal())
        
def POST(s, req, type, data):
    size = 0
    if type == 'json':
        type = 'application/json'
        data = json.dumps(data)
        size = len(data)
        data = data.encode()
        header = h['POST'].replace('$req',req).replace('$type',type)
    elif type == 'img':
        type = 'image/jpeg'
        size = len(data)
        header = h['POST'].replace('$req',req).replace('$type',type)

    s.send(b'%s %d\r\n\r\n' % (header, size))
    s.send(data)
    s.send(b'\r\n')


def start():
    print(color.yellow()+'\n Starting CAM_SYSTEM')
    #server_list = get_server_list()
    host, port = ['asmon.com.ar','8081'] #server_list[0].split(':')
    if host != 'null':
        print(color.green()+'\nStart server communication\n' +
              'IP:', host, '\nPORT:', port+'\n'+color.normal())
        try:
            address = socket.getaddrinfo(host, port)[0][-1]
            print(address)
            th(start_cam, (address,))
        except:
            print(color.red()+'Error getting addr info from', host, port, color.normal())
    else:
        print(color.red()+'Error starting CAM_SYSTEM'+color.normal())

def ur(s):
    print(color.yellow()+'\n Starting ESP_DATA SYSTEM')
    while True:
        url = "http://asmon.com.ar:8080/esp_data/dev_cam01"
        headers = {'X-AIO-Key': 'xxxxxxxxxxxxxxxxxxx',
                   'Content-Type': 'application/json'}
        
        data = json.dumps(machine_data.get())
        results={}
        try:
            r = requests.post(url, data=data, headers=headers)
            results = r.json()
            print(blue,results,normal)
        except OSError as error:
            print('\n'+red)
            print('esp_data failed')
            print(error)
            print('\n'+normal)
    gc.collect()
    sleep(.1)
    
def snap(s):
    print(color.yellow()+'\n Starting CAM_SYSTEM')
    while True:
        url = "http://asmon.com.ar:8081/snap/dev_cam01"
        headers = {'X-AIO-Key': 'xxxxxxxxxxxxxxxxxxx',
                   'Content-Type': 'image/jpeg'}
        data = next(pic)
        results={}
        try:
            r = requests.post(url, data=data, headers=headers)
            results = r.json()
            print(green,results,normal)
        except OSError as error:
            print('\n'+red)
            print('cam failed')
            print(error)
            print('\n'+normal)
    gc.collect()
    sleep(.1)
    
    
def plus(s):
    print(color.yellow()+'\n Starting CAM+DATA_SYSTEM')
    while True:
        e=''
        url = "http://asmon.com.ar:8080/esp_data/dev_cam01"
        headers = {'X-AIO-Key': 'xxxxxxxxxxxxxxxxxxx',
                   'Content-Type': 'application/json'}
        data = json.dumps(machine_data.get())

        while True:
            try: 
                r = requests.post(url, data=data, headers=headers)
                results = r.json()
                print(results)
            except:
                e=''
            break
        
        url = "http://asmon.com.ar:8081/snap/dev_cam01"
        headers = {'X-AIO-Key': 'xxxxxxxxxxxxxxxxxxx',
                    'Content-Type': 'image/jpeg'}
        while True:
            try:
                data = next(pic)
                r = requests.post(url, data=data, headers=headers)
                results = r.json()
            except:
                e=''
            break
    sleep(.1)
    
    
def sp():
    th(plus,('st',))
def sn():
    th(snap,('st',))
def ud():
    th(ur,('st',))
def sc():
    host, port = ['asmon.com.ar','8080'] #server_list[0].split(':')
    address = socket.getaddrinfo(host, port)[0][-1]
    th(start_com,(address,))
    
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
    #asmon_sys.start()