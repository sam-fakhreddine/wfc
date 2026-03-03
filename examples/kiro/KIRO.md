# Kiro — WFC Integration

## WFC Skills

WFC skills are installed at `~/.kiro/skills/wfc-*/`. Use them as slash commands.

### Core Commands

```
/wfc-review                       # 5-agent consensus code review
/wfc-build "feature description"  # Quick feature builder with TDD
/wfc-plan                         # Structured task breakdown
/wfc-implement                    # Parallel TDD execution
/wfc-security                     # STRIDE threat modeling
```

### Quality Standards

- Consensus Score ≥7.0 required to merge
- Security reviewer findings trigger Minority Protection Rule
- All code changes require `/wfc-review` before merge
