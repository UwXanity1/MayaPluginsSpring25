from PySide2.QtWidgets import QMainWindow, QSlider, QWidget 
from PySide2.QtCore import Qt
import maya.OpenMayaUI as omui
import shiboken2 
from PySide2.QtGui import QIntValidator, QRegExpValidator
from PySide2.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QVBoxLayout
import maya.cmds as mc
import os

def GetMayaMainWindow()->QMainWindow: 
    mayaWindow = omui.MQtUtil.mainWindow() 
    return shiboken2.wrapInstance(int(mayaWindow), QMainWindow)

def DeleteWidgetWithName(name): 
    for widget in GetMayaMainWindow().findChildren(QWidget, name):  
        widget.deleteLater() 

     
class MayaWindow(QWidget): 
    def __init__(self):
        super().__init__(parent = GetMayaMainWindow())  
        DeleteWidgetWithName(self.GetWidgetUniqueName())  
        self.setWindowFlags(Qt.WindowType.Window) 
        self.setObjectName(self.GetWidgetUniqueName()) 

    def GetWidgetUniqueName(self): 
       return "UniqueName"

class PlaceJointBasedOnSelectedVerts():
    def __init__(self):
        mc.selectPref(tso=True)
        print("setting select pref")
        self.verts = ""
        self.model = ""
        self.jnts = []        
        
    def PlaceJoints(self, jntNameBase):
        self.verts = mc.ls(os=True, fl=True)
        print(jntNameBase)
        if self.verts:
            for i, vert in enumerate(self.verts):
                x,y,z = mc.pointPosition(vert)
                mc.select(cl=True)
                jntName = jntNameBase + "_" + str(i+1).zfill(2)
                newJnt = mc.joint()
                mc.setAttr(newJnt + ".tx", x)
                mc.setAttr(newJnt + ".ty", y)
                mc.setAttr(newJnt + ".tz", z)

    def PlaceControls(self):
        self.jnts = mc.ls(sl=True)

class VertexToJointWidget(MayaWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vertex to Joint Rigger")
        self.vertexToJoint = PlaceJointBasedOnSelectedVerts()
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.masterLayout.addWidget(QLabel("Select certain joints of the model, then click Place Joints"))
        placeJointsBtn = QPushButton("Place Joints")
        self.masterLayout.addWidget(placeJointsBtn)
        placeJointsBtn.clicked.connect(self.PlaceJntBtnClicked)

        self.masterLayout.addWidget(QLabel("Now, Selected each of joints in order, and press Connect Joints"))
        connectJointsBtn = QPushButton("Connect Joints")
        self.masterLayout.addWidget(connectJointsBtn)
        connectJointsBtn.clicked.connect(self.ConnectJoints)

        self.masterLayout.addWidget(QLabel("Now that the joints are connected, click Place Controls"))
        placeControlsBtn = QPushButton("Place Controls")
        self.masterLayout.addWidget(placeControlsBtn)
        placeControlsBtn.clicked.connect(self.CreateControls)

        self.masterLayout.addWidget(QLabel("Joint Name -"))
        self.jntNamesLineEdit = QLineEdit("")
        self.masterLayout.addWidget(self.jntNamesLineEdit)

        self.controllerSizeLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.controllerSizeLayout)

        self.controllerSizeSlider = QSlider()
        self.controllerSizeSlider.setOrientation(Qt.Horizontal)
        self.controllerSizeSlider.setRange(1, 15)
        self.controllerSizeSlider.setValue(10)
        self.controllerSizeLayout.addWidget(self.controllerSizeSlider)
        self.controllerSizeSlider.valueChanged.connect(self.ControllerSizeChanged)
        
        self.controllerSizeLabel = QLabel(f"{10}")
        self.controllerSizeLayout.addWidget(self.controllerSizeLabel)

    def CreateControls(self):
        rootJnt = mc.ls(sl=True)[0]
        self.CreateControlForJntChain(rootJnt)


    def ControllerSizeChanged(self, newSize):
        self.controllerSizeLabel.setText(f"{newSize}")

    def PlaceJntBtnClicked(self):
        self.vertexToJoint.PlaceJoints(self.jntNamesLineEdit.text())

    def ConnectJoints(self):
        jntNameBase = self.jntNamesLineEdit.text()
        jnts = mc.ls(sl=True)
        for i in range(len(jnts)-1, 0, -1):
                child = jnts[i]
                parent = jnts[i-1]
                mc.parent(child, parent)
                mc.rename(child, jntNameBase + "_" + str(i+1).zfill(2))

        mc.rename(jnts[0], jntNameBase + "_" + str(1).zfill(2))

    def CreateControlForJntChain(self, root):
        ctrl, ctrlGrp = self.CreateControlForJnt(root)
        children = mc.listRelatives(root, c=True, type="joint")
        childrenCtrlGrps = []
        if children:
           for child in children:
                childCtrl, childCtrlGrp = self.CreateControlForJntChain(child)
                childrenCtrlGrps.append(childCtrlGrp)

        if childrenCtrlGrps:
            mc.parent(childrenCtrlGrps, ctrl)

        return ctrl, ctrlGrp
        

    def CreateControlForJnt(self, jnt):
        ctrlName = "ac_" + jnt
        controllerSize = self.controllerSizeSlider.value()
        mc.circle(name = ctrlName, radius = controllerSize, normal = (0,1,0)) 
        
        ctrlGrpName = ctrlName + "_grp"
        mc.group(ctrlName, n=ctrlGrpName) 
        mc.matchTransform(ctrlGrpName, jnt)
        mc.orientConstraint(ctrlName, jnt)
        # ctrlName = "l_" + jntname # use what was put in the textbox for joint name as the control name
        # ctrlGrpName = ctrlName + "_grp"

        return ctrlName, ctrlGrpName
    
    
    def NameJoints(self, jntname):
        jntname = QLineEdit() + jntNum # use what was put in text box to name the joint
        jntNum += 1 


    def GetWidgetUniqueName(self):
        return "VertexToJointUnique"


VertexToJointWidget().show()
