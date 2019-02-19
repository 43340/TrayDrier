import lcddriver
from time import *
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

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


def getKey():
    finput = ""

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

                        if (key=="#"):
                            print(finput)
                            lcd.lcd_clear()
                            lcd.lcd_display_string("Success", 1)
                            return finput
                        elif (key=="*"):
                            finput = ""
                            lcd.lcd_clear()
                        else:
                            finput = finput + key
                            lcd.lcd_display_string(finput, 1)
                            time.sleep(0.5)

                        while(GPIO.input(ROW_PINS[i]) == 0):
                            pass
                GPIO.output(COL_PINS[j],1)
            #time.sleep(0.2)
    except KeyboardInterrupt:
        GPIO.cleanup()

lcd = lcddriver.lcd()
lcd.lcd_clear()
 
lcd.lcd_display_string("Arvin", 1)
lcd.lcd_display_string("John", 2)
lcd.lcd_display_string("Yadao", 3)
lcd.lcd_display_string("BS CpE V", 4)
time.sleep(5)
lcd.lcd_clear()

getKey()

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