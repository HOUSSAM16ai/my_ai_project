import { useState, useRef, useCallback, useEffect } from 'react';

const isBrowser = typeof window !== 'undefined';
const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL ?? '';
const WS_ORIGIN = process.env.NEXT_PUBLIC_WS_URL ?? '';

const logWebSocketEvent = (...args) => {
    if (process.env.NODE_ENV === 'development') {
        console.info(...args);
    }
};

const resolveWebSocketProtocol = (protocol) => {
    if (protocol === 'https:') return 'wss:';
    if (protocol === 'http:') return 'ws:';
    if (protocol === 'wss:' || protocol === 'ws:') return protocol;
    return 'ws:';
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

const buildWebSocketUrlSafe = (baseUrl, endpoint, token) => {
    try {
        const wsUrl = new URL(endpoint, baseUrl);
        wsUrl.searchParams.set('token', token);
        return wsUrl.toString();
    } catch (error) {
        logWebSocketEvent('Invalid WebSocket URL parts', error);
        return '';
    }
};

const generateId = () => Math.random().toString(36).substr(2, 9) + Date.now().toString(36);

export const useAgentSocket = (endpoint, token, onConversationUpdate) => {
    const [messages, setMessages] = useState([]);
    const [status, setStatus] = useState('disconnected');
    const [conversationId, setConversationId] = useState(null);
    const [agentStates, setAgentStates] = useState({
        strategist: { status: 'idle', progress: 0 },
        architect: { status: 'idle', progress: 0 },
        operator: { status: 'idle', progress: 0 },
        auditor: { status: 'idle', progress: 0 },
        supervisor: { status: 'idle' },
        contextualizer: { status: 'idle', progress: 0 }
    });

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

    const updateAgentState = useCallback((agent, newState) => {
        setAgentStates(prev => ({
            ...prev,
            [agent.toLowerCase()]: { ...prev[agent.toLowerCase()], ...newState }
        }));
    }, []);

    const handleMessage = useCallback((data) => {
        const { type, payload } = data;

        if (type === 'status') return;

        // Handle Agent Events
        if (type === 'phase_start') {
            const { phase, agent } = payload;
            if (agent) {
                updateAgentState(agent, { status: 'active', progress: 0, currentPhase: phase });
            }
            return;
        }

        if (type === 'phase_completed') {
            const { phase, agent } = payload;

            let agentName = agent ? agent.toLowerCase() : null;

            if (!agentName) {
                if (phase === 'PLANNING') agentName = 'strategist';
                if (phase === 'DESIGN') agentName = 'architect';
                if (phase === 'EXECUTION') agentName = 'operator';
                if (phase === 'REFLECTION') agentName = 'auditor';
                if (phase === 'CONTEXT_ENRICHMENT') agentName = 'contextualizer';
            }

            if (agentName) {
                 updateAgentState(agentName, { status: 'completed', progress: 100 });
            }
            return;
        }

        if (type === 'loop_start') {
             // Reset states for new loop?
             setAgentStates(prev => ({
                strategist: { status: 'pending', progress: 0 },
                architect: { status: 'pending', progress: 0 },
                operator: { status: 'pending', progress: 0 },
                auditor: { status: 'pending', progress: 0 },
                supervisor: { status: 'active' },
                contextualizer: { status: 'completed', progress: 100 } // Keep previous phases
             }));
             return;
        }

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
                    const updated = { ...last, content: last.content + content };
                    return [...prev.slice(0, -1), updated];
                } else {
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
            // Reset agents to idle
            setAgentStates({
                strategist: { status: 'idle', progress: 0 },
                architect: { status: 'idle', progress: 0 },
                operator: { status: 'idle', progress: 0 },
                auditor: { status: 'idle', progress: 0 },
                supervisor: { status: 'idle' },
                contextualizer: { status: 'idle', progress: 0 }
            });
        }
    }, [onConversationUpdate, setConversationId, addMessage, updateAgentState]);

    const connect = useCallback(() => {
        if (!token || !endpoint || !mountedRef.current) return;
        if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) return;

        const wsBase = getWsBase();
        if (!wsBase) {
            setStatus('error');
            notifyConnectionIssue('تعذر تحديد عنوان WebSocket.');
            return;
        }

        setStatus('connecting');
        const wsUrl = buildWebSocketUrlSafe(wsBase, endpoint, token);
        if (!wsUrl) {
            setStatus('error');
            notifyConnectionIssue('تعذر بناء رابط WebSocket.');
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
                notifyConnectionIssue('تعذر الاتصال بالخادم.');
            };

        } catch (err) {
            logWebSocketEvent("WebSocket creation failed", err);
            setStatus('error');
            notifyConnectionIssue('تعذر إنشاء اتصال WebSocket.');
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

    const sendMessage = useCallback((text, metadata = {}) => {
        if (!text.trim()) return;

        if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
             addMessage({ id: generateId(), role: 'assistant', content: 'Connection lost. Reconnecting...', isError: true });
             connect();
             return;
        }

        addMessage({ id: generateId(), role: 'user', content: text });

        const payload = { question: text, ...metadata };
        if (conversationId) payload.conversation_id = String(conversationId);

        socketRef.current.send(JSON.stringify(payload));

        // Initial agent state for a new mission
        if (metadata.mission_type === 'mission_complex') {
             setAgentStates({
                contextualizer: { status: 'active', progress: 0 },
                strategist: { status: 'pending', progress: 0 },
                architect: { status: 'pending', progress: 0 },
                operator: { status: 'pending', progress: 0 },
                auditor: { status: 'pending', progress: 0 },
                supervisor: { status: 'active' }
            });
        }

    }, [conversationId, connect, addMessage]);

    const clearMessages = () => setMessages([]);
    const setMessagesSafe = (msgs) => setMessages(msgs);

    return {
        messages,
        sendMessage,
        status,
        conversationId,
        setConversationId,
        clearMessages,
        setMessages: setMessagesSafe,
        agentStates
    };
};
