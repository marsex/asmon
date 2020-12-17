from structure import cam
cam.start()
from structure import machine_data, color, cam, wifi
import network
import socket
import time
import json
import uasyncio as asyncio
from time import sleep
import uerrno
import gc
import _thread
th = _thread.start_new_thread


wifi.connect('1255','12551255')

data_host = "asmon.com.ar"
USER = "espcam"
data_address = ''
cam_address = ''
json_command={}

h={
'POST': """POST /$req HTTP/1.1
Host: 127.0.0.1:9515
X-AIO-Key: xxxxxxxxxxxxxxxxxxx
Content-Type: $type
Content-Length: """
}

while data_address == '':
    try:
        data_address = socket.getaddrinfo(data_host, 8080)[0][-1]
    except:
        data_address = ''
        print('Error getting data addr info')
    sleep(.1)
    pass
    
while cam_address == '':
    try:
        cam_address = socket.getaddrinfo(data_host, 8081)[0][-1]
    except:
        cam_address = ''
        print('Error getting cam addr info')
    sleep(.1)
    pass

def start(to):
    try:
        main_loop = asyncio.get_event_loop()  
        main_loop.create_task(camv2(to))
        main_loop.create_task(comv2(to))
        main_loop.run_forever()
    except OSError as e:
        print("async failed"+str(e)) 
    print("async out")   
    gc.collect()
    gc.mem_free()
    start(to)
 
async def comv2(to):
    global json_command
    print(color.green()+'SENDING ESP DATA'+color.normal())
    await asyncio.sleep(1)
    conn_try=0
    while True:
        try:
            s = socket.socket()
            s.setblocking(False)
            connected = False
            while connected == False:
                try:
                    #print('connecting')
                    s.connect(data_address)
                except OSError as e:
                    #print(conn_try)
                    if str(e) == "127":
                        connected = True
                        conn_try = 0
                    else:
                        conn_try = conn_try+1
                        if conn_try > to:
                            print(color.red()+'DATA CONN F'+color.normal())
                            break
                await asyncio.sleep(.05)
                pass
            if conn_try != to:
                print(color.green()+'{\n\tconnected to data_address'+color.normal())
                conn_try = 0
                try:
                    #POST(s, 'esp_data/dev_cam01', 'json',{'uptime':9999,"out_s":[1,0,0,0,0,0,0,1],"in_s":[1,0,0,0,0,0,0,1]})
                    print('\tsending esp_data')
                    #POST(s, 'esp_data/dev_cam01', 'json',machine_data.get())
                    while True:
                        try:
                            type = 'application/json'
                            data = json.dumps(machine_data.get())
                            size = len(data)
                            data = data.encode()
                            req = 'esp_data/dev_cam01'
                            header = h['POST'].replace('$req',req).replace('$type',type)
                            s.send(b'%s %d\r\n\r\n' % (header, size))
                            while data:
                                sent = s.send(data)
                                data = data[sent:]
                                await asyncio.sleep(.5)
                            conn_try = 0
                            break
                        except OSError as e:
                            print(e)
                            if conn_try > to:
                                print(color.red()+'DATA SEND F'+color.normal())
                                break
                            conn_try = conn_try+1
                            
                    if conn_try != to:
                        while True:
                            try:
                                print('\treceiving server data')
                                res = str(s.recv(1024))
                                await asyncio.sleep(.2)
                                if res.find('200 OK') != -1:
                                    print('\tserver data received')
                                    try:
                                        command = str(res)[str(res).find('\\r\\n\\r\\n')+len('\\r\\n\\r\\n'):len(str(res))-1]
                                        new_json_command = json.loads(command)
                            #            if json_command != new_json_command:
                            #                json_command = new_json_command    
                                        print(color.green()+str(new_json_command)+color.normal())
                                        #print('\nright recv',res)
                                        break
                                    except OSError as e:
                                        print('wrong recv '+res+str(e))
                                        break
                            except OSError as e:
                                if conn_try > to:
                                    print(color.red()+'DATA RECV F'+color.normal())
                                    break
                                conn_try = conn_try + 1
                                #print('error receiving '+str(e))
                            await asyncio.sleep(.2)
                    s.close()
                except OSError as e:
                    print('data com failed '+ str(e))
            print(color.red()+'\tesp_data out\n}\n'+color.normal())
            s.close()
            del s
        except OSError as e:
            print('data socket failed',str(e))
        gc.collect()
        conn_try = 0
        await asyncio.sleep(.1)

async def camv2(to):
    print(color.blue()+'SENDING CAM'+color.normal())
    await asyncio.sleep(1)
    conn_try=0
    while True:
        connected = False
        #print('try to connect')
        try:
            s = socket.socket()
            s.setblocking(False)
            while connected == False:
                try:
                    s.connect(cam_address)
                except OSError as e:
                    #print(conn_try)
                    if str(e) == "127":
                        connected = True
                        conn_try = 0
                    else:
                        conn_try = conn_try+1
                        if conn_try > to:
                            print(color.red()+'CAM CONN F'+color.normal())
                            break
                await asyncio.sleep(.05)
                pass
            if conn_try != to:
                print(color.green()+'{\n\tconnected to cam_address'+color.normal())
                try:
                    n_try = 0
                    buf = False
                    while (n_try < 10 and buf == False): #{
                        # wait for sensor to start and focus before capturing image
                        print('\tgetting img')
                        buf = camera.capture()
                        if (buf == False): await asyncio.sleep(2)
                        n_try = n_try + 1
                    print('\tsending img')
                    while True:
                        try:
                            type = 'image/jpeg'
                            size = len(buf)
                            req = 'snap/dev_cam01'
                            header = h['POST'].replace('$req',req).replace('$type',type)
                            s.send(b'%s %d\r\n\r\n' % (header, size))
                            while buf:
                                sent = s.send(buf)
                                buf = buf[sent:]
                                await asyncio.sleep(.5)
                            break
                        except OSError as e:
                            print(e)
                            if conn_try > to:
                                print(color.red()+'CAM SEND F'+color.normal())
                                break
                            conn_try = conn_try+1
                    #POST(s, 'snap/dev_cam01', 'img',buf)
                    print('\timg sent')
                except OSError as e:
                    print('\tsending cam failed '+str(e))
            s.close()
            print(color.red()+'\tcam out\n}\n'+color.normal())
            del s
        except OSError as e:
            print('cam socket failed',str(e))
        gc.collect()
        conn_try = 0
        await asyncio.sleep(.1)