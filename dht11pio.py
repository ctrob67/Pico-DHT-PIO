import utime
import rp2 
from rp2 import PIO, asm_pio
from machine import Pin

@asm_pio(set_init=(PIO.OUT_HIGH),autopush=True, push_thresh=8) #output one byte at a time
def DHT11():
    label ('start')
    # 500Khz clock
    # Drive output low for at least 20ms
    set(pindirs,1)              #set pin to output  
    set(pins,0)                 #set pin low

    set(y,9)           [7]     # 20ms delay
    label ('waity')            # 10 * 31 * (31 + 1) / 500kHz = 20ms
    set(x,30)                  # plus fine tuning for the sake of it
    label ('waitx')
    jmp(x_dec,'waitx') [31]
    jmp(y_dec,'waity') [5]
     
    # Switch to input mode and look for device response (~90us low pulse)
    # Add some delay for debouncing
    set(pindirs,0)              #set pin to input
    wait(1,pin,0) [1]           # wait for signal to rise (high pulse ~12us)
    wait(0,pin,0) [1]           # wait for device to drive low (low pulse ~83us)
    wait(1,pin,0) [1]           # wait for device to release line (high pulse ~86us)

    #read databit
    wrap_target()

    # (once 40 bits have been read code will block here with input permanently high)
    wait(0,pin,0) [1]           #wait for start of data + debounce (low pulse ~54us)
    wait(1,pin,0) [24]          #wait for high signal and then 50us

    # After 50us input will indicate bit value (high pulse zero ~23us, one ~70us)
    in_(pins, 1)                #shift one bit into the isr
    wrap()                      #read the next bit
    

#main program
#dht_pwr = Pin(14, Pin.OUT)      #connect GPIO 14 to '+' on DHT11
dht_data = Pin(15, Pin.IN, Pin.PULL_UP) #connect GPIO 15 to 'out' on DHT11

#dht_pwr.value(1)                #power on DHT11
sm=rp2.StateMachine(1)          #create empty state machine
#utime.sleep(2)                  #wait for DHT11 to start up


while True:
    print('reading')
    data=[]
    total=0
    sm.init(DHT11, freq=500000, set_base=dht_data, in_base=dht_data) #start state machine
    #sm.exec("mov(pc,null)")
    sm.active(1)
    for i in range(5):         #data should be 40 bits (5 bytes) long
        data.append(sm.get())  #read byte
    sm.active(0)
    
    print("data: " + str(data))
    
    #check checksum (lowest 8 bits of the sum of the first 4 bytes)
    for i in range(4):
        total=total+data[i]
    if((total & 255) == data[4]):
        humidity=data[0]        #DHT11 provides integer humidity (no decimal part)
        temperature=data[2]     #DHT11 provides signed integer temperature (no decimal part)
        print("Humidity: %d%%, Temp: %dC" % (humidity, temperature))        
    else:
        print("Checksum: failed")
    utime.sleep_ms(1000)
