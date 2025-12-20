import os
from datetime import datetime, timezone
from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory, render_template,
    abort
)

from werkzeug.utils import secure_filename
import tcp_protocol
TCP_handle = tcp_protocol.TCP('192.168.1.166', 5001, False)

from utils.image_utils import (
    get_image, apply_image_enhancement, pad_image_blur,
    apply_device_colour_palette, compute_image_bitstream
)


UPLOAD_FOLDER = os.path.join(os.getcwd(), "server", "uploaded_files")
HOST = "0.0.0.0"
PORT = int("5000")

app = Flask(__name__, static_folder="static", template_folder="templates", 
            instance_relative_config=True)

# The "hello" site isn't used for anything, just a nice to have to prove that the Flask setup
# is working. Will be removed in future releases.
#TODO - See issue #16
@app.route("/hello")
def hello():
    return render_template("hello.html")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=("POST",))
def upload():
    # Two supported upload ways:
    # 1) Standard multipart/form-data (browser/form)
    # 2) Raw binary POST body with ?filename=desired_name
    #       Number 2) is intended for pico use, however not being used yet.
    #TODO - See issue #14
    filename = None

    if "file" in request.files:
        f = request.files["file"]
        filename = secure_filename(str(f.filename)) # Protected read of `filename` so it removes 
                                                    # any special characters that may confuse 
                                                    # Python
        if not filename:
            return ("Bad Request: missing filename", 400)

        dest = os.path.join(UPLOAD_FOLDER, filename)
        f.save(dest)
        return ("OK", 201)
    
    # raw binary upload
    filename = request.args.get("filename") or request.headers.get("X-FILENAME")
    if not filename:
        return ("Bad Request: missing filename (provide?filename= or multipart form key)")
    
    filename = secure_filename(filename)
    dest_path = os.path.join(UPLOAD_FOLDER, filename)
    # stream save
    with open(dest_path, "wb") as out_f:
        #request.get_data() reads the body
        out_f.write(request.get_data())

    return ("OK", 201)

@app.route("/files", methods=("GET",))
def list_files():
    files = []
    for name in os.listdir(UPLOAD_FOLDER):
        path = os.path.join(UPLOAD_FOLDER, name)
        if os.path.isfile(path):
            st = os.stat(path)
            files.append({
                "filename"  : name,
                "size"      : st.st_size,
                "modified"  : datetime.fromtimestamp(st.st_mtime, timezone.utc)
            })
    
    return jsonify(files)

@app.route("/files/<path:filename>", methods=("GET",))  # For note, just filename is used
def get_file(filename):
    filename = secure_filename(filename)    # Protected read of `filename` so it removes any 
                                            # special characters that may confuse Python
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
        abort(404)
    
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route("/delete/<path:filename>", methods=("DELETE", ))
def delete_file(filename):
    filename = secure_filename(filename)    # Protected read of `filename` so it removes any
                                            # special characters that may confuse Python
    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return ("Not Found", 404)
    
    os.remove(path)
    return ("Deleted", 200)

@app.route("/push_to_eink/<path:filename>", methods=("POST",))
def push_to_eInk(filename):
    filename = secure_filename(filename)


    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return ("Not Found", 404)
    
    newfilename = f"/sd/{os.path.splitext(filename)[0]}.bin"

    temp_location =os.path.join("server", "testImage-preprocessed.bin")

    print(f"Processing the image - {filename}...")
    # Open the image, and then generate the pre-processed image for device to display
    # A "quick" way to re-size the image
    # === 1. Load image, orientate and re-size/pad ===
    processed_img   =  get_image(path)
    processed_img   = pad_image_blur(processed_img, (600, 448))

    # === 2. Apply any image colour enhancements, Saturation, Contract, Saturation, and Sharpness
    processed_img   = apply_image_enhancement(img=processed_img)

    # === 3. Apply the specific device colour palette
    processed_img   = apply_device_colour_palette(img=processed_img)    

    # === 4. Further compress the bytearray so 1byte includes 2 pixels
    buffer          = compute_image_bitstream(processed_img)

    with open(temp_location, "wb") as binary_file:
        binary_file.write(buffer)

    print(f"File to be sent; {path}, with size {os.path.getsize(temp_location)}. "
           "New location on device {newfilename}")

    print("Sending...", end="")
    TCP_handle.client_write(temp_location, newfilename)
    print("OK")

    return ("OK", 201)

if __name__ == "__main__":
    print(f"Starting server on {HOST}:{PORT}, upload folder: {UPLOAD_FOLDER}")
    app.run(host=HOST, port=PORT, debug=True)