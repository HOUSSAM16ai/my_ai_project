import React from 'react';

const AgentCard = ({ name, role, status, progress, icon }) => {
    const getStatusColor = () => {
        if (status === 'active') return 'var(--primary-color)';
        if (status === 'completed') return 'var(--success-color)';
        if (status === 'error') return 'var(--error-color)';
        if (status === 'pending') return 'var(--warning-color)';
        return 'var(--text-secondary)';
    };

    const isIdle = status === 'idle';

    return (
        <div className={`agent-card ${status}`} style={{ opacity: isIdle ? 0.6 : 1 }}>
            <div className="agent-header">
                <div className="agent-icon-wrapper" style={{ borderColor: getStatusColor() }}>
                    <i className={`fas ${icon}`} style={{ color: getStatusColor() }}></i>
                </div>
                <div className="agent-info">
                    <h4>{name}</h4>
                    <span className="agent-role">{role}</span>
                </div>
                <div className="agent-status-icon">
                    {status === 'active' && <i className="fas fa-circle-notch fa-spin" style={{color: 'var(--primary-color)'}}></i>}
                    {status === 'completed' && <i className="fas fa-check-circle" style={{color: 'var(--success-color)'}}></i>}
                    {status === 'pending' && <i className="fas fa-hourglass-half" style={{color: 'var(--warning-color)'}}></i>}
                </div>
            </div>
            {!isIdle && (
                <div className="agent-progress-container">
                    <div
                        className="agent-progress-bar"
                        style={{
                            width: `${status === 'completed' ? 100 : Math.max(5, progress)}%`,
                            backgroundColor: getStatusColor()
                        }}
                    />
                </div>
            )}
            <div className="agent-status-text">
                {status === 'active' ? 'جارٍ العمل...' :
                 status === 'completed' ? 'تم الإنجاز' :
                 status === 'pending' ? 'في الانتظار' : ''}
            </div>
        </div>
    );
};

export const AgentStatusBoard = ({ agentStates }) => {
    // If no complex mission is active, we might want to hide it, or show "System Ready"
    // But per requirements, we want visibility.
    // The "hasActivity" check in previous code hid it if all idle.
    // Let's keep it visible if at least one agent is not idle.
    const hasActivity = Object.values(agentStates).some(s => s && s.status !== 'idle');

    if (!hasActivity) return (
        <div style={{ padding: '1rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
            <p>لا توجد مهام نشطة حالياً.</p>
        </div>
    );

    return (
        <div className="agent-board-container">
            <h3 className="agent-board-title">مجلس الحكمة (Super Agents)</h3>
            <div className="agent-board">
                 <AgentCard
                    name="المُثري السياقي"
                    role="Contextualizer"
                    status={agentStates.contextualizer?.status || 'idle'}
                    progress={agentStates.contextualizer?.progress || 0}
                    icon="fa-search-location"
                />
                <AgentCard
                    name="المخطط الاستراتيجي"
                    role="Strategist"
                    status={agentStates.strategist.status}
                    progress={agentStates.strategist.progress}
                    icon="fa-chess-knight"
                />
                <AgentCard
                    name="المصمم المعماري"
                    role="Architect"
                    status={agentStates.architect.status}
                    progress={agentStates.architect.progress}
                    icon="fa-drafting-compass"
                />
                <AgentCard
                    name="المنفذ التقني"
                    role="Operator"
                    status={agentStates.operator.status}
                    progress={agentStates.operator.progress}
                    icon="fa-robot"
                />
                <AgentCard
                    name="المدقق النوعي"
                    role="Auditor"
                    status={agentStates.auditor.status}
                    progress={agentStates.auditor.progress}
                    icon="fa-clipboard-check"
                />
            </div>
        </div>
    );
};
