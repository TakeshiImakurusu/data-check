# -*- mode: python ; coding: utf-8 -*-
block_cipher = None
from PyInstaller.utils.hooks import copy_metadata

datas_list = [
    ('app_settings.json', '.'),
    ('check_definitions.json', '.'),
    ('dekispart.py', '.'),
    ('innosite.py', '.'),
    ('dekispart_school.py', '.'),
    ('cloud.py', '.'),
    ('common.py', '.'),
    ('constants.py', '.'),
]
datas_list += copy_metadata('pytz')


a = Analysis(
    ['data_check.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'dekispart', 'innosite', 'dekispart_school', 'cloud',
        'common', 'constants',
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
        'pandas', 'openpyxl', 'configparser', 'chardet'
    ],

    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DataCheck-Test',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
)