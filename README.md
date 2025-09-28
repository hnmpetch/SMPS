# Smart Parking System

This project is smart pparking system to check each car that in parking lot use yolo model to detect each car

This project will open websocket server at `main-server.py` and let `main-ras.py` connect and send data.
After main-ras.py send data main-server.py will show camera view and let process to check each slot and return status to main-ras.py to user servo and lcd.

webapp will connect websocket to main-server.py to get data and show slot

---

## Hardware

1. Rasberry pi 5
2. Camera
3. Notebook or Laptop or PC
4. lcd
5. servo

---

## Start

1. `git clone https://github.com/hnmpetch/SMPS.git`
2. `cd SMPS`
3. `pip install -r requirements.txt` install requirements
4. copy `main-ras.py` and install `pip install -r requirements.py`
5. run `setup.py` to setup
6. config file `config/config.yml`
7. run main-server.py `python3 main-server.py`
8. run main-ras.py `python3 main-ras.py`
9. `cd backend` (optional)
10. `npm i` (optional)
11. `cd ../frontend/smps`
12. `npm i` install requirements.
13. `npm run build` build product.
14. `npm run start` start webapp.
15. Create line message api server if you want.

---

### developer [HNM Studio](https://github.com/hnmpetch)