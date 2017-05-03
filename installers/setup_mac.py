"""
This is a setup.py script partly generated by py2applet

Usage:
    python setup.py py2app


NOTES:
   12/01/2011: When seeing an error related to pytz.zoneinfo not being found, change the following line in py2app/recipes/matplotlib.py
               mf.import_hook('pytz.tzinfo', m, ['UTC'])
   12/05/2011: Needs macholib >= 1.4.3 and py2app >= 0.6.4 to create a 64-bit app
"""
from __future__ import print_function

import os
import string
import sys

from distutils.util import get_platform
from distutils.filelist import findall
from distutils.sysconfig import get_python_lib

from setuptools import setup

import macholib_patch

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
platform = '%s-%s'%(get_platform(), sys.version[:3])
doc_path = os.path.join(root, 'build', 'lib.'+platform, 'doc')
env = os.path.join(root, 'sasview-install', 'lib', 'python2.7', 'site-packages')
#sys.path.insert(0, env)

#Extending recursion limit
sys.setrecursionlimit(10000)

print("BUILDING PATH INSIDE", env)

from sas.sasview import local_config

ICON = local_config.SetupIconFile_mac
RESOURCES_FILES = []
DATA_FILES = []

#Periodictable data file
import periodictable
DATA_FILES += periodictable.data_files()
#invariant and calculator help doc
from sas.sasgui.perspectives import fitting
DATA_FILES += fitting.data_files()
from sas.sasgui.perspectives import calculator
DATA_FILES += calculator.data_files()
from sas.sasgui.perspectives import invariant
DATA_FILES += invariant.data_files()
import sasmodels
DATA_FILES += sasmodels.data_files()
from sas.sasgui import guiframe
DATA_FILES += guiframe.data_files()

#CANSAxml reader data files
from sas.sascalc.dataloader import readers
RESOURCES_FILES.append(os.path.join(readers.get_data_path(),'defaults.json'))

# Copy the config files
sas_path = os.path.join('..', 'src', 'sas')
DATA_FILES.append(('.', [os.path.join(sas_path, 'logging.ini')]))
sasview_path = os.path.join(sas_path,'sasview')
custom_config_file = os.path.join(sasview_path, 'custom_config.py')
local_config_file = os.path.join(sasview_path, 'local_config.py')
logging_ini = os.path.join(sasview_path, 'logging.ini')
DATA_FILES.append(('.', [custom_config_file]))
DATA_FILES.append(('config', [custom_config_file]))
DATA_FILES.append(('.', [local_config_file]))
DATA_FILES.append(('.', [logging_ini]))

# default_categories.json is beside the config files
category_config = os.path.join(sasview_path, 'default_categories.json')
if os.path.isfile(category_config):
    DATA_FILES.append(('.', [category_config]))

if os.path.isfile("BUILD_NUMBER"):
    DATA_FILES.append(('.', ["BUILD_NUMBER"]))

images_dir = local_config.icon_path
media_dir = local_config.media_path
test_dir = local_config.test_path
test_1d_dir = os.path.join(test_dir, "1d_data")
test_2d_dir = os.path.join(test_dir, "2d_data")
test_save_dir = os.path.join(test_dir, "save_states")
test_upcoming_dir = os.path.join(test_dir, "upcoming_formats")

# Copying the images directory to the distribution directory.
for f in findall(images_dir):
    DATA_FILES.append(("images", [f]))

# Copying the HTML help docs
for f in findall(media_dir):
    DATA_FILES.append(("media", [f]))

# Copying the sample data user data
for f in findall(test_1d_dir):
    DATA_FILES.append((os.path.join("test","1d_data"), [f]))

# Copying the sample data user data
for f in findall(test_2d_dir):
    DATA_FILES.append((os.path.join("test","2d_data"), [f]))

# Copying the sample data user data
for f in findall(test_save_dir):
    DATA_FILES.append((os.path.join("test","save_states"), [f]))

