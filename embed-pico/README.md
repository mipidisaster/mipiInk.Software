# Embed Pico
The `.uf2` file has been downloaded from the following website:
https://micropython.org/download/RPI_PICO2_W/

# eInk driver information

Within this repository, I have taken copies of various of other repositories, and modified so as to work in my application.
The original sources will be captured within the scripts themselves, however a summary of the repositories are located below:

## Waveshare

Within the [Waveshare](https://github.com/waveshareteam) github, it has two repositories that give various drivers for their eInk displays;
- [e-Paper](https://github.com/waveshareteam/e-Paper)
- [Pico_ePaper_Code](https://github.com/waveshareteam/Pico_ePaper_Code)

In terms of construction I believe that they both have the same drivers, however the [Pico_ePaper_Code](https://github.com/waveshareteam/Pico_ePaper_Code) version is obviously configured for use on a Pico. Hence this is the main one that I will be making use of.

It is worth pointing out that I think there are some drivers that exist within the [e-Paper](https://github.com/waveshareteam/e-Paper) that doesn't appear within [Pico_ePaper_Code](https://github.com/waveshareteam/Pico_ePaper_Code); maybe because it requires some extra level of functionality?

I'm hoping that my variation of the implementation avoids any limitation...

## Pimoroni

Now I believe that the drivers are effectively the same between the Waveshare and Pimoroni; with the main difference being that within the Pimoroni eInk displays there is a EEPROM, which includes the model/encoder for the display - allowing for a single "auto" function to interface with the display.
- [inky-frame](https://github.com/pimoroni/inky-frame)
- [inky-dashboard](https://github.com/jaeheonshim/inky-dashboard)

All these versions make use of the [Pimoroni micropython image](https://github.com/pimoroni/pimoroni-pico) `.uf2` build, which has a `picographics` library. However, again using this by itself in a custom setup will NOT work; as it needs to have the EEPROM available.

Within the [InkyPi](https://github.com/fatihak/InkyPi) project (which is another project that I have taken inspriation from), it uses the [inky](https://github.com/pimoroni/inky) repository. Which has a `auto` feature; [auto.py (at time of writing)](https://github.com/pimoroni/inky/blob/3c7c0d723ff638c9c5bee359d6a84b26e0f25b8a/inky/auto.py); which does this EEPROM and then select driver feature.

## Mine

The process of getting a driver for a display;
- Starting with the [Pico_ePaper_Code](https://github.com/waveshareteam/Pico_ePaper_Code), see if it is there
- If not, then try looking in [e-Paper](https://github.com/waveshareteam/e-Paper), and get the sequence for interface and create a custom one
- Lastly, if it is a Pimoroni display, then do the above but check against [auto.py](https://github.com/pimoroni/inky/blob/main/inky/auto.py), and see what their driver looks like

Once you have found a version to make use of - import into this repository (with a reference to source), and then modify to make use of `/sd`