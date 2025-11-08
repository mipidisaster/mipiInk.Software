from machine import Pin, SPI
from utime import sleep
import sdcard, uos

from ePaper5_65 import EPD_5in65 as display

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

print("Starting the ePaper script!")
epd = display()

#print("Displaying pre-processed image...")
#epd.EPD_5IN65F_Display_from_File("/sd/testImage-preprocessed.bin")

print("Displaying white...")
epd.EPD_5IN65F_Clear(epd.White)

print("LED starts flashing...")
while True:
    pin.toggle()
    sleep(1) # sleep 1sec

pin.off()
print("Finished.")