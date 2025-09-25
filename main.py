import os
import subprocess
import time
import cv2
import json
import yaml
from ultralytics import YOLO
import numpy as np
import asyncio
import websockets
from gpiozero import Servo
from RPLCD.i2c import CharLCD

print("starting...")



config_path = os.path.join("config", "config.yml")
with open(config_path, "r", encoding="utf-8") as yml:
    config_yml = yaml.safe_load(yml)
        
        
try :
    with open(os.path.join("config", "config_lot.json"),  'r', encoding="utf-8") as config:
        config_lot = json.load(config)
except FileNotFoundError :
    print("No file setup config found try setup..")
    subprocess.call("py setup.py")
    try :
        with open(os.path.join("config", "config_lot.json"),  'r', encoding="utf-8") as config:
            config_lot = json.load(config)
    except FileNotFoundError :
        print("No file setup config found try setup..")
        subprocess.call("py setup.py")
        
CAM_ID = config_yml["main"]["cam"]
model = YOLO("yolov8n.pt")
parking_slots = config_lot["parking_lot"]
main_parking_area = config_lot["main_area"]
in_area = config_lot["in_area"]
out_area = config_lot["out_area"]

servo_in = Servo(18)
servo_out = Servo(17)

lcd = CharLCD('PCF8574', 0x27)  # 0x27 คือ address ของ I2C LCD
lcd.cursor_pos = (0, 0)
lcd.write_string('Smart parking system')
lcd.cursor_pos = (1, 0)
lcd.write_string('Starting...')


lcd.cursor_pos = (1, 0)
lcd.write_string('|XX|--1      4--|XX|')
lcd.cursor_pos = (2, 0)
lcd.write_string('|XX|--2      5--|XX|')
lcd.cursor_pos = (3, 0)
lcd.write_string('|XX|--3      6--|XX|')

cap = cv2.VideoCapture(CAM_ID)

# Create mask for main parking area
ret, frame = cap.read()
if not ret:
    print("❌ Error opening video")
    exit()

cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 520)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

cap.set(cv2.CAP_PROP_FPS, 1)

async def open_gate():
    servo_in.value = 1
    await asyncio.sleep(3)
    servo_in.value = 0

async def close_gate():
    servo_out.value = 1
    await asyncio.sleep(3)
    servo_out.value = 0

client = set()
client_subscribe = set()

async def client_handle(ws):
    client.add(ws)
    try:
        try:
            async for message in ws:
                print(f"Client message: {message}")
                demessage = json.loads(message)
                if demessage['action'] == "reserve":
                    slot_idx = demessage['slot']
                    parking[slot_idx] = {
                        "id": slot_idx + 1,
                        "slot": slot_idx + 1,
                        "time": 0,
                        "free": True,
                        "reserve": True,
                        "pay": False
                    }
                    reserve_lot[slot_idx] = True
                    await ws.send(json.dumps({
                        "action": "reserve",
                        "lot": demessage['lot'],
                        "status": "success",
                        "status_code": 200
                    }))
                elif demessage['action'] == "subscribe":
                    client_subscribe.add(ws)
                    await ws.send(json.dumps({
                        "action": "subscribe",
                        "data": result_ws,
                        "status": "success",
                        "status_code": 200
                    }))
                elif demessage['action'] == "pay":
                    await ws.send(json.dumps({
                        "action": "pay",
                        "status": "success",
                        "status_code": 200
                    }))
        finally:
            client.remove(ws)
    except Exception as e:
        print(f"Error when trying to start websocket, error : {e}")
        


#! ########################################################
#! ########################################################
#! ########################################################



# * 1.ลูกค้าเลือกที่จอดรถ
# * 2.เข้ามาจอด
# * 3.ตอนออกให้จ่ายเงินแล้วมายืนยันเปิดประตุ
# * 4.ต่อจาก 3. ลูกค้าส่งคำขอจ่ายเงินมาแล้วส่งรหัส QR ให้ลูกค้าพร้อมกับยอดเงิน
# * 5.ลูกค้าจ่ายเสร็จอ่านรหัสสลิปแล้วส่งไปยืนยันด้วย SlipOk
# * 6.เปิดประตูให้ลูกค้าออกไป
# TODO: ระบบคิดเงิน
# TODO: ระบบ QR
# TODO: ระบบจ่ายเงิน
# TODO: ระบบการจองที่จอดรถ

#! ########################################################
#! ########################################################
#! ########################################################




async def start_websocket():
    server = await websockets.serve(client_handle, "127.0.0.1", 4001)
    print(f"Websocket server started at ws://127.0.0.1:4001")
    await asyncio.Future()  # Run forever
    server.close()
    await server.wait_closed()
    

