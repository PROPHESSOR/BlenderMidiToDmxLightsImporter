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
    file = bpy.props.StringProperty(default="/home/prophessor/tmp/reaperlightsmiditoblender/In The End6.mid", subtype='FILE_PATH', description="Select a .json file, then click \"Add\" button below and you'll see a configuration box created.")
    track_id = bpy.props.IntProperty(name='Track ID', default=1, min=0, max=512, description='')

    config = PRO_MTL_CFG()


class PRO_MLI_LoadFile(bpy.types.Operator):
    bl_idname = 'scene.pro_mli_loadfile'
    bl_label = 'scene.pro_mli_loadfile'

    def execute(self, context):
        config: PRO_MLI_CONFIG = bpy.data.scenes[0].CONFIG_PRO_MLI

        config.config.midiReader = MidiLightParser()

        config.config.midiReader.load(config.file)

        return {'FINISHED'}

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
        config.config.selected_track = False
        config.config.midiReader = None
        # config.midiReader = MidiLightParser()

        return {'FINISHED'}

class PRO_MLI_Import(bpy.types.Operator):
    bl_idname = 'scene.pro_mli_import'
    bl_label = 'scene.pro_mli_import'

    def execute(self, context):
        return {'FINISHED'}

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
        print('Notes', notes)
        if not notes: return
        base_note = min(notes)

        channelsrow = window.column()
        channelsrow.label(text=f'The track uses {len(notes)} channels')
        channelsrow.label(text=f'Base note is {base_note}')

        if len(notes) != 4:
            channelsrow.label(text='NOT IMPLEMENTED')
            channelsrow.label(text='Implemented only 4-channels DRGB lights')
        else:
            window.operator("scene.pro_mli_import", icon="NONE", text="Import")

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