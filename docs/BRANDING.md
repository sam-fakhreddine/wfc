# WFC Branding Modes

WFC supports two branding modes to accommodate different environments and preferences.

## Modes

### SFW (Safe For Work) - "Workflow Champion"

**When to use:**
- Corporate/enterprise environments
- Client-facing work
- Professional settings where explicit language is inappropriate
- Teams with strict communication policies

**Characteristics:**
- Professional language throughout
- "Workflow Champion" branding
- Tagline: "Professional Multi-Agent Framework"
- Clean, corporate-friendly messaging

**Example messages:**
```
Success! Workflow Champion is ready.
Task completed successfully.
Quality checks failed. Please address issues.
```

---

### NSFW (Default) - "World Fucking Class"

**When to use:**
- Personal projects
- Startups with casual culture
- Environments that value directness over politeness
- Default choice for most users

**Characteristics:**
- Direct, no-bullshit language
- "World Fucking Class" branding
- Tagline: "Multi-Agent Framework That Doesn't Fuck Around"
- Unapologetically straightforward messaging

**Example messages:**
```
Success! World Fucking Class is ready.
Done. No bullshit.
Quality checks failed. Fix your shit.
```

---

## Selection During Installation

The installer prompts you to choose:

```
🎨 Choose branding mode:

1) SFW (Safe For Work)  → Workflow Champion
   └─ Professional language, corporate-friendly

2) NSFW (Default)        → World Fucking Class
   └─ Original branding, no bullshit

Choose mode (1-2) [default: 2]:
```

Your choice is saved in `~/.wfc/.wfc_branding` and applied across all platforms.

---

## Changing Branding Mode

### Option 1: Re-run Installer

```bash
cd /path/to/wfc
./install.sh
```

Choose a different mode when prompted. Your skills and configuration are preserved.

### Option 2: Manual Edit

Edit `~/.wfc/.wfc_branding`:

```bash
# For SFW mode
mode=sfw
name=Workflow Champion
tagline=Professional Multi-Agent Framework

# For NSFW mode
mode=nsfw
name=World Fucking Class
tagline=Multi-Agent Framework That Doesn't Fuck Around
```

---

## Technical Details

### Configuration File

Location: `~/.wfc/.wfc_branding`

Format:
```bash
# WFC Branding Configuration
mode=nsfw
name=World Fucking Class
tagline=Multi-Agent Framework That Doesn't Fuck Around
```

### Accessing Branding in Code

**Python (WFC Skills):**
```python
from wfc.shared.branding import get_branding, get_message

branding = get_branding()

if branding.is_sfw:
    print("Using SFW mode")

# Get branding-aware messages
print(get_message("success"))  # Adapts to mode
print(get_message("error"))    # Adapts to mode
```

**Bash (Scripts):**
```bash
source scripts/get_branding.sh

echo "$WFC_NAME"        # Auto-detects mode
echo "$WFC_MODE"        # "sfw" or "nsfw"

# Use branding-aware messages
wfc_message tagline
wfc_message success
```

---

## Philosophy

### Why Two Modes?

WFC was built with a direct, no-bullshit philosophy. But we recognize that:

1. **Corporate environments** have different standards
2. **Professional contexts** require different language
3. **Global teams** have diverse cultural norms

Rather than dilute the original vision, we offer both:
- **NSFW** preserves the unapologetic, direct approach
- **SFW** provides professional alternatives without losing functionality

### What Changes Between Modes?

**Only messaging and branding.** The functionality is identical:

| Aspect | Changes? |
|--------|----------|
| **Core functionality** | No - identical |
| **Quality standards** | No - same rigor |
| **Agent capabilities** | No - same 54 personas |
| **Performance** | No - same optimizations |
| **Messages/UI** | Yes - language adapts |
| **Documentation** | Yes - branding adapts |

### What Stays the Same?

- **Quality**: Both modes enforce the same standards
- **Rigor**: No compromise on technical excellence
- **Capabilities**: Full feature parity
- **Performance**: Identical optimization

---

## FAQs

**Q: Does SFW mode make WFC less capable?**
A: No. Only the messaging changes. Technical capabilities are identical.

**Q: Can I switch modes later?**
A: Yes. Re-run the installer or edit `~/.wfc/.wfc_branding`.

**Q: Does the mode affect my team?**
A: No. Each developer chooses their own mode locally. It only affects their CLI output.

**Q: What's the default?**
A: NSFW (World Fucking Class). It's the original vision and preferred mode.

**Q: Will documentation use my chosen mode?**
A: Generated documents (TASKS.md, PROPERTIES.md, etc.) adapt to your mode. External docs use NSFW by default.

**Q: Does branding affect Git commits?**
A: No. Git messages use neutral language regardless of mode.

---

## Examples

### SFW Mode Output

```
Workflow Champion: wfc-plan

✓ Task breakdown complete
  Generated: TASKS.md (5 tasks)
  Generated: PROPERTIES.md (3 properties)
  Generated: TEST-PLAN.md (8 tests)

Next: Execute with /wfc-implement

This is Workflow Champion.
Professional Multi-Agent Framework
```

### NSFW Mode Output

```
WFC: wfc-plan

✓ Task breakdown complete
  Generated: TASKS.md (5 tasks)
  Generated: PROPERTIES.md (3 properties)
  Generated: TEST-PLAN.md (8 tests)

Next: Execute with /wfc-implement

This is World Fucking Class.
Multi-Agent Framework That Doesn't Fuck Around
```

---

**Choose the mode that fits your environment. The quality never changes.**
