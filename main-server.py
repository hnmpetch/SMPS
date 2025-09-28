import cv2
import numpy as np
import websockets
import asyncio
import json
import base64
import time
import aiohttp
from ultralytics import YOLO

with open("config/config_lot.json", "r") as f:
    config = json.load(f)

parking_slots = config["parking_lot"] 
in_area = np.array(config["in_area"])
out_area = np.array(config["out_area"])

url = "https://script.google.com/macros/s/AKfycbzQAQ2snkD8s7mW7DHIWhy08pRj19UwZSswkkOcY-ypdQrfxzU2UuTkR7ww7G4bEfaBlA/exec"

model = YOLO("yolov8n.pt")

slot_state = {}
clients = {
    "pi": set(),
    "web": set()
}

def draw_parking_view(frame, car_centers, parking_status, park_info):
    for (cx, cy) in car_centers:
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

    for slot, status in zip(parking_slots, parking_status):
        polygon = np.array(slot["polygon"], np.int32).reshape((-1, 1, 2))

        color = (0, 0, 255) if status["occupied"] else (0, 255, 0)
        cv2.polylines(frame, [polygon], isClosed=True, color=color, thickness=2)

        text = str(slot.get("label", slot.get("id", "")))
        M = cv2.moments(polygon)
        if M["m00"] != 0:
            tx = int(M["m10"] / M["m00"])
            ty = int(M["m01"] / M["m00"])
        else:
            tx, ty = int(polygon[0][0][0]), int(polygon[0][0][1])
        cv2.putText(frame, text, (tx - 10, ty + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    def polygons_from_area(area):
        if not area:
            return []
        try:
            first = area[0]
            if isinstance(first[0], (int, float, np.integer, np.floating)):
                return [area]
            else:
                return area
        except Exception:
            return []

    for poly in polygons_from_area(in_area):
        polygon = np.array(poly, np.int32).reshape((-1, 1, 2))
        color = (0, 0, 255) if park_info.get("open_gate", False) else (0, 255, 0)
        cv2.polylines(frame, [polygon], isClosed=True, color=color, thickness=2)
        M = cv2.moments(polygon)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = int(polygon[0][0][0]), int(polygon[0][0][1])
        cv2.putText(frame, "IN", (cx - 10, cy + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    for poly in polygons_from_area(out_area):
        polygon = np.array(poly, np.int32).reshape((-1, 1, 2))
        color = (0, 0, 255) if park_info.get("close_gate", False) else (0, 255, 0)
        cv2.polylines(frame, [polygon], isClosed=True, color=color, thickness=2)
        M = cv2.moments(polygon)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = int(polygon[0][0][0]), int(polygon[0][0][1])
        cv2.putText(frame, "OUT", (cx - 10, cy + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    return frame



async def notify_gas(open_gate, close_gate, parking_status):
    async with aiohttp.ClientSession() as session:

        if open_gate:
            available_slots = [slot for slot in parking_status if not slot["occupied"]]
            if not available_slots:
                print("ไม่มีช่องจอดว่าง")
            else:
                slot_to_use = min(available_slots, key=lambda x: x["id"])
                slot_id = slot_to_use["id"]

                params = {
                    "action": "entry",
                    "id": slot_id
                }

                try:
                    async with session.get(url, params=params, timeout=5) as resp:
                        text = await resp.text()
                        print("Entry Response:", text)
                except Exception as e:
                    print("Entry Request Error:", e)

        if close_gate:
            params = {"action": "exit"}
            try:
                async with session.get(url, params=params, timeout=5) as resp:
                    text = await resp.text()
                    print("Exit Response:", text)
            except Exception as e:
                print("Exit Request Error:", e)


def check_in_polygon(point, polygon):
    return cv2.pointPolygonTest(np.array(polygon, np.int32), point, False) >= 0

async def process_frame(frame):
    results = model.predict(frame, conf=0.5, verbose=True, classes=[2])
    detections = results[0].boxes.xyxy.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy()

    car_centers = []
    for box, cls_id in zip(detections, classes):
        x1, y1, x2, y2 = map(int, box[:4])
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        car_centers.append((cx, cy))

    parking_status = []
    for slot in parking_slots:
        idx = slot["id"]
        polygon = slot["polygon"]

        occupied = any(check_in_polygon(c, polygon) for c in car_centers)

        # update join_at
        if occupied:
            if idx not in slot_state:
                slot_state[idx] = time.time()
        else:
            if idx in slot_state:
                del slot_state[idx]

        parking_status.append({
            "id": idx,
            "label": slot.get("label", f"{idx+1}"),
            "reserved": slot.get("reserved", False),
            "occupied": occupied,
            "zone": slot.get("zone", 0),
            "side": slot.get("side", "left"),
            "pay": slot.get("pay", False),
            "join_at": slot_state.get(idx, 0)
        })

    total_parking = len(parking_status)
    occupied_slots = sum(1 for p in parking_status if p["occupied"])
    empty_slots = total_parking - occupied_slots

    open_gate = any(check_in_polygon(c, in_area) for c in car_centers)
    close_gate = any(check_in_polygon(c, out_area) for c in car_centers)
    
    if(open_gate == True or close_gate == True):
        await notify_gas(open_gate, close_gate, parking_status)
        
        
        
    park_info = {
        "action": "subscribe",
        "timestamps": time.time(),
        "slot": total_parking,
        "Empty": empty_slots,
        "Car amount": occupied_slots,
        "info": parking_status,
        "open_gate": open_gate,
        "close_gate": close_gate
    }

    frame_overlay = draw_parking_view(frame.copy(), car_centers, park_info["info"], park_info)
    cv2.imshow("Parking View", frame_overlay)
    cv2.waitKey(1)

    return park_info


async def handler(websocket):
    print("Client connected!")
    try:
        async for message in websocket:
            data = json.loads(message)

            # client subscribe
            if data.get("action") == "subscribe":
                ctype = data.get("type", "web")
                clients[ctype].add(websocket)
                await websocket.send(json.dumps({"msg": f"Subscribed as {ctype}"}))

            elif data.get("action") == "frame":
                print("Pi server connect!")
                frame_data = base64.b64decode(data["data"])
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                frame = cv2.resize(frame, (640, 480))

                park_info = await process_frame(frame)

                for ctype, cset in clients.items():
                    to_remove = []
                    for ws in cset:
                        try:
                            await ws.send(json.dumps(park_info))
                        except:
                            to_remove.append(ws)
                    for ws in to_remove:
                        cset.remove(ws)
    except Exception as e:
        print(f"Client error: {e}")
        for cset in clients.values():
            if websocket in cset:
                cset.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 5000):
        print("Server started ws://0.0.0.0:5000")
        await asyncio.Future()

asyncio.run(main())
