import lcddriver
from time import *
import RPi.GPIO as GPIO
import time
import requests
import json
import datetime

GPIO.setmode(GPIO.BCM)

lcd = lcddriver.lcd()
lcd.lcd_clear()

MATRIX = [
    ['1','2','3','A'],
    ['4','5','6','B'],
    ['7','8','9','C'],
    ['*','0','#','D']
]
 
ROW_PINS = [18, 23, 24, 25]
COL_PINS = [12, 16, 20, 21]

# Set GPIO Pins
for i in range(4):
    GPIO.setup(ROW_PINS[i], GPIO.IN, pull_up_down = GPIO.PUD_UP)

for j in range(4):
    GPIO.setup(COL_PINS[j], GPIO.OUT)
    GPIO.output(COL_PINS[j], 1)


def getKey(prompt="", prompt2=""):
    finput = ""

    if(prompt == "" and prompt2 == ""):
        pass
    else:
        lcd.lcd_clear()
        lcd.lcd_display_string(prompt, 1)
        lcd.lcd_display_string(prompt2, 2)

    try:
        GPIO.output(12, 1)
        GPIO.output(16, 1)
        GPIO.output(20, 1)
        GPIO.output(21, 1)

        while True:
            # test #
            for j in range(4):
                GPIO.output(COL_PINS[j], 0)
            #time.sleep(0.1)
                for i in range(4) :
                    if GPIO.input (ROW_PINS[i]) == 0:
                        key = (MATRIX[i][j])

                        if (key=="A"):
                            time.sleep(0.3)
                            return finput
                        elif (key=="B"):
                            finput = finput[:-1]
                            lcd.lcd_clear()
                            lcd.lcd_display_string(prompt, 1)
                            lcd.lcd_display_string(prompt2, 2)
                            lcd.lcd_display_string(finput, 3)
                            time.sleep(0.3)
                        elif (key=="C"):
                            finput = ""
                            lcd.lcd_clear()
                        elif (key=="D"):
                            getTempAndHum()
                        elif (key=="#"):
                            return "#"
                        else:
                            finput = finput + key
                            lcd.lcd_display_string(finput, 3)
                            time.sleep(0.3)

                        #while(GPIO.input(ROW_PINS[i]) == 0):
                        #    pass
                GPIO.output(COL_PINS[j],1)
            #time.sleep(0.2)
    except KeyboardInterrupt:
        GPIO.cleanup()


### get functions ###


def get_set_temp():
    prompt = "Please enter the set"
    prompt2 = "temp for the process"
    set_temp = getKey(prompt, prompt2)
    return set_temp


def get_cook_time():
    prompt = "Enter the desired"
    prompt2 = "cook time"
    cook_time = getKey(prompt, prompt2)
    return cook_time


def get_read_interval():
    prompt = "Enter the interval"
    prompt2 = "to read data"
    read_interval = getKey(prompt, prompt2)
    return read_interval


def getTempAndHum():
    r = requests.get('http://192.168.254.103:8023/data')
    data = r.json()
    ctemp = data['temperature']
    chum = data['humidity']
    lcd.lcd_clear()
    lcd.lcd_display_string("Data", 1)
    lcd.lcd_display_string("Temp: " + str(ctemp), 3)
    lcd.lcd_display_string("Hum: " + str(chum), 4)


def checkProcess():
    r = requests.get('http://192.168.254.103:8023/check')
    data = r.json()

    status = data['status']

    if not status:
        return False
    else:
        return True


def sequence():
    lcd.lcd_display_string("Tray Dryer", 1)
    lcd.lcd_display_string("Control System", 2)
    time.sleep(5)
    lcd.lcd_clear()

    name = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    set_temp = get_set_temp()
    cook_time = get_cook_time()
    read_interval = get_read_interval()

    lcd.lcd_clear()
    lcd.lcd_display_string("Confirm", 1)
    lcd.lcd_display_string(set_temp + "C", 2)
    lcd.lcd_display_string(cook_time + "mins", 3)
    lcd.lcd_display_string(read_interval + "sec", 4)

    key = getKey()

    while(key != '#'):
        key = getKey()


    lcd.lcd_clear()
    lcd.lcd_display_string("Sending...", 1)
    time.sleep(1)
    lcd.lcd_clear()
    lcd.lcd_display_string("Sent", 1)
    time.sleep(1)

    lcd.lcd_clear()

    return name, set_temp, cook_time, read_interval


def set_variables():
    name, stemp, ctime, rinte = sequence()
    url = 'http://192.168.254.103:8023/start'
    datas = {
        "name": str(name),
        "stemp": int(stemp),
        "ctime": float(ctime),
        "rinte": float(rinte)
    }

    r = requests.post(url, json=datas)

    print(r.status_code)


def main():
    while True:
        if checkProcess():
            set_variables()
        else:
            getTempAndHum()
    
main()



"""
class KeyStore:
    def __init__(self):
        self.pressed_keys = []

    def store_key(self, key):
        if(key=="#"):
            print(self.pressed_keys)
        else:
            self.pressed_keys.append(key)
    
    def clear_keys(self):
        self.pressed_keys.clear()

keys = KeyStore()

keypad.registerKeyPressHandler(keys.store_key)

print(keys.pressed_keys)"""