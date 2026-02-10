import React from "react";
import { useAgentTimeline } from "../hooks/useAgentTimeline";

const PHASE_LABELS = {
  contextualize: "فهم السؤال",
  plan: "وضع الخطة",
  research: "البحث",
  execute: "التنفيذ",
  review: "المراجعة",
};

export function AgentTimeline() {
  const events = useAgentTimeline();

  return (
    <div className="timeline">
      {Object.entries(PHASE_LABELS).map(([key, label]) => {
        const phaseEvents = events.filter(e => e.phase === key);
        const lastEvent = phaseEvents[phaseEvents.length - 1];

        const done = lastEvent && lastEvent.status === 'completed';
        const running = lastEvent && lastEvent.status === 'running';

        return (
          <div key={key} className={`step ${done ? 'completed' : running ? 'running' : ''}`}>
            <span className="step-icon">
              {done ? "✔" : running ? "●●●" : "○"}
            </span>
            <span className="step-label">{label}</span>
          </div>
        );
      })}
    </div>
  );
}
