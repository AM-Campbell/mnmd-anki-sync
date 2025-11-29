# Editor Protocol Setup Guide

This guide explains how to set up custom URL protocol handlers for opening files from Anki.

## Quick Reference

| Editor | Works Out of Box? | Setup Required? |
|--------|------------------|-----------------|
| VS Code | ✅ Yes | No (auto-registered on install) |
| VSCodium | ✅ Yes | No (auto-registered on install) |
| Obsidian | ✅ Yes | No (auto-registered on install) |
| Neovim | ❌ No | Yes (see below) |
| File | ✅ Yes | No (uses system default) |

## Option 1: Use File Protocol (Easiest)

Set your editor to `file` and configure your system to open `.md` files with your preferred editor:

```bash
# In ~/.mnmdrc
editor_protocol: file
```

Then set Neovim as your default markdown editor using your system settings or `xdg-mime`:

```bash
# Linux
xdg-mime default nvim.desktop text/markdown

# Or create a desktop file (see below)
```

## Option 2: Register nvim:// Protocol (Linux)

### Step 1: Create a Handler Script

Create `/usr/local/bin/nvim-url-handler`:

```bash
#!/bin/bash
# Parse nvim:// URL and open file in Neovim

url="$1"

# Extract file path and line number from URL
# Format: nvim://open?file=/path/to/file&line=123
file=$(echo "$url" | sed -n 's/.*file=\([^&]*\).*/\1/p')
line=$(echo "$url" | sed -n 's/.*line=\([^&]*\).*/\1/p')

# Default to line 1 if not specified
if [ -z "$line" ]; then
    line=1
fi

# Open in terminal (adjust terminal command for your setup)
if [ -n "$file" ]; then
    # Choose your terminal emulator:

    # For kitty:
    kitty nvim "+$line" "$file"

    # For alacritty:
    # alacritty -e nvim "+$line" "$file"

    # For gnome-terminal:
    # gnome-terminal -- nvim "+$line" "$file"

    # For konsole:
    # konsole -e nvim "+$line" "$file"

    # For xterm:
    # xterm -e nvim "+$line" "$file"
fi
```

Make it executable:
```bash
sudo chmod +x /usr/local/bin/nvim-url-handler
```

### Step 2: Create Desktop Entry

Create `~/.local/share/applications/nvim-url-handler.desktop`:

```desktop
[Desktop Entry]
Type=Application
Name=Neovim URL Handler
Exec=/usr/local/bin/nvim-url-handler %u
StartupNotify=false
Terminal=false
MimeType=x-scheme-handler/nvim;
```

### Step 3: Register the Protocol

```bash
# Update desktop database
update-desktop-database ~/.local/share/applications/

# Set as default handler for nvim:// URLs
xdg-mime default nvim-url-handler.desktop x-scheme-handler/nvim

# Verify registration
xdg-mime query default x-scheme-handler/nvim
# Should output: nvim-url-handler.desktop
```

### Step 4: Test It

```bash
# Test from command line
xdg-open "nvim://open?file=/tmp/test.md&line=5"

# This should open /tmp/test.md at line 5 in Neovim
```

### Step 5: Configure mnmd-anki-sync

```bash
echo "editor_protocol: nvim" > ~/.mnmdrc
```

## Option 3: Register nvim:// Protocol (macOS)

### Using Automator

1. Open **Automator**
2. Create new **Application**
3. Add "Run Shell Script" action
4. Set shell to `/bin/bash`
5. Paste this script:

```bash
url="$1"
file=$(echo "$url" | sed -n 's/.*file=\([^&]*\).*/\1/p')
line=$(echo "$url" | sed -n 's/.*line=\([^&]*\).*/\1/p')

if [ -z "$line" ]; then
    line=1
fi

# Adjust terminal command for your setup
osascript -e "tell application \"Terminal\" to do script \"nvim '+$line' '$file'\""
```

6. Save as "NvimURLHandler.app" in `/Applications/`
7. Register the protocol:

```bash
# Create Info.plist for the app
# Then register with:
open -a "NvimURLHandler" "nvim://open?file=/tmp/test.md&line=5"
```

## Option 4: Use Existing Terminal Integration

Some terminal emulators support opening files directly. Check your terminal's documentation:

### Kitty

Kitty has built-in support. You can use:
```bash
kitty +kitten open_file.py /path/to/file:line
```

### WezTerm

WezTerm can be configured with URL handlers.

## Neovim GUI Alternatives

If you use a Neovim GUI, they may have their own protocol:

- **Neovide**: Supports command-line arguments
- **VimR**: Has macOS integration
- **Goneovim**: Has protocol support

## Troubleshooting

### URL Opens in Browser

Your protocol isn't registered. Follow the registration steps above.

### Terminal Doesn't Open

Adjust the terminal command in the handler script to match your terminal emulator.

### Permission Denied

Make sure the handler script is executable:
```bash
chmod +x /usr/local/bin/nvim-url-handler
```

### Protocol Not Recognized

Update the desktop database:
```bash
update-desktop-database ~/.local/share/applications/
```

## Alternative: Use File Protocol with Custom Opener

Instead of registering `nvim://`, you can use the `file` protocol and create a custom file opener:

```bash
# In ~/.mnmdrc
editor_protocol: file

# Then set your default text editor
xdg-mime default nvim.desktop text/markdown
xdg-mime default nvim.desktop text/plain
```

## Recommended Setup by Editor

| Editor | Recommended Protocol | Setup Complexity |
|--------|---------------------|------------------|
| VS Code | `vscode` | ⭐ None |
| VSCodium | `vscodium` | ⭐ None |
| Obsidian | `obsidian` | ⭐ None |
| Neovim (terminal) | `file` | ⭐⭐ System default |
| Neovim (terminal) | `nvim` | ⭐⭐⭐⭐ Custom handler |
| Neovim GUI | Check GUI docs | ⭐⭐⭐ Varies |

## Quick Commands

```bash
# Test protocol registration
xdg-mime query default x-scheme-handler/nvim

# List all protocol handlers
grep -r "x-scheme-handler" ~/.local/share/applications/

# Test URL opening
xdg-open "nvim://open?file=/tmp/test.md&line=5"

# Check desktop file
desktop-file-validate ~/.local/share/applications/nvim-url-handler.desktop
```

## Example Handler Scripts

### Minimal Script (No Line Number Support)

```bash
#!/bin/bash
file=$(echo "$1" | sed 's/nvim:\/\/open?file=//; s/&.*//')
kitty nvim "$file"
```

### Advanced Script (with Error Handling)

```bash
#!/bin/bash
set -e

url="$1"

if [ -z "$url" ]; then
    notify-send "Neovim Handler" "No URL provided"
    exit 1
fi

file=$(echo "$url" | sed -n 's/.*file=\([^&]*\).*/\1/p' | python3 -c "import sys, urllib.parse; print(urllib.parse.unquote(sys.stdin.read().strip()))")
line=$(echo "$url" | sed -n 's/.*line=\([^&]*\).*/\1/p')

if [ -z "$file" ]; then
    notify-send "Neovim Handler" "No file specified in URL"
    exit 1
fi

if [ ! -f "$file" ]; then
    notify-send "Neovim Handler" "File not found: $file"
    exit 1
fi

line=${line:-1}

# Open in new kitty window
kitty --detach nvim "+$line" "$file"
```

Save this as `/usr/local/bin/nvim-url-handler` and make it executable.
