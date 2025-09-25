"use client";

import React, { useState } from "react";
import { toast } from "react-toastify";

export type ParkingSlot = {
    id: number;
    label: string;
    reserved?: boolean;
    occupied?: boolean;
    zone: number;
    side: string;
    pay: boolean;
    join_at: number;
};

interface ParkingMapProps {
    slots: ParkingSlot[];
}

export const ParkingMap: React.FC<ParkingMapProps> = ({ slots }) => {
    
    const [ paypopup, setPaypopup ] = useState(false);

        
    const zones = Array.from(new Set(slots.map((s) => s.zone)));

    const HandleReserve: React.FC<{ slot:ParkingSlot }> = ({ slot }) => {

        if (slot.pay === false && slot.occupied === true) {
            setPaypopup(true)

        }


        return 0
    }

    const ParkingSlotBox: React.FC<{ slot: ParkingSlot }> = ({ slot }) => {
        let bg = "bg-green-300 hover:bg-green-500"; // ว่าง
        if (slot.occupied) bg = "bg-red-400 hover:bg-red-600"; // มีรถจอด
        else if (slot.reserved) bg = "bg-yellow-300 hover:bg-yellow-500"; // จองไว้แล้ว


        return (
            <a
                onClick={() => {
                    if (slot.occupied = true){
                        toast.error("ที่จอดรถนี้มีคนจองแล้ว")
                    }
                }}
                className={`flex h-20 items-center justify-center rounded-md shadow-xl ${bg} transition-all duration-300`}
            >
                <span className="font-bold text-2xl text-shadow-2xs">{slot.label}</span>
            </a>
            );
    };

    return (
    <div className="space-y-6 w-full max-w-6xl mx-auto p-2  rounded-lg">

        <div className={`${paypopup ? "block" : "hidden"} h-full w-full bg-black fixed left-0 top-0 z-50 opacity-60`} onClick={() => {setPaypopup(!paypopup)}}>

        </div>


        {zones.map((zone) => {
        const zoneSlots = slots.filter((s) => s.zone === zone);
        const leftSlots = zoneSlots.filter((s) => s.side === "left");
        const rightSlots = zoneSlots.filter((s) => s.side === "right");

        return (
            <div key={zone} className="p-4 bg-green-100 rounded-lg shadow-md">
                <h2 className="mb-4 text-xl font-bold text-center text-black">Zone {zone}</h2>
                <div className="grid grid-cols-2 gap-6">
                    {/* Left side */}
                    <div>
                        <h3 className="mb-2 text-center font-semibold text-black">Left</h3>
                        <div className="grid grid-cols-1 gap-3">
                            {leftSlots.map((slot) => (
                            <ParkingSlotBox key={slot.id} slot={slot} />
                            ))}
                        </div>
                    </div>

                    {/* Right side */}
                    <div>
                        <h3 className="mb-2 text-center font-semibold text-black">Right</h3>
                        <div className="grid grid-cols-1s gap-3">
                            {rightSlots.map((slot) => (
                            <ParkingSlotBox key={slot.id} slot={slot} />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
        })}
    </div>
    );
};

