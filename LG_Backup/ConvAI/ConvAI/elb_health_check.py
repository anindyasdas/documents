import getopt
import http.server
import socketserver
import sys
from functools import partial

"""
reference :
https://stackabuse.com/serving-files-with-pythons-simplehttpserver-module/

Usage :
nohup python3 elb_health_check.py -u <path> -p <port> &
<example>
nohup python3 elb_health_check.py -u aiefw_alive 8787 &
nohup python3 elb_health_check.py -u pcc_alive 8787 &

http.server need python 3.x
"""


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, uri, *args, **kwargs):
        self.uri = uri
        super().__init__(*args, **kwargs)

    def do_GET(self):
        print(self.uri)
        if self.path == '/' + self.uri + '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
        else:
            self.send_response(404)


def main(argv):
    # default value
    port = 8787
    uri = 'aiefw_alive'

    # parse uri and port
    argv = argv[1:]
    try:
        opts, args = getopt.getopt(argv, "hu:p:", ["uri=", "port="])
    except getopt.GetoptError:
        print('elb_health_check.py -u <uri> -p <port>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('elb_health_check.py -u <uri> -p <port>')
            sys.exit()
        if opt in ("-u", "--uri"):
            uri = arg
        elif opt in ("-p", "--port"):
            port = int(arg)
    print(f"Health check: {uri}:{port}")

    # Create an object of the above class using partial for parameter uri
    handler_object = partial(MyHttpRequestHandler, uri)

    # server start SO_REUSEADDR
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(('', port), handler_object)
    server.serve_forever()


if __name__ == '__main__':
    main(sys.argv)
