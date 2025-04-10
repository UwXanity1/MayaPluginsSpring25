from PySide2.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QSlider, QVBoxLayout, QWidget # imports classes from PySide2.QtCore module
from PySide2.QtCore import Qt # imports 'Qt' from PySide2.QtCore module
import maya.OpenMayaUI as omui # imports module as 'omui'
import maya.mel as mel
from maya.OpenMaya import MVector
import shiboken2 # translates Qt class to Python

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

import maya.cmds as mc # transfers over the the actions maya has and registers it as 'mc'.
    
class LimbRigger: # classed named "LimbRigger"
    def __init__(self): 
        self.root = "" # placeholder for root joint in window
        self.mid = "" # placeholder for mid joint in window
        self.end = "" # placeholder for end joint in window
        self.controllerSize = 5 # sets the controller size to a given int

    def FindJointBasedOnSelection(self):
        self.root = mc.ls(sl=True, type="joint")[0] # detects if a root joint has been selected 
        self.mid = mc.listRelatives(self.root, c=True, type="joint")[0] # detects if mid joint is attached to selected root joint
        self.end = mc.listRelatives(self.mid, c=True, type="joint")[0] # detects if end joint is attached to selected mid joint

    def CreateFKControllerForJoint(self, jntname):
        ctrlName = "ac_l_fk_" + jntname # sets the naming for the controller along with the pre-existing joint name
        ctrlGrpName = ctrlName + "_grp" # sets the naming for the groups' to be have the contorls name with '_grp'
        mc.circle(name = ctrlName, radius = self.controllerSize, normal = (1,0,0)) # gives ctrlGrp a controller with an given size
        mc.group(ctrlName, n=ctrlGrpName) # creates a group for the controls
        mc.matchTransform(ctrlGrpName, jntname) # this matches the transforms of the ctrlGrp to the joint 
        mc.orientConstraint(ctrlName, jntname) # this essentially parents the joint, already parented to the controller, to the ctrlGrp
        return ctrlName, ctrlGrpName # returns output of ctrlName and CtrlGrpName
    
    def CreateBoxCtroller(self,name):
        mel.eval(f"curve -n {name} -d 1 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 -0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 -0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 -0.5 -0.5 -p 0.5 -0.5 -0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 ;")
        mc.scale(self.controllerSize, self.controllerSize, self.controllerSize, name)
        mc.makeIdentity(name, apply=True) #freeze transformation
        grpName = name + "_grp"
        mc.group(name, n = grpName)
        return name, grpName
    
    def CreatePlusController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p 33.333333 16.666667 0 -p 33.333333 50 0 -p 0 50 0 -p 0 83.333333 0 -p 33.333333 83.333333 0 -p 33.333333 116.666667 0 -p 66.666667 116.666667 0 -p 66.666667 83.333333 0 -p 100 83.333333 0 -p 100 50 0 -p 66.666667 50 0 -p 66.666667 16.666667 0 -p 33.333333 16.666667 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
        grpName = name + "_grp"
        mc.group(name, n = grpName)
        return name, grpName 
    
    def GetObjectLocation(self, objectName):
        x, y, z = mc.xform(objectName, q=True, ws=True, t=True)
        return MVector(x, y, z)
    
    def PrintVector(self, vector):
        print(f"<{vector.x}, {vector.y}, {vector.z}>")

    def RigLimb(self):
        rootCtrl, rootCtrlGrp = self.CreateFKControllerForJoint(self.root) # creates an FK controller for "root" joint
        midCtrl, midCtrlGrp = self.CreateFKControllerForJoint(self.mid) # creates an FK controller for "mid" joint
        endCtrl, endCtrlGrp = self.CreateFKControllerForJoint(self.end) # creates an FK controller for "end" joint

        mc.parent(midCtrlGrp, rootCtrl) # parents the midCtrlGrp to the rootCtrl
        mc.parent(endCtrlGrp, midCtrl) # parents the endCtrlGrp to the midCtrl

        ikEndCtrl = "ac_ik_" + self.end
        ikEndCtrl, ikEndCtrlGrp = self.CreateBoxCtroller(ikEndCtrl)
        mc.matchTransform(ikEndCtrlGrp, self.end)
        endOrientConstraint = mc.orientConstraint(ikEndCtrl, self.end)[0]

        rootJntLoc = self.GetObjectLocation(self.root)
        self.PrintVector(rootJntLoc)

        ikHandleName = "ikHandle_" + self.end
        mc.ikHandle(n=ikHandleName, sol="ikRPsolver", sj=self.root, ee=self.end)

        poleVectorLocationVals = mc.getAttr(ikHandleName + ".poleVector")[0]
        polevector = MVector(poleVectorLocationVals[0], poleVectorLocationVals[0], poleVectorLocationVals[0])
        polevector.normalize()

        endJntLoc = self.GetObjectLocation(self.end)
        rootToEndVector = endJntLoc - rootJntLoc

        polevectorCtrlLoc = rootJntLoc + rootToEndVector /2 + polevector * rootToEndVector.length()
        self.PrintVector(polevectorCtrlLoc)
        poleVectorCtrl = "ac_ik_" + self.mid
        mc.spaceLocator(n=poleVectorCtrl)
        poleVectorCtrlGrp = poleVectorCtrl + "_grp"
        mc.group(polevector, n=poleVectorCtrlGrp)
        mc.setAttr(poleVectorCtrlGrp + ".t", polevectorCtrlLoc.x, polevectorCtrlLoc.y, polevectorCtrlLoc.z, typ="double3")

        mc.poleVectorConstraint(poleVectorCtrl, ikHandleName)

        ikfkBlendCtrl = "ac_ikfk_blend_" + self.root
        ikfkBlendCtrl, ikfkBlendCtrlGrp = self.CreatePlusController(ikfkBlendCtrlGrp)
        mc.setAttr(ikfkBlendCtrlGrp+".t", rootJntLoc.x*2, rootJntLoc.y, rootJntLoc.z*2, typ="double3")



