import socket
import threading
import signal
import sys
import os
import time
from collections import deque

config =  {
            "HOST_NAME" : "localhost",
            "BIND_PORT" : 12345,
            "MAX_REQUEST_LEN" : 2048,
            "CONNECTION_TIMEOUT" : 8
          }

# global Q_size 
# global Q  
# Q_size = 0
# Q = deque()

class Server:
    """ The server class """

    def __init__(self, config):
        signal.signal(signal.SIGINT, self.shutdown)     # Shutdown on Ctrl+C
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)             # Create a TCP socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    # Re-use the socket
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT'])) # bind the socket to a public host, and a port
        self.serverSocket.listen(10)    # become a server socket
        self.__clients = {}
        self.files=[-1,-1,-1]
        self.dates = ['','','']
        self.Q_size = 0
        self.Q = deque()
        self.lm = 0


    def listenForClient(self):
        """ Wait for clients to connect """
        while True:
            (clientSocket, client_address) = self.serverSocket.accept()   # Establish the connection
            d = threading.Thread(name=self._getClientName(client_address), target=self.proxy_thread, args=(clientSocket, client_address))
            d.setDaemon(True)
            d.start()
        self.shutdown(0,0)


    def proxy_thread(self, conn, client_addr):
        """
        *******************************************
        *********** PROXY_THREAD FUNC *************
          A thread to handle request from browser
        *******************************************
        """
        time.sleep(0.1)
        request = conn.recv(config['MAX_REQUEST_LEN'])        # get the request from browser
        first_line = request.split('\r\n')[0]                   # parse the first line
        url = first_line.split(' ')[1]                        # get url
        if(url):
            filename = url.split('/')[3]
        else:
            time.sleep(0.1)    
        # find the webserver and port
        http_pos = url.find("://")          # find pos of ://
        if (http_pos==-1):
            temp = url
        else:
            temp = url[(http_pos+3):]       # get the rest of url
        port_pos = temp.find(":")           # find the port pos (if any)

        # find end of web server
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if (port_pos==-1 or webserver_pos < port_pos):      # default port
            port = 20000
            webserver = temp[:webserver_pos]
        else:                                               # specific port
            port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
            webserver = temp[:port_pos]

        try:
            # create a socket to connect to the web server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(config['CONNECTION_TIMEOUT'])
            #Establishing connection with server
            s.connect((webserver, port))
            
            req = 'GET ' + "/" + request[request.find(filename):]
            print req
            #Checking whether the requested file is in cache
            if(filename in self.files):
                #Adding If-Modified-Since to the header.
                if_m = "If-Modified-Since: " + self.dates[self.files.index(filename)] + "\r\n"
                req = req.strip('\n').strip('\r') + if_m + '\r\n\r\n'
                #Sending the request to web server.
                s.sendall(req)
                print "File present in web_cache"
                
                time.sleep(0.1)
                #Recieving data from web server.
                data = s.recv(config['MAX_REQUEST_LEN'])
                
                st = data.split('\r\n')

                error_c = st[0].split(' ')[1].strip(' ')
                if error_c == "304":
                    print "File not modified and sending data from cache"
                    #Sending the file from cache.
                    r = open(str(self.files.index(filename)),"r")
                    buf  = r.readline()
                    while 1:
                        print "......"
                        data = r.read(2048)         
                        if (len(data) > 0):
                            conn.send(data)                               
                        else:
                            break
                    print "Data sent from cache\n\n"
                    r.close()
                else:
                    print "File modified since last cached"
                    #Sending and writing the file if the file in web cache is modified.
                    last_m = st[5][st[5].find(':')+1:].strip(' ')
                    self.dates[self.files.index(filename)] = last_m 
                    f = open(str(self.files.index(filename)),'w')
                    f.write('\n')
                    f.write(data)
                    print "Sending and caching new data"
                    conn.send(data)
                    while 1:
                        data = s.recv(config['MAX_REQUEST_LEN'])
                        print "....."    
                        if (len(data) > 0):
                            conn.send(data)
                            f.write(data)
                            
                            time.sleep(0.1)
                        else:                       
                            break 
                    print "File recieved from web server and sent to client\n\n"
                    f.close()    
            else:           
                #Writing and sending a file if the file not present in the cache.
                print "File is not cached"
                req = 'GET ' + "/" + request[request.find(filename):]
                s.sendall(req)
                print "Requesting server"
                time.sleep(0.1)
                self.files[self.lm%3]=filename
                #Opening the file to be written.
                f= open(str(self.lm%3),"w") 
                self.lm =self.lm+ 1
                f.write('\n')       
                print "Receiving data from web server"
                while 1:
                    data = ['\0' for i in range(2048)]
                    print "........"
                    data = s.recv(config['MAX_REQUEST_LEN'])     # receive data from web server
                    if (len(data) > 0):
                        conn.send(data)
                        f.write(data)
                        time.sleep(0.1)
                    else:                       
                        break
                f.close()
                r = open(str(self.files.index(filename)),"r")
                r = r.read(2048)
                st = r.split('\r\n')
                error_c = st[0].split(' ')[1].strip(' ')
                #Checking the error code if any. 
                if error_c == '404':
                    print "Requested file not present\n\n"
                    os.remove(str(self.files.index(filename)))
                    self.files[self.files.index(filename)] = -1
                    self.lm -= 1
                else:
                    #Updating the last modified date of the file for verification.
                    print "File recieved from web server and sent to client\n\n"        
                    last_m = st[5][st[5].find(':')+1:].strip(' ')
                    self.dates[self.files.index(filename)] = last_m 
                    if  (st[6][st[6].find(':')+1:].strip(' ') == "no-cache"):
                        os.remove(str(self.files.index(filename)))
                        self.files[self.files.index(filename)] = -1
                        self.lm -= 1

                
            s.close()
            conn.close()
        #Errors in creating and connecting a socket   
        except socket.error as error_msg:
            print 'ERROR: ',client_addr,error_msg
            if s:
                s.close()
            if conn:
                conn.close()


    def _getClientName(self, cli_addr):
        """ Return the clientName.
        """
        return "Client"


    def shutdown(self, signum, frame):
        """ Handle the exiting server. Clean all traces """
        self.serverSocket.close()
        sys.exit(0)


if __name__ == "__main__":
    server = Server(config)
    server.listenForClient()