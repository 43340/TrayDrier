#!/usr/bin/env python

# pigpio_cgi.py
# 2015-05-04
# Public Domain

# Apache2 Instructions
#
# 1. Enable cgi
# sudo a2enmod cgid
#
# 2. Make script executable
# sudo chmod +x pigpio_cgi.py
#
# 3. Copy the script to /usr/lib/cgi-bin
# sudo cp pigpio_cgi.py /usr/lib/cgi-bin
#
# 4. Ensure the pigpio daemon is running on the Pi
#    (http://abyz.co.uk/rpi/pigpio/download.html)
# sudo pigpiod
#
# 5. Enter the url in a browser
#    (where pi is the name or IP address of the Pi)
# http://pi/cgi-bin/pigpio_cgi.py
#
# If you want to locate the file under /var/www add the
# following lines to /etc/apache2/sites-enabled/000-default.conf
# in the <Directory /var/www> section.
#    Options +ExecCGI
#    AddHandler cgi-script .py

import cgi
import subprocess

import pigpio

import cgitb   # Comment out when debugged.
cgitb.enable() # Comment out when debugged.

print("Content-type:text/html\r\n\r\n")

print("""<html><head><title>pigpio cgi</title></head><body>""")

form = cgi.FieldStorage(keep_blank_values=True)

#for k in form.keys():
#   print("<h3>{}={}</h3>".format(k, form[k].value))

pigs = ""

if "action" in form:
   action = form["action"].value
else:
   action = ""

lvl = [0]*32
mde = [0]*32

mdestr = ["Input", "Output", "Alt5", "Alt4", "Alt0", "Alt1", "Alt2", "Alt3"]
lvlstr = ["Low", "High"]

pigpio.exceptions = False # Get error code returned, not exceptions.

pi=pigpio.pi()

try:

   command = ""

   err = 0

   if "gpio" in form:
      gpio = int(form["gpio"].value)
   else:
      gpio = -1

   if action == "Low":

      err = pi.write(gpio, 0)

      command = "Low {}".format(gpio)

   if action == "High":

      err = pi.write(gpio, 1)

      command = "High {}".format(gpio)

   if action == "PWM":

      if "dc" in form:
         dc = int(form["dc"].value)
      else:
         dc = 0

      if "freq" in form:
         freq = int(form["freq"].value)
      else:
         freq = 0

      f = pi.set_PWM_frequency(gpio, freq) # returns nearest frequency

      if f >= 0:
         freq = f
         err = pi.set_PWM_dutycycle(gpio, dc)
      else:
         err = f

      command = "PWM {}/{}/{}Hz".format(gpio, dc, freq)

   if action == "Servo":

      if "pw" in form:
         pw = int(form["pw"].value)
      else:
         pw = 0

      err = pi.set_servo_pulsewidth(gpio, pw)

      command = "Servo {}/{}".format(gpio, pw)

   if action == "Mode":

      if "mode" in form:
         mode = int(form["mode"].value)
      else:
         mode = -1

      err = pi.set_mode(gpio, mode)

      command = "Mode {}/{}".format(gpio, mode)

   if action == "pigs":

      if "pigs" in form:
         pigs = (form["pigs"].value).strip()
      else:
         pigs = ""

      pigsres = subprocess.check_output(["/usr/local/bin/pigs", pigs])

      command = "pigs {}({})".format(pigs, pigsres)


   for g in range(32):
      lvl[g] = pi.read(g)
      mde[g] = pi.get_mode(g)

except:
   pass

pi.stop()

print('<table border="1" style="width:100%">')

for g in range(32):
   if (g % 6) == 0:
      print("<tr>")

   print("<td>{} {} {}</td>".format(g, lvlstr[lvl[g]], mdestr[mde[g]]))

   if (g % 6) == 5:
      print("</tr>")

print("""
</table><form method="post" action="pigpio_cgi.py">
<input type="submit" value="Refresh" name="action">
</form>""")

print("""<hr><form method="post" action="pigpio_cgi.py">
   <table border="1">
   <tr>
   <td>
      gpio <input type="number" name="gpio" min="0" max="31" value="4">
      <small>Select a gpio and then an action<br>
      (entering any parameters first).</small>
   </td>
   <td><small>
      <input type="submit" value="Mode" name="action">
      <input type="radio" name="mode" value="0" checked>Input
      <input type="radio" name="mode" value="1">Output
      <input type="radio" name="mode" value="4">Alt0
      <input type="radio" name="mode" value="5">Alt1
      <input type="radio" name="mode" value="6">Alt2
      <input type="radio" name="mode" value="7">Alt3
      <input type="radio" name="mode" value="3">Alt4
      <input type="radio" name="mode" value="2">Alt5
   </small></td>
   </tr>
   <tr>
   <td><input type="submit" value="Low" name="action"></td>
   <td><input type="submit" value="High" name="action"></td>
   </tr>
   <tr>
   <td>
   <input type="submit" value="PWM" name="action">
    duty cycle <input type="number" name="dc" min="0" max="255" value="0">
    frequency <input type="number" name="freq" min="0" max="50000" value="0">
   </td>
   <td>
   <input type="submit" value="Servo" name="action">
    pulse width <input type="number" name="pw" min="0" max="2500" value="0">
   </td>
   </tr>
   </table>
</form>
""")

print("""<hr><form method="post" action="pigpio_cgi.py">
<table><tr>
<td><input type="submit" value="pigs" name="action"></td>
<td><textarea name="pigs"></textarea></td>
<td>Enter pigs commands in the text box and press the pigs button to submit.
<br>E.g. <b>pud 11 d</b> to set the internal pull-down on gpio 11.</td>
</tr></table>
</form><hr>""")

if err < 0:
   command = command + ' <span style="color:red">(Error: {})</span>'.format(pigpio.error_text(err))

if command != "":
   print("<br>Last command: " + command)

print("</body></html>")
