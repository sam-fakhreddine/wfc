# WFC Universal Installation

**WFC works with Claude Code, Kiro, or both simultaneously.**

## Quick Install

```bash
git clone https://github.com/sam-fakhreddine/wfc.git
cd wfc
./install.sh
```

The installer detects your platform(s) and asks where to install.

**Note:** `install.sh` is a symlink to `install-universal.sh` (the universal installer).

## CI/Non-Interactive Mode

For CI or automated installation, use the `--ci` flag:

```bash
./install.sh --ci
```

This skips all prompts and uses sensible defaults:
- Existing install: Refresh (keep settings)
- Branding: NSFW (World Fucking Class)
- Platform: All detected platforms

---

## Installation Modes

### 1. Claude Code Only

```
~/.claude/skills/
├── wfc-review/
├── wfc-implement/
├── wfc-plan/
├── wfc-safeguard/
├── wfc-rules/
├── wfc-playground/
├── ... (17 skills total)
└── wfc/              # Shared resources
    ├── personas/
    ├── shared/
    ├── scripts/hooks/       # Hook infrastructure
    └── templates/           # Reusable templates
```

**When to use:** You only have Claude Code installed

### 2. Kiro Only

```
~/.kiro/skills/
├── wfc-review/
├── wfc-implement/
├── wfc-plan/
├── wfc-safeguard/
├── wfc-rules/
├── wfc-playground/
├── ... (17 skills total)
└── wfc/              # Shared resources
    ├── personas/
    ├── shared/
    ├── scripts/hooks/       # Hook infrastructure
    └── templates/           # Reusable templates
```

**When to use:** You only have Kiro installed

### 3. Both (Recommended)

```
~/.wfc/                                  # Source of truth
├── skills/
│   ├── wfc-review/
│   ├── wfc-implement/
│   ├── wfc-safeguard/
│   ├── wfc-rules/
│   ├── wfc-playground/
│   └── ... (17 skills total)
├── personas/
├── scripts/hooks/                       # Hook infrastructure
└── templates/                           # Reusable templates

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

# Use any WFC skill (17 available)
/wfc-review
/wfc-implement
/wfc-plan
/wfc-safeguard
/wfc-rules
/wfc-playground
# ... and more
```

### In Kiro

```bash
# Start Kiro in your project
kiro

# Use any WFC skill (17 available)
/wfc-review
/wfc-implement
/wfc-plan
/wfc-safeguard
/wfc-rules
/wfc-playground
# ... and more
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
./install.sh

# Updates automatically sync to both Claude Code and Kiro
```

### Single Platform

```bash
cd ~/path/to/wfc-repo
git pull
./install.sh

# Updates only the installed platform
```

### What Gets Preserved During Updates

The installer preserves user customizations across updates:

- **User rules** (`.wfc/rules/`) - Custom rules defined via wfc-rules are never overwritten
- **Configuration** (`.wfc_branding`, `wfc.config.json`) - Settings preserved on refresh
- **Custom personas** - User-added personas in custom directories are retained

The installer also now installs additional infrastructure:
- **Hook system** (`scripts/hooks/`) - Extensible workflow hooks for patterns like post-review simplification and confidence filtering
- **Templates** (`templates/`) - Reusable templates including playground sandbox environments

---

## Reinstalling WFC

When you run the installer on an existing installation, you'll get reinstall options:

### 1. Refresh Installation

**Use when:** You want to update files but keep all settings

```bash
./install.sh

# Choose: "1) Refresh installation"
```

**What happens:**
- ✅ Updates all WFC files to latest version
- ✅ Keeps current branding mode
- ✅ Preserves all configuration
- ✅ Maintains symlinks and platform setup

**Best for:**
- Pulling latest updates from Git
- Fixing corrupted files
- Restoring deleted files

---

### 2. Change Branding Mode

**Use when:** You want to switch between SFW and NSFW modes

```bash
./install.sh

# Choose: "2) Change branding mode"
```

**What happens:**
- ✅ Keeps all files and configuration
- ✅ Prompts for new branding choice
- ✅ Updates branding config only
- ✅ Everything else stays the same

**Best for:**
- Moving from personal to corporate environment
- Switching teams or projects
- Testing both modes

---

### 3. Full Reinstall

**Use when:** You want to reset everything to defaults

```bash
./install.sh

# Choose: "3) Full reinstall"
```

**What happens:**
- ✅ Backs up current config to `~/.wfc_backup_TIMESTAMP/`
- ✅ Runs complete installation from scratch
- ✅ Prompts for all settings again
- ✅ Fresh start with clean configuration

**Best for:**
- Major troubleshooting
- Broken configuration
- Starting over with different setup

**Backup location:**
```bash
~/.wfc_backup_20260211_143022/.wfc_branding
```

---

### 4. Cancel

**Use when:** You don't want to make any changes

```bash
./install.sh

# Choose: "4) Cancel"
```

**What happens:**
- ✅ Exits installer without changes
- ✅ No files modified
- ✅ Configuration unchanged

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
./install.sh
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
