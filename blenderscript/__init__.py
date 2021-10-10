# -*- coding: utf-8 -*-

bl_info = {
    "name": "PRO: MIDI Lights Importer",
    "author": "PROPHESSOR",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "Properties space > Scene tab > PRO: MIDI Lights Importer panel",
    "description": "Import lights from .mid file and create f-curves.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
}

import bpy
from .midi_parser import MidiLightParser

'''
File: [               ]

[  Load  ]
--- if tracks ---

Tracks:
| id name events |
| id name events |
| id name events |
| id name events |
| id name events |

[  Parse  ]
--- if parsed ---

The track uses {} channels.

Light type:
| Simple (1 channel) |
| RGB (3 channels) |
| DRGB (4 channels) |

Import as fcurves for selected light:
[  Import  ]
'''

class PRO_MTL_CFG:
    def __init__(self):
        self.midiReader: MidiLightParser = None
        self.selected_track = False
        self.track_notes = None

    def reset(self):
        self.midiReader = None
        self.selected_track = False
        self.track_notes = None

class PRO_MLI_CONFIG(bpy.types.PropertyGroup):
    # props
    file = bpy.props.StringProperty(default="", subtype='FILE_PATH', description="Select a .json file, then click \"Add\" button below and you'll see a configuration box created.")
    track_id = bpy.props.IntProperty(name='Track ID', default=1, min=0, max=512, description='')
    use_drivers = bpy.props.BoolProperty(name='Use Drivers', default=True, description='Use custom properties and drivers to map variable parameters (such as light energy) instead of hardcoding them')

    config = PRO_MTL_CFG()


class PRO_MLI_LoadFile(bpy.types.Operator):
    bl_idname = 'scene.pro_mli_loadfile'
    bl_label = 'scene.pro_mli_loadfile'

    def execute(self, context):
        config: PRO_MLI_CONFIG = bpy.data.scenes[0].CONFIG_PRO_MLI

        config.config.midiReader = MidiLightParser()

        config.config.midiReader.load(self.getPath(config.file))

        return {'FINISHED'}

    def getPath(self, path):
        if path[0:2] == "//":
            return bpy.path.abspath(path)
        else:
            return path

class PRO_MLI_SelectTrack(bpy.types.Operator):
    bl_idname = 'scene.pro_mli_selecttrack'
    bl_label = 'scene.pro_mli_selecttrack'

    def execute(self, context):
        config: PRO_MLI_CONFIG = bpy.data.scenes[0].CONFIG_PRO_MLI

        config.config.selected_track = True

        config.config.track_notes = config.config.midiReader.getNotesInTrack(config.track_id)

        return {'FINISHED'}


class PRO_MLI_Reset(bpy.types.Operator):
    bl_idname = 'scene.pro_mli_reset'
    bl_label = 'scene.pro_mli_reset'

    def execute(self, context):
        config: PRO_MLI_CONFIG = bpy.data.scenes[0].CONFIG_PRO_MLI

        config.property_unset('file')
        config.property_unset('track_id')
        config.property_unset('use_drivers')
        config.config.selected_track = False
        config.config.midiReader = None
        # config.midiReader = MidiLightParser()

        return {'FINISHED'}

class PRO_MLI_Back(bpy.types.Operator):
    bl_idname = 'scene.pro_mli_back'
    bl_label = 'scene.pro_mli_back'

    def execute(self, context):
        config: PRO_MLI_CONFIG = bpy.data.scenes[0].CONFIG_PRO_MLI

        config.config.selected_track = False

        return {'FINISHED'}

class ActionAccessor:

    @staticmethod
    def create(name):
        return bpy.data.actions.new(name)

    @staticmethod
    def get(name):
        return bpy.data.actions[name]

    @staticmethod
    def exists(name):
        return name in bpy.data.actions

    @classmethod
    def get_or_create(cls, name):

        if cls.exists(name):
            return cls.get(name)
        else:
            return cls.create(name)

class FCurveAccessor:

    @classmethod
    def create(cls, action, path_name, index, *args):

        fcurve = cls.get(action, path_name, index)
        if fcurve == None:
            return action.fcurves.new(path_name, index, *args)
        else:
            action.fcurves.remove(fcurve)
            return fcurve

    @staticmethod
    def get(action, path_name, index):

        for fcurve in action.fcurves:
            if fcurve.data_path == path_name and fcurve.array_index == index:
                return fcurve

        return None

    @classmethod
    def exists(cls, action, path_name, index):
        return not cls.get(action, path_name, index) == None

    @classmethod
    def get_or_create(cls, action, path_name, index, *args):

        fcurve = cls.get(action, path_name, index)
        if fcurve == None:
            if len(args)>0:
                return action.fcurves.new(data_path=path_name, index=index, action_group = args[0])
            else:
                return action.fcurves.new(data_path=path_name, index=index)
        else:
            return fcurve

