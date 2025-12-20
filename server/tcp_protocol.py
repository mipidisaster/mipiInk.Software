# Common script to handle the file transfer vetween a python script running on a local session
# and one running on a embedded device

import os
import socket
import hashlib, binascii
import gc

class TCP:
    BUFFER_SIZE         = 4096  # Constant for the maximum buffer size of data transfered
    HASH_BUFFER_SIZE    = 2048  # Constant for the maximum buffer size for hash calculation
    SEPARATOR = "<SEPARATOR>"   # Seperate between filename and filesize (and any other data)

    def __init__(self, ip_address, socket_number, device_is_server=False):
        self.ip_address     = ip_address
        self.socket_number  = socket_number
        self.is_server      = device_is_server
        self.active_listen  = False
        
        self.s              = socket.socket()
        self.conn           = socket.socket()

    def setup_socket(self):
        if (self.is_server == False) or \
           (self.is_server == True and self.active_listen == False):
        # Whilst in `server` configuration, don't want to keep closing/opening sockets (at
        # least with current design). So using `active_listen` as an indication of socket
        # already being setup. And to only close when `close_socket` has been run, which would
        # be externally in a `server` setup (as in not done in this class)
        # -----------------------------------------------------------------------------------------

        # 'getaddrinfo' returns a list; which is basically a tuple wrapped in a list
        #  tuple includes; (family, type, proto, canonname, socketaddr)
        #    -- Only interested in `socketaddr`, so [0][-1] used (convert list to tuple
        #       and get last entry)
        #
        # See https://docs.python.org/3/library/socket.html#socket.getaddrinfo
            self.s      = socket.socket()
            self.conn   = socket.socket()

            self.addr   = socket.getaddrinfo(self.ip_address, self.socket_number)[0][-1]
            
            if (self.is_server == False):   # If client, then need to connect to external website
                self.s.connect(self.addr)
                self.conn = self.s          # Duplicate to `conn` for script management
            
            else:                           # Otherwise, need to listen on the address
                self.s.bind(self.addr)
                self.s.listen(5)            # Allow for upto 5 unaccepted connections before 
                self.active_listen = True   # refusing
    
    def close_socket(self):
        self.active_listen = False
        try:
            self.conn.close()
        
        except:
            print("Specific socket is already closed...")
        
        try:
            self.s.close()
        
        except:
            print("Global socket is also closed...")

    # Please see `README.md` in the `common` package for visual of the sequence for file transfer
    def send_file_no_SHA256_or_check(self, file, name, filesize):
        # Step 1, setup socket and transfer filename and size
        self.conn.send(f"{name}{self.SEPARATOR}{filesize}".encode())

        # Step 2, transfer file
        with open(file, "rb") as f:
            while True:
                # read the bytes from the file
                bytes_read = f.read(self.BUFFER_SIZE)
                if not bytes_read:
                    # file transmitting is done
                    break

                self.conn.send(bytes_read)
    
    def receive_file(self, filename, filesize):
        with open(filename, "wb") as f:
            while True:
                bytes_read = self.conn.recv(self.BUFFER_SIZE)

                if ((not bytes_read) or (len(bytes_read) == 0)):
                    # nothing is received
                    # file transmitting is done
                    break

                f.write(bytes_read)
                print(f"Expected file size {filesize}, and have received {len(bytes_read)}")

                filesize -= len(bytes_read)
                
                if (filesize == 0): # Extra level of check
                    break           # if no more data expected, exit

    def client_write(self, file_to_write, name_to_write):
        self.setup_socket()
        size_to_write = os.stat(file_to_write)[6]

        try:
            self.send_file_no_SHA256_or_check(file_to_write, name_to_write, size_to_write)
            ack = str(self.conn.recv(self.BUFFER_SIZE))
            if (ack == "NACK"):
                print("Encountered a failed package, no logic to support - exitting...")
                return
            
            hash = self.stream_hash_from_file(file_to_write)

            hash_filename = "temp_hash_file.txt"

            with open(hash_filename, "wb") as f:
                f.write(hash)
            
            hash_filesize = os.stat(hash_filename)[6]
            self.send_file_no_SHA256_or_check(hash_filename, hash_filename, hash_filesize)
            
            os.remove(hash_filename)    # No need to store the file with the hash...

            ack = self.conn.recv(self.BUFFER_SIZE).decode()
            if (ack == "NACK"):
                print("Encountered a failed package, no logic to support - exitting...")
                return

        except() as e:
            print(f"Encountered an unexpected error with the write, see error {e}")
            print("Socket should be closed out successfully")

        self.close_socket()

    def server_read(self):
        self.setup_socket()

        try:
            self.conn, client_addr = self.s.accept()
            print(f"[+] {client_addr} is connected...")

            received = self.conn.recv(self.BUFFER_SIZE).decode()
            filename_to_read, size_to_read = received.split(self.SEPARATOR)

            size_to_read = int(size_to_read)

            self.receive_file(filename_to_read, size_to_read)

            self.conn.send("ACK")
            
            received = self.conn.recv(self.BUFFER_SIZE).decode()
            hash_to_read, hashsize_to_read = received.split(self.SEPARATOR)

            hashsize_to_read = int(hashsize_to_read)

            self.receive_file(hash_to_read, hashsize_to_read)

            # Calculate the CRC of the original file retrieved... (not to be confused with the
            # second file, which is the `hash_to_read`)
            hash = self.stream_hash_from_file(filename_to_read)
            read_hash = open(hash_to_read).read()

            read_hash = read_hash.encode()  # Calculated `hash` will be of type "bytes" so convert
                                            # read hash to "bytes", though encode...
            if (hash == read_hash):
                self.conn.send("ACK".encode())
            
            else:
                self.conn.send("NACK".encode())

            os.remove(hash_to_read) # No need to store the file with the hash...
            
            self.conn.close()
        
        except() as e:
            print(f"Encountered an unexpected error with the read, see error {e}")
            print("Socket should be closed out successfully")
            return None
    
        return filename_to_read
        

    def stream_hash_from_file(self, file):
        gc.collect()    # Free up memory before big operation (Micropython)
        h = hashlib.sha256()

        with open(file, "rb") as f:
            while True:
                chunk = f.read(self.HASH_BUFFER_SIZE)
                if not chunk:
                    break
                    
                h.update(chunk)
            
            digest = binascii.hexlify(h.digest())
            gc.collect()

            return digest