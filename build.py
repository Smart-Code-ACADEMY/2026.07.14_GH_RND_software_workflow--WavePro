import subprocess
from pathlib import Path

# 4. Create a standalone executable with icon
try:
    subprocess.run(
        "pyinstaller --onefile --windowed --name WavePro "
        "--icon=..\\assets\\01_media\\01_icons\\icon.ico "
        "--distpath publish --workpath publish\\build "
        "--specpath publish main\\main.py",
        shell=True,
        check=True
    )

    # 5. Remove unnecessary files (keep only .exe)
    subprocess.run(
        'Get-ChildItem -Path .\\publish -Recurse | '
        'Where-Object { $_.Extension -ne ".exe" } | '
        'Remove-Item -Force -Recurse',
        executable="powershell.exe",
        shell=True,
        check=True
    )

    print("\nSUCCESS: Build and cleanup completed successfully!")

except subprocess.CalledProcessError as e:
    print(f"\nFAILED: {e}")