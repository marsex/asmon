import gc
import esp
import camera
import _thread 
import usocket as socket
import json
import time
from time import sleep
from machine import Pin
from structure import wifi, machine_data, asmon_sys, sock_state, color
import uerrno  
th = _thread.start_new_thread

sset = sock_state.set
sget = sock_state.get

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
            time.sleep(0.1)  # try as fast as we can
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

    
def create_html():
    print('\n\nget_networks')
    scan_list = wifi.get_networks()

    tr_swap = ""
    tr_format = """
    <tr>
        <td onclick="set_ssid(this)">$ssid</td>
        <td class=$signal_state style="width:120px">$signal_state</td>
    </tr>
    """
    if len(scan_list) != 0:
        for wifi_net in scan_list:
            net_signal = int(str(wifi_net[3]).replace('-', ''))
            net_ssid = str(wifi_net[0]).replace("b'", '')
            net_ssid = net_ssid.replace("'", '')
            signal_state = ''
            if net_signal <= 66:
                signal_state = "Excelente"

            if net_signal >= 67:
                signal_state = "Buena"

            if net_signal >= 80:
                signal_state = "Mala"

            tr_done = tr_format.replace('$ssid', net_ssid).replace('$signal_state', signal_state)
            tr_swap = tr_swap + tr_done

    credentials_state, cred_ssid, cred_psw = wifi.get_credentials()
    print(tr_swap)
    gc.collect()
    file = open('/structure/index.html', 'r')
    chtml = file.read()
    chtml = chtml.replace('$tr_swap', tr_swap).replace('$cred_ssid', cred_ssid).replace('$cred_psw', cred_psw)
    file.close()
    return chtml

    
def port1(cs, req):
    req = req[1].split('/')
    if req[1] == 'apikey':  # Must have /apikey/<REQ>
        if req[2] == 'live':  # start streaming
            cs.send(b'%s' % hdr['stream'])
            # start frame sending
            send_frame([cs, hdr['frame']])
        else:
            cs.send(b'%s' % hdr['none'])
            clean_up(cs)
    else:
        cs.send(b'%s' % hdr['err'])
        clean_up(cs)


def port2(cs, req):
    req = req[1].split('/')
    if req[1] == 'apikey':  # Must have /apikey/<REQ>
        if req[2] == 'snap':
            try:
                img = next(pic)
                cs.send(b'%s %d\r\n\r\n' % (hdr['snap'], len(img)))
                cs.send(img)
                cs.send(b'\r\n')
            except:
                pass
        elif req[2] == 'blitz':
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


def port3(cs, req):
    req = req[1].split('/')
    if req[1] == 'apikey':  # Must have /apikey/<REQ>
        if req[2] == 'flash':  # /apikey/flash/<what>
            if req[3] == 'on':
                flash_light.on()
            else:
                flash_light.off()
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'fmt':
            w = int(req[3])
            if w >= 0 and w <= 2:
                camera.pixformat(w)
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'pix':
            w = int(req[3])
            if w > 0 and w < 13:
                camera.framesize(w)
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'qua':
            w = int(req[3])
            if w > 9 and w < 64:
                camera.quality(w)
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'con':
            w = int(req[3])
            if w > -3 and w < 3:
                camera.contrast(w)
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'sat':
            w = int(req[3])
            if w > -3 and w < 3:
                camera.saturation(w)
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'bri':
            w = int(req[3])
            if w > -3 and w < 3:
                camera.brightness(w)
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'ael':
            w = int(req[3])
            if w > -3 and w < 3:
                camera.aelevels(w)
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'aev':
            w = int(req[3])
            if w >= 0 and w <= 1200:
                camera.aecvalue(w)
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'agc':
            w = int(req[3])
            if w >= 0 and w <= 30:
                camera.agcgain(w)
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'spe':
            w = int(req[3])
            if w >= 0 and w < 7:
                camera.speffect(w)
            cs.send(b'%s' % hdr['OK'])
        elif req[2] == 'wbl':
            w = int(req[3])
            if w >= 0 and w < 5:
                camera.whitebalance(w)
            cs.send(b'%s' % hdr['OK'])
        else:
            cs.send(b'%s' % hdr['none'])
    else:
        cs.send(b'%s' % hdr['err'])
    clean_up(cs)


def port4(client, req):
    req = req[1].split('/')
    print('port1 req:', req)
    if req[1] == 'app':  # Must have /apikey/<REQ>
        index_page = create_html()
        html=hdr['html'].replace('$html',index_page)
        client.send(b'%s' % html)
        sleep(.25)
    elif req[1] == 'logo.png':
        client.send(logo_img)
        sleep(.25)
    elif req[1] == ('gpio'):
        pin, value = req[2], req[3]
        
        command_json = {'command': 'output_state', 'data': pin+'='+value}
        machine_data.parse_data(command_json)

        esp_data = machine_data.get()
        gpio_output = esp_data['gpio']['output_state']
        
        json_response = json.dumps({'command':'output_state','output_state': gpio_output})
        json_header = hdr['json'].replace('$len',str(len(json_response)))
        
        client.send(b'%s' % json_header)
        client.sendall(json_response.encode())
        sleep(.25)
    else:
        client.send(b'%s' % hdr['err'])
    clean_up(client)
    

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
            sset('cam','connecting')
            s.connect(("asmon.com.ar" , 8081))
        #    s.sendall(b"GET /connect/espcam/hola HTTP/1.1\r\nHost: feelfree.softether.net\r\nAccept: application/json\r\n\r\n")
            
            sset('cam','connected')
            img = next(pic)
            
            sset('cam','sending_img')
            s.send(b'%s %d\r\n\r\n' % (hdr['POST'], len(img)))
            s.send(img)
            s.send(b'\r\n')
            sset('cam','img_sent')
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



def start_cam(address):
    json_data = machine_data.create()
    while True:
        client_socket = socket.socket()
        client_socket.setblocking(False)

        try:    
            client_socket.connect(address)
        except OSError as error:
          if error.args[0] not in [uerrno.EINPROGRESS, uerrno.ETIMEDOUT]:
            print(color.red()+'**** Error connecting ****', error+color.normal())
        
        try:
            POST(client_socket, 'snap/dev_cam01', 'img',next(pic)) 
            sleep(0.2)        
            while True:
                res = str(client_socket.recv(2000))
                command = str(res)[str(res).find('\\r\\n\\r\\n')+len('\\r\\n\\r\\n'):len(str(res))-1]
                json_command = ujson.loads(command)
                print(json_command)
                break    
        except OSError as error:
            if error.args[0] not in [uerrno.EINPROGRESS, uerrno.ETIMEDOUT]:
                print(color.red()+'\t\t\t**** ERROR writing ****\n\t\t\t', error+color.normal())
                attempts = 0

        client_socket.close()  # flash buffer and close socket
        del client_socket
        gc.collect()
        sleep(.1)


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


# ------------------


# """,
    # 'POST': """POST /snap HTTP/1.1
# Host: 127.0.0.1:9515
# Content-Type: image/jpeg
# Content-Length: """
# }

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

h={
'POST': """POST /$req HTTP/1.1
Host: 127.0.0.1:9515
Content-Type: $type
Content-Length: """
}

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
    machine_data.create()
    file = open('/structure/logo.png','r')
    logo_img = file.read()
    file.close()
    
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