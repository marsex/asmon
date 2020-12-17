import camera, time, gc
from machine import Pin
def frame_gen():
    while True:
        buf = camera.capture()
        yield buf
        del buf
        gc.collect()

def start():
    global cr
    wc = 0
    while True:
        cr = camera.init(0, format=camera.JPEG) 
        print("Camera ready?: ", cr)
        if cr:
            camera.framesize(7)
            break
        time.sleep(2)
        wc += 1
        if wc >= 5:
            break
    return cr

def flash(state):
    if state == 1:
        flash_light.on()
    else:
        flash_light.off()

def state():
    return cr
camera.deinit()
cr = False
gc.collect()
flash_light = Pin(04, Pin.OUT)
flash = False
#start()