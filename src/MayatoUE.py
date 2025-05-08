import os
from Maya_Utils import *
from PySide2.QtCore import Signal
from PySide2.QtGui import QIntValidator, QRegExpValidator
from PySide2.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QVBoxLayout
import maya.cmds as mc
import MayaPlugins
import remote_execution

def TryAction(actionFunc):
    def wrapper(*args, **kwargs):
        try:
            actionFunc(*args, **kwargs)
        except Exception as e:
            QMessageBox().critical(None, "Error!", f"{e}")

    return wrapper

class AnimClip:
    def __init__(self):
        self.subfix = ""
        self.frameMin = mc.playbackOptions(q=True, min=True)
        self.frameMax = mc.playbackOptions(q=True, min=True)
        self.shouldExport = True

class MayaToUE:
    def __init__(self):
        self.rootJnt = ""
        self.models = set()
        self.animations: list[AnimClip] = []
        self.fileName = ""
        self.saveDir = ""

    def SendToUnreal(self): 
        allJnts = []
        allJnts.append(self.rootJnt)
        children = mc.listRelatives(self.rootJnt, c=True, ad=True, typ="joint")
        if children:
            allJnts.extend(children)

        allMeshes = self.models
        allObjectToExport = allJnts + list(allMeshes)
        
        mc.select(allObjectToExport, r=True)
        skeletalMeshExportPath = self.GetSkeletalMeshSavePath()

        mc.FBXResetExport()
        mc.FBXExportSmoothingGroups("-v", True)
        mc.FBXExportInputConnections("-v", False)

        mc.FBXExport('-f', skeletalMeshExportPath, '-s', True, '-ea', False)

        if self.animations:
            mc.FBXExportBakeComplexAnimation('-v', True)

            os.makedirs(os.path.join(self.saveDir, "animations"), exist_ok=True)

            for animClip in self.animations:
                if not animClip.shouldExport:
                    continue

                animExportPath = self.GetSavePathForAnimClip(animClip)

                startFrame = animClip.frameMin
                endFrame = animClip.frameMax

                mc.FBXExportBakeComplexStart('-v', startFrame)
                mc.FBXExportBakeComplexEnd('-v', endFrame)
                mc.FBXExportBakeComplexStep('-v', 1)

                mc.playbackOptions(e=True, min=startFrame, max=endFrame)

                mc.FBXExport('-f', animExportPath, "-s", True, '-ea', True)

        ueUtilPath = os.path.join(MayaPlugins.srsDir, "UnrealUtils.py")
        ueUtilPath = os.path.normpath(ueUtilPath)

        meshPath = self.GetSkeletalMeshSavePath().replace("\\", "/")
        aimDir = os.path.join(self.saveDir, "animations").replace("\\", "/")

        commandLines = []
        with open(ueUtilPath, 'r') as ueUtilityFile:
            commandLines = ueUtilityFile.readlines()

        commandLines.append(f"\nImportMeshandAnimations(\'{meshPath}\', \'{aimDir}\')")

        command = "".join(commandLines)
        print(command)

        remoteExec = remote_execution.RemoteExecution()
        remoteExec.start()
        remoteExec.open_command_connection(remoteExec.remote_nodes)
        remoteExec.run_command(command)
        remoteExec.stop()


    def GetSkeletalMeshSavePath(self):
        savePath = os.path.join(self.saveDir, self.fileName + ".fbx")
        return os.path.normpath(savePath)
    
    def GetSavePathForAnimClip(self, animClip: AnimClip):
        savePath = os.path.join(self.saveDir, "animations", self.fileName + animClip.subfix + ".fbx")
        return os.path.normpath(savePath)

    def RemoveAnimClip(self, animClip: AnimClip):
        self.animations.remove(animClip)
        print(f"removed anim clip, now have: {len(self.animations)} left")

    def AddNewAnimClip(self):
        self.animations.append(AnimClip())
        return self.animations[-1]
    
    def AddSelectedMeshes(self):
        selection = mc.ls(sl=True)

        if not selection:
            raise Exception("No Mesh Selected, please select all the meshes of your rig.")
        
        meshes = []
        for sel in selection:
            if IsMesh(sel):
                meshes.append(sel)

        if len(meshes) == 0:
            raise Exception("No Mesh Selected, please select all the meshes of your rig.")
        
        self.models = meshes

    def AddRootJoint(self):
        if not self.rootJnt:
            raise Exception("No Root Joint Assigned. Please add the root joint of your rig first.")
        if mc.objExists(self.rootJnt):
            currentRootPos = mc.xform(self.rootJnt, q=True, ws=True, t=True)
            if currentRootPos[0] == 0 and currentRootPos[1] == 0 and currentRootPos[2] == 0:
                raise Exception("Current root joint is at origin already. No need to make a new one!")
            
        mc.select(cl=True)
        rootJntName = self.rootJnt + "_root"
        mc.joint(n=rootJntName)
        mc.parent(self.rootJnt, rootJntName)
        self.rootJnt = rootJntName

    def SetSelectedJointAsRoot(self):
        selection = mc.ls(sl=True, type="joint")
        if not selection:
            raise Exception("Wrong Selection! Please select the root joint of your rig!")
        
        self.rootJnt = selection[0]

