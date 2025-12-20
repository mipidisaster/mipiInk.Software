from machine import Pin, SPI
from utime import sleep
import sdcard, uos
import network

from tcp_protocol import TCP
from ePaper5_65 import EPD_5in65 as display

from private_keys import ssid, password

# Assign chip select (CS) pin (and start it high)
cs = Pin(15, Pin.OUT)

# Intialize SPI peripheral (start with 1 MHz)
spi = SPI(1,
          baudrate=1000000,
          polarity=0,
          phase=0,
          bits=8,
          firstbit=SPI.MSB,
          sck=Pin(10),
          mosi=Pin(11),
          miso=Pin(12))

# Initialize SD card
try:
    sd = sdcard.SDCard(spi, cs)
    uos.mount(sd, '/sd')
    print(uos.listdir('/sd'))
    
except:
    print("NO SD Card attached")

pin = Pin("LED", Pin.OUT)
pin.value(0)

wlan = network.WLAN(network.STA_IF)	# This makes the pico connect to external WiFi
wlan.active(True)
network.hostname('miPico_Test')

wlan.connect(ssid, password)

# Wait for connect or fail
max_wait = 10
while wlan.active() == False:
    if max_wait == 0:
        break
    else:
        max_wait -= 1

    print("Waiting for connection...")
    sleep(1)

if (wlan.active() == False):
    #raise RunTimeError("Network connection failed")
    print("Ah shit!!")
else:
    print("Connection successful")
    sleep(5)	# Wait 2seconds
    print(wlan.ifconfig())

print("Starting the ePaper script!...", end="")
epd = display()
print("OK")

print("Listening on the TCP handle...", end="")
TCP_handle = TCP('0.0.0.0', 5001, True)
print("OK")

while True:
    try:
        filename_read = TCP_handle.server_read()

        if filename_read is not None:
            pin.value(1)
            print(f"Retrieved file {filename_read}, displaying to eInk display...", end="")
            epd.EPD_5IN65F_Display_from_File(filename_read)
            print("OK")
            pin.value(0)
        else:
            print("I read something, but encountered an error")

    except() as e:
        print("Timed out on the read I believe...")
        print(f"{e}")
        print("Going back around again...")

# Additional eInk display features, for future
print("Displaying white...")
epd.EPD_5IN65F_Clear(epd.White)