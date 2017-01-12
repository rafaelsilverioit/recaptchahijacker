#!/usr/bin/env python
from urlparse import urlparse
from multiprocessing import Process
import BaseHTTPServer
import CGIHTTPServer
import SocketServer
import sys, getopt
import webbrowser
import time

# Overrides do_GET from CGIHTTPRequestHandler for handle GET requests
class MyHandler(CGIHTTPServer.CGIHTTPRequestHandler, object):
  # Tries to read a key parameter
  def do_GET(self):
    try:
      query = urlparse(self.path).query
      queryComponents = dict(qc.split("=") for qc in query.split("&"))
      key = queryComponents["key"]

      # Since we know the key, we can build our session and render on user browser
      recaptcha = '<!DOCTYPE html><html lang="en"><head><title>Recaptcha v2 - Hijacker</title><script>'
      recaptcha += 'function onload() {document.querySelectorAll("textarea")[0].style = "display: block; width: 100%; height: 100%;";}</script>'
      recaptcha += '</head><body onload="onload()"><form action="" method="post"><div class="g-recaptcha" data-sitekey="' + key + '"></div>'
      recaptcha += '</form><script src="https://www.google.com/recaptcha/api.js"></script></body></html>'

      self.wfile.write(recaptcha)
    except:
      self.wfile.write("<h1>400 - Bad request</h1>")

# Responsible for starting a HTTPServer used to host the hijacked session
class RecaptchaServer():
  PORT = None

  # Define the port to listen on
  def __init__(self, port=8000):
    self.PORT = port

  # Start a HTTPServer
  def start(self):
    server = BaseHTTPServer.HTTPServer
    server_addr = ("", self.PORT)

    httpd = BaseHTTPServer.HTTPServer(server_addr, MyHandler)
    httpd.handle_request()

# Responsible for hijacking user session
class RecaptchaHijacker():
  KEY = None

  def __init__(self):
    self.KEY = None

  # Read recaptcha token from file
  def readKey(self, inFile):
    with open(inFile, 'r') as f:
      self.KEY = f.readline()

  # Starts RecaptchaServer
  def start_server(self):
    webServer = RecaptchaServer()
    webServer.start()

  # Open Chrome browser to solve recaptcha
  def hijack_session(self):
    url = "http://127.0.0.1:8000/?key=" + self.KEY
    chrome_path = "/usr/bin/google-chrome %s"
    webbrowser.get(chrome_path).open(url)

  # Start processes: runs RecaptchaServer, wait for 3 seconds and then hijacks the captcha session.
  def hijack(self):
    methods = [self.start_server, self.hijack_session]
    processes = []

    for method in methods:
      time.sleep(3)
      p = Process(target=method)
      p.start()
      processes.append(p)

    return processes

  # Stop processes
  def stop(self, processes=[]):
    for p in processes:
      p.join()

# Runs the program
if __name__ == "__main__":
  ifile = ''

  try:
    opts, args = getopt.getopt(sys.argv[1:], "hi", ["ifile="])
  except:
    print 'Invalid argument'
    sys.exit(2)

  if len(opts) < 1:
    print 'Invalid argument'
    sys.exit(2)

  for opt, arg in opts:
    if opt in ("-i", "--ifile"):
      ifile = arg
    else:
      print 'Invalid argument'
      sys.exit(2)

  solver = RecaptchaHijacker()
  solver.readKey(ifile)
  solver.hijack()

  time.sleep(10)

  solver.stop()

# THE END
