"use client";

import React, { useState, useEffect, useRef, useCallback, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// ══════════════════════════════════════════════════════════════════════
// PERFORMANCE CONFIGURATION & UTILS
// ══════════════════════════════════════════════════════════════════════

const isBrowser = typeof window !== 'undefined';
const IS_CODESPACES = isBrowser && (window.location.hostname.includes('github.dev') ||
    window.location.hostname.includes('app.github.dev'));

const IS_CLOUD_ENV = isBrowser && (IS_CODESPACES ||
    window.location.hostname.includes('gitpod.io') ||
    window.location.hostname.includes('repl.it'));

const RAW_API_ORIGIN = process.env.NEXT_PUBLIC_API_URL ?? '';
const WS_ORIGIN = process.env.NEXT_PUBLIC_WS_URL ?? '';
const resolveApiOrigin = () => {
    if (RAW_API_ORIGIN) return RAW_API_ORIGIN;
    if (!isBrowser) return '';
    const { protocol, hostname, port } = window.location;
    if (port === '3000') {
        return `${protocol}//${hostname}:8000`;
    }
    return '';
};
const API_ORIGIN = resolveApiOrigin();
const apiUrl = (path) => `${API_ORIGIN}${path}`;
const isDevEnvironment = process.env.NODE_ENV === 'development';
const logWebSocketEvent = (...args) => {
    if (isDevEnvironment) {
        console.info(...args);
    }
};
const resolveWebSocketProtocol = (protocol) => {
    if (protocol === 'https:') return 'wss:';
    if (protocol === 'http:') return 'ws:';
    if (protocol === 'wss:' || protocol === 'ws:') return protocol;
    return 'ws:';
};
const buildWebSocketUrl = (baseUrl, endpoint, token) => {
    const wsUrl = new URL(endpoint, baseUrl);
    wsUrl.searchParams.set('token', token);
    return wsUrl.toString();
};
const buildWebSocketUrlSafe = (baseUrl, endpoint, token) => {
    try {
        return buildWebSocketUrl(baseUrl, endpoint, token);
    } catch (error) {
        logWebSocketEvent('Invalid WebSocket URL parts', error);
        return '';
    }
};

const getWsBase = () => {
    if (!isBrowser) return '';
    const configuredOrigin = WS_ORIGIN || API_ORIGIN;
    if (configuredOrigin) {
        try {
            const parsed = new URL(configuredOrigin);
            const wsProtocol = resolveWebSocketProtocol(parsed.protocol);
            return `${wsProtocol}//${parsed.host}`;
        } catch (error) {
            logWebSocketEvent('Invalid WebSocket base configuration:', error);
            return '';
        }
    }
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.host;
    return `${protocol}://${host}`;
};

const generateId = () => Math.random().toString(36).substr(2, 9) + Date.now().toString(36);

// ══════════════════════════════════════════════════════════════════════
// COMPONENTS
// ══════════════════════════════════════════════════════════════════════

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }
    static getDerivedStateFromError(error) { return { hasError: true }; }
    componentDidCatch(error, errorInfo) { console.error("React Error:", error, errorInfo); }
    render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: '20px', color: 'var(--error-color)', textAlign: 'center' }}>
                    <h2>⚠️ Interface Error</h2>
                    <button onClick={() => window.location.reload()} style={{ width: 'auto', marginTop: '10px' }}>Reload</button>
                </div>
            );
        }
        return this.props.children;
    }
}

const preprocessMath = (content) => {
    if (!content) return "";

    // 1. Replace block delimiters \[ ... \] with $$ ... $$
    let processed = content.replace(/\\\[([\s\S]*?)\\\]/g, '$$$$$1$$$$');

    // 2. Replace inline delimiters \( ... \) with $ ... $
    processed = processed.replace(/\\\(([\s\S]*?)\\\)/g, '$$$1$$');

    return processed;
};

const Markdown = memo(({ content }) => {
    const safeContent = (content || "");
    const processedContent = preprocessMath(safeContent);

    return (
        <div className="markdown-content">
            <ReactMarkdown
                remarkPlugins={[remarkMath]}
                rehypePlugins={[rehypeKatex]}
            >
                {processedContent}
            </ReactMarkdown>
        </div>
    );
});
Markdown.displayName = 'Markdown';

