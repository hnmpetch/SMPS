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
# from gpiozero import Servo

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

reserve_lot = [False,False,False,False,False,False]

# servo_in = Servo(18)
# servo_out = Servo(18)

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

current_fps = cap.get(cv2.CAP_PROP_FPS)
print(f"Current FPS: {current_fps}")

cap.set(cv2.CAP_PROP_FPS, 1)

client = set()
async def client_handle(ws):
    client.add(ws)
    try:
        try:
            async for message in ws:
                log.log_event(f"Client message: {message}")
                
                demessage = json.loads(message)
                
                if demessage['action'] == "reserve":
                    reserve_lot[demessage['lot']]
                    await ws.send(json.dumps({
                        "action": "reserve",
                        "lot": demessage['lot'],
                        "status": "success",
                        "status_code": 200
                    }))
                    
        finally:
            client.remove(ws)
    except Exception as e:
        log.error_event(f"Error when trying to start websocket, error : {e}")


async def start_websocket():
    server = await websockets.serve(client_handle, "127.0.0.1", 4001)
    log.success_event(f"Websocket server started at ws://127.0.0.1:4001")
    await asyncio.Future()  # Run forever
    server.close()
    await server.wait_closed()
    

parking = [
    {
        "id" : i+1,
        "slot": i+1,
        "time": 0,
        "free": True
    }
    for i in range(len(parking_slots))]

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
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 200, 0), 2)

        total_parking = len(parking_slots)
        empty_slots = 0
        occupied_slots = 0
        

        # * Check each slot
        for idx, slot in enumerate(parking_slots):
            pts_slot = np.array(slot, np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts_slot], isClosed=True, color=(255, 255, 0), thickness=2)
            M = cv2.moments(pts_slot)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = slot[0]

            color = (0, 255, 0)  # green = empty
            occupied = False
            # Check if the center of the lot is inside any car bounding box
            for i, car in enumerate(cars, start=1):
                x1, y1, x2, y2 = car
                cv2.putText(frame, f"Car {i}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    color = (0, 0, 255)  # red = occupied
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
                        "free": False
                    }
                elif parking[idx]['free'] == True and reserve_lot[idx] == True:
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": parking[idx]['time'],
                        "free": False
                    }
                    
                    reserve_lot[idx] = False
                else:
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": time.time,
                        "free": False
                    }
            else:
                empty_slots += 1
                log.log_event(f"Lot {idx + 1} is free")
                if parking[idx]['free'] != True:
                    bet = 0
                    
                    log.log_event(f"Parking {idx} bet {bet}")
                    
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": 0,
                        "free": True
                    }
                    
                
                elif parking[idx]['free'] == True and reserve_lot[idx] == True:
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": time.time,
                        "free": False
                    }
                    
                else:
                    parking[idx] = {
                        "id" : idx,
                        "slot": idx + 1,
                        "time": 0,
                        "free": True
                    }

            cv2.circle(frame, (cx, cy), 10, color, -1)
            cv2.putText(frame, str(idx + 1), (cx - 10, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
        
        
        for idx, slot in enumerate(in_area):
            pts_slot = np.array(slot, np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts_slot], isClosed=True, color=(255, 255, 0), thickness=2)
            M = cv2.moments(pts_slot)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = slot[0] if isinstance(slot[0], (list, tuple)) else (0, 0)


            color = (0, 255, 0)  # green = empty
            occupied = False
            
            for i, car in enumerate(cars, start=1):
                x1, y1, x2, y2 = car
                cv2.putText(frame, f"Car {i}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    color = (0, 0, 255)  # red = occupied
                    occupied = True
                    break
                
            if occupied and empty_slots > 0:
                try:
                    servo_in.value = 1
                    await asyncio.sleep(3)
                    servo_in.value = 0
                except Exception:
                    pass
            else:
                pass
        
        
        for idx, slot in enumerate(out_area):
            pts_slot = np.array(slot, np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts_slot], isClosed=True, color=(255, 255, 0), thickness=2)
            M = cv2.moments(pts_slot)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = slot[0] if isinstance(slot[0], (list, tuple)) else (0, 0)

            color = (0, 255, 0)  # green = empty
            occupied = False
            
            for i, car in enumerate(cars, start=1):
                x1, y1, x2, y2 = car
                cv2.putText(frame, f"Car {i}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    color = (0, 0, 255)  # red = occupied
                    occupied = True
                    break
                
            if occupied:
                try:
                    servo_in.value = -1
                    await asyncio.sleep(3)
                    servo_in.value = 0
                except Exception:
                    pass
            else:
                pass

        log.log_event(f"Total Parking: {total_parking}")
        log.log_event(f"Occupied: {occupied_slots}")
        log.log_event(f"Empty: {empty_slots}")


        park_info = {
            "action":"subscribe",
            "timestamps": time.time,
            "slot": total_parking,
            "Empty": empty_slots,
            "Car amount": occupied_slots,
            "info": parking
        }

        try:
            result_ws = json.dumps(park_info,default=str, indent=4)
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
        cv2.imshow("Parking", frame)

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