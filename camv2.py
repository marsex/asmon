import camera
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


def start(to,to2):
    global cam_address
        
    while cam_address == '':
        try:
            cam_address = socket.getaddrinfo(data_host, 8081)[0][-1]
        except:
            cam_address = ''
            print('Error getting cam addr info')
        sleep(.1)
        pass
        
    try:
        main_loop = asyncio.new_event_loop()  
        main_loop.create_task(cam(to,to2))
        main_loop.run_forever()
    except OSError as e:
        print("async failed"+str(e)) 
    print("async out")   
    gc.collect()
    gc.mem_free()

async def cam(to,to2):
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
                    buf = camera.capture()
                    while True:
                        try:
                            type = 'image/jpeg'
                            size = len(buf)
                            req = 'snap/dev_cam01'
                            header = h['POST'].replace('$req',req).replace('$type',type)
                            s.send(b'%s %d\r\n\r\n' % (header, size))
                            print('img size',size)
                            while buf:
                                sent = s.send(buf)
                                buf = buf[sent:]
                                await asyncio.sleep(to2)
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