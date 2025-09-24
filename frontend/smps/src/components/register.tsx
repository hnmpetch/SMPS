"use client";


import { useState } from 'react';
import { registerUser } from '../api/userApi';
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

        if (user.password == user.confirm_password){
            setMatch(true);
        } else{
            setMatch(false)
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess(false);
        try {
            await registerUser(user);
            setSuccess(true);
            toast.success("Register successful!")
            setTimeout(() => {
                location.replace('/login')
            }, 300)
        } catch (err) {
            setError('Registration failed');
            toast.error("Fail to register")
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className='relative w-auto h-full rounded-lg overflow-hidden text-black m-10 items-center transition'>
            <form onSubmit={handleSubmit} className='login-form `w-full h-full rounded bg-gray-200 inline-block items-center justify-center text-lg font-bold opacity-100 p-3 shadow-gray-300 shadow-2xs' >
                <h1 className='self-center text-center text-2xl m-2 mt-2'>Register</h1>
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
                    type="password"
                    name="password"
                    value={user.password}
                    onChange={handleChange}
                    className='block bg-gray-100 w-full p-2 rounded-lg mt-2'
                    placeholder='Password'
                />
                <label className='block mt-2' >Confirm Password</label>
                <input
                    type="password"
                    name="confirm_password"
                    value={user.confirm_password}
                    onChange={handleChange}
                    className='block bg-gray-100 w-full p-2 rounded-lg mt-2'
                    placeholder='Confirm Password'
                />
                <a onClick={() => setHint(!hint)} className='text-sm mt-2'>{hint ? "Hide password" : "Show password"}</a>
                <p className='text-red-400 mt-2'>{match ? '' : 'Password do not match'}</p>

                <label className='block mt-2'>Email</label>
                <input
                    type="email"
                    name="email"
                    value={user.email}
                    onChange={handleChange}
                    className='block bg-gray-100 w-full p-2 rounded-lg mt-2'
                    placeholder='Email'
                />

                <button type="submit" disabled={loading} className='submit-btn block bg-green-300 w-2xs p-2 rounded-lg mt-4'>
                    {loading ? 'Registering...' : 'Register'}
                </button>
            </form>

        </div>
    );
}
