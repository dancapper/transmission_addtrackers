#!/usr/bin/python

###
### transmission_addtrackers.py
###
### A simple script to add a list of trackers to every torrent
### Requires transmissionrpc - can be installed with:
### > easy_install transmissionrpc
###
### Provided as-is where-is.  Use at your own risk + please don't ask me for support :)
###
### Copyright 2016 Dan Capper <dan@hopfulthinking.com>
###
### Licensed under the Apache License, Version 2.0 (the "License");
### you may not use this file except in compliance with the License.
### You may obtain a copy of the License at
###
###    http://www.apache.org/licenses/LICENSE-2.0
###
### Unless required by applicable law or agreed to in writing, software
### distributed under the License is distributed on an "AS IS" BASIS,
### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
### See the License for the specific language governing permissions and
### limitations under the License.
###

import transmissionrpc
from syslog import syslog
import sys
import os
import fcntl

### Set these as you require ###

host = "localhost"   # Transmission host
port = 9091          # port
user = ""            # auth user
password = ""        # auth password
timeout = 30         # timeout to make the connection
trackersToAdd = [u"http://example.com/announce",u"udp://www.something.com:6969/announce"] # put your trackers here

debug = False        # set to true for more syslog
lockFilePath = "/var/run/lock" # usually you won't need to change this

### Don't edit below this line ###

fp = None
lockfile = "{0}/{1}".format(lockFilePath, os.path.basename(__file__))

def lockFile():
    global fp, lockfile
    try:
        fp = open(lockfile, 'w')
    except IOError:
        msgString = "Could not open lockfile {0} - exiting...".format(lockfile)
        syslog(msgString)
        sys.exit(msgString) # Unable to open lock
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError:
        return False

if not lockFile():
    msgString = "Could not get lock on {0} - process already running?".format(lockfile)
    syslog(msgString)
    sys.exit(msgString) # Could not get lock

msgString = "Connecting to Transmission at {0}:{1}".format(host, port)
print(msgString)        
if debug: syslog(msgString)
try:
    tc = transmissionrpc.Client(host, port=port, user=user, password=password, timeout=timeout)
except transmissionrpc.error.TransmissionError as err:
    errstring = "Unable to connect to {1}, error was: [{0}] - Exiting".format(err, host)
    syslog(errstring)
    sys.exit(errstring)
except:
    errstring = "Unexpected error {0} connecting to host".format(sys.exc_info()[0])
    syslog(errstring)
    raise

torrents = tc.get_torrents(arguments=["id", "name", "trackers"])

countString = "Total number of Torrents: {0}".format(len(torrents))
print(countString)
if debug: syslog(countString)

for torrent in torrents:
    torrentID = getattr(torrent,"id")
    trackers = getattr(torrent,"trackers")
    name = getattr(torrent,"name")
    msgstring = "Torrent id: [{0}] [{2}] has [{1}] trackers".format(torrentID,len(trackers),name)
    print(msgstring)
    if debug: syslog(msgstring)
    trackersToAddFiltered = list(trackersToAdd)
    for tracker in trackers:
        if tracker[u'announce'] in trackersToAddFiltered:
                trackersToAddFiltered.remove(tracker[u'announce'])

    if len(trackersToAddFiltered) > 0:
        msgString = "Adding {0} trackers to {1}".format(len(trackersToAddFiltered),name)
        print(msgString)
        syslog(msgString)
        tc.change_torrent(torrentID, trackerAdd=trackersToAddFiltered)
        torrent.update()
        trackers = getattr(torrent,"trackers")
        msgString = "Torrent id: [{0}] [{2}] has [{1}] trackers".format(torrentID,len(trackers),name)
        print(msgString)
        if debug: syslog(msgString)
