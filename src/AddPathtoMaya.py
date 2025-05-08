import sys

prjPath = "D:/profile redirect/jclee1/Downloads/MayaPlugins/src"
moduleDir = "D:/profile redirect/jclee1/Downloads"

if prjPath not in sys.path:
    sys.path.append(prjPath)

if moduleDir not in sys.path:
    sys.path.append(moduleDir)


