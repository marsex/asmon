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

inp_gpio = [13, 15]
out_gpio = [2, 14, 12]

hostname = "asmon.com.ar"
USER = "espcam"
ap_wlan = None
st_wlan = None
ap_socket = None


def start():
    global ble_status
    ble_status = "disconnected"
    address = ''

    # ble_loop = asyncio.get_event_loop()
    # ble_loop.create_task(ble_start(ble_status))
    # ble_loop.run_until_complete(killer())
    while address == '':
        try:
            address = socket.getaddrinfo(hostname, 1259)[0][-1]
        except:
            address = ''
            print('Error getting addr info from')
        sleep(1)
        pass
        
    print('got address')
    
    main_loop = asyncio.get_event_loop()  
    main_loop.create_task(com(address))
    main_loop.create_task(check_dht())
    main_loop.run_forever()
    print("done")
  
  
async def killer():
    print("killer")
    
async def ble_start(ble_st):
    while True:
        if ble_st == "disconnected":
            from structure import ble_basic
            ble_st="connected"
            print("start ble")
            ble_basic.advertise()
        await asyncio.sleep(1)
  

async def com(address):
  while True:
    input_state = [machine.Pin(i, machine.Pin.IN).value() for i in inp_gpio]
    output_state = [machine.Pin(i, machine.Pin.OUT).value() for i in out_gpio]
    machine_data['dht1']['tmp']=1#dht1.temperature()
    machine_data['dht1']['hmd']=2#dht1.humidity()
    machine_data['dht2']['tmp']=3#9dht2.temperature()
    machine_data['dht2']['hmd']=4#dht2.humidity()
    machine_data['uptime']=str(time.time())
    machine_data['gpio']['input_state']=input_state
    machine_data['gpio']['output_state']=output_state
    
    ip, port = str(address[0]), str(address[1])
    st_socket = socket.socket()
    st_socket.setblocking(False)

    # print('try to connect')
    try:
      # print('connecting')
      st_socket.connect(address)
    except OSError as e:
      if e.args[0] not in [uerrno.EINPROGRESS, uerrno.ETIMEDOUT]:
        print('Error connecting', e)
    attempts = 2
    while attempts:
      attempts=attempts-1
      # print('try to send data: ', attempts)
      try:
        # print('sending data')
        st_socket.sendall(bytes(str(machine_data), 'UTF-8')) # MQTT ping
        await asyncio.sleep(0.2)
        # print('data sent')
        while True:
          buffer_data = st_socket.recv(2000)
          host_data = str(buffer_data)
          if host_data.find('null') == -1:
            parse_data(host_data)
          attempts = 0
          # print('Got Data: ', host_data)
          break
      except OSError as e:
        if e.args[0] not in [uerrno.EINPROGRESS, uerrno.ETIMEDOUT]:
          print('**** ERROR writing ****', e)
          attempts = 0
      await asyncio.sleep(0.1)
    st_socket.close()


def parse_data(client_data):
  print(client_data)
  try:
    parsed_input = str(client_data[2:len(client_data)-1].replace("\'", "\""))
    print(parsed_input)
    command_json = ujson.loads(parsed_input)
    print(command_json)
    
    if command_json['command'] == 'output_state':
      update = command_json['update'].split('=')
      pin=int(update[0])-1
      state=int(update[1])
      Pin(out_gpio[pin], value=state)

    if command_json['command'] == 'dht1':
      update = command_json['update'].split(',')
      print(update)
      for x in update:
        objeto = x.split('=')
        machine_data['dht1'][objeto[0]]=objeto[1]
        
      machine_data['dht1']['tmp_on_tick']=0
      machine_data['dht1']['tmp_off_tick']=0
        
    if command_json['command'] == 'remote_update':
      update_info = command_json['update'].split(',')
      print('try to update', update_info)
      from structure import update
      update.remote(update_info[0],update_info[1],update_info[2])

  except:
    print('error reading json')


async def check_dht():
  while True:
    tmp_enable=machine_data['dht1']['tmp_enable']
    tmp=machine_data['dht1']['tmp']
    tmp_set=float(machine_data['dht1']['tmp_set'])
    tmp_salida=int(machine_data['dht1']['tmp_salida'])-1
    tmp_on_time=int(machine_data['dht1']['tmp_on_time'])
    tmp_on_tick=int(machine_data['dht1']['tmp_on_tick'])
    tmp_off_time=int(machine_data['dht1']['tmp_off_time'])
    tmp_off_tick=int(machine_data['dht1']['tmp_off_tick']) 

    if tmp_enable == 'true':
      #print('tmp_enable = true')

      if tmp_set > tmp:
        if tmp_on_tick < tmp_on_time:
          machine_data['dht1']['tmp_on_tick']=tmp_on_tick+1
          #print('tmp_on_tick=', tmp_on_tick)

          if Pin(out_gpio[tmp_salida]).value() != 1:
            Pin(out_gpio[tmp_salida], value=1)

        if tmp_on_tick >= tmp_on_time:
          if Pin(out_gpio[tmp_salida]).value() != 0:
            Pin(out_gpio[tmp_salida], value=0)
          if tmp_off_tick < tmp_off_time:
            #print('tmp_off_tick=', tmp_off_tick)
            machine_data['dht1']['tmp_off_tick']=tmp_off_tick+1
        
        if tmp_off_tick >= tmp_off_time:
          if Pin(out_gpio[tmp_salida]).value() != 1:
            Pin(out_gpio[tmp_salida], value=1)
          machine_data['dht1']['tmp_on_tick']=0
          machine_data['dht1']['tmp_off_tick']=0

      if tmp_set < tmp:
        Pin(out_gpio[tmp_salida], value=0)
      
      #print('')
    await asyncio.sleep(1)


async def await_dht():
  print('await_dht start')
  while True:
    print('get dht1')
    try:
      dht1.measure()
      print('dh1 ok')
    except:
      print('dh1 fail')
    
    print('dht1_done')
    print('')
    await asyncio.sleep(5)
    print('get dht2')
    
    try:
      dht2.measure()
      print('dh2 ok')
    except:
      print('dh2 fail')
    print('dht2_done')
    print('')
    await asyncio.sleep(5)


def create_data():
  global machine_data
  machine_data = {
    "command":"null",
    "version":"v0.9.1.1",
    "platform":"envasadora",
    "uptime":str(time.time()),
    "user":USER,
    "timer":{
        "timer_enable":0,
        "on_interval":0,
        "off_interval":0,
        "timer_output":0,
    },
    "gpio":{
      "input_enable":[0,0,1,0,0,0,0,0],
      "input_state":[0,0,1,0,0,0,0,0],
      "input_prog":[0,0,2,0,0,0,0,0],
      "output_enable":[1,1,1,1,1,1,1,1],
      "output_state":[0,0,0,0,0,1,0,0],
      "output_prog":[0,0,0,0,0,0,0,0]
    },
    "dht1":{
      "tmp_enable":0,
      "tmp":0,
      "tmp_salida":3,
      "tmp_set":0,
      "tmp_on_time":0,
      "tmp_on_tick":0,
      "tmp_off_time":0,
      "tmp_off_tick":0,
      "tmp_interval":0,
      "tmp_tick":0,
      "hmd_enable":0,
      "hmd":0,
      "hmd_salida":3,
      "hmd_set":0,
      "hmd_on_time":0,
      "hmd_on_tick":0,
      "hmd_off_time":0,
      "hmd_off_tick":0,
      "hmd_interval":0,
      "hmd_tick":0
    },
    "dht2":{
      "tmp_enable":0,
      "tmp":0,
      "tmp_salida":3,
      "tmp_set":0,
      "tmp_on_time":0,
      "tmp_on_tick":0,
      "tmp_off_time":0,
      "tmp_off_tick":0,
      "tmp_interval":0,
      "tmp_tick":0,
      "hmd_enable":0,
      "hmd":0,
      "hmd_salida":3,
      "hmd_set":0,
      "hmd_on_time":0,
      "hmd_on_tick":0,
      "hmd_off_time":0,
      "hmd_off_tick":0,
      "hmd_interval":0,
      "hmd_tick":0
    }
  }
