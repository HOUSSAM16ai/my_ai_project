import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { AgentStatusBoard } from './AgentStatusBoard';

const preprocessMath = (content) => {
    if (!content) return "";
    let processed = content.replace(/\\\[([\s\S]*?)\\\]/g, '$$$$$1$$$$');
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

const MissionSelector = ({ selected, onSelect }) => {
    const modes = [
        { id: 'chat', label: 'دردشة عادية', icon: 'fa-comments', color: '#3b82f6' },
        { id: 'mission_complex', label: 'المهمة الخارقة', icon: 'fa-rocket', color: '#8b5cf6' },
        { id: 'deep_analysis', label: 'تحليل عميق', icon: 'fa-brain', color: '#ec4899' },
        { id: 'code_search', label: 'برمجة وبحث', icon: 'fa-code', color: '#10b981' },
    ];

    return (
        <div className="mission-selector">
            {modes.map(mode => (
                <button
                    key={mode.id}
                    className={`mission-btn ${selected === mode.id ? 'active' : ''}`}
                    onClick={() => onSelect(mode.id)}
                    style={{ '--btn-color': mode.color }}
                >
                    <i className={`fas ${mode.icon}`}></i>
                    <span>{mode.label}</span>
                </button>
            ))}
        </div>
    );
};

export const ChatInterface = ({ messages, onSendMessage, status, user, agentStates }) => {
    const [input, setInput] = useState('');
    const [missionType, setMissionType] = useState('chat');
    const [isMissionSelected, setIsMissionSelected] = useState(false);
    const messagesEndRef = useRef(null);
    const messagesContainerRef = useRef(null);
    const [autoScroll, setAutoScroll] = useState(true);

    const scrollToBottom = useCallback(() => {
        if (messagesEndRef.current) {
             messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
        }
    }, []);

    useEffect(() => {
        if (autoScroll) {
            const container = messagesContainerRef.current;
            if (container) {
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
        setAutoScroll(true);
        onSendMessage(input, { mission_type: missionType });
        setInput('');
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleMissionSelect = (type) => {
        setMissionType(type);
        setIsMissionSelected(true);
    };

    return (
        <div className="chat-container">
            {/* Agent Visualization */}
            {agentStates && <AgentStatusBoard agentStates={agentStates} />}

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

            <div className="input-area-wrapper">
                {!isMissionSelected ? (
                    <div className="mission-selection-container">
                        <h4 className="mission-selection-title">اختر نوع المهمة للبدء</h4>
                        <MissionSelector selected={missionType} onSelect={handleMissionSelect} />
                    </div>
                ) : (
                    <>
                        <div className="selected-mission-bar">
                            <span>النمط المحدد: <strong>{missionType}</strong></span>
                            <button
                                onClick={() => setIsMissionSelected(false)}
                                className="change-mission-btn"
                            >
                                تغيير
                            </button>
                        </div>
                        <div className="input-area">
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={missionType === 'mission_complex' ? "اكتب مهمتك الخارقة..." : "اكتب سؤالك..."}
                                rows="1"
                                disabled={status !== 'connected'}
                            />
                            <button onClick={handleSend} disabled={status !== 'connected' || !input.trim()}>
                                <i className="fas fa-arrow-up"></i>
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
