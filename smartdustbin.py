import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json

# MongoDB connection details
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["smartdustbin"]
collection = db["sensor_data"]

# MQTT connection details
MQTT_BROKER = "34.121.56.36"
MQTT_PORT = 1883
MQTT_TOPIC = "smartdustbin"

# Callback when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

# Callback when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    print(f"Message received: {msg.payload.decode()}")
    try:
        # Parse the JSON payload
        data = json.loads(msg.payload.decode())
        # Insert the data into MongoDB
        collection.insert_one(data)
        print("Data inserted into MongoDB")
        
    except Exception as e:
        print(f"Error: {e}")

# Create an MQTT client instance
client = mqtt.Client()

# Assign event callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Blocking call that processes network traffic, dispatches callbacks and handles reconnecting.
client.loop_forever()