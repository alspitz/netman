#!/usr/bin/python

import os
import signal
import sys
import time

class NetMan(object):
  SCAN_CMD = "iw wlan0 scan | grep SSID"
  SSIDS = ["2.4G", "eduroam", "RedRover", "Courtyard_GUEST", "FairfieldInn_Guest", "si-visitor", "Fairfield_GUEST", "HolidayInn", "Super 8", "CUAUV-SOFTWARE", "OCH214\\x20", "capri", "SpaceX Guest"]
  configs = ["home", "eduroam", None, None, None, None, None, None, None, "CUAUV-SOFTWARE", "oakwood", "hotspot", None]
  interface = "wlan0"
  def __init__(self):
    self.encrypted = False
    self.config_map = { k : value for (k, value) in zip(self.SSIDS, self.configs) }
    self.reset_state()

  def reset_state(self):
    self.connected = None
    self.better = self.SSIDS

  def get_visible_ssids(self):
    os.system("ip link set %s up" % self.interface)
    scan_out = os.popen(self.SCAN_CMD).read()
    print scan_out
    ssids = [line.strip().split("SSID: ")[1::2] for line in scan_out.split(os.linesep)]
    print ssids
    return [ssid[0] for ssid in ssids if len(ssid)]

  def connect(self, name):
    print "Trying to connect to %s..." % name
    if self.connected is not None:
      self.network_off()

    if self.config_map[name] is not None:
      self.connect_encrypted(name)
    else:
      self.connect_open(name)

    os.system("dhcpcd -L %s" % self.interface)

    self.connected = name
    self.better = self.SSIDS[:self.SSIDS.index(name)]
    print "Connected to %s." % name

  def connect_encrypted(self, name):
    os.system("wpa_supplicant -B -Dnl80211 -i%s -c/etc/sysconfig/wpa_supplicant-%s.conf" % (self.interface, self.config_map[name]))
    self.encrypted = True

  def connect_open(self, name):
    os.system("iw %s connect \"%s\"" % (self.interface, name))

  def network_off(self):
    print "Killing network."
    if self.encrypted:
      os.system("pkill -f wpa_supplicant")
      self.encrypted = False
    else:
      os.system("iw %s disconnect" % self.interface)

    os.system("pkill -f dhcpcd")
    self.reset_state()

  def run(self):
    while 1:
      print "scanning..."
      visible_ssids = self.get_visible_ssids()
      if self.connected not in visible_ssids:
        candidates = self.SSIDS
      else:
        candidates = self.better

      print visible_ssids

      for ssid in candidates:
        if ssid in visible_ssids:
          self.connect(ssid)
          break

      if self.connected and not self.encrypted:
        # This is in case of the dreaded "Calling CRDA to update world
        # regulatory domain" event which disassociates from the AP.
        self.connect_open(self.connected)

      time.sleep(5)

  def cleanup(self):
    self.network_off()
    sys.exit(0)

if __name__ == "__main__":
  netman = NetMan()

  signals = [signal.SIGINT, signal.SIGTERM]
  [signal.signal(s, lambda x, y: netman.cleanup()) for s in signals]

  netman.run()
