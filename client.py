import gc
import esp
import camera
import _thread
import socket
import json
from time import sleep
from machine import Pin
from structure import wifi, machine_data

th = _thread.start_new_thread
esp.osdebug(None)

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


def port1(client, req):
    print('port1 req:', req)
    req = req.split('/')
    if req[1] == 'app':  # Must have /apikey/<REQ>
        index_page = create_html()
        html=hdr['html'].replace('$html',index_page)
        client.send(b'%s' % html)
        sleep(.1)
    elif req[1] == 'logo.png':
        client.send(logo_img)
        sleep(.1)
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
    else:
        client.send(b'%s' % hdr['err'])
    clean_up(client)

def clean_up(client):
    client.close()  # flash buffer and close socket
    del client
    gc.collect()

def sockets():
    socks = []
    # client port server - app server
    s = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
    s.setsockopt(soc.SOL_SOCKET, soc.SO_REUSEADDR, 1)
    socks.append(s)
    return socks

def cli(p):     
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("feelfree.softether.net" , 8080))
    s.sendall(b"GET /connect/espcam/hola HTTP/1.1\r\nHost: feelfree.softether.net\r\nAccept: application/json\r\n\r\n")
    result = s.recv(10000)
    while (len(result) > 0):
        print(result)
        result = s.recv(10000)

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

th(cli, (0,))
print(green+'server started'+normal)
