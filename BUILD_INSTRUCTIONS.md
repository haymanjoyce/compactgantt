# Building Windows Executable

## Prerequisites

1. Install Python 3.8+ with all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

## Building

### Option 1: Using the build script (Recommended)
```bash
build.bat
```

### Option 2: Manual build
```bash
pyinstaller compact_gantt.spec
```

## Output

The executable will be created in the `dist/` folder:
- `dist/CompactGantt.exe` - Single-file executable (ready to distribute)

## Distribution

Simply distribute the `CompactGantt.exe` file. Users can:
- Run it directly (no installation required)
- The app will create its own config/logs in user directories:
  - Config: `%APPDATA%\compact_gantt\settings.json`
  - Logs: `logs/` folder (created next to the .exe)

## File Size

The executable will be approximately 50-100MB (includes Python runtime and all dependencies).

## Troubleshooting

### "Module not found" errors
- Add missing modules to `hiddenimports` in `compact_gantt.spec`

### Icon not showing
- Ensure `assets/favicon.ico` exists
- Check that the icon path in the spec file is correct

### Large file size
- This is normal for PyInstaller one-file mode
- Consider using one-folder mode if size is a concern (modify spec file)

### Antivirus false positives
- Some antivirus software may flag PyInstaller executables
- This is a known issue with PyInstaller
- Consider code signing for production releases
