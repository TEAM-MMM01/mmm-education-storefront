# Mac Disk Space Clearing Guide

**Current status:** 16 GiB free of 228 GiB (80% used)
**Goal:** Clear space for macOS update

---

## SAFE TO DELETE (no risk)

### DMG installers (already installed)
| File | Size | Action |
|---|---|---|
| `~/LM-Studio-0.4.19-2-arm64.dmg` | 543 MB | Delete — LM Studio already installed |
| `HermesOS-Vault/02 Areas/HermesOS/Obsidian-1.12.7.dmg` | ~200 MB | Delete — Obsidian already installed |

### Old backups
| File | Size | Action |
|---|---|---|
| `~/.hermes/backups/pre-update-2026-08-08-182028.zip` | 261 MB | Delete — old pre-update backup |

### Archive.zip in vault
| File | Size | Action |
|---|---|---|
| `HermesOS-Vault/Archive.zip` | 1.2 GB | Delete — old vault archive |

### Duplicate collectibles zip
| File | Size | Action |
|---|---|---|
| `Collectibles 4 Sale/1.-20260722T024713Z-1-001.zip` | ~100 MB | Delete if duplicate of vault copy |

**Total safe to delete: ~2.3 GB**

---

## CAN CLEAR (safe but optional)

### Browser caches
| Location | Size | Action |
|---|---|---|
| `~/Library/Caches/Comet` | 342 MB | Clear — browser cache rebuilds |
| `~/Library/Caches/Google/Chrome` | 4.0 GB | Clear Chrome cache (not profile) |

### App caches
| Location | Size | Action |
|---|---|---|
| `~/Library/Application Support/Code` (cache only) | ~500 MB | Clear VS Code cache |
| `~/Library/Application Support/Claude` (cache) | ~200 MB | Clear Claude cache |

### MobileSync backup
| Location | Size | Action |
|---|---|---|
| `~/Library/Application Support/MobileSync/Backup` | 1.0 GB | Delete old iPhone backup if synced to iCloud |

**Total can clear: ~6 GB**

---

## DO NOT DELETE

| File | Size | Why |
|---|---|---|
| `~/.opencode/bin/opencode` | 137 MB | Active tool |
| `~/.kimi-code/bin/kimi` | 169 MB | Active tool |
| `~/.codex/plugins/.plugin-appserver/codex` | 255 MB | Active tool |
| `~/.bun/bin/bun` | 60 MB | Active runtime |
| `~/.lmstudio/bin/lms` | 62 MB | Active tool |
| `HermesOS-Vault/` | 3.0 GB | Active vault (but Archive.zip inside can go) |

---

## RECOMMENDED ACTIONS

### Run these commands to clear space:

```bash
# Delete DMGs (already installed)
rm ~/LM-Studio-0.4.19-2-arm64.dmg
rm "HermesOS-Vault/02 Areas/HermesOS/Obsidian-1.12.7.dmg"

# Delete old backup
rm ~/.hermes/backups/pre-update-2026-08-08-182028.zip

# Delete vault archive
rm ~/HermesOS-Vault/Archive.zip

# Clear browser cache
rm -rf ~/Library/Caches/Comet

# Clear Chrome cache (keeps profile)
rm -rf ~/Library/Caches/Google/Chrome

# Clear VS Code cache
rm -rf ~/Library/Application\ Support/Code/CachedData
rm -rf ~/Library/Application\ Support/Code/Cache

# Empty trash
osascript -e 'tell application "Finder" to empty the trash'
```

**Expected recovery: ~3-5 GB**

---

## AFTER CLEARING

Run this to check new space:
```bash
df -h / | tail -1
```

If still low, consider:
- Moving `HermesOS-Vault/` to an external drive (saves 3 GB)
- Clearing `~/Library/Application Support/MobileSync/Backup` (saves 1 GB)
