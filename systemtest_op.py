import time
from neopixel import *
import argparse
import sqlite3
import io
from threading import Timer,Thread,Event

fadePeriod = 0.01
oldPid = 0
newLine=""

conn = sqlite3.connect('/var/www/html/db/pixelAtmosphere.db')
conn.text_factory = bytes
c = conn.cursor()


# LED strip configuration:
c.execute("SELECT setting FROM settings WHERE property='LED_COUNT'")
LED_COUNT      = c.fetchone()[0]      # Number of LED pixels.

c.execute("SELECT setting FROM settings WHERE property='LED_PIN'")
LED_PIN        = c.fetchone()[0]      # GPIO pin connected to the pixels (18 uses PWM!).

#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).

c.execute("SELECT setting FROM settings WHERE property='LED_FREQ_HZ'")
LED_FREQ_HZ    = c.fetchone()[0] # LED signal frequency in hertz (usually 800khz)

c.execute("SELECT setting FROM settings WHERE property='LED_DMA'")
LED_DMA        = c.fetchone()[0]      # DMA channel to use for generating signal (try 10)

c.execute("SELECT setting FROM settings WHERE property='LED_BRIGHTNESS'")
desiredBrightness = c.fetchone()[0]     # Set to 0 for darkest and 255 for brightest

c.execute("SELECT setting FROM settings WHERE property='LED_INVERT'")
LED_INVERT     = c.fetchone()[0]   # True to invert the signal (when using NPN transistor level shift)

c.execute("SELECT setting FROM settings WHERE property='LED_CHANNEL'")
LED_CHANNEL    = c.fetchone()[0]       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_TYPE       = ws.WS2811_STRIP_GRB
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, 0, LED_CHANNEL)
# Intialize the library (must be called once before other functions).
strip.begin()
print("LEDS:\t" + str(LED_COUNT))
print("PIN:\t" + str(LED_PIN))
print("HZ:\t" + str(LED_FREQ_HZ))
print("DMA:\t" + str(LED_DMA))
#print("BRIGHT:\t" + str(LED_BRIGHTNESS))
print("INVERT:\t" + str(LED_INVERT))
print("CHNL:\t" + str(LED_CHANNEL))

def goToBrightness():
	currentStripB = strip.getBrightness()
	if currentStripB != desiredBrightness:
		amount = 1 if desiredBrightness > currentStripB else -1
		amount = 0 if desiredBrightness == currentStripB else amount
		newB = currentStripB+amount
		strip.setBrightness(newB);



def section(i,j):
    strip.setPixelColor(i,Color(0,255,0))
    for x in range(i+1,j):
        strip.setPixelColor(x,Color(255,0,0))
    strip.setPixelColor(j,Color(0,255,0))
    strip.show()

def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        time.sleep(wait_ms/1000.0)

def rgbToChar(x):
	return chr(int(x[0:3])) + chr(int(x[4:7])) + chr(int(x[8:11]))


#colorWipe(strip, 0)
prevTime = time.time()
while True:
	strip.show()
	refresh = False
	c.execute("SELECT setting FROM settings WHERE property='LED_BRIGHTNESS'")
	b = c.fetchone()[0]
	strip.show()
	c.execute("SELECT status FROM current where id=1")
	s = c.fetchone()[0]
	desiredBrightness = b*s
	strip.show()

	print("desired:",desiredBrightness)
	print("current:",strip.getBrightness())

	print("BRIGHT\t" + str(desiredBrightness))
	strip.show()
	c.execute("SELECT pid, time  FROM current WHERE id='1'")
	strip.show()
	res = c.fetchone()
	strip.show()
	currentProfile=res[0]
	strip.show()
	lastUpdated = res[1]
	print("PID:\t" + str(currentProfile))

	strip.show()
	c.execute("SELECT data,period,optimized FROM profiles WHERE pid=?", (currentProfile,))
	strip.show()
	result = c.fetchone()
	strip.show()
	if(result[2] != 1):
		colorWipe(strip, 0, 0)
		profileData = result[0].splitlines()
		line = list()
		strip.setPixelColor(428, Color(0, 150, 255))
		for x in profileData:
			strip.show()
			led = ""
			for i in range(0, len(x)/12 + 1):
				j = i*12
				led += str(rgbToChar(x[j:j+11]))
			line.append(led)
		opSeq = "[EndOfFrame]".join(line)
		c.execute("UPDATE profiles SET data=?, optimized='1' WHERE pid=?", (opSeq,currentProfile))
		conn.commit()
		print("Should've updated")
		continue
	strip.show()
	profileData = result[0].split("[EndOfFrame]")
	strip.show()
	timing = result[1]
	print("FPS:\t" + str(1/timing))
	while refresh == False:
		#periods = list()
		periodPrevTime = time.time()
		periodCurTime = 0
		for x in profileData:

			compPrev=time.time()
			for i in range(0, len(x)/3):
				j=i*3
				strip.setPixelColor(i, Color(ord(x[j]),ord(x[j+1]),ord(x[j+2])))
			currentTime = time.time()
			if currentTime > (prevTime + 2):
				#print("FPS: " + str(1/(sum(periods)/len(periods))));
				#periods = list()
				prevTime = currentTime
				c.execute("SELECT time FROM current WHERE id='1'")
				curTime = c.fetchone()[0]
				if curTime > lastUpdated:
					print("\nNew values:")
					refresh = True
					break
			if (currentTime > (prevTime + fadePeriod)):
				if strip.getBrightness != desiredBrightness:
					goToBrightness()
			strip.show()
			delay=timing-(time.time()-compPrev)
			time.sleep(delay if delay>0 else 0)
			periodCurTime = time.time()
			#periods.append(periodCurTime - periodPrevTime)
			periodPrevTime = time.time()

