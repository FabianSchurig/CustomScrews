import os
import json
import unittest
from ....lib.presetUtils.preset_utils import Preset, PresetManagerBuilder, PresetManager

class TestPresetManagerBuilder(unittest.TestCase):

    def setUp(self):
        self.test_config_file = 'test_config.json'
        self.test_file_path = 'test_presets.json'
        with open(self.test_config_file, 'w') as file:
            json.dump({"file_paths": []}, file)

    def tearDown(self):
        preset_utils_path = os.path.abspath(os.path.join(__file__, '../../../lib/presetUtils'))
        resources_path = os.path.join(preset_utils_path, 'resources')
        
        test_config_full_path = os.path.join(resources_path, self.test_config_file)
        test_file_full_path = os.path.join(resources_path, self.test_file_path)
        
        if os.path.exists(test_config_full_path):
            os.remove(test_config_full_path)
        if os.path.exists(test_file_full_path):
            os.remove(test_file_full_path)
    
    def test_build_managers_with_none_config(self):
        builder = PresetManagerBuilder()
        # It is the default manager which is initialized with the default config file
        self.assertEqual(len(builder.managers), 1)
        self.assertIsInstance(builder.managers[0], PresetManager)
        self.assertEqual(os.path.basename(builder.config_file), 'config.json')
        self.assertEqual(os.path.basename(builder.managers[0].file_path), 'iso_4762.json')
        # Check the first preset in the default manager
        preset = builder.managers[0].presets[0]
        self.assertEqual(preset.name, "M  1.4")
        self.assertEqual(preset.parameters["body_diameter"], 0.14)
        self.assertEqual(preset.parameters["body_length"], 0.2)
        self.assertEqual(preset.parameters["head_diameter"], 0.26)
        self.assertEqual(preset.parameters["head_height"], 0.14)
        self.assertEqual(preset.parameters["hexagon_diameter"], 0.13)
        self.assertEqual(preset.parameters["hexagon_height"], 0.07)
        self.assertEqual(preset.parameters["thread_length"], 0.1)
        self.assertEqual(preset.id, 1)



    def test_build_managers_with_empty_config(self):
        builder = PresetManagerBuilder(self.test_config_file)
        managers = builder.get_managers()
        self.assertEqual(len(managers), 0)

    def test_add_manager_creates_file_and_updates_config(self):
        builder = PresetManagerBuilder(self.test_config_file)
        manager = builder.add_manager(self.test_file_path)
        
        self.assertTrue(os.path.exists(self.test_file_path))
        self.assertIsInstance(manager, PresetManager)
        
        with open(self.test_config_file, 'r') as file:
            config = json.load(file)
            self.assertIn(self.test_file_path, config['file_paths'])

    def test_get_managers_returns_correct_managers(self):
        builder = PresetManagerBuilder(self.test_config_file)
        builder.add_manager(self.test_file_path)
        managers = builder.get_managers()
        
        self.assertEqual(len(managers), 1)
        self.assertIsInstance(managers[0], PresetManager)
        self.assertEqual(os.path.basename(managers[0].file_path), os.path.basename(self.test_file_path))
        # Check that the file_path has resources subfolder in it
        self.assertIn('resources', managers[0].file_path)


class TestPreset(unittest.TestCase):

    def test_preset_initialization(self):
        preset = Preset(name="Test Preset", param1="value1", param2="value2")
        self.assertEqual(preset.name, "Test Preset")
        self.assertIn("param1", preset.parameters)
        self.assertIn("param2", preset.parameters)
        self.assertEqual(preset.parameters["param1"], "value1")
        self.assertEqual(preset.parameters["param2"], "value2")
        self.assertIsNotNone(preset.id)

    def test_preset_to_dict(self):
        preset = Preset(name="Test Preset", param1="value1", param2="value2")
        preset_dict = preset.to_dict()
        self.assertEqual(preset_dict["name"], "Test Preset")
        self.assertEqual(preset_dict["param1"], "value1")
        self.assertEqual(preset_dict["param2"], "value2")
        self.assertEqual(preset_dict["id"], preset.id)


class TestPresetManager(unittest.TestCase):
    def setUp(self):
        self.test_file_path = 'test_presets.json'
        with open(self.test_file_path, 'w') as file:
            json.dump([], file)

    def tearDown(self):
        preset_utils_path = os.path.abspath(os.path.join(__file__, '../../../../lib/presetUtils'))
        resources_path = os.path.join(preset_utils_path, 'resources')
        test_file_full_path = os.path.join(resources_path, self.test_file_path)
        if os.path.exists(test_file_full_path):
            os.remove(test_file_full_path)

    def test_load_presets_returns_empty_list_for_non_existing_file(self):
        manager = PresetManager(self.test_file_path)
        self.assertEqual(manager.presets, [])

    def test_add_preset(self):
        manager = PresetManager(self.test_file_path)
        preset = Preset(name="Test Preset", param1="value1", param2="value2")
        manager.add_preset(preset)
        self.assertEqual(len(manager.presets), 1)
        self.assertEqual(manager.presets[0].name, "Test Preset")

    def test_get_preset_by_id(self):
        manager = PresetManager(self.test_file_path)
        preset = Preset(name="Test Preset", param1="value1", param2="value2")
        manager.add_preset(preset)
        id = manager.presets[0].id
        found_preset = manager.get_preset_by_id(id)
        self.assertEqual(found_preset.name, "Test Preset")

    def test_update_preset(self):
        manager = PresetManager(self.test_file_path)
        preset = Preset(name="Test Preset", param1="value1", param2="value2")
        manager.add_preset(preset)
        id = manager.presets[0].id
        updated_preset = manager.update_preset(id, name="Updated Preset", param1="updated_value1")
        self.assertEqual(updated_preset.name, "Updated Preset")
        self.assertEqual(updated_preset.parameters["param1"], "updated_value1")

    def test_delete_preset(self):
        manager = PresetManager(self.test_file_path)
        preset = Preset(name="Test Preset", param1="value1", param2="value2")
        manager.add_preset(preset)
        id = manager.presets[0].id
        manager.delete_preset(id)
        self.assertEqual(len(manager.presets), 0)

if __name__ == '__main__':
    unittest.main()