import React, { useState } from 'react';
import myLogo from './my-logo.png';

export default function AuthPage({ onLoginSuccess }) {
    const [isLoginView, setIsLoginView] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');
        const endpoint = isLoginView ? '/login' : '/register';
        const url = `http://${window.location.hostname}:5000${endpoint}`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
                credentials: 'include'
            });
            const data = await response.json();
            if (!response.ok) { throw new Error(data.message || 'An error occurred.'); }
            if (isLoginView) {
                onLoginSuccess();
            } else {
                setMessage('Registration successful! Please log in.');
                setIsLoginView(true);
            }
        } catch (error) {
            setMessage(error.message || 'Failed to fetch. Is the backend server running?');
        }
    };

    return (
        <div className="auth-container">
            <header className="App-header" style={{ marginBottom: '40px' }}>
                <img src={myLogo} className="App-logo" alt="My Company Logo" />
                <h1>☁️ ColorCloud Trading Tool</h1>
            </header>
            <div className="auth-form">
                <h2>{isLoginView ? 'Login' : 'Register'}</h2>
                <form onSubmit={handleSubmit}>
                    <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" required />
                    <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
                    <button type="submit">{isLoginView ? 'Login' : 'Register'}</button>
                </form>
                {message && <p className="auth-message">{message}</p>}
                <button onClick={() => setIsLoginView(!isLoginView)} className="toggle-auth">
                    {isLoginView ? 'Need an account? Register' : 'Have an account? Login'}
                </button>
            </div>
        </div>
    );
}
