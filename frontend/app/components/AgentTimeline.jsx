import React from "react";
import { useAgentTimeline } from "../hooks/useAgentTimeline";

const PHASE_LABELS = {
  contextualize: "فهم السؤال",
  plan: "وضع الخطة",
  design: "تصميم الحل",
  research: "البحث",
  execute: "التنفيذ",
  review: "المراجعة",
  replan: "إعادة التخطيط",
};

export function AgentTimeline() {
  const phases = useAgentTimeline(); // Returns array of { phase, status }

  return (
    <div className="timeline">
      {Object.entries(PHASE_LABELS).map(([key, label]) => {
        // useAgentTimeline returns current status of phases directly
        const phaseInfo = phases.find(p => p.phase === key);

        const done = phaseInfo && phaseInfo.status === 'completed';
        const running = phaseInfo && phaseInfo.status === 'running';

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
