# CPC357_PROJECT: EcoSort Bin

## Introduction  
**EcoSort Bin** is an IoT-based project designed for kitchen waste management, focusing on the segregation of wet and dry waste. The system automates waste classification using sensors and actuators, making disposal more efficient and hygienic. A real-time dashboard displays the waste status, ensuring users stay informed and proactive in managing their kitchen waste.  

This project was developed as part of the **CPC357: IoT Architecture & Smart Applications** course to demonstrate practical IoT applications and sustainable solutions.

## Features  
- **Automated Waste Segregation**: Uses IR, ultrasonic, and moisture sensors to distinguish between wet and dry waste.  
- **Water Filtering Mechanism**: Reduces excess water in wet waste, minimizing leakage and odors.  
- **IoT Integration**: Real-time data visualization via a cloud-based dashboard.  

---

## How to Run the Project  

### 1. Complete the IoT Circuit  
Ensure the hardware circuit is properly assembled. Refer to the project documentation for the circuit diagram and component setup.

### 2. Upload the Arduino Code  
1. Open the `cpcProject.ino` file in the Arduino IDE.  
2. Select the correct board and COM port in the IDE.  
3. Compile and upload the code to your microcontroller.  

### 3. Set Up the Dashboard  
Run the following Python scripts from the Google Cloud Platform (GCP) SSH Browser:  

#### a. Run the Smart Dustbin Script 
In one SSH browser terminal, execute:  
python3 smartdustbin.py

#### b. Run the Dashboard Script
In another SSH browser terminal, execute:
python3 newDash.py
