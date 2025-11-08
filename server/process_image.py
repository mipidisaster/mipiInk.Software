from PIL import Image, ImageOps, ImageFilter

EPD_WIDTH = 600
EPD_HEIGHT = 448

# A "quick" way to re-size the image
# === 1. Load image, orientate and re-size/pad ===
pre_img = Image.open("server/images/testImage.jpg").convert("RGB")
pre_img = ImageOps.exif_transpose(pre_img)
#pre_img = ImageOps.pad(pre_img, (EPD_WIDTH, EPD_HEIGHT), color="#f00")

# This is what the `InkyPi` project does to its images...
bkg = ImageOps.fit(pre_img, (EPD_WIDTH, EPD_HEIGHT))
bkg = bkg.filter(ImageFilter.BoxBlur(8))
pre_img = ImageOps.contain(pre_img, (EPD_WIDTH, EPD_HEIGHT))

img_size = pre_img.size
bkg.paste(pre_img, ((EPD_WIDTH - img_size[0]) // 2, (EPD_HEIGHT - img_size[1]) // 2))

pre_img = bkg

# === 2. Generate a new Image class for display palette ===
pal_image = Image.new("P", (1,1))
pal_image.putpalette( (0,0,0,  255,255,255,  0,255,0,   0,0,255,  255,0,0,  255,255,0, 255,128,0) + (0,0,0)*249)
# Provide the 4 colours supported by display

# === 3. Convert loaded image to the new colour palette ===
image_eInk_7colour = pre_img.convert("RGB").quantize(palette=pal_image)
img_data = image_eInk_7colour.load()

#image_eInk_7colour.show()

# === 4! Further compress the bytearray so 1byte includes 2 pixels
buffer = bytearray(EPD_WIDTH * EPD_HEIGHT // 2)
idx = 0
for y in range(EPD_HEIGHT):
    for x in range(0, EPD_WIDTH, 2):
        # Get color indices for two pixels
        c1 = img_data[x, y]             # type: ignore
        c2 = img_data[x+1, y]           # type: ignore
        # Pack into a single byte: high nibble = first pixel, low nibble = second pixel
        buffer[idx] = (c1 << 4) | c2    # type: ignore
        idx += 1

with open("server/testImage-preprocessed.bin", "wb") as binary_file:
    binary_file.write(buffer)


print(pre_img.size)
print(image_eInk_7colour.size)