# GitHubGrid

A GitHub contribution calendar in your system tray.

| Platform | Implementation | Status |
|---|---|---|
| **Windows** | WPF / C# / .NET 8 | Original — see `*.cs`, `*.xaml` files |
| **Linux KDE** | Python / PyQt6 | New — see `github_grid/`, `github-grid` |

## Linux (KDE) — Quick Start

### 1. Install

```bash
git clone <repo-url>
cd GitHubGrid
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Authenticate

**Recommended — `gh` CLI (most secure):**
```bash
gh auth login
```

**Alternative — GitHub token:**
```bash
python3 setup-token.py
```

Token created at https://github.com/settings/tokens (no scopes required for public data).

The app checks credentials in this order:
1. `gh` CLI
2. KWallet / GNOME Keyring via `secret-tool`
3. `GITHUB_TOKEN` environment variable
4. `~/.config/github-grid/config.json`

### 3. Install to your system

```bash
./install-desktop.sh
```

This adds the app to:
- KDE application menu (Start Menu → Utilities → GitHubGrid)
- Autostart on login

### 4. Run

```bash
./github-grid
```

Left-click the tray icon to toggle the contribution grid popup.

## Windows

Open `GitHubGrid.csproj` in Visual Studio or build with `dotnet build`.

Requires:
- .NET 8
- `gh` CLI authenticated

## Uninstall

```bash
rm ~/.config/autostart/github-grid.desktop
rm ~/.local/share/applications/github-grid.desktop
rm -rf ~/.config/github-grid
```

## License

MIT
