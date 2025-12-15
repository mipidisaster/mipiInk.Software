from machine import Pin
from utime import sleep

sleep(5)

pin = Pin("LED", Pin.OUT)
pin.value(0)
sleep(2)
pin.value(1)
sleep(2)
pin.value(0)

sleep(5)
print("I think I just had a reset...")
print("did you see that?")

pin.value(0)
sleep(2)
pin.value(1)
sleep(2)
pin.value(0)