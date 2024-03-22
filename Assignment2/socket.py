import socket
from _thread import *
import re

proxy_port = 12349
buffer = 8192

def start():

    # Create a socket for the proxy server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.bind(('', proxy_port))
    client.listen(5)
    print(f"Listening for Connections.")

    while True:
        # Accept incoming client connections
        clientsocket, address = client.accept()
        
        
        # Receive client data and start a new thread
        data = clientsocket.recv(buffer)
        start_new_thread(client_proxy, (clientsocket, data))

def client_proxy(clientsocket, data):

    # Finds url and port from the webserver
    line1 = data.split(b'\n')[0]
    url = line1.split()[1]

    # Find the position of ://
    # If :// is not found returns -1
    http_pos = url.find(b'://')
    
    # If there is no ://, then assign the entire url to temp.
    if(http_pos==-1):
        temp=url
    # Otherwise temp is assigned the value of a substring of everything after :// 
    else:
        temp = url[(http_pos+3):]
    
    # Find the position of : in temp (the url)
    port_pos = temp.find(b':')
    
    # Find the first / in temp (the url)
    webserver_pos = temp.find(b'/')
    
    # If there is no /, then assign the length of temp (the url) to webserver_pos
    if webserver_pos == -1:
        webserver_pos = len(temp)
    else:
        webserver_pos

    # If there is no port found in the url, then assign 80 to port.
    # And assign webserver as the part from the start of temp (the url) till the webserver_pos (the position of the /)
    # This gives us the url of the site without any slashes
    if(port_pos == -1):
        port = 80
        host = temp[:webserver_pos]
    # In case there is a port, then retrive that port and assign it to port.
    # Retrived using string slicing, by taking temp (the url) and taking everything after the position in which the 
    # port starts (port_pos) onwards then it's sliced again at the webserver_pos (/) - port_pos (:) -1 to not take the / character.
    # Also returns the webserver as everything from the start of the url up till the position in which the port is located.
    else:
        port = int((temp[(port_pos+1):])[:webserver_pos - port_pos-1])
        host = temp[:port_pos]

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    server.send(data)

    data2 = server.recv(buffer).decode()
    
    # Replaces of occurrences of strings: 
    # 'Smiley', with 'Trolly'
    # 'Stockholm', with 'Linköping'
    # Replaces images:
    # Any image that starts with '.' and ends with '.jpg', with another image
    data2 = re.sub(r"Smiley", "Trolly", data2)
    data2 = re.sub(r"Stockholm", "Linköping", data2)
    data2 = re.sub(r"\./\w+[-\w]*\.jpg", "https://cdn3.emoji.gg/emojis/2232-troll-3d.png", data2)
    clientsocket.sendall(data2.encode())
    
    # Closes proxy server socket
    server.close()

    # Closes client socket
    clientsocket.close()

# Runs the start function if started as a main file, not a module.
if __name__ == "__main__":
    start()
