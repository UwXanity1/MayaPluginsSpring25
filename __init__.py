import os
import sys 

initFilePath = os.path.abspath(__file__)
pluginDir = os.path.dirname(initFilePath)
srsDir = os.path.join(pluginDir, "src")
unrealSDKDir = os.path.join(pluginDir, "vendor", "unrealSDK")

def AddDirtoPath(dir):
    if dir not in sys.path:
        sys.path.append(dir)
        print(f"added {dir} to path")

AddDirtoPath(pluginDir)
AddDirtoPath(srsDir)
AddDirtoPath(unrealSDKDir)