import http.server,sys,os,urllib.parse
OUT=sys.argv[1]
class H(http.server.BaseHTTPRequestHandler):
    def cors(self):
        self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Methods','POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','*');self.send_header('Access-Control-Allow-Private-Network','true')
    def do_OPTIONS(self):
        self.send_response(204);self.cors();self.end_headers()
    def do_POST(self):
        n=int(self.headers['Content-Length']);data=self.rfile.read(n)
        name=os.path.basename(urllib.parse.urlparse(self.path).path) or 'x.bin'
        open(os.path.join(OUT,name),'wb').write(data)
        self.send_response(200);self.cors();self.end_headers();self.wfile.write(b'ok %d'%n)
http.server.HTTPServer(('127.0.0.1',8765),H).serve_forever()
