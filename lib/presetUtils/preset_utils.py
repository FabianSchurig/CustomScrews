import json
import os
import uuid

class Preset:
    def __init__(self, name, id=None, **kwargs):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.parameters = kwargs

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            **self.parameters
        }
            

class PresetManager:
    def __init__(self, file_path):
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.path.dirname(__file__), 'resources', file_path)
        self.file_path = file_path
        self.presets = self.load_presets()

    def load_presets(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                return [Preset(**preset) for preset in json.load(file)]
        return []

    def save_presets(self):
        with open(self.file_path, 'w') as file:
            json.dump([preset.to_dict() for preset in self.presets], file, indent=4)

    def add_preset(self, preset):
        self.presets.append(preset)
        self.save_presets()

    def get_preset_by_id(self, id):
        for preset in self.presets:
            if preset.id == id:
                return preset
        return None

    def update_preset(self, id, **kwargs):
        preset = self.get_preset_by_id(id)
        if preset:
            preset.name = kwargs.get('name', preset.name)
            preset.parameters.update(kwargs)
            self.save_presets()
            return preset
        return None

    def delete_preset(self, id):
        self.presets = [preset for preset in self.presets if preset.id != id]
        self.save_presets()

class PresetManagerBuilder:
    def __init__(self, config_file=None):   
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.config_file = config_file  
        self.managers = self.build_managers()

    def build_managers(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                config = json.load(file)
                return [PresetManager(file_path) for file_path in config.get('file_paths', [])]
        return []
    
    def add_manager(self, file_path):
        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                json.dump([], file)
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r+') as file:
                config = json.load(file)
                if 'file_paths' not in config:
                    config['file_paths'] = []
                if file_path not in config['file_paths']:
                    config['file_paths'].append(file_path)
                    file.seek(0)
                    json.dump(config, file, indent=4)
                    file.truncate()
        manager = PresetManager(file_path)
        self.managers.append(manager)
        return manager

    def get_managers(self):
        return self.managers

# # Example usage
# if __name__ == "__main__":
#     manager = PresetManager('presets.json')

#     # Add a new preset
#     new_preset = Preset(1, "M2 x8", body_diameter=0.2, head_diameter=0.38, head_height=0.2, hexagon_diameter=0.15, hexagon_height=0.1, thread_length=0.6, body_length=0.8)
#     manager.add_preset(new_preset)

#     # Get a preset by ID
#     preset = manager.get_preset_by_id(1)
#     if preset:
#         print(preset.to_dict())

#     # Update a preset
#     updated_preset = manager.update_preset(1, name="M2 x10", body_length=1.0)
#     if updated_preset:
#         print(updated_preset.to_dict())

#     # Delete a preset
#     manager.delete_preset(1)