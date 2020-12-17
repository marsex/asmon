import camera, time, gc
def frame_gen():
    while True:
        buf = camera.capture()
        yield buf
        del buf
        gc.collect()
		
def pic():
    return frame_gen()

def start():
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
    return cr

def flash(state)
    if state == 1:
        flash_light.on()
    else:
        flash_light.off()
        
flash_light = Pin(04, Pin.OUT)

