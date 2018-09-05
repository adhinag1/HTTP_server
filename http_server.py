import collections
import datetime
import json
import mimetypes
import os
import socket
import threading

allowed_path = ['/www/server.html', '/www/pdf_sample.pdf', '/www/lena_std.tif',
                '/www/skype-ubuntu.deb', '/www/access_list.txt']
is_socket_open = True


def read_data():
    """Reads the access entry data from the file once the server is started"""

    if os.path.isfile(os.getcwd() + "/www/access_list.txt") and os.stat(os.getcwd() + "/www/access_list.txt").st_size != 0:
        data = json.load(open(os.getcwd() + "/www/access_list.txt"))
        return collections.defaultdict(dict, data)
    else:
        return collections.defaultdict(dict)


def write_data(data):
    """
    Writes access entries into the file
    :param data:
    :return:
    """

    db = open(os.getcwd() + "/www/access_list.txt", 'w')
    json.dump(dict(data), db)


def collect_request_data(request_path, request_address):
    """
    Formats the data which is to be written into the file
    :param request_path:
    :param request_address:
    :return:
    """

    def is_entry_exist(path, address):
        is_exist = False

        if path in access_entries:
            if address[0] + "-" + str(address[1]) in access_entries[path]:
                is_exist = True

        return is_exist

    if is_entry_exist(request_path, request_address):
        access_entries[request_path][request_address[0] + "-" + str(request_address[1])] \
            = int(access_entries[request_path][request_address[0] + "-" + str(request_address[1])]) + 1
    else:
        access_entries[request_path][request_address[0] + "-" + str(request_address[1])] = 1


def parse_request(client_connection):
    """
    Parses incoming request
    Returns request parameters and request data if the request is valid or returns empty data
    :param client_connection:
    :return:
    """

    request_data = client_connection.recv(1024)
    try:
        parsed_request = request_data.split('\r\n')
        request_method, request_path, request_proto = parsed_request[0].split(' ', 3)
        if request_path[-1] == '/' and len(request_path) > 1:
            request_path = request_path[:-1]
        return request_method, request_path, request_proto, request_data
    except:
        return '', '', '', ''


def request_handler(client_connection, request_path, request_proto, response_code, response_string, response_body,
                    is_request_valid):
    """
    Receives the parsed request info. and forms response headers and sends the response
    :param client_connection:
    :param request_path:
    :param request_proto:
    :param response_code:
    :param response_string:
    :param response_body:
    :param is_request_valid:
    :return:
    """

    response_headers = {}
    client_connection.send_header('Access-Control-Allow-Origin', '*')
    client_connection.send("%s %s %s\r\n" % (request_proto, response_code, response_string))

    if is_request_valid:
        response_headers['Date'] = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S %Z')
        response_headers['Last-Modified'] = datetime.datetime.fromtimestamp(
            int(os.path.getmtime(os.getcwd() + request_path))).strftime('%a, %d %b %Y %H:%M:%S %Z')
        response_headers['Server'] = 'bing_2.0 (Unix)'
        response_headers['Content-Length'] = os.path.getsize(os.getcwd() + request_path)
        response_headers['Content-Type'] = mimetypes.guess_type(os.getcwd() + request_path)[0]
        if request_path == '/www/access_list.txt':
            response_headers['Content-Type'] = 'text/html'
        if response_headers['Content-Type'] is None:
            response_headers['Content-Type'] = 'application/octet-stream'
        client_connection.send(''.join('%s: %s\n' % (k, v) for k, v in response_headers.iteritems()))

    client_connection.send("\n")
    client_connection.send(response_body)


def construct_access_entries_data():
    """Builds the view of the access entries page"""

    final_tag = '<html><head><style>table, th, td {border: 1px solid black;}</style></head><body><table><tr><th>Path</th><th>Host-Port - Count</th></tr> '
    for i, j in access_entries.iteritems():
        final_tag += '<tr><td>' + i + '</td><td>'
        for k, v in j.iteritems():
            final_tag += '<span>' + k + ' - ' + str(v) + '</span><br/>'
        final_tag += '</td></tr>'
    final_tag += '</table></body></html>'
    return final_tag


def threading_handler(client_connection, client_address):
    """
    Handles the threads and its processes.
    :param client_connection:
    :param client_address:
    :return:
    """

    while True:
        request_method, request_path, request_proto, request_data = parse_request(client_connection)

        if not request_data:
            break

        collect_request_data(request_path, client_address)
        write_data(access_entries)

        if request_method == 'GET':
            if request_path in allowed_path:
                requested_file = open(os.getcwd() + request_path, 'rb')
                data = requested_file.read(os.path.getsize(os.getcwd() + request_path))
                requested_file.close()
                request_handler(client_connection, request_path, request_proto, '200', 'OK', data, True)
                break
            elif '/www' == request_path or '/' == request_path:
                request_handler(client_connection, request_path, request_proto, '403', 'Forbidden', '403 Unauthorized',
                                False)
                break
            elif '/www/access_entries.html' == request_path:
                final_tag = construct_access_entries_data()
                request_handler(client_connection, '/www/access_list.txt', request_proto, '200', 'OK', final_tag, True)
                break
            else:
                request_handler(client_connection, request_path, request_proto, '404', 'Not found', '404 Not Found',
                                False)
                break
        else:
            request_handler(client_connection, request_path, request_proto, '405', 'Method Not Allowed',
                            '405 Method Not Allowed', False)

    client_connection.close()
    print (" --- Connection Closed --- ", client_address)


if not os.path.isdir(os.getcwd() + '/www'):
    print "\nResource Temporarily Unavailable\n"
    is_socket_open = False
else:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 8080))
    server_socket.listen(5)
    access_entries = read_data()
    print ("\nServer running on Host -- %s -- on Port -- %s --\n" % (str(socket.gethostname()), str(8080)))

try:
    while is_socket_open:
        print '\nWaiting for connection... Listening on port 8080\n'
        client_connection, client_address = server_socket.accept()
        print '\nConnected from:\n', client_address
        t = threading.Thread(target=threading_handler, args=(client_connection, client_address,))
        print ("\nThread Name: %s \n" % t.getName())
        t.setDaemon(True)
        t.start()

except KeyboardInterrupt:
    print "\nServer Stopped.....\n"
    server_socket.close()