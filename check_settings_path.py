
import os
import importlib

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EcommerceMgmt.settings')

settings_module = importlib.import_module(os.environ['DJANGO_SETTINGS_MODULE'])
print("Settings module file:", settings_module.__file__)