class AnimClipWidget(QWidget):
    animClipRemoved = Signal(AnimClip)
    animClipSubfixChange = Signal(str)
    def __init__(self, animClip: AnimClip):
        super().__init__()
        self.animClip = animClip
        self.masterLayout = QHBoxLayout()
        self.setLayout(self.masterLayout)

        # Export Checkbox

        shouldExportCheckbox = QCheckBox()
        shouldExportCheckbox.setChecked(self.animClip.shouldExport)
        self.masterLayout.addWidget(shouldExportCheckbox)
        shouldExportCheckbox.toggled.connect(self.ShouldExportCheckboxToggled)

        # Subfix Label

        subfixLabel = QLabel("Subfix: ")
        self.masterLayout.addWidget(subfixLabel)

        subfixLineEdit = QLineEdit()
        subfixLineEdit.setValidator(QRegExpValidator("\w+"))
        subfixLineEdit.setText(self.animClip.subfix)
        subfixLineEdit.textChanged.connect(self.SubfixTextChanged)
        self.masterLayout.addWidget(subfixLineEdit)

        # Min-Frame Input

        minframeLabel = QLabel("Min: ")
        self.masterLayout.addWidget(minframeLabel)
        minframeLabelEdit = QLineEdit()
        minframeLabelEdit.setValidator(QIntValidator())
        minframeLabelEdit.setText(str(int(self.animClip.frameMin)))
        minframeLabelEdit.textChanged.connect(self.MinFrameChanged)
        self.masterLayout.addWidget(minframeLabelEdit)

        # Max-Frame Input

        maxframeLabel = QLabel("Max: ")
        self.masterLayout.addWidget(maxframeLabel)
        maxframeLabelEdit = QLineEdit()
        maxframeLabelEdit.setValidator(QIntValidator())
        maxframeLabelEdit.setText(str(int(self.animClip.frameMax)))
        maxframeLabelEdit.textChanged.connect(self.MaxFrameChanged)
        self.masterLayout.addWidget(maxframeLabelEdit)

        # Set Range

        setRangeBtn = QPushButton("[-]")
        setRangeBtn.clicked.connect(self.SetRangeBtnClicked)
        self.masterLayout.addWidget(setRangeBtn)

        # Delete Window

        deleteBtn = QPushButton("X")
        deleteBtn.clicked.connect(self.DeleteBtnClicked)
        self.masterLayout.addWidget(deleteBtn)

    def DeleteBtnClicked(self):
        self.animClipRemoved.emit(self.animClip)
        self.deleteLater()

    def SetRangeBtnClicked(self):
        mc.playbackOptions(e=True, min = self.animClip.frameMin, max = self.animClip.frameMax)
        mc.playbackOptions(e=True, ast = self.animClip.frameMin, aet = self.animClip.frameMax)

    def MinFrameChanged(self, newVal):
        self.animClip.frameMin = int(newVal)

    def MaxFrameChanged(self, newVal):
        self.animClip.frameMax = int(newVal)
    
    def SubfixTextChanged(self, newText):
        self.animClip.subfix = newText
        self. animClipSubfixChange.emit(newText)

    def ShouldExportCheckboxToggled(self):
        self.animClip.shouldExport = not self.animClip.shouldExport


