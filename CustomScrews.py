#Author-Fabian Schurig
#Description-

# Simple Add-In imports
import adsk.core, adsk.fusion, adsk.cam, traceback, os, gettext
# math imports
import math
import requests

'''
QAT = Quick Access Toolbar
define commandIds and inputIds
'''
commandIdOnQAT = 'createScrewCommandOnQAT'
commandIdOnPanel = 'createScrewCommandOnPanel'
selectionInputId = 'selectionInput'
distanceInputId = 'distanceValueCommandInput'
panelId = 'SolidCreatePanel'

'''
define default parameters to initialize the screw
0.1 = 1mm
'''
defaultCylinderheadScrewName= 'Screw'
defaultCylinderheadDiameter = 0.55 #dk
defaultCylinderheadHeight = 0.3 #k
defaultHexagonDiameter = 0.25 #s
defaultHexagonHeight = 0.19 #t
defaultThreadLength = 0.8 #b
defaultBodyLength = 1.0 #bodylength
defaultBodyDiameter = 0.25 #d
defaultFilletRadius = 0.025 #f
defaultChamferDistance = 0.025 #c

# {name,d=k,dk,s,t,b,bodylength}
#ISO 4762/ DIN912
presets = [[1,'M2 x8',0.2,0.38,0.2,0.15,0.1,0.6,0.8],[2,'M2 x10',0.2,0.38,0.2,0.15,0.1,0.6,1.0],[3,'M2 x12',0.2,0.38,0.2,0.15,0.1,0.6,1.2],
           [4,'M3 x8',0.3,0.568,0.3,0.25,0.19,0.6,0.8],[5,'M3 x10',0.3,0.568,0.3,0.25,0.19,0.6,1.0],[6,'M3 x12',0.3,0.568,0.3,0.25,0.19,0.6,1.2]]
lastPresetId = 0

# global set of event handlers to keep them referenced for the duration of the command
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

newComp = None
rowNumber = 0

def addRow(tableInput,inputs,preset):
    
    button = inputs.addBoolValueInput(tableInput.id + '_button{}'.format(rowNumber), '', False, './resources/B', False)
    #button.isFullWidth = True
    
    stringInput = inputs.addStringValueInput(tableInput.id + '_stringInput{}'.format(rowNumber), '', str(preset[1]))
    stringInput.isReadOnly = True
    
    s = ''
    if preset[8] != None:
        s = str(preset[8]*10) + " mm"
    else:
        s = 'None'
    bodyLength = inputs.addStringValueInput(tableInput.id + '_bodyLength{}'.format(rowNumber), '', str(s))
    bodyLength.isReadOnly = True
    
    row = tableInput.rowCount
    tableInput.addCommandInput(button, row, 0)
    tableInput.addCommandInput(stringInput, row, 1)
    tableInput.addCommandInput(bodyLength, row, 2)
    
    global rowNumber
    rowNumber = rowNumber + 1

def getPresetParameters():
    try:
        r = requests.get('http://adsk.hk-fs.de') # http://adsk.hk-fs.de localhost:5000
        return r.json()
    except:
        return None

'''
function createNewComponent
This function gets the current design of the user and creates a new component in it.
returns a new component in the current design
'''
def createNewComponent():
    # Get the active design.
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component

'''
Support localization
function getUserLanguage
returns the users language
'''
_ = None
def getUserLanguage():
    app = adsk.core.Application.get()
    
    return {
        adsk.core.UserLanguages.ChinesePRCLanguage: "zh-CN",
        adsk.core.UserLanguages.ChineseTaiwanLanguage: "zh-TW",
        adsk.core.UserLanguages.CzechLanguage: "cs-CZ",
        adsk.core.UserLanguages.EnglishLanguage: "en-US",
        adsk.core.UserLanguages.FrenchLanguage: "fr-FR",
        adsk.core.UserLanguages.GermanLanguage: "de-DE",
        adsk.core.UserLanguages.HungarianLanguage: "hu-HU",
        adsk.core.UserLanguages.ItalianLanguage: "it-IT",
        adsk.core.UserLanguages.JapaneseLanguage: "ja-JP",
        adsk.core.UserLanguages.KoreanLanguage: "ko-KR",
        adsk.core.UserLanguages.PolishLanguage: "pl-PL",
        adsk.core.UserLanguages.PortugueseBrazilianLanguage: "pt-BR",
        adsk.core.UserLanguages.RussianLanguage: "ru-RU",
        adsk.core.UserLanguages.SpanishLanguage: "es-ES"
    }[app.preferences.generalPreferences.userLanguage]

