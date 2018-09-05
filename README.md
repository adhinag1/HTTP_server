# HTTP_server
This is a simple multi-threaded HTTP server build using sockets. The interaction between client and server is through sockets. This server supports only GET requests and maintains the server access details for the admin to view at any time(no authorization). The access details will be persisted even though the server is restarted or crashed. Server will return the precise response for the request made by the user. If the request is invalid or unauthorized, server will give the exact reason for the denial. Also, we can view the access details in a HTML view.

## How to use the HTTP server
Steps:

1) Execute the server script ./server inside the HTTP_server folder.
2) Host and Port information will be displayed when the server is started.
3) With the above information users can access the following URL's via web browser, wget or any REST client:
   http://<hots_name>:<port>/www/server.html,
   http://<hots_name>:<port>/www/pdf_sample.pdf,
   http://<hots_name>:<port>/www/lena_sdf.tif,
   http://<hots_name>:<port>/www/skype-ubuntu.deb
 4) To view server access list:
   http://<hots_name>:<port>/www/access_entries.html
 5) stop the server using ctrl+c