parking = [
    {
        "id": i + 1,
        "slot": i + 1,
        "time": 0,
        "free": True,
        "reserve": False,
        "pay": False
    }
    for i in range(len(parking_slots))
]
reserve_lot = [False for _ in range(len(parking_slots))]

def calculate_bet(timein, timeout, rate) :
    return float(((timeout - timein)/3600) * rate)



async def main():
    frame_count = 0
    
    while True:
        
        success, frame = cap.read()
        if not success:
            break
        
        frame_count += 1
        if frame_count % 3 != 0:
            continue  # skip this frame


        # Detect cars only (YOLO class 2 = car)
        results = model(frame, stream=True, classes=[2])
        cars = []

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cars.append((x1, y1, x2, y2))
                

        total_parking = len(parking_slots)
        empty_slots = 0
        occupied_slots = 0
        

        # * Check each slot
        for idx, slot in enumerate(parking_slots):
            pts_slot = np.array(slot, np.int32).reshape((-1, 1, 2))
            M = cv2.moments(pts_slot)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = slot[0]

            occupied = False
            # Check if the center of the lot is inside any car bounding box
            for i, car in enumerate(cars, start=1):
                x1, y1, x2, y2 = car
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    occupied = True
                    break

            if occupied:
                occupied_slots += 1
                print(f"Lot {idx + 1} is full")
                
                
                
                if parking[idx]['free'] != True and parking[idx]['time'] != 0:
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": parking[idx]['time'],
                        "free": False,
                        "reserve": False,
                        "pay": False
                    }
                elif parking[idx]['free'] == True and reserve_lot[idx] == True:
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": parking[idx]['time'],
                        "free": False,
                        "reserve": False,
                        "pay": False
                    }
                    
                    reserve_lot[idx] = False
                else:
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": time.time(),
                        "free": False,
                        "reserve": False,
                        "pay": False
                    }
            else:
                empty_slots += 1
                print(f"Lot {idx + 1} is free")
                    
                
                if parking[idx]['free'] == True and reserve_lot[idx] == True:
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": time.time(),
                        "free": False,
                        "reserve": True,
                        "pay": False
                    }
                elif parking[idx]['free'] != True and parking[idx]['pay'] == False:
                    parking[idx] = {
                        "id": idx,
                        "slot": idx + 1,
                        "time": parking[idx]['time'],
                        "free": False,
                        "reserve": False,
                        "pay": False
                    }
                elif parking[idx]['free'] != True and parking[idx]['pay'] == True:
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": 0,
                        "free": True,
                        "reserve": False,
                        "pay": True
                    }
                    
                elif parking[idx]['free'] != True:
                    
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": time.time(),
                        "free": True,
                        "reserve": False,
                        "pay": False
                    }
                    
                else:
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": 0,
                        "free": True,
                        "reserve": False,
                        "pay": False
                    }
    
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f'|{"XX" if parking[0]["free"] != True else "  "}|--1      4--|{"XX" if parking[3]["free"] != True else "  "}|')
        lcd.cursor_pos = (2, 0)
        lcd.write_string(f'|{"XX" if parking[1]["free"] != True else "  "}|--2      5--|{"XX" if parking[4]["free"] != True else "  "}|')
        lcd.cursor_pos = (3, 0)
        lcd.write_string(f'|{"XX" if parking[2]["free"] != True else "  "}|--3      6--|{"XX" if parking[5]["free"] != True else "  "}|')

        print(f"Total Parking: {total_parking}")
        print(f"Occupied: {occupied_slots}")
        print(f"Empty: {empty_slots}")

        
        park_info = {
            "action": "subscribe",
            "timestamps": time.time(),
            "slot": total_parking,
            "Empty": empty_slots,
            "Car amount": occupied_slots,
            "info": parking
        }

        try:
            global result_ws
            result_ws = json.dumps(park_info, default=str, indent=4)
            results = await asyncio.gather(
                *(ws.send(result_ws) for ws in client),
                return_exceptions=True
            )
            for ws, res in zip(list(client), results):
                if isinstance(res, Exception):
                    print(f"Client {ws} disconnected ({res}), removing..")
                    client.remove(ws)
        except Exception as e:
            print(f'{e}')

        await asyncio.sleep(3)



async def start():
    tasks = [
        asyncio.create_task(start_websocket()),
        asyncio.create_task(main())
    ]
    try:
        await asyncio.gather(*tasks)
    except (KeyboardInterrupt, SystemExit):
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    
if __name__ == "__main__":
    asyncio.run(start())