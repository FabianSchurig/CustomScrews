# Author-Fabian Schurig
# Description-

# Simple Add-In imports
import adsk.core, adsk.fusion, adsk.cam, traceback, os, gettext
# math imports
import math
import inspect
import sys

_script_path = os.path.abspath(inspect.getfile(inspect.currentframe()))
_script_dir = os.path.dirname(_script_path)
_module_dir = os.path.abspath(os.path.join(_script_dir, "modules"))
sys.path.append(_module_dir)

from .screw import Screw
import requests
import logging
from pathlib import Path

# global set of event handlers to keep them referenced for the duration of the command
_handlers = []
_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)
_host = 'https://adsk.hk-fs.de'    # "http://localhost"
_command_id = 'createScrewId_blaaa'
_command_name = 'Create Screw'
_command_tooltip = 'Create a cylinderhead screw by manipulating different parameters or select preset values.'
_command_resource_folder = './resources'
_toolbar_id = 'InsertPanel'
_logging_directory = 'CustomScrews'

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

# {name,d=k,dk,s,t,b,bodylength}
# ISO 4762/ DIN912
presets = [{
    "id": 1,
    "name": "M2 x8",
    "body_diameter": 0.2,
    "head_diameter": 0.38,
    "head_height": 0.2,
    "hexagon_diameter": 0.15,
    "hexagon_height": 0.1,
    "thread_length": 0.6,
    "body_length": 0.8
}, {
    "id": 2,
    "name": "M2 x10",
    "body_diameter": 0.2,
    "head_diameter": 0.38,
    "head_height": 0.2,
    "hexagon_diameter": 0.15,
    "hexagon_height": 0.1,
    "thread_length": 0.6,
    "body_length": 1.0
}, {
    "id": 3,
    "name": "M2 x12",
    "body_diameter": 0.2,
    "head_diameter": 0.38,
    "head_height": 0.2,
    "hexagon_diameter": 0.15,
    "hexagon_height": 0.1,
    "thread_length": 0.6,
    "body_length": 1.2
}, {
    "id": 4,
    "name": "M3 x8",
    "body_diameter": 0.3,
    "head_diameter": 0.568,
    "head_height": 0.3,
    "hexagon_diameter": 0.25,
    "hexagon_height": 0.19,
    "thread_length": 0.6,
    "body_length": 0.8
}, {
    "id": 5,
    "name": "M3 x10",
    "body_diameter": 0.3,
    "head_diameter": 0.568,
    "head_height": 0.3,
    "hexagon_diameter": 0.25,
    "hexagon_height": 0.19,
    "thread_length": 0.6,
    "body_length": 1.0
}, {
    "id": 6,
    "name": "M3 x12",
    "body_diameter": 0.3,
    "head_diameter": 0.568,
    "head_height": 0.3,
    "hexagon_diameter": 0.25,
    "hexagon_height": 0.19,
    "thread_length": 0.6,
    "body_length": 1.2
}]
lastPresetId = 0

# global set of event handlers to keep them referenced for the duration of the command
handlers = []
newComp = None
rowNumber = 0
HOST = "https://adsk.hk-fs.de"    # "http://adsk.hk-fs.de" #localhost:5000
isSaved = True
lengthSaved = True
buttonClicked = True
buttonNewClicked = True
screwId = None
lastThreadLength = 0
lastBodyLength = 0
textArea = ""


def addRow(tableInput, inputs, preset):
    global rowNumber
    button = inputs.addBoolValueInput(tableInput.id + '_button{}'.format(rowNumber), '', False,
                                      './resources/B', False)
    # button.isFullWidth = True

    stringInput = inputs.addStringValueInput(tableInput.id + '_stringInput{}'.format(rowNumber), '',
                                             str(preset['name']))
    stringInput.isReadOnly = True

    s = ''
    if 'body_length' in preset.keys() and (preset['body_length']
                                           is not None) and preset['body_length'] != 'null':
        s = str(preset['body_length'] * 10) + " mm"
    else:
        s = 'None'
    bodyLength = inputs.addStringValueInput(tableInput.id + '_bodyLength{}'.format(rowNumber), '',
                                            str(s))
    bodyLength.isReadOnly = True

    row = tableInput.rowCount
    tableInput.addCommandInput(button, row, 0)
    tableInput.addCommandInput(stringInput, row, 1)
    tableInput.addCommandInput(bodyLength, row, 2)

    rowNumber = rowNumber + 1


