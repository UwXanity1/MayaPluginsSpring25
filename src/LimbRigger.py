import importlib
import Maya_Utils
importlib.reload(Maya_Utils)
from Maya_Utils import MayaWindow
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QColorDialog, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QSlider, QVBoxLayout, QWidget # imports classes from PySide2.QtCore module
from PySide2.QtCore import Qt, Signal # imports 'Qt' from PySide2.QtCore module
import maya.OpenMayaUI as omui # imports module as 'omui'
import maya.mel as mel
from maya.OpenMaya import MVector
import shiboken2 # translates Qt class to Python

import maya.cmds as mc # transfers over the the actions maya has and registers it as 'mc'.
    
class LimbRigger:
    def __init__(self): 
        self.root = "" # placeholder for root joint in window
        self.mid = "" # placeholder for mid joint in window
        self.end = "" # placeholder for end joint in window
        self.controllerSize = 5 # sets the controller size to a given int
        self.controllerColor = [0,0,0]

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

        # Creating FK controllers for Joints

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

        # Creating IK handles for the joints

        ikHandleName = "ikHandle_" + self.end
        mc.ikHandle(n=ikHandleName, sol="ikRPsolver", sj=self.root, ee=self.end)

        # Pole Vectors

        poleVectorLocationVals = mc.getAttr(ikHandleName + ".poleVector")[0]
        polevector = MVector(poleVectorLocationVals[0], poleVectorLocationVals[1], poleVectorLocationVals[2])
        polevector.normalize()

        endJntLoc = self.GetObjectLocation(self.end)
        rootToEndVector = endJntLoc - rootJntLoc

        polevectorCtrlLoc = rootJntLoc + rootToEndVector /2 + polevector * rootToEndVector.length()
        poleVectorCtrl = "ac_ik_" + self.mid
        mc.spaceLocator(n=poleVectorCtrl)
        poleVectorCtrlGrp = poleVectorCtrl + "_grp"
        mc.group(poleVectorCtrl, n=poleVectorCtrlGrp)
        self.PrintVector(polevectorCtrlLoc)
        mc.setAttr(poleVectorCtrlGrp + ".t", polevectorCtrlLoc.x ,polevectorCtrlLoc.y, polevectorCtrlLoc.z, typ="double3")

        mc.poleVectorConstraint(poleVectorCtrl, ikHandleName)

        # F/IK Blend

        ikfkBlendCtrl = "ac_ikfk_blend_" + self.root
        ikfkBlendCtrl, ikfkBlendCtrlGrp = self.CreatePlusController(ikfkBlendCtrl)
        mc.setAttr(ikfkBlendCtrlGrp+".t", rootJntLoc.x*2, rootJntLoc.y, rootJntLoc.z*2, typ="double3")
        
        ikfkBlendAttrName = "ikfkBlend" 
        mc.addAttr(ikfkBlendCtrl, ln=ikfkBlendAttrName, min=0, max = 1, k=True)
        ikfkBlendAttr = ikfkBlendCtrl + "." + ikfkBlendAttrName

        mc.expression(s=f"{ikHandleName}.ikBlend={ikfkBlendAttr}")
        mc.expression(s=f"{ikEndCtrlGrp}.v={poleVectorCtrlGrp}.v={ikfkBlendAttr}")
        mc.expression(s=f"{rootCtrlGrp}.v=1-{ikfkBlendAttr}")
        mc.expression(s=f"{endOrientConstraint}.{endCtrl}W0 = 1-{ikfkBlendAttr}")
        mc.expression(s=f"{endOrientConstraint}.{ikEndCtrl}W1 = {ikfkBlendAttr}")

        topGrpName = f"{self.root}_rig_grp"
        mc.group([rootCtrlGrp, ikEndCtrlGrp, poleVectorCtrlGrp, ikfkBlendCtrlGrp], n=topGrpName)
        mc.parent(ikHandleName, ikEndCtrl)

        # Enabling Drawing Overrides 

        mc.setAttr(topGrpName+".overrideEnabled", 1)
        mc.setAttr(topGrpName+".overrideRGBColors", 1)
        mc.setAttr(topGrpName+".overrideColorRGB", self.controllerColor[0], self.controllerColor[1], self.controllerColor[2], type="double3")

