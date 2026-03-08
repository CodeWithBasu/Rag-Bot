import React, { useState } from 'react';
import API from '../api';
import { User, Lock, Mail } from 'lucide-react';

export default function Login({ setToken }) {
    const [isLogin, setIsLogin] = useState(true);
    const [formData, setFormData] = useState({ username: '', email: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (isLogin) {
                const params = new URLSearchParams();
                params.append('username', formData.username);
                params.append('password', formData.password);

                const res = await API.post('/auth/login', params);
                setToken(res.data.access_token);
                localStorage.setItem('token', res.data.access_token);
            } else {
                await API.post('/auth/register', {
                    username: formData.username,
                    email: formData.email,
                    password: formData.password
                });
                setIsLogin(true); // Switch to login view after successful registration
                setError('Registration successful! Please login.');
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'An error occurred.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container fade-in">
            <div className="login-card">
                <h2>{isLogin ? 'Welcome Back' : 'Create an Account'}</h2>
                <p className="subtitle">{isLogin ? 'Login to access your bot' : 'Sign up to start chatting with your docs'}</p>

                {error && <div className={`alert ${error.includes('successful') ? 'success' : 'error'}`}>{error}</div>}

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="input-group">
                        <User size={18} className="input-icon" />
                        <input 
                            type="text" 
                            placeholder="Username" 
                            value={formData.username}
                            onChange={e => setFormData({...formData, username: e.target.value})}
                            required 
                        />
                    </div>
                    
                    {!isLogin && (
                        <div className="input-group">
                            <Mail size={18} className="input-icon" />
                            <input 
                                type="email" 
                                placeholder="Email" 
                                value={formData.email}
                                onChange={e => setFormData({...formData, email: e.target.value})}
                                required 
                            />
                        </div>
                    )}

                    <div className="input-group">
                        <Lock size={18} className="input-icon" />
                        <input 
                            type="password" 
                            placeholder="Password" 
                            value={formData.password}
                            onChange={e => setFormData({...formData, password: e.target.value})}
                            required 
                        />
                    </div>

                    <button type="submit" className="btn-primary login-btn" disabled={loading}>
                        {loading ? 'Submitting...' : (isLogin ? 'Sign In' : 'Sign Up')}
                    </button>
                    
                    <p className="switch-mode" onClick={() => { setIsLogin(!isLogin); setError(''); }}>
                        {isLogin ? "Don't have an account? Sign up" : "Already have an account? Log in"}
                    </p>
                </form>
            </div>
        </div>
    );
}
