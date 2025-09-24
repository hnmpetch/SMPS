import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import './alert.css';

type AlertProps = {
    message: string;
    type: 'success' | 'error';   // จำกัดค่า type
    timeout?: number;            // optional
    onClose?: () => void;        // optional callback
};

export default function AlertPopup ({ message, type, timeout = 3000, onClose }: AlertProps) {
    const [visible, setVisible] = useState(true);
    const delay = timeout / 100 * 90;

    useEffect(() => {
        const timer = setTimeout(() => {
            setVisible(false); // ซ่อน Popup
            setTimeout(() => {
                if (onClose) onClose(); // เรียก onClose หลังจากซ่อน Popup
            }, 300); // เพิ่มเวลาเล็กน้อยเพื่อให้ Animation เสร็จสมบูรณ์
        }, timeout);

        return () => clearTimeout(timer);
    }, [timeout, onClose]);

    const containerStyle = {
        color: type === 'success' ? '#22c55e' : '#ef4444', // green / red
        animationDelay: `${delay}ms`,
        animationDuration: `${timeout}ms`,
    };

    const timeoutbar = {
        backgroundColor: type === 'success' ? '#22c55e' : '#ef4444',
        animationDuration: `${timeout}ms`,
    };

    if (!visible) return null;

    return (
        <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1, right: 0 }}
            exit={{ scale: 0.8, opacity: 0, right: '-20px' }}
            style={containerStyle}
            className="alert-container"
        >
            <p style={{ fontSize: '20px', fontWeight: 'bold' }}>{message}</p>
            <div className="alert-progress" style={timeoutbar}></div>
        </motion.div>
    );
}