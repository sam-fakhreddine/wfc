# WFC References

Reference documentation and data loaded on demand (progressive disclosure).

## Structure

```
references/
├── personas/                    # Persona definitions
│   ├── panels/                 # 54 expert personas (JSON)
│   ├── custom/                 # User-created personas  
│   └── registry.json           # Persona index
├── ARCHITECTURE.md              # Architecture docs
├── TOKEN_MANAGEMENT.md          # Token optimization guide
└── ULTRA_MINIMAL_RESULTS.md     # Performance results
```

## Progressive Disclosure

These files are NOT loaded at startup. They're loaded on demand when:
- A skill activates persona review
- Documentation is referenced
- Specialized knowledge is needed

This keeps initial context small while providing deep knowledge when needed.
