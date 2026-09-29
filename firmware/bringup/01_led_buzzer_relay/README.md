# Stage 01: Discrete Actuators Physical Bring-Up

**Subsystem:** Status LEDs (Green, Yellow, Red), Audio Buzzer, 5V Relay  
**MCU:** ESP32-WROOM-32 (38-pin Dev Module) on CP2102 (`COM3`)  
**Status:** Isolated Hardware Bring-Up Stage 01  

---

## 1. Pin Assignment Table

| Component | Pin Function | ESP32 GPIO | Electrical Connection | Logic Polarity |
| :--- | :--- | :--- | :--- | :--- |
| **Green LED** | Normal / Healthy Status | **GPIO 19** | Series 220Ω / 330Ω resistor to GND | HIGH = ON, LOW = OFF |
| **Yellow LED** | Warning / Risk Status | **GPIO 21** | Series 220Ω / 330Ω resistor to GND | HIGH = ON, LOW = OFF |
| **Red LED** | Critical / Bloom Status | **GPIO 22** | Series 220Ω / 330Ω resistor to GND | HIGH = ON, LOW = OFF |
| **5V Buzzer** | Audio Alarm Chirp | **GPIO 23** | Driver module I/O or Transistor Base | HIGH = Chirp, LOW = Silent |
| **5V Relay** | Pump / Actuator Trigger | **GPIO 27** | Relay Module `IN` Pin | Tested HIGH & LOW |

---

## 2. Breadboard Wiring Instructions

### A. LEDs (Green, Yellow, Red)
1. Insert the 3 LEDs into separate rows on the breadboard.
2. Note the polarity of each LED:
   - **Anode (Longer leg / Round side):** Positive
   - **Cathode (Shorter leg / Flat edge):** Ground
3. Connect current-limiting resistors:
   - Place a **220Ω or 330Ω resistor** in series between the cathode (short leg) of each LED and the breadboard Common Ground rail (`GND`).
4. Connect the GPIO control lines:
   - Green LED anode $\rightarrow$ **ESP32 GPIO 19**
   - Yellow LED anode $\rightarrow$ **ESP32 GPIO 21**
   - Red LED anode $\rightarrow$ **ESP32 GPIO 22**
5. Connect ESP32 `GND` pin to the breadboard Common Ground rail.

### B. 5V Active Buzzer Module
1. `VCC` pin $\rightarrow$ **5V Rail** (ESP32 `VIN` / `5V` pin) or `3.3V` (if 3.3V buzzer module)
2. `GND` pin $\rightarrow$ **Common Ground Rail** (`GND`)
3. `I/O` or `SIG` pin $\rightarrow$ **ESP32 GPIO 23**

### C. 5V Relay Module (DRY-CONTACT ONLY)
1. `VCC` pin $\rightarrow$ **5V Rail** (ESP32 `VIN` / `5V` pin)
2. `GND` pin $\rightarrow$ **Common Ground Rail** (`GND`)
3. `IN` pin $\rightarrow$ **ESP32 GPIO 27**
4. **DO NOT connect any AC mains or pump loads to the relay terminals.** The relay's onboard status LED and the audible mechanical click are the verification indicators.

---

## 3. PlatformIO Commands

### A. Compile Firmware (Without Uploading)
```bash
pio run -d "firmware/bringup/01_led_buzzer_relay"
```

### B. Flash to ESP32 (COM3)
```bash
pio run -d "firmware/bringup/01_led_buzzer_relay" -t upload --upload-port COM3
```

### C. Open Serial Monitor (115200 Baud)
```bash
pio device monitor -d "firmware/bringup/01_led_buzzer_relay" -p COM3 -b 115200
```
*(Or combine upload and monitor in one step:)*
```bash
pio run -d "firmware/bringup/01_led_buzzer_relay" -t upload -t monitor
```

---

## 4. Electrical Safety Constraints

1. **Current Limiting:** NEVER connect LEDs directly between an ESP32 GPIO and GND without a 220Ω or 330Ω resistor. ESP32 pins are rated for 12mA recommended / 40mA absolute maximum.
2. **5V Tolerance:** ESP32 GPIO pins are strictly 3.3V tolerant. The relay and buzzer input pins only accept the 3.3V digital output from the ESP32; ensure no 5V potential is fed back into GPIO 23 or GPIO 27.
3. **Dry-Contact Mode:** The relay must remain completely unconnected from external AC power or pump motors during this bring-up stage.
