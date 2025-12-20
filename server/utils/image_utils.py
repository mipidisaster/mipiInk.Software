from PIL import Image, ImageOps, ImageFilter, ImageEnhance

EPD_WIDTH = 600
EPD_HEIGHT = 448

def get_image(image_url):
    img = Image.open(image_url).convert("RGB")
    img = ImageOps.exif_transpose(img)

    return img

def apply_image_enhancement(img, image_settings={}):
    # Convert image to RGB mode if necessary for enhancement operations
    if img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
    
    # Apply Brightness (default to 1.0 if doesn't exist)
    img = ImageEnhance.Brightness(img).enhance(image_settings.get('brightness', 1.0))

    # Apply Contract (default to 1.0 if doesn't exist)
    img = ImageEnhance.Contrast(img).enhance(image_settings.get('contract', 1.0))

    # Apply Saturation/Colour (default to 1.0 if doesn't exist)
    img = ImageEnhance.Color(img).enhance(image_settings.get('saturation', 1.0))

    # Apply Sharpness (default to 1.0 if doesn't exist)
    img = ImageEnhance.Sharpness(img).enhance(image_settings.get('sharpness', 1.0))

    return img

def pad_image_blur(img, dimensions):    
    bkg = ImageOps.fit(img, dimensions)
    bkg = bkg.filter(ImageFilter.BoxBlur(8))
    img = ImageOps.contain(img, dimensions)

    img_size = img.size
    bkg.paste(img, ((dimensions[0] - img_size[0]) // 2, (dimensions[1] - img_size[1]) // 2))

    return bkg

def apply_device_colour_palette(img, device_config={}):
    pal_image = Image.new("P", (1,1))
    pal_image.putpalette(device_config.get('colour_palette', 
                        (0,0,0,  255,255,255,  0,255,0,   0,0,255,  255,0,0,  255,255,0, 255,128,0)
                        + (0,0,0)*249))

    img = img.quantize(palette=pal_image)

    return img

def compute_image_bitstream(img, device_config={}):
    image_width = device_config.get('width', EPD_WIDTH)
    image_height = device_config.get('height', EPD_HEIGHT)

    pixel_per_byte = device_config.get('pixel_per_byte', 2)

    img_data = img.load()

    buffer = bytearray(image_width * image_height // pixel_per_byte)
    idx = 0
    for y in range(image_height):
        for x in range(0, image_width, pixel_per_byte):
            # Get color indices for two pixels
            c1 = img_data[x, y]
            c2 = img_data[x+1, y]
            # Pack into a single byte: high nibble = first pixel, low nibble = second pixel
            buffer[idx] = (c1 << 4) | c2
            idx += 1
    
    return buffer
    #       This function has some level of support for any display and pixels per byte. However,
    #       the buffer shift only supports 2pixels per byte. This needs to be corrected in the 
    #TODO - See issue #15

if __name__ == "__main__":
    # Just running this script will do a basic image conversion; just to show that it works.
    # to be removed at some point in the future...
    #TODO - See issue #16
    # === 1. Load image, orientate and re-size/pad ===
    image_eInk_7colour = get_image("server/images/testImage.jpg")
    image_eInk_7colour = pad_image_blur(image_eInk_7colour, (EPD_WIDTH, EPD_HEIGHT))

    # === 2. Apply any image colour enhancements, Saturation, Contract, Saturation, and Sharpness
    image_eInk_7colour  = apply_image_enhancement(img=image_eInk_7colour)

    # === 3. Apply the specific device colour palette
    image_eInk_7colour  = apply_device_colour_palette(img=image_eInk_7colour)    

    # === 4. Further compress the bytearray so 1byte includes 2 pixels
    buffer              = compute_image_bitstream(image_eInk_7colour)

    with open("server/testImage-preprocessed.bin", "wb") as binary_file:
        binary_file.write(buffer)