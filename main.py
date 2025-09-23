from datetime import datetime
import os
import pandas as pd
import subprocess
import time
import cv2
import json
import mysql.connector
import yaml
from ultralytics import YOLO
import numpy as np
from utils.log import log
import asyncio
import websockets
from gpiozero import Servo
from RPLCD.i2c import CharLCD




config_path = os.path.join("config", "config.yml")
with open(config_path, "r", encoding="utf-8") as yml:
    config_yml = yaml.safe_load(yml)
        
        
try :
    with open(os.path.join("config", "config_lot.json"),  'r', encoding="utf-8") as config:
        config_lot = json.load(config)
except FileNotFoundError :
    log.warning_event("No file setup config found try setup..")
    subprocess.call("py setup.py")
    try :
        with open(os.path.join("config", "config_lot.json"),  'r', encoding="utf-8") as config:
            config_lot = json.load(config)
    except FileNotFoundError :
        log.warning_event("No file setup config found try setup..")
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
lcd.write_string('Hello, World!')

cap = cv2.VideoCapture(CAM_ID)

# Create mask for main parking area
ret, frame = cap.read()
if not ret:
    print("❌ Error opening video")
    exit()

mask = np.zeros_like(frame[:, :, 0])
pts = np.array(main_parking_area, np.int32).reshape((-1, 1, 2))
cv2.fillPoly(mask, [pts], 255)
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

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
                log.log_event(f"Client message: {message}")
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
        log.error_event(f"Error when trying to start websocket, error : {e}")
        


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
    log.success_event(f"Websocket server started at ws://127.0.0.1:4001")
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
    
    while True:
        
        success, frame = cap.read()
        if not success:
            break

        masked_frame = cv2.bitwise_and(frame, frame, mask=mask)

        # Detect cars only (YOLO class 2 = car)
        results = model(masked_frame, stream=True, classes=[2])
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
                log.log_event(f"Lot {idx + 1} is full")
                
                
                
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
                log.log_event(f"Lot {idx + 1} is free")
                    
                
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
    

        log.log_event(f"Total Parking: {total_parking}")
        log.log_event(f"Occupied: {occupied_slots}")
        log.log_event(f"Empty: {empty_slots}")


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
                    log.warning_event(f"Client {ws} disconnected ({res}), removing..")
                    client.remove(ws)
        except Exception as e:
            log.warning_event(f'{e}')

        await asyncio.sleep(3)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            exit(0)

    # Release
    cap.release()
    cv2.destroyAllWindows()


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