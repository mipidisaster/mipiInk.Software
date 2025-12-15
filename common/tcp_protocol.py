# Common script to handle the file transfer vetween a python script running on a local session
# and one running on a embedded device

import os
import socket
import hashlib, binascii

# Detect Micropyton robustly
#try:
#    IS_MICROPYTHON = getattr(sys, "implementation", None) and sys.implementation.name == "micropython"
#except Exception:
#    IS_MICROPYTHON = "micropython" in getattr(sys, "version", "").lower()

class TCP:
    BUFFER_SIZE = 4096
    SEPARATOR = "<SEPARATOR>"

    def __init__(self, ip_address, socket_number, device_is_server=False):
        self.addr = socket.getaddrinfo(ip_address, socket_number)[0][-1]
        self.is_server = device_is_server

    def setup_socket(self):
        self.s = socket.socket()
        print("Setting up socket...")
        if (self.is_server == False):
            print(f"Local computer, so connecting to address: {self.addr}")
            self.s.connect(self.addr)
        
        else:
            print(f"Embedded device, so binding to : {self.addr} : and listening")
            self.s.bind(self.addr)
            self.s.listen(5)
    
    def close_socket(self):
        print(f"Closing out socket...")
        self.s.close()

    # Send file to location, WITHOUT any check for SHA256 or external device NACK/ACK.
    # Steps followed;
    # 1. Filename, and size transfered
    # 2. File transferred
    def send_file_no_SHA256_or_check(self, file, name, filesize):
        # Step 1, setup socket and transfer filename and size
        
        print(f"Sending file {name}, heading being sent; {name} and {filesize}", end="")
        if (self.is_server == False):
            self.s.send(f"{name}{self.SEPARATOR}{filesize}".encode())
        else:
            self.cl.send(f"{name}{self.SEPARATOR}{filesize}".encode())

        print("Successful!")

        # Step 2, transfer file
        print("Transmitting file now...", end="")
        with open(file, "rb") as f:
            while True:
                # read the bytes from the file
                bytes_read = f.read(self.BUFFER_SIZE)
                print(len(bytes_read))
                if not bytes_read:
                    # file transmitting is done
                    break
                # we use sendall to assure transimission in 
                # busy networks
                if (self.is_server == False):
                    self.s.send(bytes_read)
                else:
                    self.cl.send(bytes_read)

        print("Finished...")
    
    def receive_file(self, filename, filesize):
        print("Receiving the file...", end="")
        with open(filename, "wb") as f:
            while True:
                # read 1024 bytes from the socket (receive)
                if (self.is_server == False):
                    bytes_read = self.s.recv(self.BUFFER_SIZE)
                else:
                    bytes_read = self.cl.recv(self.BUFFER_SIZE)
                
                print(f"Received - {len(bytes_read)} bytes")
                if ((not bytes_read) or (len(bytes_read) == 0)):
                    # nothing is received
                    # file transmitting is done
                    break
                # write to the file the bytes we just received
                f.write(bytes_read)
                
                print(f"Expected file size {filesize}, and have received {len(bytes_read)}")
                filesize -= len(bytes_read)
                print(f"Remaining {filesize}")
                
                if (filesize == 0):
                    break
        
        print("Finished...")

    def client_write_file(self, file_to_write, name_to_write, size_to_write):
        print(f"Transmitting file; {file_to_write}, {name_to_write}, {size_to_write}")
        self.setup_socket()

        try:
            self.send_file_no_SHA256_or_check(file_to_write, name_to_write, size_to_write)

            print("Waiting on device response...", end="")
            ack = str(self.s.recv(self.BUFFER_SIZE))
            if (ack == "NACK"):
                print("Ahh....shit")
                return
            
            print(f"Received response! {ack}")

            # Calculate CRC
            print(f"Calculating the CRC, of file {file_to_write}...")
            hash = binascii.hexlify(hashlib.sha256(open(file_to_write, "rb").read()).digest())
            print(f"Hash that I calculated   - {hash}")

            hash_filename = "temp.txt"

            print(f"Writing to a temp location...")
            with open(hash_filename, "wb") as f:
                f.write(hash)
            
            hash_filesize = os.stat(hash_filename)[6]
            print(f"Filename - {hash_filename}, and size - {hash_filesize}")

            self.send_file_no_SHA256_or_check(hash_filename, hash_filename, hash_filesize)
            os.remove(hash_filename)

            print("Waiting on device response...", end="")
            ack = str(self.s.recv(self.BUFFER_SIZE))
            if (ack == "NACK"):
                print("Ahh....shit")
                return
            
            print(f"Received response! {ack}")

        except() as e:
            print(f"Should really say something went wrong here...From the computer no less!!...{e}")

        self.close_socket()

    def server_read_file(self):
        self.setup_socket()

        try:
            print("Listening on the socket...")
            self.cl, self.addr = self.s.accept()
            print(f"[+] {self.addr} is connected...")

            print("Heard something, decoding header...")

            received = self.cl.recv(self.BUFFER_SIZE).decode()
            print("Got here...")

            filename_to_read, size_to_read = received.split(self.SEPARATOR)
            print(f"Received = {filename_to_read}, and {size_to_read}")

            size_to_read = int(size_to_read)

            self.receive_file(filename_to_read, size_to_read)

            self.cl.send("ACK")
            print("Send acknowledge...")

            print("Waiting on the hash from the computer...")
            
            received = self.cl.recv(self.BUFFER_SIZE).decode()
            print("Received the header, decoding...")

            hash_to_read, hashsize_to_read = received.split(self.SEPARATOR)
            print(f"Received = {hash_to_read}, and {hashsize_to_read}")

            hashsize_to_read = int(hashsize_to_read)

            self.receive_file(hash_to_read, hashsize_to_read)
            # file received, checking the contents against calculated CRC...
            hash = binascii.hexlify(hashlib.sha256(open(filename_to_read, "rb").read()).digest())
            read_hash = open(hash_to_read).read()

            print(f"Hash that I calculated   - {hash}")
            print(f"Hash received externally - {(open(hash_to_read).read()).encode()}")

            print("Attempting to encode...")
            read_hash = read_hash.encode()

            if (hash == (open(hash_to_read).read()).encode()):
                print("Hashes match!!")
                self.cl.send("ACK")
            
            else:
                print("Hashes doesn't match...")
                self.cl.send("NACK")

            os.remove(hash_to_read)
            self.cl.close()
        
        except() as e:
            print(f"Should really say something went wrong here...{e}")

        self.close_socket()