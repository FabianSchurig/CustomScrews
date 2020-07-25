import adsk.core, adsk.fusion, adsk.cam, traceback, os, gettext
# math imports
import math
import inspect
import sys

_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)


def createNewComponent():
    '''
    function createNewComponent
    This function gets the current design of the user and creates a new component in it.
    returns a new component in the current design
    '''
    global _app, _ui
    # Get the active design.
    _app = adsk.core.Application.get()
    _ui = _app.userInterface
    product = _app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component


class Screw:
    '''
    class Screw
    '''

    def __init__(self):
        '''
        define default parameters to initialize the screw
        0.1 = 1mm
        '''
        global _app, _ui
        defaultCylinderheadScrewName = 'Screw'
        defaultCylinderheadDiameter = 0.55    # dk
        defaultCylinderheadHeight = 0.3    # k
        defaultHexagonDiameter = 0.25    # s
        defaultHexagonHeight = 0.19    # t
        defaultThreadLength = 0.8    # b
        defaultBodyLength = 1.0    # bodylength
        defaultBodyDiameter = 0.25    # d
        defaultFilletRadius = 0.025    # f
        defaultChamferDistance = 0.025    # c-

        self._id = None
        self._isSaved = True
        self._lengthSaved = False
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
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

    #properties
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def isSaved(self):
        return self._isSaved

    @isSaved.setter
    def isSaved(self, value):
        self._isSaved = value

    @property
    def lengthSaved(self):
        return self._lengthSaved

    @isSaved.setter
    def lengthSaved(self, value):
        self._lengthSaved = value

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
        sketch.sketchCurves.sketchCircles.addByCenterRadius(center, self.headDiameter / 2)

        extrudes = newComp.features.extrudeFeatures
        prof = sketch.profiles[0]
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        distance = adsk.core.ValueInput.createByReal(self.headHeight)
        extInput.setDistanceExtent(False, distance)
        headExt = extrudes.add(extInput)

        endFaceOfExtrude = headExt.endFaces.item(0)

        # Create the joint geometry
        jointGeometry = adsk.fusion.JointGeometry.createByPlanarFace(
            endFaceOfExtrude, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)

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
        hexagonOuterDiameter = self.hexagonDiameter / math.sqrt(3)
        for i in range(0, 6):
            vertex = adsk.core.Point3D.create(
                center.x + (hexagonOuterDiameter) * math.cos(math.pi * i / 3),
                center.y + (hexagonOuterDiameter) * math.sin(math.pi * i / 3), 0)
            vertices.append(vertex)

        for i in range(0, 6):
            sketchHex.sketchCurves.sketchLines.addByTwoPoints(vertices[(i + 1) % 6], vertices[i])

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
        bodySketch.sketchCurves.sketchCircles.addByCenterRadius(center, self.bodyDiameter / 2)

        bodyProf = bodySketch.profiles[0]
        bodyExtInput = extrudes.createInput(bodyProf,
                                            adsk.fusion.FeatureOperations.JoinFeatureOperation)

        bodyExtInput.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
        bodyExtInput.setDistanceExtent(False, self.bodyLength)
        bodyExt = extrudes.add(bodyExtInput)

        # create chamfer
        edgeCol = adsk.core.ObjectCollection.create()
        edges = bodyExt.endFaces[0].edges
        for edgeI in edges:
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
                if (len(edgeLoop.edges) == 1):
                    edgeCol.add(edgeLoop.edges[0])
                    break

        #edgeCol.add(headExt.faces[0].loops[0].edges[0])
        #edgeCol.add(headExt.faces[0].loops[1].edges[0])
        #edgeCol.add(headExt.endFaces[0].loops[0].edges[0])

        if self.filletRadius > 0:
            filletFeats = newComp.features.filletFeatures
            filletInput = filletFeats.createInput()
            filletInput.addConstantRadiusEdgeSet(
                edgeCol, adsk.core.ValueInput.createByReal(self.filletRadius), True)
            filletFeats.add(filletInput)

        #create thread
        sideFace = bodyExt.sideFaces[0]
        threads = newComp.features.threadFeatures
        threadDataQuery = threads.threadDataQuery
        defaultThreadType = threadDataQuery.defaultMetricThreadType
        recommendData = threadDataQuery.recommendThreadData(self.bodyDiameter, False,
                                                            defaultThreadType)
        if recommendData[0]:
            threadInfo = threads.createThreadInfo(False, defaultThreadType, recommendData[1],
                                                  recommendData[2])
            faces = adsk.core.ObjectCollection.create()
            faces.add(sideFace)
            threadInput = threads.createInput(faces, threadInfo)
            threadInput.isFullLength = False
            threadInput.threadLength = adsk.core.ValueInput.createByReal(self.threadLength)
            threads.add(threadInput)

    def joinScrew(self, jointOrigin, joinComp):
        product = _app.activeProduct
        design = adsk.fusion.Design.cast(product)

        rootComp = design.rootComponent

        #Get the occurrence of the new component
        #occ = rootComp.occurrences.item(0)

        jointOrigins_ = joinComp.jointOrgins
        jointOriginInput = jointOrigins_[0]

        joints = rootComp.joints
        entity = jointOrigin.entity
        #ui.messageBox(str(jointOrigin.entity.objectType))
        if (jointOrigin.entity.objectType == adsk.fusion.SketchPoint.classType() or
                jointOrigin.entity.objectType == adsk.fusion.ConstructionPoint.classType() or
                jointOrigin.entity.objectType == adsk.fusion.BRepVertex.classType()):
            #ui.messageBox(str(jointOrigin.entity.objectType))
            entity = adsk.fusion.JointGeometry.createByPoint(jointOrigin.entity)
        if (jointOrigin.entity.objectType == adsk.fusion.JointOrigin.classType()):
            entity = jointOrigin.entity
        if (jointOrigin.entity.objectType == adsk.fusion.BRepEdge.classType()):
            entity = adsk.fusion.JointGeometry.createByCurve(
                jointOrigin.entity, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        #adsk.fusion.BRepBody.classType()
        jointInput = joints.createInput(jointOriginInput, entity)

        # Set the joint input
        # Set the joint input
        angle = adsk.core.ValueInput.createByString('0 deg')
        jointInput.angle = angle
        offset = adsk.core.ValueInput.createByString('0 cm')
        jointInput.offset = offset
        if (jointOrigin.entity.objectType == adsk.fusion.BRepEdge.classType()):
            jointInput.isFlipped = False
        else:
            jointInput.isFlipped = True
        jointInput.setAsRigidJointMotion()

        #Create the joint
        joint = joints.add(jointInput)

    def copy(self):
        global newComp, _app
        product = _app.activeProduct
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
            if face.centroid.z == 0:    # self.headHeight
                #ui.messageBox('yeyy '+str(i)+'lol '+str(self.headHeight))
                break
            i = i + 1
        face = b.faces.item(i)

        # Create the joint geometry
        jointGeometry = adsk.fusion.JointGeometry.createByPlanarFace(
            face, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)

        # Create the JointOriginInput
        jointOrigins_ = tmpComp.jointOrgins
        jointOriginInput = jointOrigins_.createInput(jointGeometry)

        # Create the JointOrigin
        jointOrigins_.add(jointOriginInput)
        return tmpComp

    def sketch(self):
        global textArea, isValid
        isValid = True
        errStr = ""
        if self.bodyDiameter / 2 < self.chamferDistance or self.chamferDistance <= 0:
            isValid = False
            errStr += "chamfer distance \n"
        if self.filletRadius < 0 or self.filletRadius >= (self.headDiameter -
                                                          self.bodyDiameter) / 4:
            isValid = False
            errStr += "fillet radius \n"
        if self.hexagonHeight >= self.headHeight:
            isValid = False
            errStr += "hexagon height \n"
        if self.bodyDiameter >= self.headDiameter:
            isValid = False
            errStr += "body diameter \n"
        if self.hexagonDiameter * 2 / math.sqrt(3) >= self.headDiameter:
            isValid = False
            errStr += "hexagon diameter \n"
        if self.threadLength > (self.bodyLength - self.chamferDistance -
                                self.filletRadius) or self.threadLength <= 0:
            isValid = False
            errStr += "thread length \n"
        if self.headDiameter < (self.bodyDiameter + 4 * self.filletRadius) or math.isclose(
                self.headDiameter,
            (self.bodyDiameter + 4 * self.filletRadius), rel_tol=1e-09, abs_tol=0.0):
            isValid = False
            errStr += "head diameter \n"
        if not isValid:
            textArea = 'wrong input values \n' + errStr
            #args.command.commandInputs.itemById('textBox').text = 'wrong input values \n'+errStr
            #ui.messageBox('wrong input values \n'+errStr,'Component Failed')
            return

        global newComp
        newComp = createNewComponent()
        if newComp is None:
            textArea = 'New component failed to create'
            #ui.messageBox('New component failed to create', 'New Component Failed')
            return

        # Create a new sketch.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        xzPlane = newComp.xZConstructionPlane
        sketch = sketches.add(xzPlane)
        center = adsk.core.Point3D.create(0, 0, 0)
        axisLine = sketch.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0),
                                                                  adsk.core.Point3D.create(0, 1, 0))

        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(0, -self.bodyLength, 0))
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(0, -self.bodyLength, 0),
            adsk.core.Point3D.create(self.bodyDiameter / 2 - self.chamferDistance, -self.bodyLength,
                                     0))
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(self.bodyDiameter / 2 - self.chamferDistance, -self.bodyLength,
                                     0),
            adsk.core.Point3D.create(self.bodyDiameter / 2, -self.bodyLength + self.chamferDistance,
                                     0))
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(self.bodyDiameter / 2, -self.bodyLength + self.chamferDistance,
                                     0), adsk.core.Point3D.create(self.bodyDiameter / 2, 0, 0))
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(self.bodyDiameter / 2, 0, 0),
            adsk.core.Point3D.create(self.headDiameter / 2, 0, 0))
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(self.headDiameter / 2, 0, 0),
            adsk.core.Point3D.create(self.headDiameter / 2, self.headHeight, 0))

        x = (self.hexagonDiameter / math.cos(math.radians(30)) - self.hexagonDiameter) / 2

        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(self.headDiameter / 2, self.headHeight, 0),
            adsk.core.Point3D.create(self.hexagonDiameter / 2 + x, self.headHeight, 0))
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(self.hexagonDiameter / 2 + x, self.headHeight, 0),
            adsk.core.Point3D.create(self.hexagonDiameter / 2, self.headHeight - x, 0))

        #Ankathete * tan(a) = Gegenkathete
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(self.hexagonDiameter / 2, self.headHeight - x, 0),
            adsk.core.Point3D.create(self.hexagonDiameter / 2, self.headHeight - self.hexagonHeight,
                                     0))
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(self.hexagonDiameter / 2, self.headHeight - self.hexagonHeight,
                                     0),
            adsk.core.Point3D.create(0, (self.headHeight - self.hexagonHeight + x) -
                                     (self.hexagonDiameter / 2) * math.tan(math.radians(31)), 0))
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(0, (self.headHeight - self.hexagonHeight + x) -
                                     (self.hexagonDiameter / 2) * math.tan(math.radians(31)), 0),
            adsk.core.Point3D.create(0, 0, 0))

        revolveProfile = sketch.profiles.item(0)
        revolves = newComp.features.revolveFeatures
        revInput = revolves.createInput(revolveProfile, axisLine,
                                        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        angle = adsk.core.ValueInput.createByReal(math.pi * 2)
        revInput.setAngleExtent(False, angle)

        extRevolve = revolves.add(revInput)

        # Get construction planes
        planes = newComp.constructionPlanes

        # Create construction plane input
        planeInput = planes.createInput()

        # Add construction plane by offset
        offsetValue = adsk.core.ValueInput.createByReal(-self.headHeight)
        planeInput.setByOffset(xyPlane, offsetValue)
        planeOne = planes.add(planeInput)

        #cut the hexagon
        sketchHex = sketches.add(planeOne)
        vertices = []
        hexagonOuterDiameter = self.hexagonDiameter / math.sqrt(3)
        for i in range(0, 6):
            vertex = adsk.core.Point3D.create(
                center.x + (hexagonOuterDiameter) * math.cos(math.pi * i / 3),
                center.y + (hexagonOuterDiameter) * math.sin(math.pi * i / 3), 0)
            vertices.append(vertex)

        for i in range(0, 6):
            sketchHex.sketchCurves.sketchLines.addByTwoPoints(vertices[(i + 1) % 6], vertices[i])

        extrudes = newComp.features.extrudeFeatures
        prof = sketchHex.profiles[0]
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)

        distance = adsk.core.ValueInput.createByReal(self.hexagonHeight)
        extInput.setDistanceExtent(False, distance)
        hexExt = extrudes.add(extInput)

        fc = hexExt.faces[0]
        bd = fc.body
        bd.name = self.screwName

        edgeCol = adsk.core.ObjectCollection.create()
        facesLoop = extRevolve.faces
        for face in facesLoop:
            loops = face.loops
            edgeLoop = None
            for edgeLoop in loops:
                if (len(edgeLoop.edges) == 1 and
                    (edgeLoop.boundingBox.maxPoint.z == -self.headHeight or
                     edgeLoop.boundingBox.maxPoint.z == 0.0)):
                    edgeCol.add(edgeLoop.edges[0])
                    #ui.messageBox(str(edgeLoop.boundingBox.maxPoint.z))
                    break
        #ui.messageBox(str(len(edgeCol)))

        if self.filletRadius > 0:
            filletFeats = newComp.features.filletFeatures
            filletInput = filletFeats.createInput()
            filletInput.addConstantRadiusEdgeSet(
                edgeCol, adsk.core.ValueInput.createByReal(self.filletRadius), True)
            filletFeats.add(filletInput)

        body = extRevolve

        cntFaces = 0
        #a = ""
        for sF in body.faces:
            #a += str(sF.boundingBox.maxPoint.z) + " " + str(sF.boundingBox.minPoint.z) + " math " + str(math.isclose(sF.boundingBox.maxPoint.z,self.bodyLength - self.chamferDistance, abs_tol=1e-09)) +  "cnt: " + str(cntFaces) + "\n"
            #ui.messageBox(str(sF.boundingBox.maxPoint.z)+ ' a ' +str(sF.boundingBox.minPoint.z) + ' a ' + str(cntFaces))
            if math.isclose(
                    sF.boundingBox.maxPoint.z, self.bodyLength - self.chamferDistance,
                    abs_tol=1e-09) and not math.isclose(sF.boundingBox.minPoint.z, self.bodyLength):
                #ui.messageBox(str(sF.boundingBox.maxPoint.z)+ ' a ' +str(sF.boundingBox.minPoint.z) + ' a ' + str(cntFaces))
                break
            cntFaces = cntFaces + 1
        #ui.messageBox(a,"Output Faces")

        #create thread
        sideFace = body.faces.item(cntFaces)
        #ui.messageBox(str(sideFace.boundingBox.maxPoint.z)+ ' a ' +str(sideFace.boundingBox.minPoint.z))

        threads = newComp.features.threadFeatures
        threadDataQuery = threads.threadDataQuery
        defaultThreadType = threadDataQuery.defaultMetricThreadType
        recommendData = threadDataQuery.recommendThreadData(self.bodyDiameter, False,
                                                            defaultThreadType)
        if recommendData[0]:
            threadInfo = threads.createThreadInfo(False, defaultThreadType, recommendData[1],
                                                  recommendData[2])
            faces = adsk.core.ObjectCollection.create()
            faces.add(sideFace)
            threadInput = threads.createInput(faces, threadInfo)
            threadInput.isFullLength = False
            threadInput.threadLength = adsk.core.ValueInput.createByReal(self.threadLength)
            threads.add(threadInput)

        return