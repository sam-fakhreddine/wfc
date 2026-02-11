# Entire.io Integration - Agent Session Capture

**Status**: ✅ IMPLEMENTED (OPTIONAL, HIGHLY RECOMMENDED)
**Security**: 🔒 LOCAL-ONLY by default, privacy-first
**Purpose**: Capture agent reasoning for debugging and cross-session learning

> 💡 **Note**: Entire.io is **OPTIONAL** but **HIGHLY RECOMMENDED**. It's disabled by default - you opt-in when you want agent session capture for debugging and learning.

---

## Why Optional But Recommended?

**Optional** because:
- Not everyone needs session capture
- Some prefer minimal tooling
- Privacy-conscious users can skip it
- Works perfectly fine without it

**Recommended** because:
- 🐛 **10x faster debugging** - Rewind to exact failure point
- 📚 **Cross-session learning** - Never repeat the same mistake
- 🔍 **Understand agent reasoning** - See "why" not just "what"
- 📊 **Retrospective analysis** - Improve over time

---

## What is Entire.io?

[Entire.io](https://entire.io) is an AI agent session capture platform that records agent decision-making, reasoning, and execution context. Think of it as "git for AI sessions" - it creates checkpoints of agent state that you can:

- **Rewind** to any phase (UNDERSTAND, TEST_FIRST, IMPLEMENT, etc.)
- **Analyze** agent reasoning and decision paths
- **Debug** failed implementations by reviewing session history
- **Learn** from past mistakes through cross-session analysis

---

## 🔒 Security & Privacy

**WFC's entire.io integration is designed with privacy as the top priority:**

### ✅ What's Safe

- ✅ **Sessions stored locally** - Never pushed to remote by default
- ✅ **Sensitive data redacted** - API keys, tokens, secrets automatically removed
- ✅ **No environment capture** - Environment variables not recorded
- ✅ **File size limits** - Large files (>100KB) excluded
- ✅ **Pattern exclusions** - `.env`, `.key`, `*secret*` automatically excluded
- ✅ **User-controlled push** - You explicitly approve remote sharing

### ❌ What's Protected

- ❌ **No auto-push** - Sessions never automatically sent to remote
- ❌ **No credentials** - API keys and tokens filtered out
- ❌ **No secrets** - Sensitive patterns automatically redacted
- ❌ **No large files** - Binary files and large artifacts excluded

### 🔐 Data Isolation

Sessions are stored on a **separate git branch** (`entire/checkpoints/v1`):

```
Main Repo:
├── main branch          ← Code only (clean)
│   ├── wfc/
│   └── tests/
│
├── entire/checkpoints/v1  ← Sessions (isolated)
│   ├── wfc-TASK-001-abc123/
│   │   ├── transcript.jsonl
│   │   ├── checkpoints/
│   │   └── summary.md
│   └── wfc-TASK-002-def456/
│
└── .worktrees/         ← Ephemeral (never committed)
```

---

## 📦 Installation

### Option 1: Homebrew (macOS/Linux)
```bash
brew install entireio/tap/entire
```

### Option 2: npm (Cross-platform)
```bash
npm install -g @entireio/cli
```

### Option 3: pip (Python)
```bash
pip install entireio-cli
```

Verify installation:
```bash
entire --version
```

---

## 🚀 Usage

### Enable Session Capture (OPT-IN)

Entire.io is **disabled by default**. Enable it when you want to debug agents or learn from failures.

**Option 1: CLI Flag (Recommended for one-time use)**
```bash
# Enable for this run only
wfc implement --tasks plan/TASKS.md --enable-entire
```

**Option 2: Configuration (For persistent enable)**
```bash
# Edit wfc.config.json
{
  "entire_io": {
    "enabled": true  // Change from false to true
  }
}

# Then run normally
wfc implement --tasks plan/TASKS.md
```

**When to enable:**
- 🐛 Debugging a failing agent
- 📚 Learning from past failures
- 🔍 Understanding agent decision-making
- 📊 Collecting data for retrospective analysis

### Configuration

WFC's entire.io integration is configured in `wfc.config.json`:

```json
{
  "entire_io": {
    "enabled": true,
    "local_only": true,
    "create_checkpoints": true,
    "checkpoint_phases": [
      "UNDERSTAND",
      "TEST_FIRST",
      "IMPLEMENT",
      "REFACTOR",
      "QUALITY_CHECK",
      "SUBMIT"
    ],
    "privacy": {
      "redact_secrets": true,
      "max_file_size": 100000,
      "exclude_patterns": [
        "*.env",
        "*.key",
        "*.pem",
        "*secret*",
        "*credential*",
        ".claude/*"
      ],
      "capture_env": false
    },
    "retention": {
      "max_sessions": 100,
      "auto_cleanup": true
    }
  }
}
```

### Disable Entire.io (Opt-Out)

```json
{
  "entire_io": {
    "enabled": false
  }
}
```

---

## 📊 View Sessions

### List All Sessions

```bash
entire status
```

### View Session Details

```bash
entire show wfc-TASK-001-abc123
```

### Rewind to Checkpoint

```bash
entire rewind <checkpoint-id>
```

---

## 🔄 TDD Phase Checkpoints

WFC automatically creates checkpoints after each TDD phase:

| Phase | Checkpoint | Metadata Captured |
|-------|-----------|-------------------|
| **UNDERSTAND** | ✅ | Confidence score, affected files |
| **TEST_FIRST** | ✅ | Test files created, initial test results |
| **IMPLEMENT** | ✅ | Implementation files, tests passing |
| **REFACTOR** | ✅ | Refactored status, complexity |
| **QUALITY_CHECK** | ✅ | Quality passed, issues found |
| **SUBMIT** | ✅ | Commit count, ready for review |

### Example Session Timeline

```
wfc-TASK-001-abc123/
├── checkpoint-1: UNDERSTAND (confidence: 85%)
├── checkpoint-2: TEST_FIRST (3 tests written)
├── checkpoint-3: IMPLEMENT (tests passing)
├── checkpoint-4: REFACTOR (code cleaned)
├── checkpoint-5: QUALITY_CHECK (0 issues)
└── checkpoint-6: SUBMIT (ready for review)
```

---

## 🔍 Debugging Failed Agents

When an agent fails, review its session to understand why:

```bash
# Get session ID from agent report
SESSION_ID="wfc-TASK-001-abc123"

# View full session
entire show $SESSION_ID

# Rewind to specific phase
entire rewind $SESSION_ID --checkpoint IMPLEMENT

# Analyze decision points
entire analyze $SESSION_ID
```

---

## 🌐 Sharing Sessions (Optional)

Sessions are **local-only by default**. To share with your team:

### Push to Remote (Requires Confirmation)

```bash
# WFC provides explicit push command
wfc push-sessions --confirm

# Or push manually
git push origin entire/checkpoints/v1
```

**⚠️ Warning:** Only push if you're certain no sensitive data is captured!

---

## 📈 Cross-Session Learning

WFC uses entire.io sessions for **cross-session learning**:

1. **Memory System** - Learn from past failures
2. **Retrospectives** - Analyze patterns across sessions
3. **Agent Improvement** - Identify common failure modes
4. **Knowledge Base** - Build repository-specific knowledge

```bash
# Run retrospective analysis
wfc retro --sessions-from entire

# Analyze common failures
wfc analyze-failures --source entire
```

---

## 🛡️ Safety Checklist

Before using entire.io, verify:

- [ ] ✅ Sessions stored on separate branch (`entire/checkpoints/v1`)
- [ ] ✅ No auto-push to remote (local-only by default)
- [ ] ✅ Sensitive data redacted (API keys, tokens, secrets)
- [ ] ✅ Environment variables NOT captured
- [ ] ✅ File size limits enforced (100KB max)
- [ ] ✅ Exclude patterns for sensitive files
- [ ] ✅ `.gitignore` blocks accidental session commits
- [ ] ✅ User confirmation required for remote push

---

## 🚫 Troubleshooting

### Sessions Not Captured

**Problem:** Entire.io not recording sessions

**Solution:**
1. Check if entire CLI is installed: `entire --version`
2. Verify configuration: `enabled: true` in `wfc.config.json`
3. Check agent logs for entire.io errors

### Sensitive Data Leaked

**Problem:** Worried about sensitive data in sessions

**Solution:**
1. Sessions are local-only by default
2. Review privacy settings in `wfc.config.json`
3. Add patterns to `exclude_patterns`
4. **Never** manually push `entire/checkpoints/v1` without review

### Storage Space

**Problem:** Sessions taking too much disk space

**Solution:**
1. Configure retention: `max_sessions: 50`
2. Enable auto-cleanup: `auto_cleanup: true`
3. Manually clean: `entire cleanup --older-than 30d`

---

## 📚 Additional Resources

- [Entire.io Documentation](https://docs.entire.io)
- [WFC Session Analysis](./RETROSPECTIVE.md)
- [WFC Memory System](./MEMORY.md)

---

## 🎯 Benefits

**What You Get:**
- ✅ Full visibility into agent reasoning
- ✅ Rewind capability for failed agents
- ✅ Cross-session learning data
- ✅ Debugging context for failures
- ✅ Retrospective analysis input

**What You Don't Risk:**
- ❌ No data leaks into main branch
- ❌ No sensitive info exposure
- ❌ No unwanted remote pushes
- ❌ No privacy violations
- ❌ No performance impact

---

**Motto:** "Your agent reasoning stays YOUR agent reasoning." 🔒
