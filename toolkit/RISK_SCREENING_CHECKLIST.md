# Risk Screening Checklist (Technical)

*To be run before any live youth audit session.*

## 1. Model Configuration
- [ ] **Safety Filters**: Are the base model's safety filters enabled (e.g., OpenAI Moderation Endpoint)?
- [ ] **System Prompt**: Does the system prompt explicitly forbid generating illegal content?
- [ ] **Logging**: Is the logging system active and anonymized (no PII)?

## 2. Content Scope
- [ ] **Blocked Topics**: Have we blacklisted keywords related to CSAM, extreme violence, or self-harm?
- [ ] **Allowed Topics**: Is the scope of the audit clearly defined (e.g., "Cultural Bias in History")?

## 3. User Interface
- [ ] **Blur Filter**: Is the image blur filter active by default for generated images?
- [ ] **Panic Button**: Is the "Stop Session" button visible on all screens?
- [ ] **Help Link**: Does the "Help" button link to the local safeguarding officer's alert system?
