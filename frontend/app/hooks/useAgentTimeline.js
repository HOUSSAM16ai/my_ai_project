import { useEffect, useState } from "react";

const PHASE_MAPPING = {
  'CONTEXT_ENRICHMENT': 'contextualize',
  'PLANNING': 'plan',
  'DESIGN': 'plan',
  'EXECUTION': 'execute',
  'REFLECTION': 'review',
  'RE-PLANNING': 'plan',
  'RESEARCH': 'research',
};

export function useAgentTimeline() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const handler = (e) => {
        const data = e.detail;
        if (!data || !data.type) return;

        if (data.type === 'phase_start' || data.type === 'phase_completed') {
            const { phase, agent, timestamp } = data.payload || {};
            if (!phase) return;

            const mappedPhase = PHASE_MAPPING[phase] || phase.toLowerCase();

            const newEvent = {
                phase: mappedPhase,
                status: data.type === 'phase_start' ? 'running' : 'completed',
                agent: agent,
                timestamp: timestamp
            };

            setEvents(prev => [...prev, newEvent]);
        }

        if (data.type === 'conversation_init') {
             setEvents([]);
        }
    };

    window.addEventListener("agent:event", handler);
    return () => window.removeEventListener("agent:event", handler);
  }, []);

  return events;
}