class LimbRiggerWidget(MayaWindow): # this class inherts from a previous mayawindow class
    def __init__(self): # A constructor of the limb Rigger Widget
        super().__init__() # calls the super class constructor 
        self.rigger = LimbRigger() # "self.rigger" is set to the LimbRigger class 
        self.setWindowTitle("Limb Rigger")

        self.masterLayout = QVBoxLayout() # Creates the master layout as a veritcal layout
        self.setLayout(self.masterLayout) # Sets the layout of the widget to be master Layout
        
        tootTipLabel = QLabel("Select the first joint of the limb, and press the auto find button") # creates a str variable
        self.masterLayout.addWidget(tootTipLabel) # adds the aformentioned variable to the master layout

        self.jntsListLineEdit = QLineEdit() # the variable self.jntsListLineEdit is set to the type of QLineEdit
        self.masterLayout.addWidget(self.jntsListLineEdit) # adds jntsListLineEdit to the master Layout
        self.jntsListLineEdit.setEnabled(False) # disables jntsListLineEdit 

        autoFindJntBtn = QPushButton("Auto Find") # creates a button named "Auto Find"
        autoFindJntBtn.clicked.connect(self.AutoFindJntBtnClicked) # detects if button is clicked
        self.masterLayout.addWidget(autoFindJntBtn) # adds the "Auto Find" button to master layout

        ctrlSizeSlider = QSlider()
        ctrlSizeSlider.setOrientation(Qt.Horizontal)
        ctrlSizeSlider.setRange(1,30)
        ctrlSizeSlider.setValue(self.rigger.controllerSize)
        self.ctrlSizeLabel = QLabel(f"{self.rigger.controllerSize}")
        ctrlSizeSlider.valueChanged.connect(self.CtrlSizeSliderChanged)

        ctrlSizeLayout = QHBoxLayout()
        ctrlSizeLayout.addWidget(ctrlSizeSlider)
        ctrlSizeLayout.addWidget(self.ctrlSizeLabel)
        self.masterLayout.addLayout(ctrlSizeLayout)

        rigLimbBtn = QPushButton("Rig Limb") # creates a button named "Rig Limb" 
        rigLimbBtn.clicked.connect(lambda : self.rigger.RigLimb()) 
        self.masterLayout.addWidget(rigLimbBtn) # adds the "Rig Limb" button to the master Layout

    def CtrlSizeSliderChanged(self, newValue):
        self.ctrlSizeLabel.setText(f"{newValue}")
        self.rigger.controllerSize = newValue

    def AutoFindJntBtnClicked(self): # function designated to call the "Auto Find" button
        self.rigger.FindJointBasedOnSelection() # When this button is click, the FindJointBasedOnSelection function will run
        self.jntsListLineEdit.setText(f"{self.rigger.root},{self.rigger.mid},{self.rigger.end}") # sets the text in input box to the selected joints

limbRiggerWidget = LimbRiggerWidget()
limbRiggerWidget.show()

GetMayaMainWindow()

