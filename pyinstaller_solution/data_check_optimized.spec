# -*- mode: python ; coding: utf-8 -*-
# PyInstaller用最適化設定ファイル

block_cipher = None

a = Analysis(
    ['data_check.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app_settings.json', '.'),
        ('check_definitions.json', '.'),
        ('input_file', 'input_file'),
    ],
    hiddenimports=[
        # 明示的にモジュールを指定
        'dekispart',
        'innosite', 
        'dekispart_school',
        'cloud',
        
        # Pandas関連
        'pandas._libs.tslibs.base',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.timestamps',
        'pandas._libs.window.aggregations',
        'pandas.io.formats.style',
        
        # その他必要なモジュール
        'openpyxl.cell._writer',
        'openpyxl.workbook.protection', 
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'configparser',
        'json',
        'datetime',
        'csv',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 不要な大容量モジュールを除外
        'matplotlib',
        'IPython',
        'jupyter',
        'pytest',
        'sphinx',
        'PIL',
        'scipy',
        'sklearn',
        'tensorflow',
        'torch',
    ],
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
    name='data_check',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # --noconsole と同等
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
