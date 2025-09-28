"use client";

import { useMemo, useState, useEffect } from "react";
import { ParkingSlot, ParkingMap } from "../components/parkingMap";
import { Topbar } from "../components/topbar";

export default function Home() {
  const [slots, setSlots] = useState<ParkingSlot[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // เปิด websocket
  useEffect(() => {
    const socket = new WebSocket("ws://10.32.104.73:5000");
    setWs(socket);

    socket.onopen = () => {
      console.log("✅ Connected to server");
      socket.send(JSON.stringify({ action: "subscribe", type: "web" }));
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.info) {
          // อัปเดต slots จาก server
          setSlots(data.info);
        }
      } catch (err) {
        console.error("❌ Parse error:", err);
      }
    };

    socket.onclose = () => {
      console.log("❌ Disconnected");
    };

    return () => {
      socket.close();
    };
  }, []);

  // จำนวนที่ว่าง (ไม่นับ reserved)
  const emptyCount = useMemo(
    () => slots.filter((s) => !s.occupied && !s.reserved).length,
    [slots]
  );
  const totalCount = slots.length;

  return (
    <div className="">
      <Topbar emptyCount={emptyCount} totalCount={totalCount} />
      <ParkingMap slots={slots} />
    </div>
  );
}
