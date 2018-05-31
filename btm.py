# -*- coding:utf-8 -*-

import subprocess
import sys
import socket
import signal
import json
import threading
import select
import Queue
import time
import re
import traceback
import urllib2
g_queue = Queue.Queue()


def get_miner_data():
    url = "http://localhost:8080/api/stats"
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    rsp = response.read()
    data = json.loads(rsp)
    ret = []
    for key, val in data.items():
        hash = val.get('hashrate', 0)
        ret.append(float(hash))
    return ret


class my_miner:
    miner = None
    turn_off = False

    def start_miner(self, params):
        cmd = 'cd btm-miner; ./miner ' + params
        self.miner = subprocess.Popen(cmd, shell=True)
        while True:
            if self.turn_off: break
            try:
                ret = get_miner_data()
                g_queue.put(dict(result = ret))
            except Exception as e:
                print traceback.format_exc()
                self.check_status()
            time.sleep(10)

    def check_status(self):
        ret_code = self.miner.poll()
        if ret_code is not None:
            print 'miner status: ', ret_code
            self.stop()

    def stop(self):
        self.turn_off = True
        time.sleep(1)
        self.miner.kill()


class my_server:

    thr = None
    soc = None
    miner = None

    def init(self, miner):
        self.miner = miner
        self.thr = threading.Thread(target=self.read_write)
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        address = ('127.0.0.1', 3333)
        self.soc.bind(address)
        self.soc.listen(5)

    def read_write(self):
        while True:
            ss, addr = self.soc.accept()
            try:
                self.miner.check_status()
                ss.settimeout(5)
                buf = "{}"
                if not g_queue.empty():
                    buf = json.dumps(g_queue.get())
                ra = ss.recv(512)
                ss.send(buf)
                ss.close()
            except Exception as e:
                print e.message
        self.soc.close()

    def run(self):
        self.thr.daemon = True
        self.thr.start()

    def stop(self):
        self.thr.do_run = False
        self.soc.close()


miner = my_miner()

svr = my_server()
svr.init(miner)
svr.run()


def handler(a, b):
    svr.stop()
    miner.stop()


signal.signal(signal.SIGALRM, handler)
signal.signal(signal.SIGINT, handler)

miner.start_miner(' '.join(sys.argv[1:]))