def getPresetParameters():
    global HOST
    try:
        r = requests.get(HOST + "/user/all/screws/")    # http://adsk.hk-fs.de localhost:5000
        return r.json()
    except:
        return None


def getPresetParametersByUserId(userId):
    # app.currentUser.displayName
    global HOST
    try:
        r = requests.get(HOST + "/user/" + userId +
                         "/screws/")    # http://adsk.hk-fs.de localhost:5000
        return r.json()
    except:
        return None


def registerUser(payload):
    global HOST
    try:
        r = requests.post(HOST + '/users/', json=payload)
        return r.json()
    except:
        return None


def publishScrewByUserId(userId, payload):
    global HOST
    # app.currentUser.displayName
    try:
        r = requests.post(HOST + "/user/" + userId + "/screws/", json=payload)
        return r.json()
    except:
        return None


def putScrewByUserId(userId, screwId, payload):
    global HOST
    # app.currentUser.displayName
    try:
        r = requests.put(HOST + "/user/" + userId + "/screw/" + screwId, json=payload)
        return r.json()
    except:
        return None


def publishScrewLength(screwId, payload):
    global HOST
    # app.currentUser.displayName
    try:
        r = requests.post(HOST + "/screw/" + screwId + "/length/", json=payload)
        return r.json()
    except:
        return None


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


def getLocStrings():
    '''
    Get loc string by language
    '''
    currentDir = os.path.dirname(os.path.realpath(__file__))
    return gettext.translation('resource', currentDir, [getUserLanguage(), "en-US"]).gettext


def destroyObject(uiObj, tobeDeleteObj):
    if uiObj and tobeDeleteObj:
        if tobeDeleteObj.isValid:
            tobeDeleteObj.deleteMe()
        else:
            uiObj.messageBox('tobeDeleteObj is not a valid object')


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    '''
    function InputChangedHandler triggers if sth was changed
    '''

    def __init__(self):
        super().__init__()

    def notify(self, args):
        global screw, isSaved, lengthSaved, screwId, lastThreadLength, lastBodyLength
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
                preset = str(cmdInput.id).replace(tableInput.id + '_button', "")
                # ui.messageBox(preset)
                # s.id,name,body_diameter,head_diameter,head_height,hexagon_diameter,hexagon_height,thread_length,body_length
                # ui.messageBox(str(presets[int(preset)]['id']))
                inputs.itemById('id').value = str(presets[int(preset)]['id'])
                inputs.itemById('screwName').value = presets[int(preset)]['name']    # 1
                inputs.itemById('bodyDiameter').value = presets[int(preset)]['body_diameter']    # 2
                inputs.itemById('headDiameter').value = presets[int(preset)]['head_diameter']    # 3
                inputs.itemById('headHeight').value = presets[int(preset)]['head_height']    # 4
                inputs.itemById('hexagonDiameter').value = presets[int(preset)][
                    'hexagon_diameter']    # 5
                inputs.itemById('hexagonHeight').value = presets[int(preset)][
                    'hexagon_height']    # 6
                if presets[int(preset)]['thread_length'] == None or presets[int(
                        preset)]['body_length'] == None:    # 8
                    inputs.itemById(
                        'threadLength').value = presets[int(preset)]['head_height'] * 5 - 0.2    # 4
                    inputs.itemById(
                        'bodyLength').value = presets[int(preset)]['head_height'] * 5    # 4
                else:
                    inputs.itemById('threadLength').value = presets[int(preset)][
                        'thread_length']    # 7
                    inputs.itemById('bodyLength').value = presets[int(preset)]['body_length']    # 8
                    lastThreadLength = presets[int(preset)]['thread_length']
                    lastBodyLength = presets[int(preset)]['body_length']

                isSaved = True
                lengthSaved = True
                screwId = str(presets[int(preset)]['id'])

            global lastPresetId
            preset = inputs.itemById('dropdownPresets')
            if preset.selectedItem.index > 0 and preset.selectedItem.index <= len(
                    presets) and preset.selectedItem.index != lastPresetId:
                inputs.itemById('bodyDiameter').value = presets[preset.selectedItem.index -
                                                                1]['body_diameter']
                inputs.itemById('headDiameter').value = presets[preset.selectedItem.index -
                                                                1]['head_diameter']
                inputs.itemById('headHeight').value = presets[preset.selectedItem.index -
                                                              1]['head_height']
                inputs.itemById('hexagonDiameter').value = presets[preset.selectedItem.index -
                                                                   1]['hexagon_diameter']
                inputs.itemById('hexagonHeight').value = presets[preset.selectedItem.index -
                                                                 1]['hexagon_height']
                inputs.itemById('threadLength').value = presets[preset.selectedItem.index -
                                                                1]['thread_length']
                inputs.itemById('bodyLength').value = presets[preset.selectedItem.index -
                                                              1]['body_length']
                screwId = presets[preset.selectedItem.index - 1]['id']
                lastThreadLength = presets[preset.selectedItem.index - 1]['thread_length']
                lastBodyLength = presets[preset.selectedItem.index - 1]['body_length']
                # ui.messageBox('input changed '+str(lastPresetId) +' '+str(preset.selectedItem.index)+' '+str(inputs.itemById('bodyDiameter').value))

            point = adsk.core.Point3D.create(0, 0, inputs.itemById('headHeight').value)
            direction = adsk.core.Vector3D.create(0, 0, 1)
            # ui.messageBox(str(inputs.itemById('bodyLength')))
            manipulator = inputs.itemById('bodyLength').setManipulator(point, direction)

            # if cmdInput.id == inputs.itemById('jointSelection').id:
            # ui.messageBox("new selected item")
            # ui.messageBox(str(inputs.itemById('jointSelection').selection(0).entity))

            lastPresetId = preset.selectedItem.index
            # ui.messageBox('asasas '+str(inputs.itemById('bodyDiameter').value))
            args.isValidResult = True

        except Exception as e:
            logging.error(f'InputChangedHandler {e}')