// ══════════════════════════════════════════════════════════════════════
// HOOKS
// ══════════════════════════════════════════════════════════════════════

/**
 * Legendary Chat Hook: Manages WebSocket connection, reconnection, and state.
 */
const useChat = (endpoint, token, onConversationUpdate) => {
    const [messages, setMessages] = useState([]);
    const [status, setStatus] = useState('disconnected'); // disconnected, connecting, connected, error
    const [conversationId, setConversationId] = useState(null);
    const socketRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const mountedRef = useRef(true);
    const lastConnectionIssueRef = useRef(null);

    const addMessage = useCallback((msg) => {
        setMessages(prev => [...prev, msg]);
    }, []);

    const notifyConnectionIssue = useCallback((message) => {
        if (lastConnectionIssueRef.current === message) return;
        lastConnectionIssueRef.current = message;
        addMessage({ id: generateId(), role: 'assistant', content: message, isError: true });
    }, [addMessage]);

    const handleMessage = useCallback((data) => {
        const { type, payload } = data;

        if (type === 'status') return;

        if (type === 'conversation_init') {
            if (payload?.conversation_id) {
                setConversationId(payload.conversation_id);
            }
            if (onConversationUpdate) onConversationUpdate();
            return;
        }

        if (type === 'error') {
            const details = payload?.details || 'Unknown error';
            addMessage({ id: generateId(), role: 'assistant', content: `Error: ${details}`, isError: true });
            return;
        }

        if (type === 'delta') {
            const content = payload?.content || '';
            if (!content) return;

            setMessages(prev => {
                const last = prev[prev.length - 1];
                if (last && last.role === 'assistant' && !last.isComplete && !last.isError) {
                    // Append to last message
                    const updated = { ...last, content: last.content + content };
                    return [...prev.slice(0, -1), updated];
                } else {
                    if (last && last.role === 'user') {
                        return [...prev, { id: generateId(), role: 'assistant', content: content, isComplete: false }];
                    }
                     return [...prev, { id: generateId(), role: 'assistant', content: content, isComplete: false }];
                }
            });
            return;
        }

        if (type === 'complete') {
             setMessages(prev => {
                const last = prev[prev.length - 1];
                if (last && last.role === 'assistant') {
                    return [...prev.slice(0, -1), { ...last, isComplete: true }];
                }
                return prev;
            });
        }
    }, [onConversationUpdate, setConversationId, addMessage]);

    const connect = useCallback(() => {
        if (!token || !endpoint || !mountedRef.current) return;
        if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) return;

        const wsBase = getWsBase();
        if (!wsBase) {
            setStatus('error');
            notifyConnectionIssue('تعذر تحديد عنوان WebSocket. تحقق من إعدادات الاتصال.');
            return;
        }

        setStatus('connecting');
        const wsUrl = buildWebSocketUrlSafe(wsBase, endpoint, token);
        if (!wsUrl) {
            setStatus('error');
            notifyConnectionIssue('تعذر بناء رابط WebSocket. تحقق من إعدادات الاتصال.');
            return;
        }

        try {
            const socket = new WebSocket(wsUrl);
            socketRef.current = socket;

            socket.onopen = () => {
                if (mountedRef.current) setStatus('connected');
                lastConnectionIssueRef.current = null;
                logWebSocketEvent('WebSocket connected');
            };

            socket.onmessage = (event) => {
                if (!mountedRef.current) return;
                try {
                    const parsed = JSON.parse(event.data);
                    handleMessage(parsed);
                } catch (e) {
                    logWebSocketEvent('WebSocket parse warning', e);
                }
            };

            socket.onclose = (e) => {
                logWebSocketEvent('WebSocket closed', e.code, e.reason);
                if (mountedRef.current) {
                    setStatus('disconnected');
                    if (e.code !== 1000 && e.code !== 4403 && e.code !== 4401) {
                        clearTimeout(reconnectTimeoutRef.current);
                        reconnectTimeoutRef.current = setTimeout(connect, 3000);
                    }
                }
            };

            socket.onerror = (e) => {
                logWebSocketEvent('WebSocket error', e);
                if (mountedRef.current) setStatus('error');
                notifyConnectionIssue('تعذر الاتصال بالخادم. سيتم إعادة المحاولة تلقائيًا.');
            };

        } catch (err) {
            logWebSocketEvent("WebSocket creation failed", err);
            setStatus('error');
            notifyConnectionIssue('تعذر إنشاء اتصال WebSocket. تحقق من إعدادات الشبكة.');
        }
    }, [token, endpoint, handleMessage, notifyConnectionIssue]);

    useEffect(() => {
        mountedRef.current = true;
        connect();
        return () => {
            mountedRef.current = false;
            if (socketRef.current) socketRef.current.close();
            clearTimeout(reconnectTimeoutRef.current);
        };
    }, [connect]);

    const sendMessage = useCallback((text) => {
        if (!text.trim()) return;

        if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
             addMessage({ id: generateId(), role: 'assistant', content: 'Connection lost. Please wait...', isError: true });
             connect();
             return;
        }

        addMessage({ id: generateId(), role: 'user', content: text });
        addMessage({ id: generateId(), role: 'assistant', content: '', isComplete: false });

        const payload = { question: text };
        if (conversationId) payload.conversation_id = String(conversationId);

        socketRef.current.send(JSON.stringify(payload));

    }, [conversationId, connect, addMessage]);

    const clearMessages = () => setMessages([]);
    const setMessagesSafe = (msgs) => setMessages(msgs);

    return { messages, sendMessage, status, conversationId, setConversationId, clearMessages, setMessages: setMessagesSafe };
};