'''
Get loc string by language
'''
def getLocStrings():
    currentDir = os.path.dirname(os.path.realpath(__file__))
    return gettext.translation('resource', currentDir, [getUserLanguage(), "en-US"]).gettext 

'''

'''
def commandDefinitionById(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox(_('commandDefinition id is not specified'))
        return None
    commandDefinitions_ = ui.commandDefinitions
    commandDefinition_ = commandDefinitions_.itemById(id)
    return commandDefinition_

'''

'''
def commandControlByIdForQAT(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox(_('commandControl id is not specified'))
        return None
    toolbars_ = ui.toolbars
    toolbarQAT_ = toolbars_.itemById('QAT')
    toolbarControls_ = toolbarQAT_.controls
    toolbarControl_ = toolbarControls_.itemById(id)
    return toolbarControl_

'''

'''
def commandControlByIdForPanel(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox(_('commandControl id is not specified'))
        return None
    workspaces_ = ui.workspaces
    modelingWorkspace_ = workspaces_.itemById('FusionSolidEnvironment')
    toolbarPanels_ = modelingWorkspace_.toolbarPanels
    toolbarPanel_ = toolbarPanels_.itemById(panelId)
    toolbarControls_ = toolbarPanel_.controls
    toolbarControl_ = toolbarControls_.itemById(id)
    return toolbarControl_

'''

'''
def destroyObject(uiObj, tobeDeleteObj):
    if uiObj and tobeDeleteObj:
        if tobeDeleteObj.isValid:
            tobeDeleteObj.deleteMe()
        else:
            uiObj.messageBox(_('tobeDeleteObj is not a valid object'))

'''
class Screw
'''
class Screw:
    def __init__(self):
        self._screwName = defaultCylinderheadScrewName
        self._headDiameter = adsk.core.ValueInput.createByReal(defaultCylinderheadDiameter)
        self._bodyDiameter = adsk.core.ValueInput.createByReal(defaultBodyDiameter)
        self._headHeight = defaultCylinderheadHeight
        self._bodyLength = adsk.core.ValueInput.createByReal(defaultBodyLength)
        self._hexagonDiameter = adsk.core.ValueInput.createByReal(defaultHexagonDiameter)
        self._hexagonHeight = adsk.core.ValueInput.createByReal(defaultHexagonHeight)
        self._filletRadius = adsk.core.ValueInput.createByReal(defaultFilletRadius)
        self._threadLength = adsk.core.ValueInput.createByReal(defaultThreadLength)
        self._chamferDistance = defaultChamferDistance

    #properties
    @property
    def screwName(self):
        return self._screwName
    @screwName.setter
    def screwName(self, value):
        self._screwName = value

    @property
    def headDiameter(self):
        return self._headDiameter
    @headDiameter.setter
    def headDiameter(self, value):
        self._headDiameter = value

    @property
    def bodyDiameter(self):
        return self._bodyDiameter
    @bodyDiameter.setter
    def bodyDiameter(self, value):
        self._bodyDiameter = value 

    @property
    def headHeight(self):
        return self._headHeight
    @headHeight.setter
    def headHeight(self, value):
        self._headHeight = value 

    @property
    def bodyLength(self):
        return self._bodyLength
    @bodyLength.setter
    def bodyLength(self, value):
        self._bodyLength = value   

    @property
    def threadLength(self):
        return self._threadLength
    @threadLength.setter
    def threadLength(self, value):
        self._threadLength = value  

    @property
    def hexagonDiameter(self):
        return self._hexagonDiameter
    @hexagonDiameter.setter
    def hexagonDiameter(self, value):
        self._hexagonDiameter = value

    @property
    def hexagonHeight(self):
        return self._hexagonHeight
    @hexagonHeight.setter
    def hexagonHeight(self, value):
        self._hexagonHeight = value
        
    @property
    def filletRadius(self):
        return self._filletRadius
    @filletRadius.setter
    def filletRadius(self, value):
        self._filletRadius = value
    
    @property
    def chamferDistance(self):
        return self._chamferDistance
    @chamferDistance.setter
    def chamferDistance(self, value):
        self._chamferDistance = value

    def buildScrew(self):
        global newComp
        newComp = createNewComponent()
        if newComp is None:
            ui.messageBox('New component failed to create', 'New Component Failed')
            return

        # Create a new sketch.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        xzPlane = newComp.xZConstructionPlane
        sketch = sketches.add(xyPlane)
        center = adsk.core.Point3D.create(0, 0, 0)
        sketch.sketchCurves.sketchCircles.addByCenterRadius(center, self.headDiameter/2)

        extrudes = newComp.features.extrudeFeatures
        prof = sketch.profiles[0]
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        distance = adsk.core.ValueInput.createByReal(self.headHeight)
        extInput.setDistanceExtent(False, distance)
        headExt = extrudes.add(extInput)

        endFaceOfExtrude = headExt.endFaces.item(0)
        
        # Create the joint geometry
        jointGeometry = adsk.fusion.JointGeometry.createByPlanarFace(endFaceOfExtrude, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)

        # Create the JointOriginInput
        jointOrigins_ = newComp.jointOrgins
        jointOriginInput = jointOrigins_.createInput(jointGeometry)

        # Create the JointOrigin
        jointOrigins_.add(jointOriginInput)
         
        fc = headExt.faces[0]
        bd = fc.body
        bd.name = self.screwName
        
        # Get construction planes
        planes = newComp.constructionPlanes
        
        # Create construction plane input
        planeInput = planes.createInput()
        
        # Add construction plane by offset
        offsetValue = adsk.core.ValueInput.createByReal(self.headHeight)
        planeInput.setByOffset(xyPlane, offsetValue)
        planeOne = planes.add(planeInput)
        
        #cut the hexagon
        sketchHex = sketches.add(xyPlane)
        vertices = []
        hexagonOuterDiameter = self.hexagonDiameter/math.sqrt(3)
        for i in range(0, 6):
            vertex = adsk.core.Point3D.create(center.x + (hexagonOuterDiameter) * math.cos(math.pi * i / 3), center.y + (hexagonOuterDiameter) * math.sin(math.pi * i / 3),0)
            vertices.append(vertex)

        for i in range(0, 6):
            sketchHex.sketchCurves.sketchLines.addByTwoPoints(vertices[(i+1) %6], vertices[i])

        extrudes = newComp.features.extrudeFeatures
        prof = sketchHex.profiles[0]
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)

        distance = adsk.core.ValueInput.createByReal(self.hexagonHeight)
        extInput.setDistanceExtent(False, distance)
        hexExt = extrudes.add(extInput)

        fc = hexExt.faces[0]
        bd = fc.body
        bd.name = self.screwName

        #create the body
        bodySketch = sketches.add(planeOne)
        bodySketch.sketchCurves.sketchCircles.addByCenterRadius(center, self.bodyDiameter/2)

        bodyProf = bodySketch.profiles[0]
        bodyExtInput = extrudes.createInput(bodyProf, adsk.fusion.FeatureOperations.JoinFeatureOperation)

        bodyExtInput.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
        bodyExtInput.setDistanceExtent(False, self.bodyLength)
        bodyExt = extrudes.add(bodyExtInput)

        # create chamfer
        edgeCol = adsk.core.ObjectCollection.create()
        edges = bodyExt.endFaces[0].edges
        for edgeI  in edges:
            edgeCol.add(edgeI)

        chamferFeats = newComp.features.chamferFeatures
        chamferInput = chamferFeats.createInput(edgeCol, True)
        chamferInput.setToEqualDistance(self.chamferDistance)
        chamferFeats.add(chamferInput)
        
        # create fillet
        edgeCol.clear()
        facesLoop = headExt.faces
        for face in facesLoop:
            loops = face.loops
            edgeLoop = None
            for edgeLoop in loops:
                if(len(edgeLoop.edges) == 1):
                    edgeCol.add(edgeLoop.edges[0])
                    break
        
        #edgeCol.add(headExt.faces[0].loops[0].edges[0])
        #edgeCol.add(headExt.faces[0].loops[1].edges[0])
        #edgeCol.add(headExt.endFaces[0].loops[0].edges[0])
        
        filletFeats = newComp.features.filletFeatures
        filletInput = filletFeats.createInput()
        filletInput.addConstantRadiusEdgeSet(edgeCol, self.filletRadius, True)
        filletFeats.add(filletInput)
        
        #create thread
        sideFace = bodyExt.sideFaces[0]
        threads = newComp.features.threadFeatures
        threadDataQuery = threads.threadDataQuery
        defaultThreadType = threadDataQuery.defaultMetricThreadType
        recommendData = threadDataQuery.recommendThreadData(self.bodyDiameter, False, defaultThreadType)
        if recommendData[0] :
            threadInfo = threads.createThreadInfo(False, defaultThreadType, recommendData[1], recommendData[2])
            faces = adsk.core.ObjectCollection.create()
            faces.add(sideFace)
            threadInput = threads.createInput(faces, threadInfo)
            threadInput.isFullLength = False
            threadInput.threadLength = adsk.core.ValueInput.createByReal(self.threadLength)
            threads.add(threadInput)
    def joinScrew(self,jointOrigin,joinComp):
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)        
        
        rootComp = design.rootComponent        
        
        #Get the occurrence of the new component
        #occ = rootComp.occurrences.item(0)
        
        jointOrigins_ = joinComp.jointOrgins
        jointOriginInput = jointOrigins_[0]
        
        joints = rootComp.joints
        jointInput = joints.createInput(jointOriginInput, jointOrigin)
        
        # Set the joint input
        # Set the joint input
        angle = adsk.core.ValueInput.createByString('0 deg')
        jointInput.angle = angle
        offset = adsk.core.ValueInput.createByString('0 cm')
        jointInput.offset = offset
        jointInput.isFlipped = True
        jointInput.setAsRigidJointMotion()
        
        #Create the joint
        joint = joints.add(jointInput)
    def copy(self):
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        rootComp = design.rootComponent
        allOccs = rootComp.occurrences
        newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
        tmpComp = newOcc.component        
        
        body = newComp.bRepBodies.item(0)
        b = body.copyToComponent(newOcc)
        #ui.messageBox('fc '+str(body.faces.count))
        
        
        i = 0
        for face in b.faces:
            #ui.messageBox('yeyy '+str(i)+'lol '+str(face.centroid.z))
            if face.centroid.z == self.headHeight:
                #ui.messageBox('yeyy '+str(i)+'lol '+str(self.headHeight))
                break
            i = i + 1
        face = b.faces.item(i)
        
        
        # Create the joint geometry
        jointGeometry = adsk.fusion.JointGeometry.createByPlanarFace(face, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)

        # Create the JointOriginInput
        jointOrigins_ = tmpComp.jointOrgins
        jointOriginInput = jointOrigins_.createInput(jointGeometry)

        # Create the JointOrigin
        jointOrigins_.add(jointOriginInput)
        return tmpComp
        

'''
run - main function of the Add-in
'''       
def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        global _
        _ = getLocStrings()
        
        global presets
        
        commandName = _('Create Screw')
        commandDescription = _('Create a cylinderhead screw by manipulating different parameters or select preset values.')
        commandResources = './resources'
        iconResources = './resources'
        
        screw = Screw()

        '''
        function InputChangedHandler triggers if sth was changed
        '''
        class InputChangedHandler(adsk.core.InputChangedEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:
                    eventArgs = adsk.core.InputChangedEventArgs.cast(args)
                    changedInput = eventArgs.input
                    
                    unitsMgr = app.activeProduct.unitsManager
                    command = args.firingEvent.sender
                    cmdInput = args.input
                    inputs = eventArgs.firingEvent.sender.commandInputs
                    defaultUnits = unitsMgr.defaultLengthUnits
                    
                    tableInput = inputs.itemById('presetTable')
                    if tableInput.id + '_button' in cmdInput.id:
                        preset = str(cmdInput.id).replace(tableInput.id + '_button',"")
                        #ui.messageBox(preset)
                        inputs.itemById('screwName').value = presets[int(preset)][1] 
                        inputs.itemById('bodyDiameter').value = presets[int(preset)][2]                        
                        inputs.itemById('headDiameter').value = presets[int(preset)][3]
                        inputs.itemById('headHeight').value = presets[int(preset)][4]
                        inputs.itemById('hexagonDiameter').value = presets[int(preset)][5]
                        inputs.itemById('hexagonHeight').value = presets[int(preset)][6]
                        if presets[int(preset)][7] == None or presets[int(preset)][8] == None:
                            inputs.itemById('threadLength').value = presets[int(preset)][4]*5 - 0.2
                            inputs.itemById('bodyLength').value = presets[int(preset)][4]*5
                        else:
                            inputs.itemById('threadLength').value = presets[int(preset)][7]
                            inputs.itemById('bodyLength').value = presets[int(preset)][8]
                               
                    global lastPresetId
                    preset = inputs.itemById('dropdownPresets')
                    if preset.selectedItem.index > 0 and preset.selectedItem.index <= len(presets) and preset.selectedItem.index != lastPresetId:
                        inputs.itemById('bodyDiameter').value = presets[preset.selectedItem.index-1][2]                        
                        inputs.itemById('headDiameter').value = presets[preset.selectedItem.index-1][3]
                        inputs.itemById('headHeight').value = presets[preset.selectedItem.index-1][4]
                        inputs.itemById('hexagonDiameter').value = presets[preset.selectedItem.index-1][5]
                        inputs.itemById('hexagonHeight').value = presets[preset.selectedItem.index-1][6]
                        inputs.itemById('threadLength').value = presets[preset.selectedItem.index-1][7]
                        inputs.itemById('bodyLength').value = presets[preset.selectedItem.index-1][8]
                        #ui.messageBox('input changed '+str(lastPresetId) +' '+str(preset.selectedItem.index)+' '+str(inputs.itemById('bodyDiameter').value))                        
                    
                    point = adsk.core.Point3D.create(0, 0, inputs.itemById('headHeight').value)
                    direction = adsk.core.Vector3D.create(0, 0, 1)
                    #ui.messageBox(str(inputs.itemById('bodyLength')))
                    manipulator = inputs.itemById('bodyLength').setManipulator(point, direction)                
                    
                    #if cmdInput.id == inputs.itemById('jointSelection').id:
                        #ui.messageBox("new selected item")
                        #ui.messageBox(str(inputs.itemById('jointSelection').selection(0).entity))
                    
                    lastPresetId = preset.selectedItem.index
                    #ui.messageBox('asasas '+str(inputs.itemById('bodyDiameter').value))
                    args.isValidResult = True
                       
                    
                except:
                    if ui:
                        ui.messageBox(_('Input changed event failed: {}').format(traceback.format_exc()))
        class CommandExecutePreviewHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:                
                    eventArgs = adsk.core.CommandEventArgs.cast(args)
                    unitsMgr = app.activeProduct.unitsManager
                    # Get the values from the command inputs.
                    inputs = eventArgs.command.commandInputs
                    
                    for input in inputs:
                        if input.id == 'screwName':
                            screw.screwName = input.value
                        elif input.id == 'headDiameter':
                            screw.headDiameter = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'bodyDiameter':
                            screw.bodyDiameter = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'headHeight':
                            screw.headHeight = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'bodyLength':
                            screw.bodyLength = adsk.core.ValueInput.createByString(input.expression)
                        elif input.id == 'filletRadius':
                            screw.filletRadius = adsk.core.ValueInput.createByString(input.expression)
                        elif input.id == 'threadLength':
                            screw.threadLength = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'hexagonDiameter':
                            screw.hexagonDiameter = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'hexagonHeight':
                            screw.hexagonHeight = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'chamferDistance':
                            screw.chamferDistance = adsk.core.ValueInput.createByString(input.expression)
                            
                    screw.buildScrew()
                    for j in range(0, inputs.itemById('jointSelection').selectionCount):
                        joinComp = screw.copy()
                        screw.joinScrew(inputs.itemById('jointSelection').selection(j).entity,joinComp)
                        j = j + 1
                    eventArgs.isValidResult = True
                except:
                    if ui:
                        ui.messageBox(_('execute preview failed: {}').format(traceback.format_exc()))
        class CommandExecuteHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:
                    eventArgs = adsk.core.CommandEventArgs.cast(args)
                    unitsMgr = app.activeProduct.unitsManager
                    # Get the values from the command inputs.
                    inputs = eventArgs.command.commandInputs
                    
                    for input in inputs:
                        if input.id == 'screwName':
                            screw.screwName = input.value
                        elif input.id == 'headDiameter':
                            screw.headDiameter = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'bodyDiameter':
                            screw.bodyDiameter = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'headHeight':
                            screw.headHeight = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'bodyLength':
                            screw.bodyLength = adsk.core.ValueInput.createByString(input.expression)
                        elif input.id == 'filletRadius':
                            screw.filletRadius = adsk.core.ValueInput.createByString(input.expression)
                        elif input.id == 'threadLength':
                            screw.threadLength = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'hexagonDiameter':
                            screw.hexagonDiameter = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'hexagonHeight':
                            screw.hexagonHeight = unitsMgr.evaluateExpression(input.expression, "mm")
                        elif input.id == 'chamferDistance':
                            screw.chamferDistance = adsk.core.ValueInput.createByString(input.expression)
                            
                    screw.buildScrew()
                    args.isValidResult = True
                    ui.messageBox(_('command: {} executed successfully').format(command.parentCommandDefinition.id))
                except:
                    if ui:
                        ui.messageBox(_('command executed failed: {}').format(traceback.format_exc()))

        class CommandCreatedEventHandlerPanel(adsk.core.CommandCreatedEventHandler):
            def __init__(self):
                super().__init__() 
            def notify(self, args):
                try:
                    cmd = args.command
                    cmd.isRepeatable = False
                    cmd.helpFile = 'help.html'
                    global presets
                    global rowNumber        
                    rowNumber = 0
        
                    fetchedPresets = '<b>Notice:</b> Database connection failed! '+str(len(presets))+' offline presets loaded'       
                    #load Presets
                    r = getPresetParameters()        
                    
                    #ui.messageBox('Get_Request '+str(r['iso_4762']))
                    if r != None:
                        presets = r['iso_4762']
                        fetchedPresets = 'Database connected! Fetched '+str(len(presets))+' online presets'
                        #ui.messageBox(str(len(r['iso_4762'])))
                    
                    #define the inputs
                    inputs = cmd.commandInputs
                    inputs.addStringValueInput('screwName', _('Screw Name'), defaultCylinderheadScrewName)
                    
                    
                    # Create the table, defining the number of columns and their relative widths.
                    table = inputs.addTableCommandInput('presetTable', 'Table', 3, '1:4:2')
                    
                    # Define some of the table properties.
                    table.minimumVisibleRows = 3
                    table.maximumVisibleRows = 4
                    table.columnSpacing = 10
                    table.rowSpacing = 2
                    # transparentBackgroundTablePresentationStyle itemBorderTablePresentationStyle nameValueTablePresentationStyle
                    table.tablePresentationStyle = adsk.core.TablePresentationStyles.itemBorderTablePresentationStyle
                    table.hasGrid = False
                    
                    for preset in presets:
                        addRow(table, inputs, preset)
                    
                    # Create dropdown input with radio style
                    dropdownInputPreset = inputs.addDropDownCommandInput('dropdownPresets', _('Presets'), adsk.core.DropDownStyles.LabeledIconDropDownStyle)
                    dropdownItems = dropdownInputPreset.listItems
                    dropdownItems.add('Default', True, '')                    
                    for preset in presets:
                        dropdownItems.add(str(preset[1]), False, '')
                    dropdownInputPreset.isVisible = False
                    
                    selectionInput = inputs.addSelectionInput('jointSelection', 'Select', 'Basic select command input')
                    selectionInput.setSelectionLimits(0)
                    selectionInput.addSelectionFilter('JointOrigins')
                    
                    
                    initBodyLength = adsk.core.ValueInput.createByReal(defaultBodyLength)
                    bodyLength = inputs.addDistanceValueCommandInput('bodyLength', _('Body Length'), initBodyLength)
                    point = adsk.core.Point3D.create(0, 0, defaultCylinderheadHeight)
                    direction = adsk.core.Vector3D.create(0, 0, 1)
                    manipulator = bodyLength.setManipulator(point, direction) 

                    initThreadLength = adsk.core.ValueInput.createByReal(defaultThreadLength)
                    inputs.addValueInput('threadLength', _('Thread Length'), 'mm', initThreadLength)                    
                    
                    # Create group input
                    groupCmdInput = inputs.addGroupCommandInput('group', _('Advanced'))
                    groupCmdInput.isExpanded = False
                    #groupCmdInput.isEnabledCheckBoxDisplayed = True
                    groupChildInputs = groupCmdInput.children

                    initHeadDiameter = adsk.core.ValueInput.createByReal(defaultCylinderheadDiameter)
                    groupChildInputs.addValueInput('headDiameter', _('Head Diameter'),'mm', initHeadDiameter)

                    initBodyDiameter = adsk.core.ValueInput.createByReal(defaultBodyDiameter)
                    groupChildInputs.addValueInput('bodyDiameter', _('Body Diameter'), 'mm', initBodyDiameter)

                    initHeadHeight = adsk.core.ValueInput.createByReal(defaultCylinderheadHeight)
                    groupChildInputs.addValueInput('headHeight', _('Head Height'), 'mm', initHeadHeight)

                    initHexagonDiameter = adsk.core.ValueInput.createByReal(defaultHexagonDiameter)
                    groupChildInputs.addValueInput('hexagonDiameter', _('Hexagon Diameter'), 'mm', initHexagonDiameter)
                    
                    initHexagonHeight = adsk.core.ValueInput.createByReal(defaultHexagonHeight)
                    groupChildInputs.addValueInput('hexagonHeight', _('Hexagon Height'), 'mm', initHexagonHeight)

                    initFilletRadius = adsk.core.ValueInput.createByReal(defaultFilletRadius)
                    groupChildInputs.addValueInput('filletRadius', _('Fillet Radius'), 'mm', initFilletRadius)
                    
                    initChamferDistance = adsk.core.ValueInput.createByReal(defaultChamferDistance)
                    groupChildInputs.addValueInput('chamferDistance', _('Chamfer Distance'), 'mm', initChamferDistance)
                    
                    textBox = inputs.addTextBoxCommandInput('textBox', 'Status', fetchedPresets, 1, True)
                    textBox.isFullWidth = True
                    
                    #Connect all Handlers
                    onExecute = CommandExecuteHandler()
                    cmd.execute.add(onExecute)

                    onInputChanged = InputChangedHandler()
                    cmd.inputChanged.add(onInputChanged)
                    
                    onPreview = CommandExecutePreviewHandler()
                    cmd.executePreview.add(onPreview)
                    
                    # keep the handler referenced beyond this function
                    handlers.append(onExecute)
                    handlers.append(onInputChanged)
                    handlers.append(onPreview)
                    
                    '''
                    selInput = commandInputs_.addSelectionInput(selectionInputId, _('Selection'), _('Select one'))
                    selInput.addSelectionFilter('PlanarFaces')
                    selInput.addSelectionFilter('ConstructionPlanes')
                    dropDownCommandInput_ = commandInputs_.addDropDownCommandInput('dropdownCommandInput', _('Drop Down'), adsk.core.DropDownStyles.LabeledIconDropDownStyle)
                    dropDownItems_ = dropDownCommandInput_.listItems
                    dropDownItems_.add(_('ListItem 1'), True)
                    dropDownItems_.add(_('ListItem 2'), False)
                    dropDownItems_.add(_('ListItem 3'), False)
                    '''
                    
                    #ui.messageBox(_('Panel command created successfully'))
                except:
                    if ui:
                        ui.messageBox(_('Panel command created failed: {}').format(traceback.format_exc()))

        commandDefinitions_ = ui.commandDefinitions
        
        # add a command on create panel in modeling workspace
        workspaces_ = ui.workspaces
        modelingWorkspace_ = workspaces_.itemById('FusionSolidEnvironment')
        toolbarPanels_ = modelingWorkspace_.toolbarPanels
        toolbarPanel_ = toolbarPanels_.itemById(panelId) # add the new command under the CREATE panel
        toolbarControlsPanel_ = toolbarPanel_.controls
        toolbarControlPanel_ = toolbarControlsPanel_.itemById(commandIdOnPanel)
        if not toolbarControlPanel_:
            commandDefinitionPanel_ = commandDefinitions_.itemById(commandIdOnPanel)
            if not commandDefinitionPanel_:
                commandDefinitionPanel_ = commandDefinitions_.addButtonDefinition(commandIdOnPanel, commandName, commandDescription, commandResources)
                commandDefinitionPanel_.toolClipFilename = './resources/technical_small.png'
            onCommandCreated = CommandCreatedEventHandlerPanel()
            commandDefinitionPanel_.commandCreated.add(onCommandCreated)
            # keep the handler referenced beyond this function
            handlers.append(onCommandCreated)
            toolbarControlPanel_ = toolbarControlsPanel_.addCommand(commandDefinitionPanel_)
            toolbarControlPanel_.isVisible = True
            ui.messageBox(_('The command is successfully added to the create panel in modeling workspace'))

    except:
        if ui:
            ui.messageBox(_('AddIn Start Failed: {}').format(traceback.format_exc()))
            
            
            
'''
Stop function runs when Add-In is stopped or Fusion crashes
'''            
def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        objArrayQAT = []
        objArrayPanel = []

        commandControlQAT_ = commandControlByIdForQAT(commandIdOnQAT)
        if commandControlQAT_:
            objArrayQAT.append(commandControlQAT_)

        commandDefinitionQAT_ = commandDefinitionById(commandIdOnQAT)
        if commandDefinitionQAT_:
            objArrayQAT.append(commandDefinitionQAT_)

        commandControlPanel_ = commandControlByIdForPanel(commandIdOnPanel)
        if commandControlPanel_:
            objArrayPanel.append(commandControlPanel_)

        commandDefinitionPanel_ = commandDefinitionById(commandIdOnPanel)
        if commandDefinitionPanel_:
            objArrayPanel.append(commandDefinitionPanel_)

        for obj in objArrayQAT:
            destroyObject(ui, obj)

        for obj in objArrayPanel:
            destroyObject(ui, obj)
        ui.messageBox(_('Addin succesfully stopped!'))
    except:
        if ui:
            ui.messageBox(_('AddIn Stop Failed: {}').format(traceback.format_exc()))
