import utime
from rp2 import PIO, asm_pio, StateMachine
from machine import Pin, mem32

ADR_PIOx_CTRL = 0x50200000 + 0x000
ADR_SMx_FSTAT = 0x50200000 + 0x004
ADR_SMx_FLEVEL = 0x50200000 + 0x00c
ADR_SMx_EXECCTRL = 0x50200000 + 0x0c8 + 0x04
ADR_SMx_ADDR = 0x50200000 + 0x0c8 + 0x0c
ADR_SMx_INSTR = 0x50200000 + 0x0c8 + 0x10

def SmRestart(smNumber):
    # Only coded for SM 0-3
    mem32[ADR_PIOx_CTRL] |= 0x10 << (smNumber & 3)

def SmAddr(smNumber):
    # Only coded for SM 0-3
    return mem32[ADR_SMx_ADDR]

def SmRxEmpty(smNumber):
    # Only coded for SM 0-3
    return mem32[ADR_SMx_FSTAT] & 0x100 << (smNumber & 3) != 0

def SmRxLevel(smNumber):
    # Only coded for SM 0-3
    return mem32[ADR_SMx_FLEVEL] >> 8 * (smNumber & 3) + 4 & 0xf

def SmExec(smNumber, instr):
    # Only coded for SM 0-3
    mem32[ADR_SMx_INSTR] = instr
    while mem32[ADR_SMx_EXECCTRL] & 0x80000000:
        pass
    

@asm_pio(set_init=(PIO.OUT_HIGH),autopush=True, push_thresh=20) #output one byte at a time
def DHT11():
    # Requires 500Khz clock, preload x with 1000, and set pin output 0
    # Drive output low for at least 2ms to activate the device
    set(pindirs,1)
    set(pins,0)
    set(x,31)
    label ('delay_ms')
    nop() [31]
    jmp(x_dec,'delay_ms') [31]
     
    # Look for the device response (~90us low pulse)
    # Add some delay to 'debounce' edges
    set(pindirs,0)
    wait(1,pin,0) [1]            # Wait for input to release (high pulse ~12us)
    wait(0,pin,0) [1]            # Wait for device to drive low (low pulse ~83us)
    wait(1,pin,0) [1]            # Wait for device to release line (high pulse ~86us)

    wrap_target()                # Read data bits from device

    label("next_bit")

    # (once 40 bits have been read code will block here with input permanently high)
    wait(0,pin,0) [1]            # Wait for start of data + debounce (low pulse ~54us)
    wait(1,pin,0) [24]           # Wait for high signal and then 50us

    # After 50us input will indicate bit value (high pulse zero ~23us, one ~70us)
    in_(pins, 1)                 # Shift the data bit into the isr

    wrap()                       # Loop to read the remaining bits from device

class Timeout(Exception):
    pass

class BadChecksum(Exception):
    pass

class DHT11_PIO:
    def __init__(self, data_pin):
        pin = Pin(data_pin, Pin.IN, Pin.PULL_UP)
        self.sm = StateMachine(0)
        self.sm.init(DHT11, freq = 500000, set_base = pin, in_base=pin)
        self.start = SmAddr(0)

    def read(self):
        # Reset the state machine to start a fresh transaction
        SmRestart(0)
        SmExec(0, self.start)

        # Activate the state machine and then sleep until it should be complete
        self.sm.active(1)
        utime.sleep_ms(20)
        self.sm.active(0)

        # Exception if the amount of data is wrong
        if SmRxLevel(0) != 2:
            while SmRxLevel(0):
                self.sm.get()
            raise Timeout()

        # Read back the data from the Rx FIFO as 
        data = self.sm.get()
        data = (data << 20) + self.sm.get()

        # Calculate and check checksum
        if (sum(data >> i * 8 for i in range(1,5)) - data) & 255:
            raise BadChecksum()

        return self.decode(data)

    def decode(self, data):
        humidity=(data >> 32) & 255         #DHT11 provides integer humidity (no decimal part)
        temperature= (data >> 16) & 255     #DHT11 provides signed integer temperature (no decimal part)
        return humidity, temperature

class DHT22_PIO(DHT11_PIO):
    def decode(self, data):
        humidity    = ((data >> 24) & 0xffff)/10 # 16 bits with 0.1% resolution 
        temperature = ((data >> 8)  & 0x7fff)/10 # 15 bits with 0.1% resolution
        if data & 0x800000:                      # Check temperature sign bit
            temperature = -temperature
        return humidity, temperature
