# ON AIR sign for Royals
# Runs on Airlift Metro M4 with 64x32 RGB Matrix display & shield

import time
import board
import displayio
from digitalio import DigitalInOut
import busio
import neopixel
import adafruit_display_text.label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.polygon import Polygon
from adafruit_bitmap_font import bitmap_font
# from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

status_light = neopixel.NeoPixel(
    board.NEOPIXEL, 1, brightness=0.2
)

wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)
# Set up where we'll be fetching data from
# Adafruit YouTube channel:
FEED_ID = (
   # "UCpOlOeQjj7EsVnDh3zuCgsA"  # this isn't a secret but you have to look it up
   "royalsonair"
)
# adaFruit_token="aio_fGcU92S58NEZ8pdntqhTIlVFyr7z"


DATA_SOURCE = (
    "https://io.adafruit.com/api/v2/bigredreevz/feeds?x-aio-key="
    + secrets["aio_key"]
    + "&feed_key="
    + FEED_ID
    
)
DATA_LOCATION1 = [0,'last_value']
#DATA_LOCATION1 = ["regionCode"]

# Number of seconds between checking, if this is too quick the query quota will run out
UPDATE_DELAY = 1

# Times are in 24-hour format for simplification
OPERATING_TIME_START = "02:00:00"  # what hour to start checking
OPERATING_TIME_END = "23:59:59"  # what hour to stop checking

# --- Display setup ---
matrix = Matrix()
display = matrix.display
## network = Network(status_neopixel=board.NEOPIXEL, debug=False) ## OLD LOGIG FOR STATUS

# --- Drawing setup ---
# Create a Group
group = displayio.Group(max_size=22)
# Create a bitmap object
bitmap = displayio.Bitmap(64, 32, 2)  # width, height, bit depth
# Create a color palette
color = displayio.Palette(5)
color[0] = 0x000000  # black
color[1] = 0xFF0000  # red
color[2] = 0x444444  # dim white
color[3] = 0xDD8000  # gold
color[4] = 0x002366  # baby blue
# Create a TileGrid using the Bitmap and Palette
tile_grid = displayio.TileGrid(bitmap, pixel_shader=color)
# Add the TileGrid to the Group
group.append(tile_grid)

# draw the frame for startup
rect1 = Rect(0, 0, 2, 32, fill=color[2])
rect2 = Rect(62, 0, 2, 32, fill=color[2])
rect3 = Rect(2, 0, 9, 2, fill=color[0])
rect4 = Rect(53, 0, 9, 2, fill=color[0])
rect5 = Rect(2, 30, 12, 2, fill=color[0])
rect6 = Rect(50, 30, 12, 2, fill=color[0])

group.append(rect1)
group.append(rect2)
group.append(rect3)
group.append(rect4)
group.append(rect5)
group.append(rect6)


def redraw_frame():  # to adjust spacing at bottom later
    rect3.fill = color[2]
    rect4.fill = color[2]
    rect5.fill = color[2]
    rect6.fill = color[2]


# draw the wings w polygon shapes
wing_polys = []

wing_polys.append(Polygon([(3, 3), (9, 3), (9, 4), (4, 4)], outline=color[1]))
wing_polys.append(Polygon([(5, 6), (9, 6), (9, 7), (6, 7)], outline=color[1]))
wing_polys.append(Polygon([(7, 9), (9, 9), (9, 10), (8, 10)], outline=color[1]))
wing_polys.append(Polygon([(54, 3), (60, 3), (59, 4), (54, 4)], outline=color[1]))
wing_polys.append(Polygon([(54, 6), (58, 6), (57, 7), (54, 7)], outline=color[1]))
wing_polys.append(Polygon([(54, 9), (56, 9), (55, 10), (54, 10)], outline=color[1]))

for wing_poly in wing_polys:
    group.append(wing_poly)


def redraw_wings(index):  # to change colors
    for wing in wing_polys:
        wing.outline = color[index]


# --- Content Setup ---
deco_font = bitmap_font.load_font("/BellotaText-Bold-21.bdf")

# Create two lines of text. Besides changing the text, you can also
# customize the color and font (using Adafruit_CircuitPython_Bitmap_Font).

# text positions
on_x = 15
on_y = 9
off_x = 12
off_y = 9
air_x = 15
air_y = 25


text_line1 = adafruit_display_text.label.Label(
    deco_font, color=color[3], text="OFF", max_glyphs=6
)
text_line1.x = off_x
text_line1.y = off_y

text_line2 = adafruit_display_text.label.Label(
    deco_font, color=color[1], text="AIR", max_glyphs=6
)
text_line2.x = air_x
text_line2.y = air_y

