"""Run the actual campaign/runtime tests and persist their unmodified reports."""
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import sys
import unittest

root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root));os.chdir(root)
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from lasttrain import __version__
from verify_assets import main as verify_assets

version='.'.join(__version__.split('.')[:2])
report=StringIO()
suite=unittest.defaultTestLoader.discover('tests')
result=unittest.TextTestRunner(stream=report,verbosity=2).run(suite)
text=report.getvalue()
(root/'release'/('qa-'+version+'.txt')).write_text(text,encoding='utf-8')
print(text)
if not result.wasSuccessful():raise SystemExit(1)
assets=StringIO()
with redirect_stdout(assets):verify_assets()
text=assets.getvalue()
(root/'release'/('assets-qa-'+version+'.txt')).write_text(text,encoding='utf-8')
print(text)
