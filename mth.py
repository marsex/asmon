import usocket as socket
import _thread as th
import camera
import time
from time import sleep
import esp
from machine import Pin
import gc
from structure import wifi

# esp.osdebug(False)
esp.osdebug(True)

red = ("\033[1;31;40m")
green = ("\033[1;32;40m")
yellow = ("\033[1;33;40m")
blue = ("\033[1;34;40m")
normal = ("\033[0;37;40m")

hdr = {
    # start page for streaming
    # URL: /apikey/webcam
    'live': """HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

<html>
<head>
<title>Web Camera</title>
</head>
<body>
  <center>
    <h1>Web Camera</h1>
    <img src="/apikey/live" width=720 height=540 />
  </center>
</body>
</html>

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

"""
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


def send_frame(pp):
    cs, h = pp
    while True:
        ee = ''
        try:
            cs.send(b'%s' % h)
            cs.send(next(pic))
            cs.send(b'\r\n')  # send and flush the send buffer
        except Exception as e:
            ee = str(e)
        if ee == '':
            time.sleep(0.005)  # try as fast as we can
        else:
            break

    clean_up(cs)
    return


def sockets():
    socks = []
    # port 81 server - streaming server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    a = ('0.0.0.0', 81)
    s.bind(a)
    s.listen(2)  # queue at most 2 clients
    socks.append(s)

    # port 81 server - still picture server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    a = ('0.0.0.0', 82)
    s.bind(a)
    s.listen(2)
    socks.append(s)

    # port 82 server - cmd server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    a = ('0.0.0.0', 83)
    s.bind(a)
    s.listen(2)
    socks.append(s)
    
    # port 80 server - streaming server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    a = ('0.0.0.0', 80)
    s.bind(a)
    s.listen(2)  # queue at most 2 clients
    socks.append(s)

    return socks


def port1(cs, rq):
    rqp = rq[1].split('/')
    if rqp[1] == 'apikey':  # Must have /apikey/<REQ>
        if rqp[2] == 'webcam':
            cs.send(b'%s' % hdr['live'])
            clean_up(cs)
        elif rqp[2] == 'live':  # start streaming
            cs.send(b'%s' % hdr['stream'])
            # start frame sending
            send_frame([cs, hdr['frame']])
        else:
            cs.send(b'%s' % hdr['none'])
            clean_up(cs)
    else:
        cs.send(b'%s' % hdr['err'])
        clean_up(cs)


def port2(cs, rq):
    rqp = rq[1].split('/')
    if rqp[1] == 'apikey':  # Must have /apikey/<REQ>
        if rqp[2] == 'snap':
            try:
                img = next(pic)
                cs.send(b'%s %d\r\n\r\n' % (hdr['snap'], len(img)))
                cs.send(img)
                cs.send(b'\r\n')
            except:
                pass
        elif rqp[2] == 'blitz':
            try:
                flash_light.on()
                img = next(pic)
                flash_light.off()
                cs.send(b'%s %d\r\n\r\n' % (hdr['snap'], len(img)))
                cs.send(img)
                cs.send(b'\r\n')
            except:
                pass
        else:
            cs.send(b'%s' % hdr['none'])
    else:
        cs.send(b'%s' % hdr['err'])
    clean_up(cs)


def port3(cs, rq):
    rqp = rq[1].split('/')
    if rqp[1] == 'apikey':  # Must have /apikey/<REQ>
        if rqp[2] == 'flash':  # /apikey/flash/<what>
            if rqp[3] == 'on':
                flash_light.on()
            else:
                flash_light.off()
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'fmt':
            w = int(rqp[3])
            if w >= 0 and w <= 2:
                camera.pixformat(w)
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'pix':
            w = int(rqp[3])
            if w > 0 and w < 13:
                camera.framesize(w)
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'qua':
            w = int(rqp[3])
            if w > 9 and w < 64:
                camera.quality(w)
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'con':
            w = int(rqp[3])
            if w > -3 and w < 3:
                camera.contrast(w)
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'sat':
            w = int(rqp[3])
            if w > -3 and w < 3:
                camera.saturation(w)
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'bri':
            w = int(rqp[3])
            if w > -3 and w < 3:
                camera.brightness(w)
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'ael':
            w = int(rqp[3])
            if w > -3 and w < 3:
                camera.aelevels(w)
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'aev':
            w = int(rqp[3])
            if w >= 0 and w <= 1200:
                camera.aecvalue(w)
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'agc':
            w = int(rqp[3])
            if w >= 0 and w <= 30:
                camera.agcgain(w)
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'spe':
            w = int(rqp[3])
            if w >= 0 and w < 7:
                camera.speffect(w)
            cs.send(b'%s' % hdr['OK'])
        elif rqp[2] == 'wbl':
            w = int(rqp[3])
            if w >= 0 and w < 5:
                camera.whitebalance(w)
            cs.send(b'%s' % hdr['OK'])
        else:
            cs.send(b'%s' % hdr['none'])
    else:
        cs.send(b'%s' % hdr['err'])
    clean_up(cs)


def srv(p):
    sa = socks[p]  # start server; catch error - loop forever
    while True:
        try:
            ok = True
            ee = ''
            try:
                # in sec NB! default browser timeout (5-15 min)
                sa.settimeout(0.05)
                cs, ca = sa.accept()
                cs.settimeout(0.5)  # in sec
            except Exception as e:
                ee = str(e)
            if ee != '':
                # print('Socket %d accept - %s' % (p, ee.split()[-1]))
                #ee = ''
                pass
                ok = False
            if ok:  # No socket.accept timeout
                ee = ''
                try:
                    # client accepted
                    r = cs.recv(1024)
                    # REQ: b''  # may be due to very short timeout
                except Exception as e:
                    ee = str(e)
                if ee != '':
                    print(ee)
                    ok = False
                else:
                    ms = r.decode('utf-8')
                    if ms.find('favicon.ico') < 0:
                        rq = ms.split(' ')
                        try:
                            print(rq[0], rq[1], ca)
                        except:
                            ok = False
                    else:
                        # handle favicon request early
                        cs.send(b'%s' % hdr['favicon'])
                        clean_up(cs)
                        ok = False
            if ok:  # No socket.recv timeout or favicon request
                try:
                    ports[p](cs, rq)
                except Exception as e:
                    ee = str(e)
                    if ee != '':
                        print(ee)
        except Exception as e:
            ee = str(e)
            if ee != '':
                print(ee)


# ------------------
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
    pic = frame_gen()
    flash_light = Pin(04, Pin.OUT)
    socks = sockets()
    ports = [port1, port2, port3]  # 80, 81, 82

    # schedule 2 servers for port 80
    # streaming hold socket until client terminate,
    # so, we service at most 2 clients on port 80
    th.start_new_thread(srv, (0,))
    th.start_new_thread(srv, (0,))

    # schedule 1 server for port 81
    th.start_new_thread(srv, (1,))

    #
    # schedule other processes here
    #

    # go for it!
    print("Up Up and Away!")

    # let the main thread take care of port 82 - block REPL
    srv(2)
