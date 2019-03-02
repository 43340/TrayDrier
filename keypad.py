#!/usr/bin/python

# -*- coding: utf-8 -*-

""" 4x4 Keypad module
4x4 keypad module for the Raspberry Pi. This module uses Pi's GPIO
pins to get the user input from a 4x4 keypad.

Credits:
        Me - 43340
License:
        MIT
"""


import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)


class keypad:
    def __init__(self, _rowPins, _colPins):

        MATRIX = [
            ['1','2','3','A'],
            ['4','5','6','B'],
            ['7','8','9','C'],
            ['*','0','#','D']
        ]

        self.rowPins = _rowPins
        self.colPins = _colPins

        for i in range(4):
            GPIO.setup(self.rowPins[i], GPIO.IN, pull_up_down = GPIO.PUD_UP)

        for j in range(4):
            GPIO.setup(self.colPins[j], GPIO.OUT)
            GPIO.output(self.colPins[j], 1)
    

    def GetKey(self, prompt="", prompt=""):
        finput = ""

        try:
            GPIO.output(self.colPins[0], 1)
            GPIO.output(self.colPins[1], 1)
            GPIO.output(self.colPins[2], 1)
            GPIO.output(self.colPins[3], 1)

            while True:
                for j in range(4):
                    GPIO.output(self.colPins[j], 0)
                    for i in range(4):
                        if GPIO.input(self.rowPins[i]) == 0:
                            key = (MATRIX[i][j])

                            if (key=="A"):
                                time.sleep(0.3) # debounce
                                return finput
                            elif (key=="B"):
                                
