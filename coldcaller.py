import re
import urllib, urllib2
import datetime
import smtplib
from email.mime.text import MIMEText

WOEID = "12758721" # http://developer.yahoo.com/geo/geoplanet/guide/concepts.html
TO_EMAIL = "bcc-mr2@lists.bostoncoop.net"
FROM_EMAIL = "c@tirl.org"
ADMIN_EMAIL = "cfd@media.mit.edu"
SUBJECT_PREFIX = "[pipe freeze]"
SERVER = "localhost"

UNITS = "f" # f: Fahrenheit, c: Celcius
WARNING_THRESHOLD = 10

API_URL = "http://weather.yahooapis.com/forecastrss?w=%(woeid)s&u=%(units)s" % \
        {'woeid': WOEID, 'units': UNITS}

temp_re = re.compile(r"""<yweather:forecast .* date="([^"]+)".* low="([^"]+)" .*\/>""")
url_re = re.compile(r"""<link>(.*)<\/link>""")

# AUTOMATICALLY SET -- DO NOT CHANGE
last_warning = ""

last_warning_re = re.compile("^last_warning = .*$")

def check_forecast_and_warn():
    forecast = urllib2.urlopen(API_URL).read()
    temps = temp_re.findall(forecast)
    url = url_re.findall(forecast)[0].split('*')[1]
    for datestr, temp in temps:
        date = datetime.datetime.strptime(datestr, "%d %b %Y")
        if int(temp) < WARNING_THRESHOLD:
            send_warning(date, temp, url)
            return

    if last_warning:
        send_all_clear(url)

def set_last_warning(value):
    with open(__file__) as this_script:
        orig_lines = this_script.readlines()

    with open(__file__, 'w') as this_script:
        lines = []
        for line in orig_lines:
            if last_warning_re.match(line):
                lines.append("last_warning = \"%s\"\n" % value)
            else:
                lines.append(line)
        this_script.write("".join(lines))

def send_warning(date, temp, url):
    set_last_warning(datetime.datetime.now())
    message = """The weather forecast calls for temperatures below %(temp)s degrees %(units)s on %(date)s.  Check the basement pipes to make sure they won't freeze!

Forecast:
%(url)s

Sincerely,
Weather Robot

(This message automatically generated.  Send complaints to %(maintainer)s)
""" % {'date': "%s %s" % (date.strftime("%A, %b"), int(date.strftime("%d"))), 
        'temp': temp, 
        'units': UNITS.upper(), 
        'url': url,
        'maintainer': ADMIN_EMAIL}
    send_email(message, "Cold weather warning!")

def send_all_clear(url):
    set_last_warning("")
    message = """We're out of cold weather danger.  The weather forecast calls for temperatures above %(temp)s degrees %(units)s.  Please check that the basement faucets are turned off.

Forecast:
%(url)s

Sincerely,
Weather Robot

(This message automatically generated.  Send complaints to %(maintainer)s)
""" % {'temp': WARNING_THRESHOLD, 'units': UNITS.upper(), 'url': url, 'maintainer': ADMIN_EMAIL }
    send_email(message, "Warmer weather on the way")

def send_email(message, subject):
    msg = MIMEText(message)
    msg['Subject'] = "%s %s" % (SUBJECT_PREFIX, subject)
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    s = smtplib.SMTP(SERVER)
    s.sendmail(FROM_EMAIL, [TO_EMAIL], msg.as_string())
    s.quit()

def send_error_report(message):
    msg = MIMEText("""%s

(Automatically generated error report for coldcaller.py script)""" % message)
    msg['Subject'] = "%s %s" % (SUBJECT_PREFIX, "ERROR")
    msg['From'] = FROM_EMAIL
    msg['To'] = ADMIN_EMAIL
    s = smtplib.SMTP(SERVER)
    s.sendmail(FROM_EMAIL, [ADMIN_EMAIL], msg.as_string())
    s.quit()

if __name__ == "__main__":
    try:
        check_forecast_and_warn()
    except Exception as e:
        send_error_report(str(e))


