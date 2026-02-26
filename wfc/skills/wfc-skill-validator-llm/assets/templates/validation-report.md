# Skill Validation Report: {skill_name}

**Stage**: {stage}
**Run**: {run_timestamp}
**Cost**: {cost_estimate}

---

## Discovery Findings

### Positive Triggers (should fire)

| # | Prompt | Confidence |
|---|--------|------------|
{positive_triggers}

### Negative Triggers (should NOT fire)

| # | Prompt | Severity |
|---|--------|----------|
{negative_triggers}

### Description Critique

**Severity**: {critique_severity}

{description_critique}

### Suggested Rewrite

```
{suggested_rewrite}
```

---

## Summary

{summary}
