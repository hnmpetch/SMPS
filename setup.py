import os
import yaml
import cv2
import json
import numpy as np
from utils.log import log


# -----------------------------
# Config
# -----------------------------
config = os.path.join("config", "config.yml")
with open(config, "r", encoding="utf-8") as yml:
    config = yaml.safe_load(yml)
    
CAM_ID =  config["main"]["cam"]


# -----------------------------
# Video input
# -----------------------------
cap = cv2.VideoCapture(config['main']['cam'])
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

ret, frame = cap.read()
if not ret:
    log.error_event("❌ Error opening video")
    exit()

clone = frame.copy()
parking_slots = []        # List to store individual parking slot polygons
current_polygon = []      # Points for the polygon being drawn
main_area = []            # Overall parking area polygon
in_area = []
out_area = []
left_side = []
left_side_poly = []
right_side = []
right_side_poly = []
drawing_main = False      # Flag: Are we drawing the main parking area?
drawing_in = False
drawing_out = False
drawing_left = False
drawing_right = False

# -----------------------------
# Mouse callback to draw polygons
# -----------------------------
def draw_polygon(event, x, y, flags, param):
    global current_polygon, frame, parking_slots, main_area, drawing_main, in_area, out_area, drawing_in,drawing_out, drawing_right,drawing_left,left_side,left_side_poly,right_side_poly, right_side

    if event == cv2.EVENT_LBUTTONDOWN:
        current_polygon.append((x, y))

    elif event == cv2.EVENT_RBUTTONDOWN:
        if len(current_polygon) > 2:
            pts = np.array(current_polygon, np.int32).reshape((-1, 1, 2))
            color = (0, 255, 0) if not drawing_main else (0, 0, 255)  # Green = slot, Red = main area
            cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)

            if drawing_main:
                main_area.extend(current_polygon)
                log.log_event(f"Main parking area defined: {current_polygon}")
            elif drawing_in:
                in_area.extend(current_polygon)
                log.log_event(f"In area defined: {current_polygon}")
            elif drawing_out:
                out_area.extend(current_polygon)
                log.log_event(f"Out area defined: {current_polygon}")
            else:
                
                if drawing_right:
                    right_side_poly.append(current_polygon.copy())
                    
                    parking_slots.append({
                        "id": len(parking_slots) + 1,
                        "side": "right",
                        "label": str(len(parking_slots) + 1),
                        "zone": 0,
                        "pay": False,
                        "reserved": False,
                        "polygon": current_polygon.copy(),
                    })
                    
                    log.log_event(f"New slot right side zone 0 slot id {len(right_side_poly)}")
                elif drawing_left:
                    left_side_poly.append(current_polygon.copy())
                    parking_slots.append({
                        "id": len(parking_slots) + 1,
                        "side": "left",
                        "label": len(parking_slots) + 1,
                        "zone": 0,
                        "pay": False,
                        "reserve": False,
                        "polygon": current_polygon.copy(),
                    })
                    log.log_event(f"New slot left side zone 0 slot id {len(left_side_poly)}")
                    
                
                
                M = cv2.moments(pts)
                if M["m00"] != 0:
                    cx = int(M["m10"]/M["m00"])
                    cy = int(M["m01"]/M["m00"])
                    cv2.putText(frame, str(len(parking_slots)), (cx-10, cy+10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        current_polygon = []

# -----------------------------
# Setup window and instructions
# -----------------------------
cv2.namedWindow("Parking Setup")
cv2.setMouseCallback("Parking Setup", draw_polygon)

log.log_event("Instructions:")
log.log_event(" - Left click to add points")
log.log_event(" - Right click to finish polygon")
log.log_event(" - Press 'm' to toggle main parking area drawing")
log.log_event(" - Press 'c' to reset")
log.log_event(" - Press 'q' to quit")

while True:
    temp = frame.copy()

    # Draw polygon while in progress (blue)
    if len(current_polygon) > 1:
        pts = np.array(current_polygon, np.int32).reshape((-1, 1, 2))
        cv2.polylines(temp, [pts], isClosed=False, color=(255, 0, 0), thickness=2)

    cv2.imshow("Parking Setup", temp)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("m"):
        drawing_main = not drawing_main
        drawing_in = False
        drawing_out = False
        drawing_left = False
        drawing_right = False
        print("Drawing main area:", drawing_main)
    elif key == ord("i"):
        drawing_in = not drawing_in
        drawing_main = False
        drawing_out = False
        drawing_left = False
        drawing_right = False
        print("Drawing in area:", drawing_in)
    elif key == ord("o"):
        drawing_out = not drawing_out
        drawing_main = False      # Flag: Are we drawing the main parking area?
        drawing_in = False
        drawing_left = False
        drawing_right = False
        print("Drawing out area:", drawing_out)
    elif key == ord("r"):
        drawing_right = not drawing_right
        drawing_main = False      # Flag: Are we drawing the main parking area?
        drawing_in = False
        drawing_out = False
        drawing_left = False
        print("Drawing right area:", drawing_right)
    elif key == ord("l"):
        drawing_left = not drawing_left
        drawing_main = False      # Flag: Are we drawing the main parking area?
        drawing_in = False
        drawing_out = False
        drawing_right = False
        print("Drawing left area:", drawing_left)

    elif key == ord("c"):
        frame = clone.copy()
        parking_slots = []        # List to store individual parking slot polygons
        current_polygon = []      # Points for the polygon being drawn
        main_area = []            # Overall parking area polygon
        in_area = []
        out_area = []
        left_side = []
        left_side_poly = []
        right_side = []
        right_side_poly = []
        drawing_main = False      # Flag: Are we drawing the main parking area?
        drawing_in = False
        drawing_out = False
        drawing_left = False
        drawing_right = False
        print("Reset all")

    elif key == ord("q"):
        break

cv2.destroyAllWindows()
cap.release()


config_lot = os.path.join("config", "config_lot.json")
with open(config_lot, "w", encoding="utf-8") as w:
    
    park = {
        "main_area": main_area,
        "parking_lot": parking_slots,
        "in_area": in_area,
        "out_area": out_area,
    }
    
    w.write(json.dumps(park, indent=4))
    

log.log_event(f"✅ All parking slots: {parking_slots}")
log.log_event(f"✅ Main parking area:{main_area}")
log.log_event(f"✅ In point parking area:{in_area}")
log.log_event(f"✅ Out point parking area:{out_area}")
