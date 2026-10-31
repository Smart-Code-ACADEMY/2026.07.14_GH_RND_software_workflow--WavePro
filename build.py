import shutil  # Removes folders and their contents.
import subprocess  # Runs PyInstaller.
import sys  # Uses the current Python interpreter.
from pathlib import Path  # Handles file and folder paths.

# Install PyInstaller in the active environment first: python -m pip install pyinstaller
# Run this file from any terminal with: python build_wavepro.py
PROJECT_ROOT = Path(__file__).resolve().parent  # Folder containing this script.

# --------------------------------------------------------------------------------------------------------------------------------------
# 1. Application configurations
# Add further dictionaries here to build more applications automatically.
# Use None for an optional parameter that should not be passed to PyInstaller.
EXE_CONFIG = [
    {
        "name": "WavePro",  # Resulting executable: WavePro.exe.
        "entry_point": "main/main.py",  # Application's main Python file.
        "onefile": True,  # Creates one EXE file.
        "windowed": True,  # Hides the console window for GUI apps.
        "icon": "../assets/01_media/01_icons/icon.ico",  # Executable icon.
        "distpath": "publish",  # Output folder.
        "workpath": "publish/build",  # Temporary build files.
        "specpath": "publish",  # Location of the .spec file.
        "add_data": None,  # No extra data files for WavePro.
    },
    # {
    #     "name": "EyeGuard",
    #     "entry_point": "main/main.py",
    #     "onefile": True,
    #     "windowed": True,
    #     "icon": "../assets/media/icons/icon.ico",
    #     "distpath": "publish",
    #     "workpath": "publish/build",
    #     "specpath": "publish",
    #     "add_data": [
    #         ("../assets/media/01_icons", "assets/media/01_icons"),
    #         ("../assets/media/02_figures", "assets/media/02_figures"),
    #         ("../assets/media/03_sounds", "assets/media/03_sounds"),
    #     ],
    # },
    # {
    #     "name": "EyeGuardConfigurator",
    #     "entry_point": "main/configurator.py",
    #     "onefile": True,
    #     "windowed": True,
    #     "icon": "../assets/media/icons/icon.ico",
    #     "distpath": "publish",
    #     "workpath": "publish/build",
    #     "specpath": "publish",
    #     "add_data": None,  # No extra data files for WavePro.
    # },
]


# --------------------------------------------------------------------------------------------------------------------------------------
# 2. Cleanup configuration
# Files and folders that must NOT be deleted during cleanup.
CLEANUP_CONFIG = {
    "enabled": True,  # True = cleanup enabled, False = disabled.

    "keep_extensions": [
        ".exe",   # Keep executable files.
        ".json",  # Keep JSON files.
        # ".txt",
        # ".xlsx",
    ],

    # "keep_names": [
    #     "templates",           # Keep this folder and all its contents.
    #     "active_config.json",  # Keep this specific file.
    # ],
}


# --------------------------------------------------------------------------------------------------------------------------------------
try:
    # 1. Detect the current Python version automatically
    python_version = ".".join(map(str, sys.version_info[:3]))

    # 2. Generate the requirements filename
    requirements_file = PROJECT_ROOT / f"requirements_python-{python_version}.txt"

    # 3. Export installed packages
    with open(requirements_file, "w", encoding="utf-8") as file:
        subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            stdout=file,
            check=True
        )

    print(f"SUCCESS: {requirements_file.name} exported!")

    # 4. Build all configured EXE applications
    for config in EXE_CONFIG:
        cmd = [sys.executable, "-m", "PyInstaller"]

        for key, flag in [("onefile", "--onefile"), ("windowed", "--windowed")]:
            if config[key]:
                cmd.append(flag)

        for key in ("name", "icon", "distpath", "workpath", "specpath"):
            if config[key] is not None:
                cmd.extend([f"--{key}", str(config[key])])

        for source, destination in config["add_data"] or []:
            cmd.extend(["--add-data", f"{source};{destination}"])

        cmd.append(config["entry_point"])

        print(f"BUILDING: {config['name']}...")
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)

        output = PROJECT_ROOT / config["distpath"] / f"{config['name']}.exe"
        if not output.is_file():
            raise FileNotFoundError(f"EXE not found: {output}")

    # 5. Cleanup after successful builds
    if CLEANUP_CONFIG["enabled"]:
        folder = (PROJECT_ROOT / "publish").resolve()

        if PROJECT_ROOT not in folder.parents:
            raise ValueError("Invalid cleanup directory")

        keep_extensions = {
            ext.lower() for ext in CLEANUP_CONFIG["keep_extensions"]
        }

        for item in folder.iterdir():
            if item.name in CLEANUP_CONFIG.get("keep_names", []):
                continue

            if item.is_file() and item.suffix.lower() in keep_extensions:
                continue

            if item.is_dir() and not item.is_symlink():
                shutil.rmtree(item)
            else:
                item.unlink()

    print("\nSUCCESS: Build and cleanup completed!")

except Exception as error:
    print(f"\nFAILED: {error}", file=sys.stderr)
    sys.exit(1)

# 6. Old text | 03_packing-app-commands
# --------------------------------------------------------------------------------------------------------------------------------------
# 1. Make sure that venv you are using is not moved, renamed or corrupted. If so delete venv, create new one, delete .idea project folder,
#    and set up this new installed interpreter for your project in pycharm.
#    1. remove old .venv from available interpreters in pycharm
#    2. configure you interpreted with that new .venv
#    3. open your project terminal
#    4. press "x" on local
#    5. make sure now stays e.g. "(.venv) PS C:\Users\Sicaja\Desktop\DB\06_DB-bussiness-and-bussiness-assets\2019.01.01_SmartCodeACADEMY_Official\2025.11.24_GitHub_PRJ_Scenify>
#
# 2. Install PyInstaller in your venv, otherwise it will use interpreter which already has it installed and it will make you a lot of troubles.
# pip install pyinstaller
#
# 3. Navigate to the folder where your main.py file is located:
# cd "C:\User..."
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 4. Create a standalone executable with icon
# pyinstaller --onefile --windowed --name WavePro --icon=..\assets\01_media\01_icons\icon.ico --distpath publish --workpath publish\build --specpath publish main\main.py
#
# 5. Optional for removing non necessary files -> run in pycharm terminal
# Get-ChildItem -Path .\publish -Recurse | Where-Object { $_.Extension -ne '.exe' } | Remove-Item -Force -Recurse