class ColorPicker(QWidget):
    colorcahnged = Signal(QColor)
    def __init__(self):
            super().__init__()
            self.masterLayout = QVBoxLayout()
            self.color = QColor()
            self.setLayout(self.masterLayout)
            self.pickColorBtn = QPushButton()
            self.pickColorBtn.setStyleSheet(f"background-color:black")
            self.pickColorBtn.clicked.connect(self.PickColorBtnClicked)
            self.masterLayout.addWidget(self.pickColorBtn)

    def PickColorBtnClicked(self):
        self.color = QColorDialog.getColor()
        self.pickColorBtn.setStyleSheet(f"background-color:{self.color.name()}")
        self.colorcahnged.emit(self.color)

class LimbRiggerWidget(MayaWindow): # this class inherts from a previous mayawindow class
    def __init__(self): # A constructor of the limb Rigger Widget
        super().__init__() # calls the super class constructor 
        self.rigger = LimbRigger() # "self.rigger" is set to the LimbRigger class 
        self.setWindowTitle("Limb Rigger")

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout) 
        
        tootTipLabel = QLabel("Select the first joint of the limb, and press the auto find button") # creates a str variable
        self.masterLayout.addWidget(tootTipLabel) # adds the aformentioned variable to the master layout

        self.jntsListLineEdit = QLineEdit() # the variable self.jntsListLineEdit is set to the type of QLineEdit
        self.masterLayout.addWidget(self.jntsListLineEdit) # adds jntsListLineEdit to the master Layout
        self.jntsListLineEdit.setEnabled(False) # disables jntsListLineEdit 

        autoFindJntBtn = QPushButton("Auto Find") # creates a button named "Auto Find"
        autoFindJntBtn.clicked.connect(self.AutoFindJntBtnClicked) # detects if button is clicked
        self.masterLayout.addWidget(autoFindJntBtn) # adds the "Auto Find" button to master layout

        # Controller Size

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

        # Controller Color

        self.colorPicker = ColorPicker()
        self.colorPicker.colorcahnged.connect(self.ColorPickerChanged)
        self.masterLayout.addWidget(self.colorPicker)

        rigLimbBtn = QPushButton("Rig Limb") 
        rigLimbBtn.clicked.connect(lambda : self.rigger.RigLimb()) 
        self.masterLayout.addWidget(rigLimbBtn) 

        # Re-set Color
        
        setColorBtn = QPushButton("Set Color")
        self.masterLayout.addWidget(setColorBtn)
        setColorBtn.clicked.connect(self.SetColorBtnClickced)

    def SetColorBtnClickced(self):
        selection = mc.ls(sl=True)[0]
        color = self.colorPicker.color
        mc.setAttr(selection +".overrideEnabled", 1)
        mc.setAttr(selection +".overrideRGBColors", 1)
        mc.setAttr(selection +".overrideColorRGB", color.redF(), color.greenF(), color.blueF(), type="double3")

    def ColorPickerChanged(self, newColor: QColor):
        self.rigger.controllerColor[0] = newColor.redF()
        self.rigger.controllerColor[1] = newColor.greenF()
        self.rigger.controllerColor[2] = newColor.blueF()

    def CtrlSizeSliderChanged(self, newValue):
        self.ctrlSizeLabel.setText(f"{newValue}")
        self.rigger.controllerSize = newValue

    def AutoFindJntBtnClicked(self): 
        self.rigger.FindJointBasedOnSelection() 
        self.jntsListLineEdit.setText(f"{self.rigger.root},{self.rigger.mid},{self.rigger.end}")

limbRiggerWidget = LimbRiggerWidget()
limbRiggerWidget.show()