// ══════════════════════════════════════════════════════════════════════
// MAIN APP COMPONENT
// ══════════════════════════════════════════════════════════════════════

const App = () => {
    const [token, setToken] = useState(null);
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const storedToken = localStorage.getItem('token');
        if (storedToken) setToken(storedToken);
        else setIsLoading(false);
    }, []);

    useEffect(() => {
        const fetchUser = async () => {
            if (token) {
                try {
                    const response = await fetch(apiUrl('/api/security/user/me'), {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (response.ok) {
                        setUser(await response.json());
                    } else {
                        logout();
                    }
                } catch (error) {
                    console.error("Failed to fetch user:", error);
                    logout();
                } finally {
                    setIsLoading(false);
                }
            } else {
                setIsLoading(false);
            }
        };
        fetchUser();
    }, [token]);

    const handleLogin = (newToken, userData) => {
        localStorage.setItem('token', newToken);
        setToken(newToken);
        setUser(userData);
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
        window.location.reload();
    };

    if (isLoading) return <div className="loading-screen"><i className="fas fa-circle-notch fa-spin"></i><h2>Initializing Reality Kernel...</h2></div>;
    if (!token || !user) return <AuthScreen onLogin={handleLogin} />;

    return <DashboardLayout user={user} onLogout={logout} />;
};

// ══════════════════════════════════════════════════════════════════════
// DASHBOARD & LAYOUT
// ══════════════════════════════════════════════════════════════════════

const DashboardLayout = ({ user, onLogout }) => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [theme, setTheme] = useState('dark');
    const [conversations, setConversations] = useState([]);
    const [isLoadingConvs, setIsLoadingConvs] = useState(false);
    const menuRef = useRef(null);

    const endpoint = user.is_admin ? '/admin/api/chat/ws' : '/api/chat/ws';
    const convEndpoint = user.is_admin ? '/admin/api/conversations' : '/api/chat/conversations';
    const historyEndpoint = user.is_admin ? (id) => `/admin/api/conversations/${id}` : (id) => `/api/chat/conversations/${id}`;

    // Callback to refresh conversations list
    const fetchConversations = useCallback(async () => {
        const token = localStorage.getItem('token');
        try {
            const res = await fetch(apiUrl(convEndpoint), {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) setConversations(await res.json());
        } catch (e) { console.error(e); }
    }, [convEndpoint]);

    useEffect(() => {
        fetchConversations();
    }, [fetchConversations]);

    const { messages, sendMessage, status, conversationId, setConversationId, clearMessages, setMessages } = useChat(endpoint, localStorage.getItem('token'), fetchConversations);

    const loadConversation = async (id) => {
        setIsSidebarOpen(false); // Close mobile sidebar
        setConversationId(id);
        const token = localStorage.getItem('token');
        try {
            const res = await fetch(apiUrl(historyEndpoint(id)), {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setMessages(data.messages || []);
                setConversationId(data.conversation_id);
            }
        } catch (e) { console.error(e); }
    };

    const handleNewChat = () => {
        clearMessages();
        setConversationId(null);
        setIsSidebarOpen(false);
        setIsMenuOpen(false); // Close menu if open
    };

    useEffect(() => {
        const storedTheme = localStorage.getItem('theme');
        const initialTheme = storedTheme === 'light' ? 'light' : 'dark';
        setTheme(initialTheme);
    }, []);

    useEffect(() => {
        if (typeof document === 'undefined') return;
        document.documentElement.dataset.theme = theme;
        document.documentElement.dir = 'rtl';
        localStorage.setItem('theme', theme);
    }, [theme]);

    useEffect(() => {
        const handleOutsideClick = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleOutsideClick);
        return () => document.removeEventListener('mousedown', handleOutsideClick);
    }, []);

    const handleToggleTheme = () => {
        setTheme((prevTheme) => (prevTheme === 'dark' ? 'light' : 'dark'));
        setIsMenuOpen(false);
    };

    const handleOpenConversations = () => {
        setIsSidebarOpen(true);
        setIsMenuOpen(false);
    };

    const handleLogout = () => {
        setIsMenuOpen(false);
        onLogout();
    };

    return (
        <div className="app-container">
            <div className="header">
                <div className="header-title">
                    <h2>
                        {user.is_admin ? 'OVERMIND CLI' : 'Overmind Education'}
                        <span className="header-status">
                            {status === 'connected' ? <span className="status-online">● Online</span> : <span className="status-offline">● {status}</span>}
                        </span>
                    </h2>
                </div>
                <div className="header-actions" ref={menuRef}>
                    <button
                        className="header-menu-btn"
                        onClick={() => setIsMenuOpen((prev) => !prev)}
                        aria-expanded={isMenuOpen}
                        aria-haspopup="true"
                        type="button"
                    >
                        <i className="fas fa-ellipsis-v"></i>
                    </button>
                    {isMenuOpen && (
                        <div className="header-menu" role="menu">
                            <button type="button" className="header-menu-item" onClick={handleNewChat} role="menuitem">
                                <i className="fas fa-plus"></i>
                                <span>New Chat</span>
                            </button>
                            <button type="button" className="header-menu-item" onClick={handleOpenConversations} role="menuitem">
                                <i className="fas fa-history"></i>
                                <span>المحادثات السابقة</span>
                            </button>
                            <button type="button" className="header-menu-item" onClick={handleToggleTheme} role="menuitem">
                                <i className={`fas ${theme === 'dark' ? 'fa-sun' : 'fa-moon'}`}></i>
                                <span>{theme === 'dark' ? 'الوضع النهاري' : 'الوضع المظلم'}</span>
                            </button>
                            <button type="button" className="header-menu-item" onClick={handleLogout} role="menuitem">
                                <i className="fas fa-sign-out-alt"></i>
                                <span>تسجيل الخروج</span>
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <div className="dashboard-layout">
                <div className={`sidebar-overlay ${isSidebarOpen ? 'visible' : ''}`} onClick={() => setIsSidebarOpen(false)}></div>
                <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
                     <div className="sidebar-header">
                        <h3>المحادثات</h3>
                        <button className="close-sidebar-btn" onClick={() => setIsSidebarOpen(false)}>
                            <i className="fas fa-times"></i>
                        </button>
                     </div>
                     <div className="conversation-list">
                         {conversations.map(conv => (
                             <div
                                 key={conv.conversation_id}
                                 className={`conversation-item ${conversationId === conv.conversation_id ? 'active' : ''}`}
                                 onClick={() => loadConversation(conv.conversation_id)}
                             >
                                 <i className="fas fa-comment-alt conversation-item__icon"></i>
                                 {conv.title || `Chat ${conv.conversation_id}`}
                             </div>
                         ))}
                     </div>
                </div>

                <div className="chat-area">
                    <ChatInterface
                        messages={messages}
                        onSendMessage={sendMessage}
                        status={status}
                        user={user}
                    />
                </div>
            </div>
        </div>
    );
};

const ChatInterface = ({ messages, onSendMessage, status, user }) => {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef(null);
    const messagesContainerRef = useRef(null);
    const [autoScroll, setAutoScroll] = useState(true);

    const scrollToBottom = useCallback(() => {
        if (messagesEndRef.current) {
             // Use scrollIntoView with 'auto' for instant update during streaming to prevent jitter
             // or 'smooth' only for new messages.
             // But for streaming 'auto' is often better to avoid the "machine gun" smooth-scroll lag.
             messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
        }
    }, []);

    // Smart scroll handling
    useEffect(() => {
        if (autoScroll) {
            const container = messagesContainerRef.current;
            if (container) {
                // If we are close to bottom, snap to bottom
                const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 150;
                if (isNearBottom) {
                    container.scrollTop = container.scrollHeight;
                }
            }
        }
    }, [messages, autoScroll]);

    const handleScroll = () => {
        const container = messagesContainerRef.current;
        if (container) {
            const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 50;
            setAutoScroll(isNearBottom);
        }
    };

    const handleSend = () => {
        if (!input.trim()) return;
        setAutoScroll(true); // Re-enable auto-scroll on send
        onSendMessage(input);
        setInput('');
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="chat-container">
            <div className="messages" ref={messagesContainerRef} onScroll={handleScroll}>
                {messages.length === 0 ? (
                    <div className="welcome-message">
                         <i className={`fas ${user.is_admin ? 'fa-brain' : 'fa-graduation-cap'}`} style={{fontSize: '3em', color: 'var(--primary-color)', marginBottom: '20px'}}></i>
                        <h3>{user.is_admin ? 'System Ready' : 'Welcome Student'}</h3>
                        <p>{user.is_admin ? 'The Overmind is listening.' : 'Ask me anything about your studies.'}</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={msg.id || idx} className={`message ${msg.role}`}>
                            <div className="message-bubble">
                                {msg.role === 'assistant' ? <Markdown content={msg.content} /> : msg.content}
                            </div>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>
            <div className="input-area">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="اكتب سؤالك..."
                    rows="1"
                    disabled={status !== 'connected'}
                />
                <button onClick={handleSend} disabled={status !== 'connected' || !input.trim()}>
                    <i className="fas fa-arrow-up"></i>
                </button>
            </div>
        </div>
    );
};

// ══════════════════════════════════════════════════════════════════════
// AUTH COMPONENTS (Simplified)
// ══════════════════════════════════════════════════════════════════════

const AuthScreen = ({ onLogin }) => {
    const [isLogin, setIsLogin] = useState(true);
    return (
        <div className="login-container">
            {isLogin ? <LoginForm onLogin={onLogin} onToggle={() => setIsLogin(false)} /> : <RegisterForm onToggle={() => setIsLogin(true)} />}
        </div>
    );
};

const LoginForm = ({ onLogin, onToggle }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await fetch(apiUrl('/api/security/login'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            if (res.ok) {
                const data = await res.json();
                onLogin(data.access_token, data.user);
            } else {
                setError((await res.json()).detail || 'Login failed');
            }
        } catch (e) { setError('Connection failed'); }
        finally { setLoading(false); }
    };

    return (
        <div className="login-form">
            <form onSubmit={handleSubmit}>
                <h2>Login</h2>
                {error && <div className="error-message">{error}</div>}
                <div className="input-group"><input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" required /></div>
                <div className="input-group"><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" required /></div>
                <button disabled={loading}>{loading ? '...' : 'Login'}</button>
            </form>
            <div className="toggle-form"><a onClick={onToggle}>Register</a></div>
        </div>
    );
};

const RegisterForm = ({ onToggle }) => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await fetch(apiUrl('/api/security/register'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ full_name: name, email, password })
            });
            if (res.ok) {
                alert('Registration successful');
                onToggle();
            } else {
                setError((await res.json()).detail || 'Failed');
            }
        } catch (e) { setError('Error'); }
        finally { setLoading(false); }
    };

    return (
        <div className="register-form">
            <form onSubmit={handleSubmit}>
                <h2>Register</h2>
                {error && <div className="error-message">{error}</div>}
                <div className="input-group"><input value={name} onChange={e=>setName(e.target.value)} placeholder="Name" required /></div>
                <div className="input-group"><input value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" required /></div>
                <div className="input-group"><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" required /></div>
                <button disabled={loading}>{loading ? '...' : 'Register'}</button>
            </form>
            <div className="toggle-form"><a onClick={onToggle}>Login</a></div>
        </div>
    );
};

export default function CogniForgeApp() {
    return (
        <ErrorBoundary>
            <App />
        </ErrorBoundary>
    );
}
