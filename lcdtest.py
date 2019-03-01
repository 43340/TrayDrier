import lcddriver
import time

while True:
    lcd = lcddriver.lcd()
    lcd.lcd_clear()
    lcd.lcd_clear()
    lcd.lcd_display_string("Tray Dryer", 1)
    lcd.lcd_display_string("Control System", 2)
    time.sleep(5)
    lcd.lcd_clear()
    print(1)