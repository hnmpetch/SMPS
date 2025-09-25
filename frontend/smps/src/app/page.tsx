import Image from "next/image";
import { useMemo } from 'react'
import { ParkingSlot, ParkingMap }from '../components/parkingMap';
import { Topbar } from "../components/topbar";

const slots: ParkingSlot[] = [
    { id: 1, label: '1', zone: 1, side: 'left', occupied: true, reserved: false, pay: true , join_at: 1111},
    { id: 2, label: '2', zone: 1, side: 'left', occupied: false, reserved: true, pay: true , join_at: 1111},
    { id: 3, label: '3', zone: 1, side: 'left', occupied: true, reserved: false, pay: true , join_at: 1111},
    { id: 4, label: '4', zone: 1, side: 'right', occupied: true, reserved: false, pay: true , join_at: 1111},
    { id: 5, label: '5', zone: 1, side: 'right', occupied: true, reserved: false, pay: true , join_at: 1111},
    { id: 6, label: '6', zone: 1, side: 'right', occupied: false, reserved: false, pay: true , join_at: 1111},

];

export default function Home() {

  const emptyCount = useMemo(() => slots.filter(s => !s.occupied && !s.reserved).length, []);
  const totalCount = slots.length;

  return (
    <div className="">
      <Topbar emptyCount={emptyCount} totalCount={totalCount} />
      <ParkingMap slots={slots} />
    </div>
  );
}