class ActionFCurveAccessor:

    def __init__(self, anim_obj):
        # assume: anim_obj can be any instance that has animation_data system,
        # including objects, materials, textures, anything that can add animation.
        self.anim_obj = anim_obj

    def create_action(self, name):
        action = ActionAccessor.create(name)
        self.__set_action_to_object(action)
        return action

    def get_or_create_action(self, name):
        action = ActionAccessor.get_or_create(name)
        self.__set_action_to_object(action)
        return action

    def __set_action_to_object(self, action):

        if self.anim_obj.animation_data == None:
            self.anim_obj.animation_data_create()

        if not self.anim_obj.animation_data.action == action:
            self.anim_obj.animation_data.action = action

        return action

    def create_fcurve(self, path_name, index, *args):
        return FCurveAccessor.create(self.anim_obj.animation_data.action, path_name, index, *args)

    def get_or_create_fcurve(self, path_name, index, *args):
        return FCurveAccessor.get_or_create(self.anim_obj.animation_data.action, path_name, index, *args)


class PRO_MLI_Import(bpy.types.Operator):
    bl_idname = 'scene.pro_mli_import'
    bl_label = 'scene.pro_mli_import'

    def execute(self, context):
        config: PRO_MLI_CONFIG = bpy.data.scenes[0].CONFIG_PRO_MLI

        base_note = min(config.config.track_notes)

        dim = config.config.midiReader.parse(config.track_id, base_note)
        red = config.config.midiReader.parse(config.track_id, base_note + 1)
        green = config.config.midiReader.parse(config.track_id, base_note + 2)
        blue = config.config.midiReader.parse(config.track_id, base_note + 3)

        print('dim', len(dim), 'red', len(red), 'green', len(green), 'blue', len(blue))

        activeObject = bpy.context.active_object

        if activeObject.type != 'LIGHT':
            raise Exception('Select a light')

        accessor = ActionFCurveAccessor(activeObject.data)

        action_name = f'Light_{config.track_id}_{base_note}'

        if config.use_drivers:
            accessor.anim_obj['power'] = 1.0
            self.addCurve(accessor, '["power"]', 0, dim, action_name)
        else:
            self.addCurve(accessor, 'energy', 0, dim * 1000, action_name)

        self.addCurve(accessor, 'color', 0, red, action_name)
        self.addCurve(accessor, 'color', 1, green, action_name)
        self.addCurve(accessor, 'color', 2, blue, action_name)

        return {'FINISHED'}

    def addCurve(self, accessor, path, index, points, name):
        accessor.get_or_create_action(name)
        curve = accessor.get_or_create_fcurve(path, index)

        for point in points:
            self.addCurvePoint(curve, point[0], point[1])

    def addCurvePoint(self, curve, frame, value):
        if not curve:
            raise Exception("Curve is not defined")

        curve.keyframe_points.insert(frame, value)


class SCENE_PT_PRO_MLI_Panel(bpy.types.Panel):
    bl_label = "PRO: MIDI Lights Importer"
    bl_context = "scene"
    bl_region_type = "WINDOW"
    bl_space_type = "PROPERTIES"

    def draw(self, context):
        config: PRO_MLI_CONFIG = bpy.data.scenes[0].CONFIG_PRO_MLI
        window = self.layout.column()

        if not config.config.midiReader or not config.config.midiReader.tracks:
            return self.drawFileSection(window, config)

        window.operator("scene.pro_mli_reset", icon="NONE", text="Reset")

        if not config.config.selected_track:
            return self.drawTracksSection(window, config)

        self.drawChannelsSection(window, config)

    def drawFileSection(self, window, config: PRO_MLI_CONFIG):
        window.prop(config, 'file', text='File')

        window.operator("scene.pro_mli_loadfile", icon="NONE", text="Load file")

    def drawTracksSection(self, window, config: PRO_MLI_CONFIG):
        tracksrow = window.row()
        tracksrow.label(text='Tracks:')

        trackslist = window.column()
        for index, track in enumerate(config.config.midiReader.tracks):
            trackslist.label(text=f'{index} - {track.name} ({len(track)} events)')

        window.prop(config, 'track_id', text='Track ID:')

        window.operator("scene.pro_mli_selecttrack", icon="NONE", text="Select track")

    def drawChannelsSection(self, window, config: PRO_MLI_CONFIG):
        notes = config.config.track_notes

        base_note = min(notes)

        channelsrow = window.column()
        channelsrow.label(text=f'The track uses {len(notes)} channels')
        channelsrow.label(text=f'Base note is {base_note}')

        channelsrow.prop(config, 'use_drivers')

        if len(notes) != 4:
            channelsrow.label(text='NOT IMPLEMENTED')
            channelsrow.label(text='Implemented only 4-channels DRGB lights')
        else:
            window.operator("scene.pro_mli_import", icon="NONE", text="Import")

        window.operator("scene.pro_mli_back", icon="NONE", text="Back")

classes = (
    PRO_MLI_LoadFile,
    PRO_MLI_SelectTrack,
    PRO_MLI_Reset,
    PRO_MLI_Import,
    SCENE_PT_PRO_MLI_Panel,
    PRO_MLI_CONFIG
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.CONFIG_PRO_MLI = bpy.props.PointerProperty(type=PRO_MLI_CONFIG)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    if bpy.context.scene.get('CONFIG_PRO_MLI') != None:
        del bpy.context.scene['CONFIG_PRO_MLI']
    try:
        del bpy.types.Scene.CONFIG_PRO_MLI
    except:
        pass

if __name__ == '__main__':
    register()
