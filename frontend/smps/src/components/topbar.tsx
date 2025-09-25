"use client";

import { useState } from "react";

interface TopBarProps {
    emptyCount: number,
    totalCount: number
};


export const Topbar:React.FC<TopBarProps> = ({emptyCount, totalCount}) => {
    
    const [menu, setmenu] = useState(false);

    

    return (
        <div>
            <nav className="inline-flex justify-between top-0 bg-gray-800 opacity-80 rounded-b-sm w-full h-10 z-40">
                <a onClick={() => setmenu(!menu)}>
                    <div className="grid absolute m-2 w-6 h-6">
                        <span className="bg-white w-full h-1 mt-0.5 rounded-2xl "></span>
                        <span className="bg-white w-full h-1 mt-0.5 rounded-2xl " ></span>
                        <span className="bg-white w-full h-1 mt-0.5 rounded-2xl "> </span>
                    </div>
                </a>

                <p className="text-xl text-black p-1 font-bold bg-white rounded-xs m-0.5 pl-2 pr-2" ><span className={
                    emptyCount / totalCount > 0.8
                    ? "text-green-500"
                    : emptyCount / totalCount > 0.5
                    ? "text-yellow-500"
                    : emptyCount / totalCount > 0.2
                    ? "text-orange-500"
                    : "text-red-500"
                } >{emptyCount} </span> / {totalCount}</p>
                <a>
                    <div className="bg-white rounded-full w-8 h-8 m-1 mr-2">
                        
                    </div>
                </a>
                
            </nav>
            <div className={`bg-white text-black w-2xs m-1 p-1 pr-2 h-lg rounded-2xl relative z-50 ${menu ? "inline-block" : "hidden"}`}>
                <a className="w-full h-full block m-1 p-2 hover:bg-gray-300 transition-all duration-100 rounded-xl">History</a>
                <a className="w-full h-full block m-1 p-2 hover:bg-gray-300 transition-all duration-100 rounded-xl">Help</a>
            </div>



        
        </div>
    )
}