class CommandExecutePreviewHandler(adsk.core.CommandEventHandler):

    def __init__(self):
        super().__init__()

    def notify(self, args):
        global screw, screwId, presets, isSaved, lengthSaved, buttonClicked, buttonNewClicked, lastBodyLength, lastThreadLength, textArea, rowNumber, newComp
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
                elif input.id == 'filletRadius':
                    screw.filletRadius = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'hexagonDiameter':
                    screw.hexagonDiameter = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'hexagonHeight':
                    screw.hexagonHeight = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'chamferDistance':
                    screw.chamferDistance = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'bodyLength':
                    screw.bodyLength = unitsMgr.evaluateExpression(input.expression, "mm")
                    if screw.bodyLength != lastBodyLength:
                        lengthSaved = False
                        lastBodyLength = screw.bodyLength
                elif input.id == 'threadLength':
                    screw.threadLength = unitsMgr.evaluateExpression(input.expression, "mm")
                    if screw.threadLength != lastThreadLength:
                        lengthSaved = False
                        lastThreadLength = screw.threadLength
                elif input.id == 'id':
                    screwId = input.value
                elif input.id == 'buttonNew':
                    if buttonNewClicked != input.value:
                        # ui.messageBox(str(buttonNewClicked))
                        screwId = None
                        inputs.itemById('id').value = ""
                        textArea = "Added new screw. Save the screw when you finished editing."
                        # ui.messageBox(screwId)
                        buttonNewClicked = input.value
                elif input.id == 'buttonSave':
                    # ui.messageBox(str(buttonClicked))
                    # ui.messageBox(str(input.value))
                    # if screwId:
                    #    ui.messageBox(str(screwId))
                    # else:
                    #    ui.messageBox("None")
                    if buttonClicked != input.value:
                        textArea = "Start saving Screw ..."
                        inputs.itemById('textBox').text = textArea
                        registerUser({
                            "userId": app.currentUser.userId,
                            "email": app.currentUser.email,
                            "display_name": app.currentUser.displayName,
                            "name": app.currentUser.userName
                        })
                        if screwId:
                            s = putScrewByUserId(
                                app.currentUser.userId, screwId, {
                                    'name': screw.screwName,
                                    'body_diameter': screw.bodyDiameter,
                                    'head_diameter': screw.headDiameter,
                                    'head_height': screw.headHeight,
                                    'hexagon_diameter': screw.hexagonDiameter,
                                    'hexagon_height': screw.hexagonHeight
                                })
                            if s:
                                textArea = textArea + "\nSaved new Screw."
                                inputs.itemById('textBox').text = textArea
                            else:
                                textArea = textArea + "\nNo connection to Server."
                                inputs.itemById('textBox').text = textArea
                                buttonClicked = input.value
                        else:
                            s = publishScrewByUserId(
                                app.currentUser.userId, {
                                    'name': screw.screwName,
                                    'body_diameter': screw.bodyDiameter,
                                    'head_diameter': screw.headDiameter,
                                    'head_height': screw.headHeight,
                                    'hexagon_diameter': screw.hexagonDiameter,
                                    'hexagon_height': screw.hexagonHeight
                                })
                            if s:
                                inputs.itemById('id').value = str(s['iso_4762']['id'])
                                screwId = str(s['iso_4762']['id'])
                                isSaved = True
                                lengthSaved = False
                                textArea = textArea + "\nSaved new Screw."
                                inputs.itemById('textBox').text = textArea
                            else:
                                textArea = textArea + "\nNo connection to Server."
                                inputs.itemById('textBox').text = textArea
                                buttonClicked = input.value
                        table = inputs.itemById('presetTable')
                        table.clear()
                        rowNumber = 0
                        r = getPresetParametersByUserId(app.currentUser.userId)

                        # ui.messageBox('Get_Request '+str(r['iso_4762']))
                        if r != None:
                            presets = r['iso_4762']
                            textArea = textArea + "\nEdited existing Screw."
                            inputs.itemById('textBox').text = textArea

                        for preset in presets:
                            addRow(table, inputs, preset)

                    # ui.messageBox(str(lengthSaved))
                    # ui.messageBox(str(screwId))
                    # ui.messageBox(str(isSaved))
                    if not lengthSaved and screwId and buttonClicked != input.value:
                        # ui.messageBox("length")
                        textArea = "Save length of Screw ..."
                        inputs.itemById('textBox').text = textArea
                        # ui.messageBox(str(s['iso_4762']['id']))
                        s = publishScrewLength(screwId, {
                            "thread_length": screw.threadLength,
                            "body_length": screw.bodyLength
                        })
                        if s:
                            # add row to table
                            table = inputs.itemById('presetTable')

                            preset = {
                                'id': screwId,
                                'name': screw.screwName,
                                'body_diameter': screw.bodyDiameter,
                                'head_diameter': screw.headDiameter,
                                'head_height': screw.headHeight,
                                'hexagon_diameter': screw.hexagonDiameter,
                                'hexagon_height': screw.hexagonHeight,
                                'thread_length': screw.threadLength,
                                'body_length': screw.bodyLength
                            }
                            presets.append(preset)
                            addRow(table, inputs, preset)
                            textArea = "Added new row for Screw ID: " + str(
                                screwId) + "\nThread Length: " + str(
                                    screw.threadLength) + "\nBody Length: " + str(screw.bodyLength)
                            inputs.itemById('textBox').text = textArea
                            lengthSaved = True

                    buttonClicked = input.value

            screw.sketch()
            inputs.itemById('textBox').text = textArea
            # screw.buildScrew()
            for j in range(0, inputs.itemById('jointSelection').selectionCount):
                joinComp = screw.copy()
                screw.joinScrew(inputs.itemById('jointSelection').selection(j), joinComp)
                j = j + 1
            if inputs.itemById('jointSelection').selectionCount > 0:
                newComp.bRepBodies.item(0).isVisible = False
            eventArgs.isValidResult = True
        except Exception as e:
            logging.error(f'CommandExecutePreviewHandler {e}')