class MayaToUEWidget(MayaWindow):
    def GetWidgetUniqueName(self):
        return "MayaToUEWidgetUnique"
    
    def __init__(self):
        super().__init__()
        self.mayaToUE = MayaToUE()
    
        self.setWindowTitle("Maya To UE")
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        # Root Joint

        self.rootJntText = QLineEdit()
        self.rootJntText.setEnabled(False)
        self.masterLayout.addWidget(self.rootJntText)

        setSelectedAsRootJntBtn = QPushButton("Set Root Joint")
        setSelectedAsRootJntBtn.clicked.connect(self.SetSelectedAsRootJntBtnClicekd)
        self.masterLayout.addWidget(setSelectedAsRootJntBtn)

        addRootJntBtn = QPushButton("Add Root Joint")
        addRootJntBtn.clicked.connect(self.AddRootJntBtnClicked)
        self.masterLayout.addWidget(addRootJntBtn)

        # Mesh List

        self.meshList = QListWidget()
        self.masterLayout.addWidget(self.meshList)
        self.meshList.setMaximumHeight(100)

        addMeshesBtn = QPushButton("Add Meshes")
        addMeshesBtn.clicked.connect(self.AddMeshesBtnClicked)
        self.masterLayout.addWidget(addMeshesBtn)

        # Animations

        addAnimEntryBtn = QPushButton("Add Animaiton Clip")
        addAnimEntryBtn.clicked.connect(self.AddAnimEntryBtnClicked)
        self.masterLayout.addWidget(addAnimEntryBtn)

        self.animClipEntryLayout = QVBoxLayout()
        self.masterLayout.addLayout(self.animClipEntryLayout)

        self.saveFileLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.saveFileLayout)

        self.saveFileLayout.addWidget(QLabel("File Name: "))
        self.filenameLineEdit = QLineEdit()
        self.filenameLineEdit.setFixedWidth(80)
        self.filenameLineEdit.setValidator(QRegExpValidator("\w+"))
        self.filenameLineEdit.textChanged.connect(self.FileNameLineEditChanged)
        self.saveFileLayout.addWidget(self.filenameLineEdit)

        self.saveFileLayout.addWidget(QLabel("Save Directory: "))
        self.saveDirLineEdit = QLineEdit()
        self.saveDirLineEdit.setEnabled(False)
        self.saveFileLayout.addWidget(self.saveDirLineEdit)

        self.pickDirBtn = QPushButton("...")
        self.pickDirBtn.clicked.connect(self.PickDirBtnClicked)
        self.saveFileLayout.addWidget(self.pickDirBtn)

        self.savePreviewLabel = QLabel("")
        self.masterLayout.addWidget(self.savePreviewLabel)

        sendToUEBtn = QPushButton("Send to Unreal")
        sendToUEBtn.clicked.connect(self.mayaToUE.SendToUnreal)
        self.masterLayout.addWidget(sendToUEBtn)

    def UpdateSavePreviewLabel(self):
        previewText = self.mayaToUE.GetSkeletalMeshSavePath()
        for animClip in self.mayaToUE.animations:
            animSavePath = self.mayaToUE.GetSavePathForAnimClip(animClip)
            previewText += "\n" + animSavePath

        self.savePreviewLabel.setText(previewText)

    def PickDirBtnClicked(self):
        pickedPath = QFileDialog().getExistingDirectory()
        self.saveDirLineEdit.setText(pickedPath)
        self.mayaToUE.saveDir = pickedPath
        self.UpdateSavePreviewLabel()

    def FileNameLineEditChanged(self, newVal):
        self.mayaToUE.fileName = newVal
        self.UpdateSavePreviewLabel()

    @TryAction
    def AddAnimEntryBtnClicked(self):
        newAnimClip = self.mayaToUE.AddNewAnimClip()
        newAnimClipWidget = AnimClipWidget(newAnimClip)
        newAnimClipWidget.animClipRemoved.connect(self.AnimationClipRemoved)
        newAnimClipWidget.animClipSubfixChange.connect(lambda *arg : self.UpdateSavePreviewLabel())
        self.animClipEntryLayout.addWidget(newAnimClipWidget)
        self.UpdateSavePreviewLabel()

    @TryAction
    def AnimationClipRemoved(self, animClip: AnimClip):
        self.mayaToUE.RemoveAnimClip(animClip)
        self.UpdateSavePreviewLabel()

    @TryAction
    def AddMeshesBtnClicked(self):
        self.mayaToUE.AddSelectedMeshes()
        self.meshList.clear()
        self.meshList.addItems(self.mayaToUE.models)

    @TryAction
    def AddRootJntBtnClicked(self):
        self.mayaToUE.AddRootJoint()
        self.rootJntText.setText(self.mayaToUE.rootJnt)

    @TryAction
    def SetSelectedAsRootJntBtnClicekd(self):
        self.mayaToUE.SetSelectedJointAsRoot()
        self.rootJntText.setText(self.mayaToUE.rootJnt)
        
MayaToUEWidget().show()