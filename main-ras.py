import base64
import cv2
import asyncio
import websockets
import json
from gpiozero import Servo
from RPLCD.i2c import CharLCD

servo_in = Servo(17)
servo_out = Servo(18)
lcd = CharLCD("PCF8574", 0x27)

CAM_ID = 0

async def open_gate():
    servo_in.value = 1
    await asyncio.sleep(3)
    servo_in.value = 0.3

async def close_gate():
    servo_out.value = -1
    await asyncio.sleep(3)
    servo_out.value = -0.3





async def set_status(parking_info):
    try:
        lcd.cursor_pos = (1, 0)
        lcd.write_string(
            f'|{"XX" if parking_info[5]["occupied"] else "  "}|--6      3--|{"XX" if parking_info[2]["occupied"] else "  "}|'
        )
        lcd.cursor_pos = (2, 0)
        lcd.write_string(
            f'|{"XX" if parking_info[4]["occupied"] else "  "}|--5      2--|{"XX" if parking_info[1]["occupied"] else "  "}|'
        )
        lcd.cursor_pos = (3, 0)
        lcd.write_string(
            f'|{"XX" if parking_info[3]["occupied"] else "  "}|--4      1--|{"XX" if parking_info[0]["occupied"] else "  "}|'
        )
    except Exception as e:
        print(f"LCD update error: {e}")

async def run_client():
    
    print("testing..")
    
    servo_in.value = 0.3
    servo_out.value = -0.3
    
    await asyncio.sleep(5)

    print("open")
    await open_gate()
    print("close")
    await close_gate()
    print("success")
    
    uri = "ws://10.32.104.73:5000"  # TODO: เปลี่ยนเป็น IP ของ server
    cap = cv2.VideoCapture(CAM_ID)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 320)
    cap.set(cv2.CAP_PROP_FPS, 1)

    while True:
        try:
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps({"action": "subscribe", "type": "pi"}))
                print("✅ Connected to server")

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        continue

                    _, buffer = cv2.imencode(".jpg", frame)
                    frame_b64 = base64.b64encode(buffer).decode("utf-8")

                    await ws.send(json.dumps({"action": "frame", "data": frame_b64}))

                    response = await ws.recv()
                    result = json.loads(response)

                    if "info" in result:
                        await set_status(result["info"])

                    if result.get("open_gate"):
                        await open_gate()
                    if result.get("close_gate"):
                        await close_gate()
                    
                    await asyncio.sleep(1)

        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            print(f"⚠️ Connection lost: {e}, retrying in 5s...")
            await asyncio.sleep(5)

asyncio.run(run_client())
