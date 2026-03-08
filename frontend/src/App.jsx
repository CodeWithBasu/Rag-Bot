import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Upload from './components/Upload';
import Chat from './components/Chat';
import { LogOut, MessageSquare, UploadCloud } from 'lucide-react';
import './index.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'chat'

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  return (
    <Router>
      <div className="app-layout">
        <header className="navbar">
          <div className="logo">
            <h1>RAG<span>Bot</span></h1>
          </div>
          {token && (
            <button className="btn-secondary" onClick={handleLogout}>
              <LogOut size={16} /> Logout
            </button>
          )}
        </header>
        
        <main className="main-content">
          <Routes>
            <Route 
              path="/login" 
              element={!token ? <Login setToken={setToken} /> : <Navigate to="/dashboard" />} 
            />
            <Route 
              path="/dashboard" 
              element={
                token ? (
                  <div style={{width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
                    <div style={{display: 'flex', gap: '1rem', marginBottom: '2rem'}}>
                      <button 
                        className={activeTab === 'upload' ? 'btn-primary' : 'btn-secondary'} 
                        onClick={() => setActiveTab('upload')}
                      >
                        <UploadCloud size={18} /> Manage Documents
                      </button>
                      <button 
                        className={activeTab === 'chat' ? 'btn-primary' : 'btn-secondary'} 
                        onClick={() => setActiveTab('chat')}
                      >
                        <MessageSquare size={18} /> AI Chat
                      </button>
                    </div>
                    
                    {activeTab === 'upload' ? <Upload /> : <Chat />}
                  </div>
                ) : <Navigate to="/login" />
              } 
            />
            <Route 
              path="*" 
              element={<Navigate to={token ? "/dashboard" : "/login"} />} 
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
