import network
import socket
import time
import dht
import ujson
import json
import machine
from machine import Timer, Pin
import uasyncio as asyncio
from time import sleep
import uerrno
from structure import machine_data, color, cam, wifi
import gc

cam.start()
wifi.connect('1255','12551255')
data_host = "asmon.com.ar"
USER = "espcam"
data_address = ''
cam_address = ''
pic = cam.frame_gen()

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
    sleep(1)
    pass
    
while cam_address == '':
    try:
        cam_address = socket.getaddrinfo(data_host, 8081)[0][-1]
    except:
        cam_address = ''
        print('Error getting cam addr info')
    sleep(1)
    pass

def tst():
    s = st_s() #creates socket
    cs(s)
    
async def stc(delay):
    while True:
        s = st_s()
        cs(s)
        await asyncio.sleep(.1)

def st_s(): #creates socket
    s = socket.socket()
    s.setblocking(False)
    return s

def cs(s): #connects using socket
    connected = False
    print('try to connect')
    
    while connected == False:
        try:
            #print('connecting')
            s.connect(data_address)
        except OSError as e:
            print(e)
            if str(e) == "127":
                connected = True
            elif str(e) == "120":
                connected = True
        pass

    print(color.green()+'connected'+color.normal())
    while True:
        if sd(s):
            print('data sent')
            while True:
                if rd(s):
                    break
            break
    s.close()
    print(color.red()+'disconnected'+color.normal())
    del s
    gc.collect()
    
def tstc():
    s = st_s()
    ccs(s)
    
    
def ccs(s):    
    #connect cam server
    connected = False
    print('try to connect')
    
    while connected == False:
        try:
            #print('connecting')
            s.connect(cam_address)
        except OSError as e:
            print(e)
            if str(e) == "127":
                connected = True
            elif str(e) == "120":
                connected = True
        pass
    print(color.green()+'connected'+color.normal())
    
    img = next(pic)
    while True:
        if sc(s,img):
            print('img sent')
            while True:
                if rd(s):
                    break
            break

def sc(s,img):
    try:
        print('sending data to server')
        POST(s, 'snap/dev_cam01', 'img',img) 
        return True
    except OSError as e:
        print('Error sending data', e)
        return False
        
def sd(s):
    try:
        #print('sending data to server')
        POST(s, 'esp_data/dev_cam01', 'json',{"uptime": str(time.time())}) 
        return True
    except OSError as e:
        #print('Error sending data', e)
        return False
    
def rd(s):
    try:
        #print('getting data from server')
        server_data = s.recv(1024)
        print(server_data)
        return True
    except OSError as e:
        #print('Error receiving data', e)
        return False


async def comv2(asd):
    print(color.green()+'SENDING ESP DATA'+color.normal())
    await asyncio.sleep(1)
    while True:
        s = socket.socket()
        s.setblocking(False)
        connected = False
        while connected == False:
            try:
                #print('connecting')
                s.connect(data_address)
            except OSError as e:
                #print(e)
                if str(e) == "127":
                    connected = True
            pass
        try:
            POST(s, 'esp_data/dev_cam01', 'json',machine_data.get())
            server_data = s.recv(1024)
            print(server_data)
        except:
            print('failed')

        s.close()
        del s
        gc.collect()
        await asyncio.sleep(.2)
    
def start():
    main_loop = asyncio.get_event_loop()  
    main_loop.create_task(camv2(.1))
    main_loop.create_task(comv2(.1))
    main_loop.run_forever()
    print("done")   
        
async def camv2(asd):
    print(color.blue()+'SENDING CAM'+color.normal())
    await asyncio.sleep(1)
    while True:
        connected = False
        #print('try to connect')
        s = socket.socket()
        s.setblocking(False)
        while connected == False:
            try:
                #print('connecting')
                s.connect(cam_address)
            except OSError as e:
                #print(e)
                if str(e) == "127":
                    connected = True
            pass
        img = next(pic)
        try:
            POST(s, 'snap/dev_cam01', 'img',img)
        except:
            print('failed')
        s.close()
        print(color.red()+'cam out'+color.normal())
        del s
        gc.collect()
        await asyncio.sleep(.2)
    
    
def POST(s, req, type, data):
    size = 0
    if type == 'json':
        type = 'application/json'
        data = json.dumps(data)
        size = len(data)
        data = data.encode()
    elif type == 'img':
        type = 'image/jpeg'
        size = len(data)
        
    header = h['POST'].replace('$req',req).replace('$type',type)
    s.send(b'%s %d\r\n\r\n' % (header, size))
    while data:
        sent = s.send(data)
        data = data[sent:]
        sleep(.1)