class CommandExecuteHandler(adsk.core.CommandEventHandler):

    def __init__(self):
        super().__init__()

    def notify(self, args):
        global screw
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
                    screw.bodyLength = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'filletRadius':
                    screw.filletRadius = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'threadLength':
                    screw.threadLength = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'hexagonDiameter':
                    screw.hexagonDiameter = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'hexagonHeight':
                    screw.hexagonHeight = unitsMgr.evaluateExpression(input.expression, "mm")
                elif input.id == 'chamferDistance':
                    screw.chamferDistance = unitsMgr.evaluateExpression(input.expression, "mm")

            screw.sketch()
            args.isValidResult = True
            logging.debug(_('command: {} executed successfully').format(eventArgs.command.parentCommandDefinition.id))
        except Exception as e:
            logging.error(f'CommandExecuteHandler {e}')


class CommandCreatedEventHandlerPanel(adsk.core.CommandCreatedEventHandler):

    def __init__(self):
        super().__init__()

    def notify(self, args):
        global textArea
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            logging.info(f"{eventArgs}")
            cmd = eventArgs.command
            cmd.isRepeatable = False
            cmd.helpFile = 'help.html'
            global presets
            global rowNumber
            rowNumber = 0
            logging.info('creating panel')

            fetchedPresets = ""
            textArea = 'Database connection failed! ' + str(
                len(presets)) + ' offline presets loaded'
            # load Presets
            r = getPresetParametersByUserId(app.currentUser.userId)

            # ui.messageBox('Get_Request '+str(r['iso_4762']))
            if r != None:
                presets = r['iso_4762']
                textArea = 'Database connected! Fetched ' + str(len(presets)) + ' online presets'
                # ui.messageBox(str(len(r['iso_4762'])))

            # define the inputs
            inputs = cmd.commandInputs
            inputs.addStringValueInput('screwName', 'Screw Name', defaultCylinderheadScrewName)

            # Create the table, defining the number of columns and their relative widths.
            table = inputs.addTableCommandInput('presetTable', 'Table', 3, '1:4:2')

            # Define some of the table properties.
            table.minimumVisibleRows = 3
            table.maximumVisibleRows = 10
            table.columnSpacing = 10
            table.rowSpacing = 2
            # transparentBackgroundTablePresentationStyle itemBorderTablePresentationStyle nameValueTablePresentationStyle
            table.tablePresentationStyle = adsk.core.TablePresentationStyles.itemBorderTablePresentationStyle
            table.hasGrid = False

            for preset in presets:
                addRow(table, inputs, preset)

            # Create dropdown input with radio style
            dropdownInputPreset = inputs.addDropDownCommandInput(
                'dropdownPresets', 'Presets', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            dropdownItems = dropdownInputPreset.listItems
            dropdownItems.add('Default', True, '')
            for preset in presets:
                dropdownItems.add(str(preset['name']), False, '')
            dropdownInputPreset.isVisible = False

            trInput = inputs.addStringValueInput('id', 'Screw Id', '')
            # trInput.isVisible = False
            trInput.isReadOnly = True

            selectionInput = inputs.addSelectionInput('jointSelection', 'Select Joins',
                                                      'Select origins to join')
            selectionInput.setSelectionLimits(0)
            selectionInput.addSelectionFilter('JointOrigins')
            selectionInput.addSelectionFilter('SketchPoints')
            selectionInput.addSelectionFilter('ConstructionPoints')
            selectionInput.addSelectionFilter('Vertices')
            selectionInput.addSelectionFilter('CircularEdges')

            initBodyLength = adsk.core.ValueInput.createByReal(defaultBodyLength)
            bodyLength = inputs.addDistanceValueCommandInput('bodyLength', 'Body Length',
                                                             initBodyLength)
            point = adsk.core.Point3D.create(0, 0, defaultCylinderheadHeight)
            direction = adsk.core.Vector3D.create(0, 0, 1)
            manipulator = bodyLength.setManipulator(point, direction)

            initThreadLength = adsk.core.ValueInput.createByReal(defaultThreadLength)
            inputs.addValueInput('threadLength', 'Thread Length', 'mm', initThreadLength)

            # Create group input
            groupCmdInput = inputs.addGroupCommandInput('group', 'Advanced')
            groupCmdInput.isExpanded = False
            # groupCmdInput.isEnabledCheckBoxDisplayed = True
            groupChildInputs = groupCmdInput.children

            initHeadDiameter = adsk.core.ValueInput.createByReal(defaultCylinderheadDiameter)
            groupChildInputs.addValueInput('headDiameter', 'Head Diameter', 'mm', initHeadDiameter)

            initBodyDiameter = adsk.core.ValueInput.createByReal(defaultBodyDiameter)
            groupChildInputs.addValueInput('bodyDiameter', 'Body Diameter', 'mm', initBodyDiameter)

            initHeadHeight = adsk.core.ValueInput.createByReal(defaultCylinderheadHeight)
            groupChildInputs.addValueInput('headHeight', 'Head Height', 'mm', initHeadHeight)

            initHexagonDiameter = adsk.core.ValueInput.createByReal(defaultHexagonDiameter)
            groupChildInputs.addValueInput('hexagonDiameter', 'Hexagon Diameter', 'mm',
                                           initHexagonDiameter)

            initHexagonHeight = adsk.core.ValueInput.createByReal(defaultHexagonHeight)
            groupChildInputs.addValueInput('hexagonHeight', 'Hexagon Height', 'mm',
                                           initHexagonHeight)

            initFilletRadius = adsk.core.ValueInput.createByReal(defaultFilletRadius)
            groupChildInputs.addValueInput('filletRadius', 'Fillet Radius', 'mm', initFilletRadius)

            initChamferDistance = adsk.core.ValueInput.createByReal(defaultChamferDistance)
            groupChildInputs.addValueInput('chamferDistance', 'Chamfer Distance', 'mm',
                                           initChamferDistance)

            buttonSave = groupChildInputs.addBoolValueInput('buttonSave', ' Save Current Screw ',
                                                            False, '', True)
            buttonSave.isFullWidth = True

            buttonNew = groupChildInputs.addBoolValueInput('buttonNew', ' Create New Screw ', False,
                                                           '', True)
            buttonNew.isFullWidth = True

            textBox = inputs.addTextBoxCommandInput('textBox', 'Status', fetchedPresets, 5, True)
            textBox.isFullWidth = True

            # Connect all Handlers
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

            logging.debug('Panel command created successfully')
        except Exception as e:
            logging.error(e)


def run(context):
    '''
    run - main function of the Add-in
    '''
    # ui = None
    global screw, app, ui, _logging_directory
    screw = None

    Path.home().joinpath(_logging_directory).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=Path.home().joinpath(_logging_directory).joinpath('custom_screws.log'),
        filemode='w', level=logging.DEBUG)

    app = adsk.core.Application.get()
    ui = app.userInterface

    # global _
    # _ = getLocStrings()

    global presets
    screw = Screw()
    # registerUser({"id": app.currentUser.userId, "email": app.currentUser.email, "display_name": app.currentUser.displayName, "name": app.currentUser.userName})

    # add a command on create panel in modeling workspace
    global _command_id, _command_name, _command_resource_folder, _command_tooltip

    # Add a command that displays the panel.
    show_screw_cmd_def = ui.commandDefinitions.itemById(_command_id)
    if not show_screw_cmd_def:
        show_screw_cmd_def = ui.commandDefinitions.addButtonDefinition(
            _command_id, _command_name, _command_tooltip, _command_resource_folder)
        # show_screw_cmd_def.toolClipFilename = './resources/technical_small.png'
        # Connect to Command Created event.
        on_command_created = CommandCreatedEventHandlerPanel()
        show_screw_cmd_def.commandCreated.add(on_command_created)
        handlers.append(on_command_created)

    # Add the command to the toolbar.
    panel = ui.allToolbarPanels.itemById(_toolbar_id)
    control = panel.controls.itemById(_command_id)
    if not control:
        button_control = panel.controls.addCommand(show_screw_cmd_def)

        button_control.isPromotedByDefault = True
        button_control.isPromoted = True

    # if ui:
    #    ui.messageBox(_('Addin succesfully stopped!'))

    logging.debug(
        'The command "Create Screw" is successfully added to the create panel in modeling workspace {}'
        .format(app.userId + ":" + app.currentUser.displayName))
    # except:
    #     if ui:
    #         ui.messageBox(_('AddIn Start Failed: {}').format(traceback.format_exc()))


'''
Stop function runs when Add-In is stopped or Fusion crashes
'''


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Delete controls and associated command definitions created by this add-ins
        panel = ui.allToolbarPanels.itemById(_toolbar_id)
        cmd = panel.controls.itemById(_command_id)
        if cmd:
            cmd.deleteMe()
        cmd_def = ui.commandDefinitions.itemById(_command_id)
        if cmd_def:
            cmd_def.deleteMe()

        # throws AddIn start failed?
        # if ui:
        #    ui.messageBox(_('Addin succesfully stopped!'))
        logging.info('Addin succesfully stopped!')
    except Exception as e:
        logging.error(f'AddIn Stop Failed: {e}')
