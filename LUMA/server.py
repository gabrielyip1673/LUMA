#!/usr/bin/env python3
"""
LUMA live-reload server with task inbox API.

Endpoints:
  GET  /                - serves LUMA.html with live-reload script
  GET  /__version       - returns md5 of LUMA.html (used for reload polling)
  POST /api/inbox       - queues tasks uploaded by the luma plugin
  GET  /api/inbox       - returns and clears pending tasks (LUMA polls this)

Run: python3 server.py  →  http://localhost:3000
"""
import http.server, hashlib, json, os, threading

PORT = 3000
HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, 'LUMA.html')
TOKEN_FILE = os.path.join(HERE, '.luma_token')

def load_token():
    env = os.environ.get('LUMA_TOKEN')
    if env:
        return env.strip()
    try:
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    except Exception:
        return ''

API_TOKEN = load_token()

INBOX_LOCK = threading.Lock()
INBOX = []  # list of task dicts, drained by GET /api/inbox

RELOAD_SCRIPT = b'''<script>
(function(){
  var _h='';
  setInterval(function(){
    fetch('/__version?_='+Date.now())
      .then(function(r){return r.text();})
      .then(function(v){ if(_h && v!==_h){ location.reload(); } _h=v; })
      .catch(function(){});
  }, 500);
})();
</script>'''


def file_hash():
    try:
        with open(FILE, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return ''


class Handler(http.server.BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def _check_auth(self):
        if not API_TOKEN:
            return True  # no token configured -> open
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Bearer ') and auth[7:].strip() == API_TOKEN:
            return True
        self._json(401, {'error': 'unauthorized: missing or invalid bearer token'})
        return False

    def do_POST(self):
        path = self.path.split('?')[0]
        if path == '/api/inbox':
            if not self._check_auth():
                return
            length = int(self.headers.get('Content-Length', '0') or 0)
            try:
                data = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            except Exception as e:
                self._json(400, {'error': f'bad json: {e}'})
                return
            tasks = data.get('tasks') or []
            if not isinstance(tasks, list):
                self._json(400, {'error': 'tasks must be a list'})
                return
            with INBOX_LOCK:
                INBOX.extend(tasks)
            self._json(200, {'queued': len(tasks)})
        else:
            self.send_response(404); self.end_headers()

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/__version':
            v = file_hash().encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', str(len(v)))
            self.end_headers()
            self.wfile.write(v)
        elif path == '/api/inbox':
            with INBOX_LOCK:
                drained = INBOX[:]
                INBOX.clear()
            self._json(200, {'tasks': drained})
        elif path in ('/', '/LUMA.html'):
            try:
                with open(FILE, 'rb') as f:
                    body = f.read()
                body = body.replace(b'</body>', RELOAD_SCRIPT + b'</body>', 1)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500); self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404); self.end_headers()

    def log_message(self, fmt, *args):
        pass


print(f'LUMA server → http://localhost:{PORT}')
print(f'  HTML:  {FILE}')
print(f'  Inbox: POST /api/inbox, GET /api/inbox')
print(f'  Auth:  {"bearer token required (from " + (".luma_token" if not os.environ.get("LUMA_TOKEN") else "LUMA_TOKEN env") + ")" if API_TOKEN else "OPEN (no token set)"}')
print('Press Ctrl+C to stop.\n')
http.server.HTTPServer(('', PORT), Handler).serve_forever()
