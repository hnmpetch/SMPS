"use client";


import { useState } from 'react';
import { loginUser } from '../api/authApi';
import './register.css'
import { toast } from 'react-toastify';

export default function RegisterComponent() {
    const [user, setUser] = useState({
        username: '',
        password: '',
        confirm_password: '',
        email: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [match, setMatch] = useState(true);
    const [hint, setHint] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setUser((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess(false);
        try {
            await loginUser(user);
            setSuccess(true);
            toast.success("Login Successful")
        } catch (err) {
            setError('Login failed');
            toast.error("Fail to login")
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className='relative w-auto h-full rounded-lg overflow-hidden text-black m-10 items-center transition'>
            <form onSubmit={handleSubmit} className='login-form `w-full h-full rounded bg-gray-200 inline-block items-center justify-center text-lg font-bold opacity-100 p-3 shadow-gray-300 shadow-2xs' >
                <h1 className='self-center text-center text-2xl m-2 mt-2'>Login</h1>
                <label className='block mt-2'>Name</label>
                <input
                    type="text"
                    name="username"
                    value={user.username}
                    onChange={handleChange}
                    className='block bg-gray-100 w-full p-2 rounded-lg mt-2'
                    placeholder='Username'
                />

                <label className='block mt-2' >Password</label>
                <input
                    type={hint ? "text" : "password"}
                    name="password"
                    value={user.password}
                    onChange={handleChange}
                    className='block bg-gray-100 w-full p-2 rounded-lg mt-2'
                    placeholder='Password'
                />
                <a onClick={() => setHint(!hint)} className='text-sm mt-2'>{hint ? "Hide password" : "Show password"}</a>

                <button type="submit" disabled={loading} className='submit-btn block bg-green-300 w-2xs p-2 rounded-lg mt-4'>
                    {loading ? 'Loging...' : 'Login'}
                </button>
            </form>

        </div>
    );
}
