import { useState, useRef, useCallback, useEffect } from 'react';
import { useRealtimeConnection } from './useRealtimeConnection';

const isBrowser = typeof window !== 'undefined';
const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL ?? '';
const WS_ORIGIN = process.env.NEXT_PUBLIC_WS_URL ?? (process.env.NODE_ENV === 'development' ? 'ws://127.0.0.1:8000' : '');

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
            console.error('Invalid WebSocket base configuration:', error);
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
        // Token is passed in header/protocol by useRealtimeConnection.
        // We add it to query param as well for compatibility if needed.
        if (token) wsUrl.searchParams.set('token', token);
        return wsUrl.toString();
    } catch (error) {
        console.error('Invalid WebSocket URL parts', error);
        return '';
    }
};

const generateId = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    return Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
};

export const useAgentSocket = (endpoint, token, onConversationUpdate) => {
    const [messages, setMessages] = useState([]);
    const [conversationId, setConversationId] = useState(null);
    const onConversationUpdateRef = useRef(onConversationUpdate);

    // Construct WebSocket URL
    const wsBase = getWsBase();
    const wsUrl = wsBase && endpoint ? buildWebSocketUrlSafe(wsBase, endpoint, token) : null;

    // Use the robust connection hook
    const { state: status, sendMessage: sendSocketMessage } = useRealtimeConnection(wsUrl, token);

    useEffect(() => {
        onConversationUpdateRef.current = onConversationUpdate;
    }, [onConversationUpdate]);

    const addMessage = useCallback((msg) => {
        setMessages(prev => [...prev, msg]);
    }, []);

    // Handle incoming events (decoupled from socket logic)
    useEffect(() => {
        const handler = (e) => {
            const { type, payload } = e.detail || {};

            if (type === 'conversation_init') {
                if (payload?.conversation_id) {
                    setConversationId(payload.conversation_id);
                }
                if (onConversationUpdateRef.current) onConversationUpdateRef.current();
            } else if (type === 'delta') {
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
            } else if (type === 'complete') {
                 setMessages(prev => {
                    const last = prev[prev.length - 1];
                    if (last && last.role === 'assistant') {
                        return [...prev.slice(0, -1), { ...last, isComplete: true }];
                    }
                    return prev;
                });
            } else if (type === 'error') {
                const details = payload?.details || 'Unknown error';
                addMessage({ id: generateId(), role: 'assistant', content: `Error: ${details}`, isError: true });
            }
        };

        window.addEventListener('agent:event', handler);
        return () => window.removeEventListener('agent:event', handler);
    }, [addMessage]);

    const sendMessage = useCallback((text, metadata = {}) => {
        if (!text.trim()) return;

        // Optimistic UI update
        addMessage({ id: generateId(), role: 'user', content: text });

        const payload = { question: text, ...metadata };
        if (conversationId) payload.conversation_id = String(conversationId);

        // Send via robust connection
        sendSocketMessage(payload);

    }, [conversationId, addMessage, sendSocketMessage]);

    const clearMessages = () => setMessages([]);
    const setMessagesSafe = (msgs) => setMessages(msgs);

    return {
        messages,
        sendMessage,
        status, // 'idle' | 'connecting' | 'connected' | 'degraded' | 'offline'
        conversationId,
        setConversationId,
        clearMessages,
        setMessages: setMessagesSafe,
        agentStates: {} // Deprecated
    };
};
