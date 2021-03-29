import utime
import dht11pio
from machine import Pin, I2C
from sh1106 import SH1106_I2C


dht = dht11pio.DHT11_PIO(data_pin = 15)

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
display = SH1106_I2C(128, 64, i2c)
display.rotate(True)
display.contrast(255)

while True:
    display.fill(0)
    try:
        h,t = dht.read()
        print("Humidity: {}%, Temp: {}C".format(h, t))        
        display.text("Temp     {0}C".format(t), 4, 0, 1)
        display.text("Humidity {0}%".format(h), 4, 12, 1)
    except dht11pio.Timeout:
        print("Sensor Timeout")        
        display.text("Sensor Timeout", 4, 0, 1)
    except dht11pio.BadChecksum:
        # Wait for the next one...
        print("Bad Checksum")        
        continue
        
    display.show()
    utime.sleep_ms(1000)
