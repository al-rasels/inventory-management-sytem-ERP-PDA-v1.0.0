import os
import sys

# This is a placeholder for a real setup script (e.g. using cx_Freeze or PyInstaller)
# To build: pyinstaller --noconfirm --onedir --windowed --add-data "src;src/" --add-data "SunERP_Master_Database.xlsx;." src/main.py

print("To build the Windows Installer, run:")
print("pip install pyinstaller")
print('pyinstaller --noconfirm --onedir --windowed --add-data "src;src/" --add-data "SunERP_Master_Database.xlsx;." src/main.py')
