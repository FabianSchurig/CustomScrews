import traceback
import adsk.core
import os
import gettext
from ...lib import fusionAddInUtils as futil
from ...lib import presetUtils as presetutils
from ...lib import screwUtils as screwutils
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_createCustomScrewDialog'
CMD_NAME = 'Create Screw'
CMD_Description = 'Create a cylinderhead screw by manipulating different parameters or select preset values.'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'InsertPanel'
COMMAND_BESIDE_ID = ''

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

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
presets = []
screw = None


def addRow(tableInput, inputs, preset):
    global rowNumber
    preset = preset.to_dict()
    button = inputs.addBoolValueInput(tableInput.id + '_button{}'.format(rowNumber), '', False,
                                      os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'B'), False)
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


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED
    control.isPromotedByDefault = IS_PROMOTED

    futil.log(
        'The command "Create Screw" is successfully added to the create panel in modeling workspace {}'
        .format(app.userId + ":" + app.currentUser.displayName))


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    global textArea, screw
    screw = screwutils.Screw()
    try:
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        futil.log(f"{eventArgs}")
        cmd = eventArgs.command
        cmd.isRepeatable = False
        cmd.helpFile = 'help.html'
        global presets
        global rowNumber
        rowNumber = 0
        futil.log('creating panel')

        fetchedPresets = ""
        textArea = 'Database connection failed! ' + str(
            len(presets)) + ' offline presets loaded'
        # load Presets
        preset_manager = presetutils.PresetManagerBuilder().get_managers()[0]
        r = preset_manager.presets
        #r = getPresetParametersByUserId(app.currentUser.userId)

        # ui.messageBox('Get_Request '+str(r['iso_4762']))
        if r != None:
            presets = r
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
            dropdownItems.add(str(preset.to_dict()['name']), False, '')
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

        futil.log('Panel command created successfully')
    except Exception as e:
        futil.log(str(e), adsk.core.LogLevels.ErrorLogLevel)

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

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
        futil.log(_('command: {} executed successfully').format(eventArgs.command.parentCommandDefinition.id))
    except Exception as e:
        futil.log(f'CommandExecuteHandler {e}')


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    global screw, screwId, presets, isSaved, lengthSaved, buttonClicked, buttonNewClicked, lastBodyLength, lastThreadLength, textArea, rowNumber, newComp
    try:
        unitsMgr = app.activeProduct.unitsManager
        inputs = args.command.commandInputs

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
                if buttonClicked != input.value:
                    handle_button_save(inputs, screw, screwId, lengthSaved)
                    buttonClicked = input.value

        screw.sketch()
        futil.log(f'Screw sketch called')
        inputs.itemById('textBox').text = textArea
        # screw.buildScrew()
        for j in range(0, inputs.itemById('jointSelection').selectionCount):
            joinComp = screw.copy()
            screw.joinScrew(inputs.itemById('jointSelection').selection(j), joinComp)
            j = j + 1
        if inputs.itemById('jointSelection').selectionCount > 0:
            newComp.bRepBodies.item(0).isVisible = False
        args.isValidResult = True
    except Exception as e:
        import traceback
        futil.log(f'CommandExecutePreviewHandler {e}\n{traceback.format_exc()}')


def handle_button_save(inputs, screw, screwId, lengthSaved):

    textArea = "Start saving Screw ..."
    inputs.itemById('textBox').text = textArea

    preset_manager = presetutils.PresetManagerBuilder().get_managers()[0]

    if screwId:
        preset = preset_manager.get_preset_by_id(screwId)
        if preset:
            preset_manager.update_preset(
                screwId,
                name=screw.screwName,
                body_diameter=screw.bodyDiameter,
                head_diameter=screw.headDiameter,
                head_height=screw.headHeight,
                hexagon_diameter=screw.hexagonDiameter,
                hexagon_height=screw.hexagonHeight
            )
            textArea = textArea + "\nSaved existing Screw."
            inputs.itemById('textBox').text = textArea
        else:
            textArea = textArea + "\nPreset not found."
            inputs.itemById('textBox').text = textArea
    else:
        new_preset = presetutils.Preset(
            name=screw.screwName,
            body_diameter=screw.bodyDiameter,
            head_diameter=screw.headDiameter,
            head_height=screw.headHeight,
            hexagon_diameter=screw.hexagonDiameter,
            hexagon_height=screw.hexagonHeight
        )
        preset_manager.add_preset(new_preset)
        inputs.itemById('id').value = new_preset.id
        screwId = new_preset.id
        isSaved = True
        lengthSaved = False
        textArea = textArea + "\nSaved new Screw."
        inputs.itemById('textBox').text = textArea

    table = inputs.itemById('presetTable')
    table.clear()
    rowNumber = 0
    presets = preset_manager.presets

    for preset in presets:
        addRow(table, inputs, preset)

    if not lengthSaved and screwId:
        textArea = "Save length of Screw ..."
        inputs.itemById('textBox').text = textArea

        preset_manager.update_preset(
            screwId,
            thread_length=screw.threadLength,
            body_length=screw.bodyLength
        )

        table = inputs.itemById('presetTable')
        preset = preset_manager.get_preset_by_id(screwId)
        addRow(table, inputs, preset)
        textArea = "Added new row for Screw ID: " + str(
            screwId) + "\nThread Length: " + str(
                screw.threadLength) + "\nBody Length: " + str(screw.bodyLength)
        inputs.itemById('textBox').text = textArea
        lengthSaved = True

# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs
    global screw, isSaved, lengthSaved, screwId, lastThreadLength, lastBodyLength
    try:
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        changedInput = eventArgs.input

        unitsMgr = app.activeProduct.unitsManager
        command = args.firingEvent.sender
        cmdInput = args.input
        inputs = eventArgs.firingEvent.sender.commandInputs
        defaultUnits = unitsMgr.defaultLengthUnits

        futil.log(f'Input changed: {changedInput.id}')

        tableInput = inputs.itemById('presetTable')
        if tableInput.id + '_button' in cmdInput.id:
            preset = str(cmdInput.id).replace(tableInput.id + '_button', "")
            futil.log(f'Preset button clicked: {preset}')
            futil.log(f'Preset: {presets[int(preset)]}')

            preset_obj = presets[int(preset)]
            inputs.itemById('id').value = str(preset_obj.id)
            inputs.itemById('screwName').value = preset_obj.name
            inputs.itemById('bodyDiameter').value = preset_obj.parameters['body_diameter']
            inputs.itemById('headDiameter').value = preset_obj.parameters['head_diameter']
            inputs.itemById('headHeight').value = preset_obj.parameters['head_height']
            inputs.itemById('hexagonDiameter').value = preset_obj.parameters['hexagon_diameter']
            inputs.itemById('hexagonHeight').value = preset_obj.parameters['hexagon_height']
            if preset_obj.parameters['thread_length'] is None or preset_obj.parameters['body_length'] is None:
                inputs.itemById('threadLength').value = preset_obj.parameters['head_height'] * 5 - 0.2
                inputs.itemById('bodyLength').value = preset_obj.parameters['head_height'] * 5
            else:
                inputs.itemById('threadLength').value = preset_obj.parameters['thread_length']
                inputs.itemById('bodyLength').value = preset_obj.parameters['body_length']
                lastThreadLength = preset_obj.parameters['thread_length']
                lastBodyLength = preset_obj.parameters['body_length']

            isSaved = True
            lengthSaved = True
            screwId = str(preset_obj.id)

        global lastPresetId
        preset = inputs.itemById('dropdownPresets')
        if preset.selectedItem.index > 0 and preset.selectedItem.index <= len(presets) and preset.selectedItem.index != lastPresetId:
            futil.log(f'Preset dropdown changed: {preset.selectedItem.index}')
            preset_dict = presets[preset.selectedItem.index - 1].to_dict()
            inputs.itemById('bodyDiameter').value = preset_dict['body_diameter']
            inputs.itemById('headDiameter').value = preset_dict['head_diameter']
            inputs.itemById('headHeight').value = preset_dict['head_height']
            inputs.itemById('hexagonDiameter').value = preset_dict['hexagon_diameter']
            inputs.itemById('hexagonHeight').value = preset_dict['hexagon_height']
            inputs.itemById('threadLength').value = preset_dict['thread_length']
            inputs.itemById('bodyLength').value = preset_dict['body_length']
            screwId = presets[preset.selectedItem.index - 1]['id']
            lastThreadLength = presets[preset.selectedItem.index - 1]['thread_length']
            lastBodyLength = presets[preset.selectedItem.index - 1]['body_length']

        point = adsk.core.Point3D.create(0, 0, inputs.itemById('headHeight').value)
        direction = adsk.core.Vector3D.create(0, 0, 1)
        manipulator = inputs.itemById('bodyLength').setManipulator(point, direction)

        lastPresetId = preset.selectedItem.index
        args.isValidResult = True

    except Exception as e:
        futil.log(f'InputChangedHandler {e}\n{traceback.format_exc()}')

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    # inputs = args.inputs
    
    # # Verify the validity of the input values. This controls if the OK button is enabled or not.
    # valueInput = inputs.itemById('value_input')
    # if valueInput.value >= 0:
    #     args.areInputsValid = True
    # else:
    #     args.areInputsValid = False
    args.areInputsValid = True
        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []
