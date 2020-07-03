import machine
from machine import Pin

inp_gpio = [13, 15]
out_gpio = [2, 14, 12]

o1 = Pin(out_gpio[0], Pin.OUT)
o2 = Pin(out_gpio[1], Pin.OUT)
o3 = Pin(out_gpio[2], Pin.OUT)

def pp():
    input_state = [Pin(i, Pin.IN).value() for i in inp_gpio]
    output_state = [Pin(i, Pin.OUT).value() for i in out_gpio]

    print(input_state)
    print(output_state)
    
pp()