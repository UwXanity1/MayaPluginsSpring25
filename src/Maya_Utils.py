from PySide2.QtWidgets import QMainWindow, QWidget 
from PySide2.QtCore import Qt
import maya.OpenMayaUI as omui
import shiboken2 
import maya.cmds as mc

def IsMesh(obj):
    shapes = mc.listRelatives(obj, s=True)
    if not shapes:
        return False
    
    for s in shapes:
        if mc.objectType(s) == "mesh":
            return True
    
    return False

def IsSkin(obj):
    return mc.objectType(obj) == "skinCluster"

def IsJoint(obj):
    return mc.objectType(obj) == "joint"

def GetUpperStream(obj):
    return mc.listConnections(obj, s=True, d=False, sh=True)

def GetLowerStream(obj):
    return mc.listConnections(obj, s=False, d=True, sh=True)

def GetAllConnectsIn(obj, nextFunc, filter = None):
    allFound = set()
    nexts = nextFunc(obj)
    searchDepth = 100
    while nexts and searchDepth > 0:
        searchDepth -= 1
        for next in nexts:
            allFound.add(next)

        nexts = nextFunc(nexts)
        if nexts:
            nexts = [x for x in nexts if x not in allFound]
    
    if not filter:
        return list(allFound)
    
    filtered = []
    for found in allFound:
        if filter(found):
            filtered.append(found)

    return filtered

def GetMayaMainWindow()->QMainWindow: # fucntion to create maya main window
    mayaWindow = omui.MQtUtil.mainWindow() # creates main window for the maya widget
    return shiboken2.wrapInstance(int(mayaWindow), QMainWindow)

def DeleteWidgetWithName(name): # function to delete maya main window
    for widget in GetMayaMainWindow().findChildren(QWidget, name): # finds new instances of the maya window in the GetMayaMainWindow class 
        widget.deleteLater() # delets the window

     
class MayaWindow(QWidget): # class called MayaWindow with QWidget as a definition
    def __init__(self):
        super().__init__(parent = GetMayaMainWindow())  
        DeleteWidgetWithName(self.GetWidgetUniqueName())  
        self.setWindowFlags(Qt.WindowType.Window) 
        self.setObjectName(self.GetWidgetUniqueName()) 

    def GetWidgetUniqueName(self): # inherited function 
       return "UniqueName" # returns the output of the GetWidgetUniqueName function