import gc
import esp
import camera
import _thread
import usocket as soc
import json
import time
from time import sleep
from machine import Pin
from structure import wifi, machine_data

th = _thread.start_new_thread
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
Cache-Control: no-cache, no-store, max-age=0, must-revali date
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
    'himg': """HTTP/1.1 200 OK
Content-Type: image/jpeg
Content-Length: 
""",
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

Hello?

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

"""
}

def sockets():
    socks = []
    # port 80 server - app server
    s = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
    s.setsockopt(soc.SOL_SOCKET, soc.SO_REUSEADDR, 1)
    a = ('0.0.0.0', 80)
    s.bind(a)
    s.listen(2)  # queue at most 2 clients
    socks.append(s)

    # port 81 server - still picture server
    s = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
    s.setsockopt(soc.SOL_SOCKET, soc.SO_REUSEADDR, 1)
    a = ('0.0.0.0', 81)
    s.bind(a)
    s.listen(2)
    socks.append(s)

    return socks


def port1(client, req):
    print('port1 req:', req)
    req = req.split('/')
    if req[1] == 'app':  # Must have /apikey/<REQ>
        index_page = create_html()
        html=hdr['html'].replace('$html',index_page)
        client.send(b'%s' % html)
        sleep(.1)
        clean_up(client)
    elif req[1] == 'logo.png':
        client.send(logo_img)
        sleep(.1)
        clean_up(client)
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
        clean_up(client)
    else:
        client.send(b'%s' % hdr['err'])
        clean_up(client)

def port2(client, req):
    print('port2 req:', req)
    req = req.split('/')
    print('port2 req1:', req[1])
    print('port2 req2:', req[2])
    if req[1] == 'apikey':  # Must have /apikey/<REQ>
        if req[2] == 'live':  # start streaming
            print(b'%s' % hdr['stream'])
            client.send(b'%s' % hdr['stream'])
            print('start frame sending')
            send_frame([client, hdr['frame']])
        else:
            client.send(b'%s' % hdr['none'])
            clean_up(client)
    else:
        client.send(b'%s' % hdr['err'])
        clean_up(client)


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
            print('send_frame')
            print(b'%s' % h)
            cs.send(b'%s' % h)
            print('sent frame header')
            cs.send(next(pic))
            print('sent pic')
            cs.send(b'\r\n')  # send and flush the send buffer
            print('sent flush')
        except Exception as e:
            ee = str(e)
            print(ee)
        if ee == '':
            time.sleep(0.005)  # try as fast as we can
        else:
            break

    clean_up(cs)
    return


def clean_up(client):
    print(client)
    client.close()  # flash buffer and close socket
    del client
    gc.collect()

def srv(p):
    socket = socks[p]  # start server; catch error - loop forever
    while True:
        try:
            ok = True
            error = ''
            try:
                # in sec NB! default browser timeout (5-15 min)
                socket.settimeout(0.05)
                client, client_address = socket.accept()
                client.settimeout(0.5)  # in sec
            except Exception as e:
                error = str(e)

            if error != '':
                pass
                ok = False

            if ok:  # No soc.accept timeout
                error = ''
                try:
                    # client accepted
                    client_data = client.recv(1024)
                    # REQ: b''  # may be due to very short timeout
                except Exception as e:
                    error = str(e)

                if error != '':
                    print(error)
                    ok = False
                else:
                    client_data = client_data.decode('utf-8')
                    if client_data.find('favicon.ico') < 0:
                        req = client_data.split(' ')
                        try:
                            print(req[0], req[1], client_address)
                        except:
                            ok = False
                    else:
                        # handle favicon request early
                        client.send(b'%s' % hdr['favicon'])
                        clean_up(client)
                        ok = False

            if ok:  # No soc.recv timeout or favicon request
                try:
                    ports[p](client, req[1])
                except Exception as e:
                    error = str(e)
                    if error != '':
                        print(error)
        except Exception as e:
            error = str(e)
            if error != '':
                print(error)
    print('error????')
    
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


# setup networking
wc = 0
while True:
    cr = camera.init(0, format=camera.JPEG) 
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
    file = open('/structure/logo.png','r')
    logo_img = file.read()
    file.close()

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
    ports = [port1, port2]  # 80, 81, 82
    th(srv, (0,))
    print(green+'server started'+normal)
