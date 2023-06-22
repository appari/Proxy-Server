###Web Cache###

**The code 'proxy.py' is the implementation of web cache.

**To run the proxy server enter the following command:

>'python2 proxy.py'
>Now you can set the proxy in the browser as "localhost:12345"
>You can now request a file at "127.0.0.1:20000"



**Folowing are the features implemented:

1.The client requests the objects via the proxy server. The proxy server will forward the client’s request to the web server. The web server will then generate a response message
and deliver it to the proxy server, which in turn sends it to the client.

2.When the proxy server gets a request, it checks if the requested object is cached  and if yes, it returns the object from the cache, without contacting the server.

3.The proxy server verifies that the cached responses are still valid (that is, haven't been updated) and that they are the correct responses to the client's requests.

4.Multiple clients can send requests at once.