# Copying the sample data user data
for f in findall(test_upcoming_dir):
    DATA_FILES.append((os.path.join("test","upcoming_formats"), [f]))

# Copying opencl include files
site_loc = get_python_lib()
opencl_include_dir = os.path.join(site_loc, "pyopencl", "cl")
for f in findall(opencl_include_dir):
    DATA_FILES.append((os.path.join("includes","pyopencl"), [f]))

# See if the documentation has been built, and if so include it.
print(doc_path)
if os.path.exists(doc_path):
    for dirpath, dirnames, filenames in os.walk(doc_path):
        for filename in filenames:
            sub_dir = os.path.join("doc", os.path.relpath(dirpath, doc_path))
            DATA_FILES.append((sub_dir, [os.path.join(dirpath, filename)]))
else:
    raise Exception("You must first build the documentation before creating an installer.")

# locate file extensions
def find_extension():
    """
    Describe the extensions that can be read by the current application
    """
    try:
        list = []
        EXCEPTION_LIST = ['*', '.', '']
        from sas.sascalc.dataloader.loader import Loader
        wild_cards = Loader().get_wildcards()
        for item in wild_cards:
            #['All (*.*)|*.*']
            file_type, ext = string.split(item, "|*.", 1)
            if ext.strip() not in EXCEPTION_LIST and ext.strip() not in list:
                list.append(ext)
    except:
        pass
    try:
        file_type, ext = string.split(local_config.APPLICATION_WLIST, "|*.", 1)
        if ext.strip() not in EXCEPTION_LIST and ext.strip() not in list:
            list.append(ext)
    except:
        pass
    try:
        for item in local_config.PLUGINS_WLIST:
            file_type, ext = string.split(item, "|*.", 1)
            if ext.strip() not in EXCEPTION_LIST and ext.strip() not in list:
                list.append(ext)
    except:
        pass

    return list

EXTENSIONS_LIST = find_extension()


plist = dict(CFBundleDocumentTypes=[dict(CFBundleTypeExtensions=EXTENSIONS_LIST,
                                         CFBundleTypeIconFile=ICON,
                                   CFBundleTypeName="sasview file",
                                   CFBundleTypeRole="Shell" )],)

# Locate libxml2 library
lib_locs = ['/usr/local/lib', '/usr/lib']
libxml_path = None
for item in lib_locs:
    libxml_path_test = '%s/libxml2.2.dylib' % item
    if os.path.isfile(libxml_path_test):
        libxml_path = libxml_path_test
if libxml_path == None:
    raise RuntimeError, "Could not find libxml2 on the system"

#Get version - NB nasty hack. Need to find correct way to give path to installed sasview (AJJ)
#h5py has been added to packages. It requires hdf5 to be installed separetly
#

from sas.sasview import __version__ as VERSION
APPNAME = "SasView "+VERSION
DMGNAME = "SasView-"+VERSION+"-MacOSX"
APP = ['sasview_gui.py']

EXCLUDES = ['PyQt4', 'sip', 'QtGui']

OPTIONS = {'argv_emulation': True,
           'packages': ['lxml', 'numpy', 'scipy', 'pytz', 'encodings',
                        'encodings', 'matplotlib', 'periodictable',
                        'reportlab', 'sasmodels', 'pyopencl', 'h5py',
                       ],
           'iconfile': ICON,
           'frameworks': [libxml_path],
           'resources': RESOURCES_FILES,
           'plist': plist,
           'excludes' : EXCLUDES,
          }
setup(
    name=APPNAME,
    app=APP,
    data_files=DATA_FILES,
    include_package_data=True,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

#Build dmg
DMG = "dist/%s.dmg"%DMGNAME
if os.path.exists(DMG):
    os.unlink(DMG)
os.system('cd dist && ../../build_tools/dmgpack.sh "%s" "%s.app"'%(DMGNAME, APPNAME))
os.system('chmod a+r "%s"'%DMG)