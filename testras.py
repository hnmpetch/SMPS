from gpiozero import Servo
from RPLCD.i2c import CharLCD
import time

servo_in = Servo(17)
servo_out = Servo(18)

lcd = CharLCD('PCF8574', 0x27)  # 0x27 คือ address ของ I2C LCD
lcd.cursor_pos = (0, 0)  # แถว 1 คอลัมน์ 1
lcd.write_string('Smart parking system')
lcd.cursor_pos = (1, 0)  # แถว 1 คอลัมน์ 1
lcd.write_string('Starting...')


servo_in.value = 0
servo_out.value = 0

for i in range(20):
    lcd.cursor_pos = (3, 0)  # แถว 1 คอลัมน์ 1
    lcd.write_string(f'    {i}')
    time.sleep(1)

time.sleep(10)

while True:
    lcd.cursor_pos = (1, 0)  # แถว 1 คอลัมน์ 1
    lcd.write_string('      SERVO IN  ')
    servo_in.value = 1
    time.sleep(3)
    servo_in.value = 0
    time.sleep(3)
    
    lcd.cursor_pos = (1, 0)  # แถว 1 คอลัมน์ 1
    lcd.write_string('      SERVO OUT')
    servo_out.value = -1
    time.sleep(3)
    servo_out.value = 0
    time.sleep(3)
    