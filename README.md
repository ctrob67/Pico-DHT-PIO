# Pi PICo PIO Based DHT11 Driver with Demo

This is a DHT11/22 driver written in micropython that uses the PIO capabaility of the Pi Pico.

It's somewhat experimental in that there are different commits with slightly different approaches.

The current approach minimises the amount of code stored in the PIO memory, to 8 instructions.  It also
restarts the state machine before each transaction - but this only works if it is the first program
loaded on a PIO (probably not an issue, yet).

The software driver initialises the statemachine and then lets it run (sleeps) for ~25ms and then checks
what happened.  This is fine for a relatively slow device that should only be polled at most once per
second.

Copy the files to the Pico - the files in lib go in the lib folder on the Pico.

The demo writes back to the serial port and updates an SH1106 OLED on I2C (GPIO0/1) but this should be
easily disabled or switched to a SSD1306.

The demo script is run with "import dht11_sh1106_demo" from the command line or by inserting it into 
main.py and storing this on the Pico.