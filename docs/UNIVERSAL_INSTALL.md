# WFC Universal Installation

**WFC works with Claude Code, Kiro, or both simultaneously.**

## Quick Install

```bash
git clone https://github.com/sam-fakhreddine/wfc.git
cd wfc
./install-universal.sh
```

The installer detects your platform(s) and asks where to install.

---

## Installation Modes

### 1. Claude Code Only

```
~/.claude/skills/
├── wfc-review/
├── wfc-implement/
├── wfc-plan/
└── wfc/              # Shared resources
    ├── personas/
    └── shared/
```

**When to use:** You only have Claude Code installed

### 2. Kiro Only

```
~/.kiro/skills/
├── wfc-review/
├── wfc-implement/
├── wfc-plan/
└── wfc/              # Shared resources
    ├── personas/
    └── shared/
```

**When to use:** You only have Kiro installed

### 3. Both (Recommended)

```
~/.wfc/                                  # Source of truth
├── skills/
│   ├── wfc-review/
│   ├── wfc-implement/
│   └── ...
└── personas/

~/.claude/skills/
├── wfc-review -> ~/.wfc/skills/wfc-review  # Symlinks
├── wfc-implement -> ~/.wfc/skills/wfc-implement
└── wfc/personas -> ~/.wfc/personas

~/.kiro/skills/
├── wfc-review -> ~/.wfc/skills/wfc-review  # Symlinks
├── wfc-implement -> ~/.wfc/skills/wfc-implement
└── wfc/personas -> ~/.wfc/personas
```

**When to use:** You have both Claude Code and Kiro

**Benefits:**
- ✅ Single source of truth
- ✅ Updates automatically sync to both platforms
- ✅ Add custom personas once, available everywhere
- ✅ Consistent behavior across platforms

---

## Platform Compatibility

### Agent Skills Standard

WFC follows the [Agent Skills specification](https://agentskills.io), making it compatible with:
- ✅ Claude Code
- ✅ Kiro
- ✅ Any Agent Skills compliant platform

### Progressive Disclosure

WFC implements progressive disclosure for optimal performance:

| Metric | Traditional | Progressive | Savings |
|--------|-------------|-------------|---------|
| **Initial context** | ~43K tokens | ~3.4K tokens | **92.1%** |
| **Load time** | Slow | Fast | **10x faster** |
| **Memory usage** | High | Low | **90% less** |

**How it works:**
1. **Initial load** - Lightweight registry (IDs + summaries)
2. **On selection** - Full persona details loaded on-demand
3. **Caching** - Loaded personas cached for session

**Works with both:**
- Claude Code: Uses Read tool for on-demand loading
- Kiro: Native progressive disclosure support

---

## Usage

### In Claude Code

```bash
# Start Claude Code in your project
claude

# Use any WFC skill
/wfc-review
/wfc-implement
/wfc-plan
```

### In Kiro

```bash
# Start Kiro in your project
kiro

# Use any WFC skill
/wfc-review
/wfc-implement
/wfc-plan
```

### In Both Simultaneously

Changes made in one platform automatically sync to the other:

1. **Add custom persona in Claude Code:**
   ```bash
   # Add to ~/.wfc/personas/custom/MY_EXPERT.json
   ```

2. **Immediately available in Kiro:**
   ```bash
   # Can now use /wfc-review --personas MY_EXPERT
   ```

---

## Updating WFC

### With Symlinks (Both Installed)

```bash
cd ~/path/to/wfc-repo
git pull
./install-universal.sh

# Updates automatically sync to both Claude Code and Kiro
```

### Single Platform

```bash
cd ~/path/to/wfc-repo
git pull
./install-universal.sh

# Updates only the installed platform
```

---

## Verification

### Check Installation

```bash
# Claude Code
ls -la ~/.claude/skills/ | grep wfc

# Kiro
ls -la ~/.kiro/skills/ | grep wfc

# Source (if using symlinks)
ls -la ~/.wfc/
```

### Test Progressive Disclosure

```bash
# Run the savings calculator
python3 ~/.wfc/scripts/personas/progressive_registry.py

# Should show:
# Summaries only: ~3395 tokens
# Full personas:  ~43200 tokens
# Savings:        ~39805 tokens (92.1%)
```

---

## Troubleshooting

### Symlinks Not Working

**Issue:** Symlinks show as broken

**Fix:**
```bash
# Re-run installer
cd ~/path/to/wfc-repo
./install-universal.sh
```

### Skills Not Showing Up

**Issue:** WFC skills don't appear in Claude Code or Kiro

**Claude Code Fix:**
```bash
# Restart Claude Code
# Check installation
ls ~/.claude/skills/ | grep wfc
```

**Kiro Fix:**
```bash
# Restart Kiro
# Check installation
ls ~/.kiro/skills/ | grep wfc
```

### Progressive Disclosure Not Working

**Issue:** Full personas loading instead of summaries

**Fix:**
```bash
# Regenerate registry
python3 ~/.wfc/scripts/personas/progressive_registry.py

# Verify registry exists
ls ~/.wfc/references/personas/registry-progressive.json
```

---

## Uninstall

### Claude Code Only

```bash
rm -rf ~/.claude/skills/wfc*
```

### Kiro Only

```bash
rm -rf ~/.kiro/skills/wfc*
```

### Both (with symlinks)

```bash
# Remove symlinks
rm -rf ~/.claude/skills/wfc*
rm -rf ~/.kiro/skills/wfc*

# Remove source
rm -rf ~/.wfc
```

---

## Advanced: Manual Installation

If you prefer manual installation:

### Claude Code

```bash
# Copy individual skills
cp -r wfc/skills/wfc-review ~/.claude/skills/
cp -r wfc/skills/wfc-implement ~/.claude/skills/
# ... repeat for all skills

# Copy shared resources
mkdir -p ~/.claude/skills/wfc
cp -r wfc/personas ~/.claude/skills/wfc/
cp -r wfc/shared ~/.claude/skills/wfc/
```

### Kiro

```bash
# Same as Claude Code, but to ~/.kiro/skills/
```

### Both with Symlinks

```bash
# Create source directory
mkdir -p ~/.wfc
cp -r wfc/* ~/.wfc/

# Create symlinks for Claude Code
ln -s ~/.wfc/skills/wfc-review ~/.claude/skills/wfc-review
# ... repeat for all skills

# Create symlinks for Kiro
ln -s ~/.wfc/skills/wfc-review ~/.kiro/skills/wfc-review
# ... repeat for all skills
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding skills and personas that work across platforms.

---

**This is World Fucking Class.** 🏆

*Universal installation. Progressive disclosure. Maximum compatibility.*
