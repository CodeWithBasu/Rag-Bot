import React, { useState, useRef, useEffect } from 'react';
import API from '../api';
import { Send, User, Bot, Loader2, Database } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function Chat() {
    const [messages, setMessages] = useState([
        { role: 'assistant', text: "Hello! I've read your uploaded documents. What would you like to know?", sources: [] }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setLoading(true);

        try {
            const res = await API.post('/chat', 
                { query: userMsg }
            );

            setMessages(prev => [...prev, { 
                role: 'assistant', 
                text: res.data.answer, 
                sources: res.data.sources 
            }]);

        } catch (error) {
            console.error(error);
            let errorMsg = "Sorry, I encountered an error trying to search your documents. Please try again.";
            
            const detail = error.response?.data?.detail || "";
            if (detail.includes("429") || detail.includes("quota") || detail.includes("Quota")) {
                errorMsg = "⏳ The AI service is temporarily rate-limited (free-tier daily quota exceeded). Please try again in a few hours.";
            } else if (detail.includes("invalid_api_key") || detail.includes("Invalid API Key")) {
                errorMsg = "🔑 Your current AI API Key is invalid. Please update it in your backend .env file.";
            } else if (detail.includes("404") || detail.includes("not found")) {
                errorMsg = "⚠️ The AI model could not be found. Please check your API configuration.";
            } else if (error.code === "ERR_NETWORK") {
                errorMsg = "🔌 Cannot connect to the backend server. Please make sure it is running.";
            }
            
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                text: errorMsg
            }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="chat-container fade-in">
            <div className="chat-header">
                <h2>Chat with your AI Brain</h2>
                <p>Retrieval Augmented Generation active</p>
            </div>

            <div className="chat-messages">
                {messages.map((msg, index) => (
                    <div key={index} className={`message-wrapper ${msg.role}`}>
                        <div className="avatar">
                            {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                        </div>
                        <div className="message-content">
                            <div className="text">
                                {msg.role === 'assistant' ? (
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.text}
                                    </ReactMarkdown>
                                ) : (
                                    msg.text
                                )}
                            </div>
                            
                            {/* Sources Section - only if the AI used documents! */}
                            {msg.sources && msg.sources.length > 0 && (
                                <div className="sources-container">
                                    <Database size={12} className="source-icon"/>
                                    <span>Sources: </span>
                                    {msg.sources.map((src, i) => (
                                        <span key={i} className="source-tag">{src}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                
                {loading && (
                    <div className="message-wrapper assistant">
                        <div className="avatar">
                            <Bot size={20} />
                        </div>
                        <div className="message-content">
                            <Loader2 className="loading-spinner" size={24} />
                            <span className="loading-text">Searching your documents...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSend} className="chat-input-form">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask a question about your documents..."
                    disabled={loading}
                    className="chat-input"
                />
                <button type="submit" disabled={!input.trim() || loading} className="send-btn">
                    <Send size={20} />
                </button>
            </form>
        </div>
    );
}
