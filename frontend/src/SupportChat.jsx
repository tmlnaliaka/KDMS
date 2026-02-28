import React, { useState, useRef, useEffect } from 'react'
import Markdown from 'react-markdown'
import { MessageSquare, X, Send, Bot, User } from 'lucide-react'
import './index.css'

export default function SupportChat({ api }) {
    const [isOpen, setIsOpen] = useState(false)
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello Admin. How can I assist you with KDMS today?' }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const endRef = useRef(null)

    useEffect(() => {
        if (endRef.current) {
            endRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages, isOpen])

    const sendMessage = async () => {
        if (!input.trim() || loading) return

        const userMsg = { role: 'user', content: input }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setLoading(true)

        try {
            const res = await fetch(`${api}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: [...messages, userMsg] })
            })
            const data = await res.json()
            setMessages(prev => [...prev, { role: 'assistant', content: data.reply }])
        } catch (e) {
            setMessages(prev => [...prev, { role: 'assistant', content: 'Connection failed. Please check backend.' }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="support-chat-widget">
            {!isOpen ? (
                <button className="chat-fab" onClick={() => setIsOpen(true)}>
                    <MessageSquare size={24} color="white" />
                </button>
            ) : (
                <div className="chat-window">
                    <div className="chat-header">
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Bot size={20} color="var(--accent-cyan)" />
                            <span style={{ fontWeight: 600 }}>KDMS Assistant</span>
                        </div>
                        <button className="icon-btn" onClick={() => setIsOpen(false)}>
                            <X size={18} />
                        </button>
                    </div>

                    <div className="chat-body">
                        {messages.map((m, i) => (
                            <div key={i} className={`chat-bubble ${m.role}`}>
                                {m.role === 'assistant' ? (
                                    <Markdown>{m.content}</Markdown>
                                ) : (
                                    m.content
                                )}
                            </div>
                        ))}
                        {loading && (
                            <div className="chat-bubble assistant typing">
                                <span className="dot"></span><span className="dot"></span><span className="dot"></span>
                            </div>
                        )}
                        <div ref={endRef} />
                    </div>

                    <div className="chat-footer">
                        <input
                            type="text"
                            placeholder="Ask about active events..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                        />
                        <button onClick={sendMessage} disabled={!input.trim() || loading}>
                            <Send size={18} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
