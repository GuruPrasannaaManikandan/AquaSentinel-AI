# PRELIMINARY BILL OF MATERIALS (BOM) & COMPONENT SPECIFICATION

**Project:** IoT-Based Artificial Immune System for Aquatic Ecosystems  
**Milestone:** Physical Hardware Design Phase — Hardware Bill of Materials  
**Document Version:** 1.0.0 (August 18, 2026)  
**Status:** Software Verified / Specifications Draft / Physical Procurement Pending  

---

## 1. Master Hardware Component List

> [!NOTE]
> Component selections below reflect required technical specifications. Exact vendor part numbers are kept flexible until physical bench validation. Vendor prices are intentionally omitted per project rules.

| Category | Component Name | Qty | Required Technical Specifications | Electrical / Interface Notes | Category Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Main MCU** | ESP32-WROOM-32 / 32E Dev Module | 1 | 240 MHz Dual-Core, 520 KB SRAM, 4 MB Flash, Wi-Fi 802.11 b/g/n, BLE | Micro-USB / Type-C programming port. `board = esp32dev`. | **REQUIRED** |
| **Camera Board** | AI-Thinker ESP32-CAM | 1 | ESP32-S MCU, 4 MB PSRAM, MicroSD slot, OV2640 camera interface | Dedicated 5V power input required. Camera board. | **REQUIRED** |
| **Camera Lens** | OV2640 Camera Sensor Module | 1 | 2 Megapixel, UXGA (1600x1200) max, standard ribbon connector | Configured to 224x224 JPEG capture mode. | **REQUIRED** |
| **Temp Sensor** | DS18B20 Temperature Sensor | 1 | Waterproof stainless steel probe, -55°C to +125°C, 9-12 bit | Digital OneWire protocol on **GPIO 18**. Requires 4.7kΩ resistor. | **REQUIRED** |
| **pH Sensor** | Analog pH Sensor Kit | 1 | Glass electrode probe + BNC signal conditioning board (0-14 pH) | Analog output on **GPIO 32 (ADC1)**. 5V VCC input. | **REQUIRED** |
| **Turbidity** | Gravity Analog Turbidity Module | 1 | Optical turbidity sensor module (0-4500 NTU), 5V VCC | Analog output on **GPIO 33 (ADC1)**. Requires 10k/20k divider. | **REQUIRED** |
| **DO Sensor** | Galvanic / Electrochemical DO Kit | 1 | Dissolved oxygen probe + signal amplifier board (0-20 mg/L) | Analog output on **GPIO 34 (ADC1)**. 5V VCC input. | **REQUIRED** |
| **Salinity/TDS**| Analog TDS / Conductivity Kit | 1 | Waterproof TDS probe + signal generator board (0-1000 ppm / ppt) | Analog output on **GPIO 36 (ADC1)**. 3.3V/5V compatible. | **REQUIRED** |
| **GPS Module** | GY-NEO6MV2 GPS Module | 1 | U-blox NEO-6M, baud rate 9600 bps, ceramic patch antenna | UART2 interface: RX on **GPIO 16**, TX on **GPIO 17**. | **REQUIRED** |
| **Status LEDs** | 5mm LEDs (Green, Yellow, Red) | 3 | Standard 5mm LEDs (1x Green, 1x Yellow, 1x Red) | Driven by **GPIO 19, 21, 22** via 220 Ω resistors. | **REQUIRED** |
| **Audio Alarm** | 5V Active / Passive Buzzer | 1 | 5V Piezo audio alarm buzzer module | Driven by **GPIO 23** via 2N2222 NPN transistor driver. | **REQUIRED** |
| **Relay Module** | 5V 1-Channel Optocoupled Relay | 1 | 5V DC coil, 10A 250VAC / 30VDC contacts, optocoupler isolation | Driven by **GPIO 27**. High/Low jumper selectable. | **REQUIRED** |
| **Aerator Pump**| 12V DC Submersible Aerator Pump | 1 | 12V DC motor, 120-240 L/h flow rate, waterproof casing | Controlled via Relay NO contacts on 12V motor supply. | **REQUIRED** |
| **Power Converter**| LM2596 / MP1584 Buck Converter | 1 | Step-Down Regulator: 7V-28V Input -> 5V Output @ 3A max | Supplies 5V rail for ESP32-CAM, relay, and sensors. | **REQUIRED** |
| **Power Supply** | 12V 3A DC Power Adapter | 1 | 120-240V AC to 12V DC 3A switching adapter | Powers 12V aerator pump and LM2596 buck converter. | **REQUIRED** |
| **Programmer** | FTDI USB-to-TTL Adapter | 1 | FT232RL module, 3.3V/5V selectable | Used for programming ESP32-CAM board. | **RECOMMENDED**|
| **Resistors** | Metal Film Resistors Assortment | 1 kit | 220 Ω (LEDs), 1 kΩ (Transistor), 4.7 kΩ (DS18B20), 10k/20k (Dividers) | Precision 1% tolerance metal film resistors. | **REQUIRED** |
| **Capacitors** | Decoupling Capacitors Assortment | 1 kit | 470 µF 16V Electrolytic, 100 µF 10V Electrolytic, 0.1 µF Ceramic | Power rail filtering & decoupling. | **REQUIRED** |
| **Transistors** | 2N2222 NPN Transistors | 2 | TO-92 NPN switching transistor (40V 600mA) | Buzzer driver on GPIO 23. | **REQUIRED** |
| **Diodes** | Rectifier & Signal Diodes | 1 kit | 1N4007 (Motor flyback), 1N4148 (Buzzer flyback) | Inductive spike protection. | **REQUIRED** |
| **Enclosure** | IP65 Waterproof Enclosure Box | 1 | Outdoor weather-resistant ABS junction box | Encloses main MCU, sensors interface, power system. | **RECOMMENDED**|
| **Prototyping** | MB-102 Breadboard & Jumpers | 1 kit | Solderless breadboard, DuPont male/female jumper wire set | Phase 1 bench testing & verification. | **REQUIRED** |
