# Running AquaSentinel-AI on a Windows laptop

Two boards are plugged in over USB:

| Board | What it runs | Firmware folder |
| --- | --- | --- |
| Sensor ESP32 (turbidity on GPIO34, pH on GPIO32) | main firmware 3.9+ | `firmware/` |
| ESP32-CAM on the MB base board (GC2145 / OV2640) | serial camera sketch | `firmware/bringup/07_ov2640_camera_verification/` |

COM numbers differ per laptop and USB socket, so nothing is hardcoded any more.

## 1. One-time install

```powershell
cd G:\AquaSentinel-AI
python -m pip install -r requirements.txt platformio
```

## 2. Find the COM ports

```powershell
python -m src.utils.serial_ports
```

It lists every port and says which one is the sensor ESP32 and which is the
ESP32-CAM (it listens to what each board prints; boards that were never flashed
are guessed from their USB chip: CH340 = camera base board, CP210x = sensor ESP32).
Close the Arduino IDE / any serial monitor first, because Windows lets only one
program open a COM port.

Below, `COM7` is the sensor ESP32 and `COM4` the camera. Use your own numbers.

## 3. Flash the sensor ESP32

```powershell
cd G:\AquaSentinel-AI\firmware
pio run -e esp32dev -t upload --upload-port COM7
pio device monitor -p COM7 -b 115200
```

You should see a `[TELEMETRY-JSON] {...}` line every 2 seconds with
`turbidity_voltage` and `ph`. Press Ctrl+C to leave the monitor.

## 4. Flash the ESP32-CAM

```powershell
cd G:\AquaSentinel-AI\firmware\bringup\07_ov2640_camera_verification
pio run -e esp32cam -t upload --upload-port COM4
```

If the upload says "Failed to connect", hold the **IO0** button on the MB base
board, press **RST** once, start the upload, and release IO0 when "Connecting..."
appears. Press **RST** again after the upload finishes.

## 5. Start the website

Three terminals, all in `G:\AquaSentinel-AI`:

```powershell
python run_demo.py                                          # backend :8000 + dashboard :8501
python scripts\live_mqtt_gateway_bridge.py --port COM7      # sensor ESP32 -> dashboard
```

Then open http://127.0.0.1:8501. The **Live Hardware Sensors** panel at the top
refreshes every 2 seconds. The camera is on the **Optical & Temporal Intelligence**
tab: click **CAPTURE PHOTO** (the backend finds the camera port itself; set
`AQUA_CAM_PORT=COM4` to force it).

`--no-mqtt` skips the public MQTT broker if there is no internet.

## Serial commands (sensor ESP32)

Type these in `pio device monitor -p COM7` (the bridge must be stopped, since
only one program can hold the port), each followed by Enter:

| Command | What it does |
| --- | --- |
| `READ` | take a reading now |
| `SET_INTERVAL 5` | read every 5 s (1-300) |
| `TURB_CLEAR` | with the turbidity probe in clear water: store it as the 0 NTU reference |
| `PH_CAL7` | with the pH probe BNC shorted (centre pin to outer shell): store the pH 7.00 point |
| `PH_CAL 4.0` | optional second point, if you have any liquid of known pH |
| `PH_SLOPE -5.7` | set the slope directly (SEN0161: `3.5`, PH-4502C: about `-5.7`) |
| `PH_INFO` / `PH_RESET` | show / reset pH calibration |
| `HELP` | list commands |

Calibration is saved in the ESP32's flash and survives reboots and re-flashing.

## pH reading "28"

The old firmware turned the pin voltage into pH with `pH = 3.5 * V` and the
pin was stuck at full scale (raw ADC 4095, 3.3 V), which gives 28.9. The new
firmware reports `ADC_SATURATED` instead of a fake number. A 5 V pH module
behind the 33k/22k divider can only reach about 2 V at GPIO32, so full scale
means a wiring problem: check that Po goes through the 33k resistor to GPIO32
with the 22k resistor from GPIO32 to GND, and that GPIO32 is not touching 3V3.
Once the raw value is below 4090, short the BNC and send `PH_CAL7`.
