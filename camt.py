import gc
import esp
import camera
import _thread 
import usocket as socket
import json
import time
from time import sleep
from machine import Pin
from structure import wifi, machine_data, asmon_sys, color
import uerrno  
th = _thread.start_new_thread

# esp.osdebug(False)
esp.osdebug(True)

red = ("\033[1;31;40m")
green = ("\033[1;32;40m")
yellow = ("\033[1;33;40m")
blue = ("\033[1;34;40m")
normal = ("\033[0;37;40m")

hdr = {
    # start page for streaming
    # URL: /app
    'html': """HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

$html
""",
    # live stream -
    # URL: /apikey/live
    'stream': """HTTP/1.1 200 OK
Content-Type: multipart/x-mixed-replace; boundary=frame
Connection: keep-alive
Cache-Control: no-cache, no-store, max-age=0, must-revalidate
Expires: Thu, Jan 01 1970 00:00:00 GMT
Pragma: no-cache

""",
    # live stream -
    # URL:
    'frame': """--frame
Content-Type: image/jpeg

""",
    # still picture -
    # URL: /apikey/snap
    'snap': """HTTP/1.1 200 OK
Content-Type: image/jpeg
Content-Length: """,
    # no content error
    # URL: all the rest
    'none': """HTTP/1.1 204 No Content
Content-Type: text/plain; charset=utf-8

Nothing here!

""",
    # bad request error
    # URL: /favicon.ico
    'favicon': """HTTP/1.1 404 


""",
    # bad request error
    # URL: all the rest
    'err': """HTTP/1.1 400 Bad Request
Content-Type: text/plain; charset=utf-8

Hello? Can not compile

""",
    # OK
    # URL: all the rest
    'OK': """HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8

OK!

""",
    'json': """HTTP/1.1 200 OK
Access-Control-Allow-Origin: *
Content-Type: application/json
Content-Length: $len
Connection: close

""",
    'POST': """POST /snap/dev_cam01 HTTP/1.1
Host: 127.0.0.1:9515
X-AIO-Key: xxxxxxxxxxxxxxxxxxx
Content-Type: image/jpeg
Content-Length: """
}


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

def cli(fs,q,d):     
    camera.framesize(fs)
    camera.quality(q)
    while True:         
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
                print('\ngot result')
                break
        except Exception as e:
            ee = str(e)
            if ee != '':
                print('cam error: '+ ee)
        s.close()  # flash buffer and close socket
        del s
        gc.collect()
        time.sleep(d)

def tt():
    connected = False
    print('try to connect')
    s = socket.socket()
    while connected == False:
        try:
            #print('connecting')
            s.connect(("asmon.com.ar" , 8081))
        except OSError as e:
            print(e)
            if str(e) == "127":
                connected = True
        pass
    img = next(pic)
    s.send(b'%s %d\r\n\r\n' % (hdr['POST'], len(img)))
    s.send(img)
    s.send(b'\r\n')
    return s
    
def tt2(d):
    while True:
        connected = False
        print('try to connect')
        s = socket.socket()
        s.setblocking(False)
        while connected == False:
            try:
                #print('connecting')
                s.connect(("asmon.com.ar" , 8081))
            except OSError as e:
                print(e)
                if str(e) == "127":
                    connected = True
            pass
        img = next(pic)
        sp2(s,img,d)
        s.close()  # flash buffer and close socket
        del s
        gc.collect()
        sleep(.1)
        
def ctt():
    connected = False
    print('try to connect')
    s = socket.socket()
    s.setblocking(False)
    while connected == False:
        try:
            #print('connecting')
            s.connect(("asmon.com.ar" , 8081))
        except OSError as e:
            print(e)
            if str(e) == "127":
                connected = True
        pass
    return s

def sh(s,img):
    s.send(b'%s %d\r\n\r\n' % (hdr['POST'], len(img)))
    
def sp2(s,img,d):
    try:
        s.send(b'%s %d\r\n\r\n' % (hdr['POST'], len(img)))
        while img:
            sent = s.send(img)
            img = img[sent:]
            sleep(d)
        print('done')
    except:
        print('failed')


def sp(s, img,d):
    try:
        sent=s.send(img)
        while True:
            if sent != 0:
                print(sent)
                break
        img = img[sent:]
        sleep(d)
        sent=s.send(img)
        while True:
            if sent != 0:
                print(sent)
                break
        img = img[sent:]
        sleep(d)
        sent=s.send(img)
        while True:
            if sent != 0:
                print(sent)
                break
        print('done')
    except:
        print('failed')
    
wc = 0
while True:
    cr = camera.init()
    print("Camera ready?: ", cr)
    if cr:
        break
    time.sleep(2)
    wc += 1
    if wc >= 5:
        break

if not cr:
    print("Camera not ready. Can't continue!")
else:
    camera.framesize(7)
    camera.quality(10)
    wifi.connect('1255','12551255')
    print(green+'Connection successful\n'+normal)
    
    sleep(2)
    
    pic = frame_gen()
    flash_light = Pin(04, Pin.OUT)
    #socks = sockets()
    #ports = [port1, port2, port3, port4, port4]  # 81, 82, 83, 80
    
    # th(srv, (3,))
    # th(srv, (2,))
    # th(srv, (3,))
    # th(srv, (2,))

    
    #
    # schedule other processes here
    #

    # go for it!
    print("Up Up and Away!")
    #sleep(2)
    #asmon_sys.start()
    # let the main thread take care of port 82 - block REPL