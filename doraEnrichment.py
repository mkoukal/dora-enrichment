from http.server import HTTPServer, BaseHTTPRequestHandler
from line_protocol_parser import parse_line
import json
import sys
import re
import os
import requests

def sendToTelegraf(line_protocol):
    try:
        telegrafurl=os.environ.get('TELEGRAF_URL')
        x = requests.post(telegrafurl, data=line_protocol)
    except:
        print('ERROR Telegraf not accessible')


def parseInput(inputData):
    valsAndTimestamp=inputData.decode('utf-8').split(" ", 1)[1]
    if valsAndTimestamp.endswith("'"):
        valsAndTimestamp = valsAndTimestamp[:-1]
        
    data = parse_line(inputData.decode('utf-8'))    
    ini_string = json.dumps(data)    
    resp = json.loads(ini_string)
        
    if str(resp['tags']['component']).startswith("k8s-"):
        component=str(resp['tags']['component'])[4:]
    else:
        component=str(resp['tags']['component'])
    try:
        configPath=os.environ.get('CFGFILE')
        file = open(configPath, "r")
        for line in file:
            if re.search(component, line):
                additional_data=line.split(":")
                resp['tags']['tribe']=additional_data[0]
                resp['tags']['squad']=additional_data[1]
                resp['tags']['application']=additional_data[2]
                resp['tags']['eamApplication']=additional_data[2]
                resp['tags']['component']=component
        file.close()
        final_measurement=""
        #final_measurement+=resp['measurement']+","
        final_measurement+="dora_metrics,"
        final_measurement+=str(json.dumps(resp['tags'],separators=(",", "="))).strip('{').strip('}').replace('"','').replace(' ','\ ') + " "
        final_measurement+=' ' + valsAndTimestamp
    except:
        final_measurement=inputData.decode('utf-8')
    return final_measurement


class Serv(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        

    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        try:
            file_to_open = open(self.path[1:]).read()
            self.send_response(200)
        except:
            file_to_open = "File not found"
            self.send_response(404)
        self.end_headers()
        self.wfile.write(bytes(file_to_open, 'utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        final_measurement=parseInput(post_data)
        self._set_response()
        self.wfile.write(final_measurement.encode('utf-8'))
        sendToTelegraf(final_measurement)


def run(server_class=HTTPServer, handler_class=Serv, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
