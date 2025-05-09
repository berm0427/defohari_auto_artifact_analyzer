# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

added_files = [('./Depohari_Refined_Logo.png', '.'),  
               ('./computer_monitor_icon.ico', '.'),
			   ('./*.json', '.'),
			   ('./image_here/*', './image_here/'),
			   ('./requirement/*', './requirement/'),
			   ('./if_csv_broken_main.py', '.'),
               ('./csv_totaler.py', '.'),
			   ('./sleuthkit/*.txt', './sleuthkit/'),
			   ('./sleuthkit/bin/*', './sleuthkit/bin/'),
			   ('./sleuthkit/lib/*', './sleuthkit/lib/'),
			   ('./sleuthkit/licenses/*', './sleuthkit/licenses/'),
			   ('./subroutine/web/*.py', './subroutine/web/'),
			   ('./subroutine/web/*.json', './subroutine/web/'),
			   ('./subroutine/web/prototype/*', './subroutine/web/prototype/'),
               ('./subroutine/prefetch/*.py', './subroutine/prefetch/'),
			   ('./subroutine/prefetch/prototype/*', './subroutine/prefetch/prototype/'),
               ('./subroutine/event_log/*.py', './subroutine/event_log/'),
			   ('./subroutine/event_log/*.json', './subroutine/event_log/'),
			   ('./subroutine/event_log/*.txt', './subroutine/event_log/'),
			   ('./subroutine/event_log/python-evtx/*.py', './subroutine/event_log/python-evtx/'),
			   ('./subroutine/event_log/python-evtx/.travis.yml', './subroutine/event_log/python-evtx/'),
			   ('./subroutine/event_log/python-evtx/*.TXT', './subroutine/event_log/python-evtx/'),
			   ('./subroutine/event_log/python-evtx/*.md', './subroutine/event_log/python-evtx/'),
			   ('./subroutine/event_log/python-evtx/.gitignore', './subroutine/event_log/python-evtx/'),
			   ('./subroutine/event_log/python-evtx/.github/workflows/*', './subroutine/event_log/python-evtx/.github/workflows/'),
			   ('./subroutine/event_log/python-evtx/Evtx/*', './subroutine/event_log/python-evtx/Evtx/'),
			   ('./subroutine/event_log/python-evtx/tests/*.py', './subroutine/event_log/python-evtx/scripts/tests/'),
			   ('./subroutine/event_log/python-evtx/tests/data/*', './subroutine/event_log/python-evtx/scripts/tests/data/'),
			   ('./subroutine/event_log/prototype/*', './subroutine/event_log/prototype/'),
               ('./subroutine/MFTJ/*.py', './subroutine/MFTJ/'),
			   ('./subroutine/MFTJ/analyzeMFT/*.py', './subroutine/MFTJ/analyzeMFT/'),
			   ('./subroutine/MFTJ/analyzeMFT/__init.py__', './subroutine/MFTJ/analyzeMFT/'),
			   ('./subroutine/MFTJ/analyzeMFT/.gitignore', './subroutine/MFTJ/analyzeMFT/'),
			   ('./subroutine/MFTJ/analyzeMFT/*.txt', './subroutine/MFTJ/analyzeMFT/'),
			   ('./subroutine/MFTJ/analyzeMFT/*.md', './subroutine/MFTJ/analyzeMFT/'),
			   ('./subroutine/MFTJ/analyzeMFT/*.MD', './subroutine/MFTJ/analyzeMFT/'),
			   ('./subroutine/MFTJ/analyzeMFT/*.toml', './subroutine/MFTJ/analyzeMFT/'),
			   ('./subroutine/MFTJ/analyzeMFT/src/analyzeMFT/*.py', './subroutine/MFTJ/analyzeMFT//src/analyzeMFT/'),
			   ('./subroutine/MFTJ/analyzeMFT/src/analyzeMFT/__pycache__/*', './subroutine/MFTJ/analyzeMFT//src/analyzeMFT/__pycache__'),
			   ('./subroutine/MFTJ/analyzeMFT/src/analyzeMFT/sql/*', './subroutine/MFTJ/analyzeMFT//src/analyzeMFT/sql/'),
			   ('./subroutine/MFTJ/analyzeMFT/tests/*', './subroutine/MFTJ/analyzeMFT/tests/'),
			   ('./subroutine/MFTJ/analyzeMFT/.github/workflows/*.yaml', './subroutine/MFTJ/analyzeMFT/.github/workflows/'),
			   ('./subroutine/MFTJ/USN-Journal-Parser/*.py', './subroutine/MFTJ/USN-Journal-Parser/'),
			   ('./subroutine/MFTJ/USN-Journal-Parser/*.rst', './subroutine/MFTJ/USN-Journal-Parser/'),
			   ('./subroutine/MFTJ/USN-Journal-Parser/LICENSE', './subroutine/MFTJ/USN-Journal-Parser/'),
			   ('./subroutine/MFTJ/USN-Journal-Parser/tests/*', './subroutine/MFTJ/USN-Journal-Parser/tests/'),
			   ('./subroutine/MFTJ/USN-Journal-Parser/usnparser/*', './subroutine/MFTJ/USN-Journal-Parser/usnparser'),
               ('./subroutine/MFTJ/prototype/*', './subroutine/MFTJ/prototype/'),
			   ('./subroutine/LNK/*.py', './subroutine/LNK/'),
			   ('./subroutine/LNK/*.json', './subroutine/LNK/'), 
			   ('./subroutine/LNK/prototype/*', './subroutine/LNK/prototype/')]
a = Analysis(['defohari.py'],
             pathex=['G:\\capstone\\defohari'],
             binaries=[],
             datas=added_files,
             hiddenimports=[
                 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'PIL'
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
            cipher=block_cipher)

exe = EXE(pyz,
           a.scripts,
           [],
           exclude_binaries=True,
           name='defohari',
           debug=True,
           bootloader_ignore_signals=False,
           strip=False,
           upx=True,
           console=False,
           icon='computer_monitor_icon.ico',
		   onefile=True)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='defohari')
