#!/user/bin/python27
import os
import traceback
import time
import subprocess

os.chdir(os.path.abspath('../'))


def main():
    subprocess.call('sphinx-apidoc -o docs colliberation -f')
    os.chdir(os.path.abspath('./docs/'))
    subprocess.call('make.bat clean')
    subprocess.call('make.bat html')

try:
    main()
except Exception:
    print(traceback.format_exc())
    raw_input()
else:
    time.sleep(30)
