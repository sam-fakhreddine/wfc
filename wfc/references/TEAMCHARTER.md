# TEAMCHARTER — Values Governance for WFC

## Mission Statement

Our mission is to revolutionize cloud operations by implementing Proactive Operations Driven by Governance. We empower teams with automation, reducing manual interventions and ensuring secure, efficient, and compliant environments. Through governance, innovation, and operational excellence, we enable scalable and transformative solutions for our stakeholders.

## Vision Statement

To be the industry leader in delivering trusted and scalable cloud solutions, setting the benchmark for automation, security, and operational excellence. As innovators and collaborators, we aim to exceed expectations, streamline operations, and become the most valued partner for our clients' success.

## Core Values

### 1. Innovation & Experimentation

We embrace creative thinking, new methodologies, and bold experimentation, ensuring fast and efficient delivery of solutions while using failure as a stepping stone for growth.

**How WFC enforces this:**
- ReflexionMemory captures learnings from failures, not just errors
- Plans are validated through IsThisSmart critique before implementation
- Future: Experiment mode (`--experiment`) for throwaway prototyping

### 2. Accountability & Simplicity

We take ownership of our actions, maintain a high Say:Do ratio, and focus on delivering impactful results with simplicity and clarity.

**How WFC enforces this:**
- Complexity-budget pre-gate flags implementations that exceed their rated complexity (S/M/L/XL)
- Say:Do ratio tracked in wfc-retro (estimated vs. actual task complexity)
- Plan validation flow ensures commitments are challenged before execution
- Immutable audit trails prove validation was performed

### 3. Teamwork & Collaboration

We foster a culture of collaboration, knowledge sharing, and mutual support, recognizing the strength of collective effort and openness to feedback.

**How WFC enforces this:**
- Multi-agent consensus review (5 expert personas per review)
- Plan validation uses two gates (IsThisSmart + Code Review) for multi-perspective feedback
- Review loop until 8.5+ weighted score ensures quality through collaboration
- Customer Advocate persona ensures stakeholder voice is heard

### 4. Continuous Learning & Curiosity

We stay curious, proactively develop skills, and ensure we remain leaders in IT innovations through learning and growth.

**How WFC enforces this:**
- ReflexionMemory persists learnings across sessions
- Values alignment tracking in memory entries enables retrospective analysis
- wfc-retro generates actionable recommendations tied to specific values

### 5. Customer Focus & Service Excellence

We listen actively to our customers, align solutions to their needs, and deliver exceptional service by combining adaptability with thought leadership.

**How WFC enforces this:**
- wfc-plan interview includes TEAMCHARTER questions: "Who is the customer?", "What does success look like from their perspective?"
- Customer Advocate persona reviews code for customer value delivery
- Tasks include Values Alignment field connecting work to customer outcomes

### 6. Trust & Autonomy

We cultivate trust, flexibility, and empowerment, enabling each team member to lead, execute, and drive change confidently.

**How WFC enforces this:**
- Agents operate with confidence thresholds (>=90% proceed, 70-89% ask, <70% stop)
- `--skip-validation` flag trusts users to make informed decisions (with audit trail)
- Backward-compatible schema changes ensure existing workflows aren't broken

## Machine-Readable Values

See `teamcharter_values.json` for the structured version that WFC agents load at runtime.
