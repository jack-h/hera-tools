"""
A simple script for reading data from
a Newmar SPM-200 power monitor.
This code uses the ability to grab an XML
representation of logger data over http,
and spits this data into a local ascii
log file.
"""



import requests
import xml.etree.ElementTree as ET
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO)

def get_vals(host):
    req = requests.get('http://%s/data.xml' % host, auth=('Admin', 'admin'))
    if not req.ok:
        return None
        logging.error("http request failed!")
    else:
        root = ET.fromstring(req.text)

        monitor_vals = {}
        # Clearly I don't really know how to use XML
        for child in root:
            if child.tag == 'devices':
                for device in child:
                    for field in device:
                        monitor_vals[field.attrib['key']] = field.attrib['value']
        return monitor_vals

def d2str(d, key_order):
    s = ''
    for key in key_order:
        s += d[key] + " "
    return s[:-1] #hack off the last space

def write_header(fh, keys):
    fh.write("Time ")
    for key in keys:
        fh.write("%s " % key)
    fh.write("\n")

def newfile(fh, name, number, header_keys):
    if fh:
        fh.close()
    fname = '%s.%d.%d' % (name, int(time.time()), number)
    logging.info("Opening File %s" % fname)
    fh = open(fname, 'w')
    write_header(fh, header_keys)
    return fh

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--filename", type=str, default="/tmp/power.log",
                   help="filename to dump log to. Default /tmp/power.log")
parser.add_argument("-t", "--polltime", type=float, default=5.0,
                   help="Poll time, in seconds (float). Default 5s")
parser.add_argument("-f", "--filetime", type=float, default=60*60*24,
                   help="Time for one output file, in seconds (float). Default 1hr")
parser.add_argument("--hostname", type=str, default="10.0.1.100",
                   help="Hostname / IP of monitor unit (string). Default '10.0.1.100'")
args = parser.parse_args()

# Get values once to figure out what the dictionary keys are
vals = get_vals(args.hostname)
if vals is None:
    exit()
else:
    dict_keys = vals.keys()

file_num = 0
fh = newfile(None, args.filename, file_num, dict_keys)
filetime = time.time()

while True:
    monitor_vals = get_vals(args.hostname)
    if monitor_vals is None:
        logging.error("Couldn't get data!")
        continue
    fh.write("%.2f %s\n" % (time.time(), d2str(monitor_vals, dict_keys)))
    if time.time() - filetime > args.filetime:
        file_num += 1
        fh = newfile(fh, args.filename, file_num, dict_keys)
        filetime = time.time()
    logging.info("Got new data")
    time.sleep(args.polltime)



