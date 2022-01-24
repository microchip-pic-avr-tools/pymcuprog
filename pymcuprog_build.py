"""
Build script for pymcuprog, tested on Windows 10, Windows 11, Ubuntu and Debian. Invoke this build
script like so:

    $ python3 pymcuprog_build.py

A 'build/' folder gets created with the executable and dll's / so's inside. To clean, invoke:

    $ python3 pymcuprog_build.py --clean
"""
import sys
import os
import platform
import subprocess
import argparse
import inspect
import shutil
import sysconfig

# Obtain the absolute path to this file
pymcuprog_build_filepath = os.path.realpath(
    inspect.getfile(
        inspect.currentframe()
    )
).replace('\\', '/')

# Obtain path to build folder
build_dirpath = os.path.join(
    os.path.dirname(pymcuprog_build_filepath),
    'build',
).replace('\\', '/')

# Store path to executable (gets computed later)
exe_filepath = ''

# Store list of site- and dist-packages folders
site_packages = []

def list_package_dirpaths():
    '''
    Site- and dist-packages are by default part of the Python search path, so modules installed
    there - for example with pip - can be imported easily afterwards. This function returns a list
    of all these folders, for example:
        - '/usr/lib/python3.9/site-packages'
        - '/home/kristof/.local/lib/python3.9/site-packages'
        - '/usr/local/lib/python3.9/dist-packages'
        - '/usr/lib/python3/dist-packages'
        - '/usr/lib/python3.9/dist-packages'
    '''
    global site_packages
    if len(site_packages) == 0:
        site_packages = [
            sysconfig.get_path('purelib').replace('\\', '/')
        ]
        for p in sys.path:
            if (('site-packages' in p) or ('dist-packages' in p)) and (p not in site_packages):
                site_packages.append(p.replace('\\', '/'))
    return [p for p in site_packages if os.path.isdir(p)]

def get_module_dirpath(module_name):
    '''
    Get the absolute path to the given module directory. This function looks for the module in all
    site- and dist-packages directories (see previous function).
    '''
    # Look in the site-packages and dist-packages for the given module
    for p in list_package_dirpaths():
        package_path = os.path.join(p, module_name).replace('\\', '/')
        if module_name == 'logging':
            package_path = os.path.join(os.path.dirname(p), module_name).replace('\\', '/')
        if os.path.exists(package_path):
            return package_path

    # Module not found, throw error
    raise RuntimeError(f"Cannot find module '{module_name}'")

def repair_copied_module(module_name):
    '''
    CX_Freeze copies a lot of modules to the 'lib/' subfolder, which is right next to the executable
    file. It only copies those files it thinks are being used by the executable. This often goes
    wrong, so some of these copied modules need to be repaired.
    To do such a reparation, this function observes the copied module and compares it file-by-file
    with the original one in the site- or dist-packages directory. Missing files are then added.
    '''
    source_dirpath = get_module_dirpath(module_name)
    target_dirpath = os.path.join(
        os.path.dirname(exe_filepath),
        f'lib/{module_name}',
    ).replace('\\', '/')
    for root, dirs, files in os.walk(source_dirpath):
        if '__pycache__' in root:
            continue
        for name in files:
            source_filepath = os.path.join(root, name).replace('\\', '/')
            target_filepath = source_filepath.replace(source_dirpath, target_dirpath)
            if os.path.exists(target_filepath):
                continue
            if '__pycache__' in target_filepath:
                continue
            print(f'COPY: {target_filepath}')
            shutil.copy2(
                source_filepath,
                target_filepath,
            )
            continue
        continue
    return

def clean(*args):
    '''
    Clean the build/ folder.
    '''
    print(f'Delete build folder:\n{build_dirpath}')
    if os.path.exists(build_dirpath):
        shutil.rmtree(build_dirpath)
    return

def build(*args):
    '''

    '''
    # STEP 1: INVOKE CXFREEZE
    # =======================
    # Invoke cxfreeze. It will create a folder 'build/' with the executable and dll's/so's inside.
    print('\n============================== START BUILD ==============================')
    process = subprocess.Popen(
        ['cxfreeze', f'--target-name=pymcuprog', 'pymcuprog_execute.py'],
        stdout   = subprocess.PIPE,
        stderr   = subprocess.PIPE,
        shell    = False,
        encoding = 'utf-8',
        errors   = 'replace',
    )
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip(), flush=True)

    # STEP 2: PATH TO EXECUTABLE
    # ==========================
    # Obtain the absolute path to the executable that was just built by CX_Freeze, and store it in a
    # global variable. It will be used in the 'repair_copied_module(module_name)' function (see next
    # step).
    global exe_filepath
    exe_filepath = os.path.join(
        build_dirpath,
        os.listdir(build_dirpath)[0],
        'pymcuprog'
    ).replace('\\', '/')
    if platform.system().lower() == 'windows':
        exe_filepath = f'{exe_filepath}.exe'

    # STEP 3: REPAIR COPIED MODULES
    # =============================
    # CX_Freeze forgets to copy several files from these modules.
    repair_copied_module('pymcuprog')
    repair_copied_module('pyedbglib')
    repair_copied_module('logging')
    repair_copied_module('yaml')
    print('\n================================== DONE ==================================')
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build pymcuprog.')
    parser.add_argument('-c', '--clean', action='store_true')
    parser_args = parser.parse_args()

    # CLEAN
    if parser_args.clean:
        clean()
        sys.exit(0)

    # BUILD
    if os.path.exists(build_dirpath):
        clean()
    build()
    sys.exit(0)
