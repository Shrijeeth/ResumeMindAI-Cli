# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
import os

# Fix recursion limit for complex ML dependencies
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

# Get the project root directory
project_root = Path.cwd()

# Get package locations
import litellm
litellm_path = Path(litellm.__file__).parent

import magika
magika_path = Path(magika.__file__).parent

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include package data
        ('resumemind', 'resumemind'),
        # Include requirements.txt for reference
        ('requirements.txt', '.'),
        # Include README and LICENSE
        ('README.md', '.'),
        ('LICENSE', '.'),
        # Include litellm data files
        (str(litellm_path / 'litellm_core_utils' / 'tokenizers'), 'litellm/litellm_core_utils/tokenizers'),
        (str(litellm_path / 'cost.json'), 'litellm'),
        (str(litellm_path / 'model_prices_and_context_window_backup.json'), 'litellm'),
        # Include magika model and config files
        (str(magika_path / 'models'), 'magika/models'),
        (str(magika_path / 'config'), 'magika/config'),
    ],
    collect_data_files=[
        'tiktoken_ext.openai_public',
        'tiktoken',
    ],
    collect_all=[
        'numpy',
        'litellm',
        'agno',
        'markitdown',
    ],
    hiddenimports=[
        # Core dependencies
        'agno',
        'falkordb',
        'litellm',
        'rich',
        'markitdown',
        'google.auth',
        # Additional imports that might be missed
        'sqlite3',
        'asyncio',
        'pathlib',
        'typing',
        'dataclasses',
        'json',
        'hashlib',
        'os',
        'sys',
        # Rich components
        'rich.console',
        'rich.table',
        'rich.prompt',
        'rich.progress',
        # LiteLLM components
        'litellm.utils',
        'litellm.exceptions',
        # Tiktoken components
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
        # NumPy 2.x internal modules
        'numpy._core',
        'numpy._core._exceptions',
        'numpy._core._multiarray_umath',
        'numpy._core._multiarray_tests',
        'numpy.core._multiarray_umath',
        # Agno components
        'agno.workflow',
        'agno.agent',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'tkinter',
        'matplotlib',
        'pandas',
        'PIL',
        'cv2',
        # Exclude heavy ML packages that cause recursion issues
        'torch',
        'tensorflow',
        'transformers',
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
    name='resumemind-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path here if you have one
)
