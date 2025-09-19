from datetime import datetime
import os
import pandas as pd
import subprocess
import time
import cv2
import json
import mysql.connector
from ultralytics import YOLO
import numpy as np
from utils.log import log
import asyncio
import websockets
from gpiozero import Servo

model = YOLO("yolov8n.pt")

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

parking_slots = config_lot["parking_lot"]
main_parking_area = config_lot["main_area"]
in_area = config_lot["in_area"]
out_area = config_lot["out_area"]

reserve_lot = []

servo_in = Servo(17)
servo_out = Servo(18)

cap = cv2.VideoCapture("example/videoplayback.mp4")
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter("parking7_output.mp4", fourcc, 30,
                      (int(cap.get(3)), int(cap.get(4))))

# Create mask for main parking area
ret, frame = cap.read()
if not ret:
    print("❌ Error opening video")
    exit()

mask = np.zeros_like(frame[:, :, 0])
pts = np.array(main_parking_area, np.int32).reshape((-1, 1, 2))
cv2.fillPoly(mask, [pts], 255)
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

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
    

async def connect_database():
    
    try:
        db = await mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="smps"
        )
        
        dbcursor = db.cursor()
        
        return dbcursor

    except mysql.connector.DatabaseError as dbe:
        log.error_event(f"Connect fail error : {dbe}")
    except Exception as e:
        log.error_event(f"Fail to connect to database, error: {e}")
    

parking = []

def calculate_bet(timein, timeout, rate) :
    return float(((timeout - timein)/3600) * rate)


async def main():
    
    db = await connect_database()
    
    
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
                
                
                
                if parking[i]['free'] != True and parking[i]['time'] != 0:
                    parking[i] = {
                        "id" : i,
                        "slot": idx + 1,
                        "time": parking[i]['time'],
                        "free": False
                    }
                elif parking[i]['free'] == True and reserve_lot[i] == True:
                    parking[i] = {
                        "id" : i,
                        "slot": idx + 1,
                        "time": parking[i]['time'],
                        "free": False
                    }
                    
                    reserve_lot[i] = False
                    try:
                        sql = f"UPDATE parking SET status = 'FULL' WHERE id = {idx + 1}"
                        db.execute(sql)
                        db.commit()
                    except Exception as e :
                        log.error_event(f"Fail to set update in line 146, error : {e}")
                        exit(1)
                else:
                    parking[i] = {
                        "id" : i,
                        "slot": idx + 1,
                        "time": time.time,
                        "free": False
                    }
                    try:
                        sql = f"UPDATE parking SET status = 'FULL' WHERE id = {idx + 1}"
                        db.execute(sql)
                        db.commit()
                    except Exception as e :
                        log.error_event(f"Fail to set update in line 146, error : {e}")
                        exit(1)
            else:
                empty_slots += 1
                log.log_event(f"Lot {idx + 1} is free")
                if parking[i]['free'] != True:
                    bet = calculate_bet(parking[i]['time'], time.time(), config['main']['rate'])
                    
                    log.log_event(f"Parking {i} bet {bet}")
                    
                    parking[i] = {
                        "id" : i,
                        "slot": idx + 1,
                        "time": 0,
                        "free": True
                    }
                    
                    try:
                        sql = f"UPDATE parking SET status = 'FREE' WHERE id = {idx + 1}"
                        db.execute(sql)
                        db.commit()
                    except Exception as e :
                        log.error_event(f"Fail to set update, error : {e}")
                        exit(1)
                
                elif parking[i]['free'] == True and reserve_lot[i] == True:
                    parking[i] = {
                        "id" : i,
                        "slot": idx + 1,
                        "time": time.time,
                        "free": False
                    }
                    try:
                        sql = f"UPDATE parking SET status = 'FULL' WHERE id = {idx + 1}"
                        db.execute(sql)
                        db.commit()
                    except Exception as e :
                        log.error_event(f"Fail to set update, error : {e}")
                        exit(1)
                    
                else:
                    parking[i] = {
                        "id" : i,
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
                cx, cy = slot[0]

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
                servo_in.value = 1
                asyncio.sleep(3)
                servo_in.value = 0
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
                cx, cy = slot[0]

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
                servo_in.value = -1
                asyncio.sleep(3)
                servo_in.value = 0
            else:
                pass

        log.log_event(f"Total Parking: {total_parking}")
        log.log_event(f"Occupied: {occupied_slots}")
        log.log_event(f"Empty: {empty_slots}")

        cv2.imshow("Parking Detection", frame)
        out.write(frame)

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

        await asyncio.sleep(0)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            exit(0)

    # Release
    cap.release()
    out.release()
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