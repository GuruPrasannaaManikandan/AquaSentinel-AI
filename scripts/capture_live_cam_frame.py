import time
import base64
import serial
import os
from PIL import Image
import io

PORT = "COM4"
BAUD = 115200

print(f"Connecting to ESP32-CAM on {PORT}...")
try:
    ser = serial.Serial(PORT, BAUD, timeout=1.0)
    print("Opened COM4 successfully.")
    time.sleep(1.0)
    
    # Flush incoming buffer
    ser.reset_input_buffer()
    
    # Send 'c' command to request frame capture and Base64 transmission
    print("Sending 'c' command to trigger physical GC2145 frame capture...")
    ser.write(b"c\r\n")
    
    b64_lines = []
    capturing = False
    start_time = time.time()
    jpeg_bytes = None
    
    while time.time() - start_time < 15.0:
        line_bytes = ser.readline()
        if not line_bytes:
            continue
        line = line_bytes.decode('utf-8', errors='replace').strip()
        
        if "<<<FRAME_B64_START:" in line:
            capturing = True
            b64_lines = []
            print("Detected <<<FRAME_B64_START>>>! Receiving frame data...")
            continue
            
        if "<<<FRAME_B64_END>>>" in line:
            capturing = False
            full_b64 = "".join(b64_lines)
            print(f"Detected <<<FRAME_B64_END>>>! Total Base64 length: {len(full_b64)} chars.")
            jpeg_bytes = base64.b64decode(full_b64)
            break
            
        if capturing:
            b64_lines.append(line)
        else:
            if line:
                print(f"  [CAM] {line}")
                
    ser.close()
    
    if jpeg_bytes and len(jpeg_bytes) > 100:
        print(f"\n✅ SUCCESSFULLY CAPTURED REAL FRAME: {len(jpeg_bytes)} bytes!")
        print(f"Magic Bytes: 0x{jpeg_bytes[0]:02X} 0x{jpeg_bytes[1]:02X} (Expected: 0xFF 0xD8)")
        assert jpeg_bytes[0] == 0xFF and jpeg_bytes[1] == 0xD8, "Invalid JPEG header!"
        
        img = Image.open(io.BytesIO(jpeg_bytes))
        w, h = img.size
        print(f"Image Dimensions: {w} x {h} ({len(img.getbands())} channels)")
        
        # Save to reports and docs
        os.makedirs("docs", exist_ok=True)
        img_out = os.path.join("docs", "LIVE_ESP32_CAM_GC2145_FRAME.jpg")
        with open(img_out, "wb") as f:
            f.write(jpeg_bytes)
        print(f"Saved real camera frame to: {img_out}")
    else:
        print("❌ Did not receive complete frame within timeout.")
        
except Exception as e:
    print(f"Error accessing COM4: {e}")
