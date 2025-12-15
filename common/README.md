# Common packages

This folder includes all the packages which are common between both the embedded device and the webserver

## TCP_Protocol

This package manages the transfer of files from one device (client) to another (server); so long as I have the definitions the correct way around...

The files are transfered using the following protocol:
```mermaid
sequenceDiagram
client->>server: Image update code
server-->>client: ACK
client->>server: Image name and size
client->>server: Image file
server-->>client: ACK
client->>server: SHA256
server-->>client: ACK
alt SHA256 failure
	server-->>client: NACK
else SHA256 success
	server-->>client: ACK
end
```