# Put each line of text into the Group
group.append(text_line1)
group.append(text_line2)


def startup_text():
    text_line1.text = " GO"
    text_line1.x = 10
    text_line1.color = color[2]
    text_line2.text = "ROYALS"
    text_line2.x = 1
    text_line2.color = color[4]
    redraw_wings(0)
    display.show(group)


startup_text()  # display the startup text


def update_text(state):
    if state:  # if switch is on, text is "ON" at startup
        text_line1.text = "ON"
        text_line1.x = on_x
        text_line1.color = color[1]
        text_line2.text = "AIR"
        text_line2.x = air_x
        text_line2.color = color[1]
        redraw_wings(1)
        redraw_frame()
        display.show(group)
    else:  # else, text if "OFF" at startup
        text_line1.text = "OFF"
        text_line1.x = off_x
        text_line1.color = color[3]
        text_line2.text = "AIR"
        text_line2.x = air_x
        text_line2.color = color[3]
        redraw_wings(3)
        redraw_frame()
        display.show(group)


def get_status():
    """
    Get the status whether we are on/off air within operating hours
    If outside of hours, return False
    """
    # Get the time values we need
    now = time.localtime()
    start_hour, start_minute, start_second = OPERATING_TIME_START.split(":")
    end_hour, end_minute, end_second = OPERATING_TIME_END.split(":")

    # Convert time into a float for easy calculations
    start_time = int(start_hour) + (int(start_minute) / 60) + (int(start_second) / 3600)
    end_time = int(end_hour) + (int(end_minute) / 60) + (int(end_second) / 3600)
    current_time = now[3] + (now[4] / 60)
    print(current_time)

    if start_time <= current_time < end_time:
        try:
            on_air = network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION1,))
            print(on_air)
            if on_air =="OnAir":
                return True
        except RuntimeError:
            return False

    return False

def connected(client):
    # Connected function will be called when the client is connected to Adafruit IO.
    # This is a good place to subscribe to feed changes.  The client parameter
    # passed to this function is the Adafruit IO MQTT client so you can make
    # calls against it easily.
    print("Connected to Adafruit IO!")

def subscribe(client, userdata, topic, granted_qos):
    # This method is called when the client subscribes to a new feed.
    print("Listening for changes on relay feed...{0}".format(userdata))


def unsubscribe(client, userdata, topic, pid):
    # This method is called when the client unsubscribes from a feed.
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))

def disconnected(client):
    # Disconnected function will be called when the client disconnects.
    print("Disconnected from Adafruit IO!")

def on_message(client, feed_id, payload):
    # Message function will be called when a subscribed feed has a new value.
    # The feed_id parameter identifies the feed, and the payload parameter has
    # the new value.
    print("Feed {0} received new value: {1}".format(feed_id, payload))
    if payload == "OnAir":
        print("OnAir - turning sign to On Air")
        update_text(1)
    elif payload == "OffAir":
        print("OffAir - turning sign to Off Air")
        update_text(0)
    else:
        print("Unexpected value received on relay feed.")

def on_relay_msg(client, topic, message):
    # Method called whenever user/feeds/relay has a new value
    if message == "OnAir":
        print("OnAir - turning sign to On Air")
        update_text(1)
    elif message == "OffAir":
        print("OffAir - turning sign to Off Air")
        update_text(0)
    else:
        print("Unexpected value received on relay feed.")
 
 

# Synchronize Board's clock to Internet
#### OLD LOGIC TO GET STATUS ####
# network.get_local_time()
# mode_state = get_status()
# update_text(mode_state)
# last_check = None

### END OLD LOGIC ####

print("Connecting to WiFi...")
wifi.connect()
print("Connected!")

# Initialize MQTT interface with the esp interface
MQTT.set_socket(socket, esp)
# Initialize a new MQTT Client object
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    username=secrets["aio_username"],
    password=secrets["aio_key"],
)

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)

# Connect the callback methods defined above to Adafruit IO
io.on_connect = connected
io.on_disconnect = disconnected
io.on_subscribe = subscribe
io.on_unsubscribe = unsubscribe
io.on_message = on_message
# Connect to Adafruit IO
print("Connecting to Adafruit IO...")
io.connect()

# Set up a message handler for the relay feed
io.add_feed_callback("RoyalsOnAir", on_relay_msg) ## not needed now may enable later for future product
# Subscribe to all messages on the relay feed
io.subscribe("RoyalsOnAir") 
# Get the most recent value on the relay feed
io.get("RoyalsOnAir")


# Start a blocking loop to check for new messages
while True:
    try:
        io.loop()
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        wifi.reset()
        io.reconnect()
        continue
    time.sleep(0.5)
