#!/usr/bin/env python
'''
  A simple hijacker for recaptcha v2 and also normal captchas.
  (It was built for an development environment, where you don't want to waste money solving captchas. On production environments, I always solve it through some services like death by captcha.)
  
  It takes as parameters either the image (.jpg) to be shown on Chrome, or a file
  that contains the recaptcha v2 site key parameter.
  
  @author: Rafael Silvério Amaral
  @email:  rafael.silverio.it@gmail.com
  @github: https://github.com/rafaelsilverioit
'''

from urlparse import urlparse
from multiprocessing import Process
import BaseHTTPServer
import CGIHTTPServer
import SocketServer
import sys, getopt
import webbrowser
import time
import os
import subprocess

''' 
  Software requirements: Google Chrome, EOG and Python.
  Python libraries: urlparse, webbrowser.
'''
# Overrides do_GET from CGIHTTPRequestHandler for handle GET requests
class MyHandler(CGIHTTPServer.CGIHTTPRequestHandler, object):
  # Tries to read a key parameter
  def do_GET(self):
    try:
      query = urlparse(self.path).query
      queryComponents = dict(qc.split("=") for qc in query.split("&"))
      key = queryComponents["key"]

      self.send_response(200, 'OK')
      self.send_header('Content-type', 'text/html')
      self.end_headers()

      # Since we know the key, we can build our session and render on user browser
      recaptcha = '<!DOCTYPE html><html lang="en"><head><title>Recaptcha v2 - Hijacker</title><script>'
      recaptcha += 'function onload() {document.querySelectorAll("textarea")[0].style = "display: block; width: 100%; height: 100%;";}</script>'
      recaptcha += '</head><body onload="onload()"><form action="" method="post"><div class="g-recaptcha" data-sitekey="' + key + '"></div>'
      recaptcha += '</form><script src="https://www.google.com/recaptcha/api.js"></script></body></html>'

      self.wfile.write(recaptcha)
    except:
      self.send_response(400, 'Bad request')
      self.send_header('Content-type', 'text/html')
      self.wfile.write("<h1>400 - Bad request</h1>")
      
      self.end_headers()

# Responsible for showing EOG with the image given by the user.
class NormalCaptchaSolver():
  def __init__(self):
    pass

  def show(self, src, time):
    default = '10s'

    if(len(time) > 0):
      default = time + "s"

    p = subprocess.Popen(['/usr/bin/timeout', default, '/usr/bin/eog', os.path.expanduser(src)])

# Responsible for starting a HTTPServer used to host the hijacked session
class RecaptchaServer():
  PORT = None

  # Define the port to listen on. Assume 8000 as default if no port is specified.
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
  KEY  = None
  PORT = None

  def __init__(self, port=None):
    self.KEY  = None
    self.PORT = port

  # Read recaptcha token from file
  def readKey(self, inFile):
    if ".jpg" in inFile:
      self.KEY = inFile
      return

    raise Exception("Input file is not an jpg image: '" + inFile + "'")

  def setKey(self, key):
    self.KEY = key

  # Starts RecaptchaServer
  def start_server(self):
    # Ternary operation in Pythonic way
    webServer = RecaptchaServer() if self.PORT is None else RecaptchaServer(self.PORT)
    webServer.start()

  # Open Chrome browser to solve recaptcha
  def hijack_session(self):
    url         = "http://127.0.0.1:8000/?key=" + self.KEY
    chrome_path = "/usr/bin/google-chrome --disable-web-security --allow-file-access-from-files --allow-file-access %s"
    webbrowser.get(chrome_path).open(url)

  # Start processes: runs RecaptchaServer, wait for 3 seconds and then hijacks the captcha session.
  def hijack(self, time=None):
    if ".jpg" in self.KEY:
      captcha = NormalCaptchaSolver()
      captcha.show(self.KEY, time)
      return

    methods   = [self.start_server, self.hijack_session]
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
  key   = ''
  url   = ''
  time  = ''

  try:
    opts, args = getopt.getopt(sys.argv[1:], "fkut", ["file=", "key=", "url=", "time="])
  except:
    print 'Invalid arguments.'
    sys.exit(2)

  if len(opts) < 1:
    print 'No arguments given.'
    print 'Either use --file for an standard captcha or --key for a recaptcha token along with its domain url (--url).'
    sys.exit(2)

  for opt, arg in opts:
    if opt in ("-f", "--file"):
      ifile = arg
    elif opt in ("-k", "--key"):
      key = arg
    elif opt in ("-u", "--url"):
      url = arg
    elif opt in ("-t", "--time"):
      time = arg
    else:
      print 'Could not parse arguments.'
      sys.exit(2)

  solver = RecaptchaHijacker()

  # If we have an key, then we read it, otherwise we just set it directly, so we can check if it's a file or not.
  if len(key) <= 0:
    solver.readKey(ifile)
  else:
    solver.setKey(key)

  solver.hijack(time)

  # Waits 10 seconds before finishing all processes started in current session.
  time.sleep(10)

  solver.stop()

# THE END

