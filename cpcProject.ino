#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <time.h>

// Function prototypes
void sendDataToGCP(String wasteType, String wasteLevel, String waterLevel = "");
float readUltrasonic(int trigPin, int echoPin);
String checkWaterLevel();
void reconnect();
void setup_wifi();

// Define the MQTT server and port (replace with your GCP MQTT server details)
const char* MQTT_SERVER = "34.121.56.36";  // Your GCP MQTT server IP or hostname
const int MQTT_PORT =1883;               // MQTT port (non-TLS)
const char* MQTT_TOPIC ="smartdustbin"; // Topic to publish sensor data

// Define WiFi credentials
const char* WIFI_SSID = "rawr"; // Your WiFi SSID
const char* WIFI_PASSWORD = "378191Eb99."; // Your WiFi password

// NTP Server and time zone
const char *ntpServer = "pool.ntp.org";
const long gmtOffset_sec =  8 * 3600;; // GMT offset in seconds (e.g., 0 for UTC)
const int daylightOffset_sec = 0; // Daylight saving time offset (in seconds)

// Ultrasonic sensor pins
const int trigPinWet = 27;
const int echoPinWet = 26;
const int trigPinDry = 22;
const int echoPinDry = 23;

const int irSensorPin = 18;
const int moisturePin = 36;
const int servoPin = 16;

int moisturePercent = 0;
int moistureValue = 0;
int dryThreshold = 100;
int objectDetected = HIGH;
float distance = 0;

const int powerPin = 10;
const int waterLevPin = 39;

float distanceWet = 0;
float distanceDry = 0;

int waterValue = 0;
const float fullThreshold = 30.0;
const int waterThreshold = 1200;

// Initialize WiFi and MQTT client objects
WiFiClient espClient;
PubSubClient client(espClient);

Servo servo1;

void setup() {
  Serial.begin(115200);
  
  // Set up WiFi and MQTT
  setup_wifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);

  // Initialize NTP client
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  Serial.println("Waiting for time sync...");

  // Wait for time to be synchronized
  while (!time(nullptr)) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("Time synchronized");


  // Initialize servo and sensors
  servo1.attach(servoPin);
  servo1.write(45);
  
  pinMode(irSensorPin, INPUT_PULLUP);
  pinMode(trigPinWet, OUTPUT);
  pinMode(echoPinWet, INPUT);
  pinMode(trigPinDry, OUTPUT);
  pinMode(echoPinDry, INPUT);
  analogSetAttenuation(ADC_11db);
  pinMode(powerPin, OUTPUT);
  digitalWrite(powerPin, LOW);
}

void loop() {
  // Reconnect to MQTT if disconnected
  if (!client.connected()) {
    reconnect();
  }

  client.loop();
  
  delay (5000);
  objectDetected = digitalRead(irSensorPin);
  
  if (objectDetected == LOW) {
    Serial.println("Object Detected!");
    distance = analogRead(irSensorPin); // Read distance value
    delay(2000);

    // Read and process moisture sensor value
    moistureValue = analogRead(moisturePin);
    moisturePercent = map(moistureValue, 0, 4095, 0, 100);

    // Prepare message to send to MQTT
  
    if (moisturePercent < dryThreshold) {
      Serial.println("Wet Waste Detected!");
      servo1.write(0);
      delay(3000);

     // Measure distance for waste level
      distanceWet = readUltrasonic(trigPinWet, echoPinWet);
      String wasteLevel = (distanceWet > fullThreshold) ? "Not Full" : "Full";

      // Check water level
      String waterLevel = checkWaterLevel();

      // Send data to GCP
      sendDataToGCP("Wet Waste", wasteLevel, waterLevel);
    } 
    else {
      Serial.println("Dry Waste Detected!");
      servo1.write(90);
      delay(3000);

     // Measure distance for waste level
      distanceDry = readUltrasonic(trigPinDry, echoPinDry);
      String wasteLevel = (distanceDry > fullThreshold) ? "Not Full" : "Full";

      // Send data to GCP
      sendDataToGCP("Dry Waste", wasteLevel);
    }

    delay(3000);
    servo1.write(45); // Reset servo position
  } else {
    Serial.println("No Object Detected");
  }

  delay(1000);
}

void setup_wifi() {
  delay(10);
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) {
      Serial.println("Connected to MQTT server");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying in 5 seconds...");
      delay(5000);
    }
  }
}

float readUltrasonic(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  float distance = duration * 0.034 / 2;
  return distance;
}



// Function to check water level
String checkWaterLevel() {
  digitalWrite(powerPin, HIGH);
  delay(10);
  int waterValue = analogRead(waterLevPin);
  digitalWrite(powerPin, LOW);
  return (waterValue >= waterThreshold) ? "Full" : "Not Full";
}

// Function to send data to GCP
void sendDataToGCP(String wasteType, String wasteLevel, String waterLevel) {
  char payload[256];
  
  // Get current time
  time_t now = time(nullptr);
  
  // Format timestamp to a human-readable format (YYYY-MM-DD HH:MM:SS)
  char formattedTime[20];
  strftime(formattedTime, sizeof(formattedTime), "%Y-%m-%d %H:%M:%S", localtime(&now));

  // Prepare the payload
  if (wasteType == "Wet Waste") {
    // If waste type is Wet Waste, include water level in the payload
    sprintf(payload, "{\"timestamp\": \"%s\", \"waste_type\": \"%s\", \"waste_level\": \"%s\", \"water_level\": \"%s\"}",
            formattedTime, wasteType.c_str(), wasteLevel.c_str(), waterLevel.c_str());
  } else {
    // If waste type is Dry Waste, omit the water level from the payload
    sprintf(payload, "{\"timestamp\": \"%s\", \"waste_type\": \"%s\", \"waste_level\": \"%s\"}",
            formattedTime, wasteType.c_str(), wasteLevel.c_str());
  }
  
  // Publish the data to MQTT
  client.publish(MQTT_TOPIC, payload);

  // Output the data to Serial Monitor for debugging
  Serial.println("Data sent to GCP:");
  Serial.println(payload);
}