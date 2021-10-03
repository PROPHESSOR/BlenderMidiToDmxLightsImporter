# -*- coding: utf-8 -*-

'''
***** BEGIN BSD LICENSE BLOCK *****

--------------------------------------------------------------------------
CSV F-Curve Importer v0.7 alpha6
--------------------------------------------------------------------------

Copyright (c) 2015 Hans.P.G. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
4. Neither the name of Hans.P.G. nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY HANS.P.G. ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL HANS.P.G. BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.

***** END BSD LICENCE BLOCK *****

History:
2020/02/15: v0.7 alpha6
  + updated for blender 2.80.
2015/05/10: v0.7 alpha5
  + added the checkboxes to select delimiter letters.
2015/05/01: v0.7 alpha4
  + updated for Blender 2.74.
  + special thanks to chebhou and vklidu, who made this script work 
    and confirm it in Blender 2.74.
  + removed prop_search and replaced to string box. Now you can specify
    any name for Action and Data Path.
2013/06/23: v0.7 alpha3
  + removed feature to select data path name to avoid addon init error.
2013/02/20: v0.7 alpha2
  + modified to read comments in .csv file.
2011/04/19: v0.7 alpha1
  + updated for Blender 2.57.
  + special thanks to bladecoder, who made this script work in Blender 
    2.57.
2011/02/20: v0.6 alpha3
  + refactoring for the class field names.
  + add unit test_one class for FCurvePointAdder.
  + fix bug related to add-on registration.
    (you MUST access bpy.data.scenes[0] ANY TIMES to get 
    CONFIG_CsvFcurveImporter contents)
2010/10/31: v0.6 alpha2
  + rewrite the logic part of script to read a file and to add points to 
    f-curves.
  + add add-on information data.
  + add a feature to output log data to console after importing.
2010/10/24: v0.6 alpha1
  + rewrite the CSV Importer script for Blender 2.5. (the minimum feature)
  + create a UI for the f-curve import configuration.
2010/06/07: v0.5 beta3
  + fixed the bug in which it doesn't import a .csv file with detailed 
    timeline. (Thank you for reporting, okchoir)
2007/08/03: v0.5 beta2
  + added New=Ipo, Object to detail setup items of AutoMode.
  + fixed lots of bug after final test.
  + can print out setups in HandleMode.
2007/07/24: v0.5 beta1
  + can write setups for both IPO curves and meshes into a CSV file and 
    import it automatically.
  + can write detailed setups for both IPO curves and meshes into a CSV 
    file (AutoMode only).
2007/07/02: v0.4 beta
  + improved GUI for better usability.
  + added buttons, Reset, SaveLogs in GUI.
  + improved the contents of logs.
2006/11/24: v0.3 beta
  + can import data from a CSV file and create meshes 
    (AutoMode unsupported).
2006/10/13: v0.2 beta
  + can print out logs for debug (suggestion of Manda).
2006/10/09: v0.1 beta
  + can write setups into a CSV file and import it automatically 
    (experimental).
2006/10/07: v0.0 beta
  + first edition.
  + can use GUI for setup.
  + can save setups to Registry in Blender.
  + can import data from a CSV file and create IPO curves.
'''

bl_info = {
    "name": "CSV F-Curve Importer Modded by PROPHESSOR",
    "author": "Hans.P.G. & PROPHESSOR",
    "version": (0, 7, 6),
    "blender": (2, 80, 0),
    "location": "Properties space > Scene tab > CSV F-Curve Importer panel",
    "description": "Import .csv file and create f-curves",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
    }


import bpy
import csv
import re
from math import *
import unittest

#import sys
#sys.path.append(r"---(^o^)---\(IDE) eclipse-cpp-helios-SR1-win32\plugins\org.python.pydev.debug_1.6.4.2011010200\pysrc")
#import pydevd
#pydevd.settrace() # breakpoint

def main():

    test = TestManager()
    test.addTestCase(Test_FCurvePointAdder)
    test.run()
    
class TestManager:
    
    def __init__(self):
        self.suite = unittest.TestSuite()
        
    def addTestCase(self, testcase_class):
        test = unittest.TestLoader().loadTestsFromTestCase(testcase_class)
        self.suite.addTest(test)
        
    def run(self):
        unittest.TextTestRunner().run(self.suite)

#---=== Logic ===

class CsvLineReader:
    # assume: delimiter is , ; \s
    # assume: comment starts with #, //, %, '
    
    def __init__(self, filename):
        
        self.re_deli = ",\s\t"
        self.filename = filename
        self.on_line_read = Event()
        self.on_finish = Event()
        
        self.read_numbers = []
        self.read_row = -1

    def readCsv(self):
        filename = self.get_net_path(self.filename)
        file = open(filename, "r")
        print('Reading file', filename)
        reader = csv.reader(file)

        values = []

        for line in reader:
            values.append(line)

        return values
    
    def read(self):
        
        self.split_line = re.compile("[^" + self.re_deli + "]+").findall # type: you can use re.split or re.findall
        # above: for many delimiters, set re.compile() like "[^,;:\s]+"
        
        filename = self.get_net_path(self.filename)
        file = open(filename, "r")
        
        row = -1
        while True:
            
            text_line = file.readline()
            if text_line == "": # if: EOF, readline() returns "" only when EOF, it returns "\n" if empty line.
                break
            
            text_line = text_line.strip()
            if text_line == "": # if: empty line
                continue
            if text_line.startswith(("#", "//", "%", "'")): # if: comments
                continue
            
            text_nums = self.split_line(text_line)
            nums = map(self.float, text_nums)
            nums = list(nums)
            row += 1
            
            self.read_numbers = nums
            self.read_row = row
            self.on_line_read.invoke()
        
        file.close()
        
        self.read_numbers = []
        self.read_row = -1
        self.on_finish.invoke()

    @staticmethod
    def get_net_path(path):
        if path[0:2] == "//":
            return bpy.path.abspath(path)
        else:
            return path

    @staticmethod
    def float(x):
        try:
            return float(x)
        except:
            return None

def addCurvePoint(curve, frame, value):
    if not curve:
        raise Exception("Curve is not defined")

    curve.keyframe_points.insert(int(frame), int(value))


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
                return action.fcurves.new(data_path=path_name, index =index, action_group = args[0])
            else:
                
                return action.fcurves.new(data_path=path_name, index =index)
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

class Event:
    
    def __init__(self):
        self.handlers = [] # type: a function or Event
        self.enable = True
        
    def invoke(self, *args):
        
        if not self.enable:
            return
        
        for handler in self.handlers:
            if isinstance(handler, Event):
                handler.invoke(*args)
            else:
                handler(*args)
    
    def add(self, func):
        self.handlers.append(func)
    
    def remove(self, func):
        self.handlers.remove(func)
    
    def clear(self):
        self.handlers = []


#---=== UI ===

class FCurveImportUIConfig(bpy.types.PropertyGroup):
    
    time_column = bpy.props.IntProperty(min=0, max=10000, default=0, 
        description="Specify what number of the columns in a .csv file you import as a time data.")
    data_column = bpy.props.IntProperty(min=0, max=10000, default=1, 
        description="Specify what number of the columns in a .csv file you import as a value data.")
    action_name__use_suggestion = bpy.props.BoolProperty(default=False, description="")
    action_name = bpy.props.StringProperty(default="Imported", 
        description="Specify the name of Action object in which f-curves are created.")
    data_path__use_suggestion = bpy.props.BoolProperty(default=False, description="")
    data_path = bpy.props.StringProperty(default="location", 
        description="Specify the type of path, for example \"location\", \"rotation_euler\", \"scale\", etc. Or click right button over any textbox in Blender and select \"Copy Data Path\" in the menu, then put the copied name into here.")
    data_path_candidates = bpy.props.EnumProperty(items=[("location", "location", ""), ("rotation_euler", "rotation_euler", ""), ("rotation_quaternion", "rotation_quaternion", ""), ("rotation_axis_angle", "rotation_axis_angle", ""), ("scale", "scale", ""), ("dimensions", "dimensions", "")], default="location",
        description="Select the type of path.")
    data_path_index = bpy.props.IntProperty(min=0, max=10000, default=0, 
        description="Specify the type of axis where 0 is x-axis, 1 is y-axis, and 2 is z-axis.")
    
    is_collapsed = bpy.props.BoolProperty(default=False, description="")
        
    def get_name(self):
    
        if self.data_path__use_suggestion:
            data_path = self.data_path_candidates
        else:
            data_path = self.data_path
        
        return "t:%d, d:%d, path:\"%s\"" % (self.time_column, self.data_column, data_path)
    
class DataPathCandidate(bpy.types.PropertyGroup):
    pass

class ImporterUIConfig(bpy.types.PropertyGroup):
    
    file_path = bpy.props.StringProperty(default="", subtype='FILE_PATH', 
        description="Select a .csv file, then click \"Add\" button below and you'll see a configuration box created.")
    deli_comma = bpy.props.BoolProperty(default=True, name="comma [,]", 
        description="Specify comma as a delimiter of .csv file. (make columns at each comma)")
    deli_space = bpy.props.BoolProperty(default=False, name="space [\\s]", 
        description="Specify space as a delimiter of .csv file. (make columns at each space)")
    deli_tab = bpy.props.BoolProperty(default=False, name="tab [\\t]", 
        description="Specify tab as a delimiter of .csv file. (make columns at each tab)")
    deli_else = bpy.props.StringProperty(default="", 
        description="Specify any other delimiters of .csv file. (taken as regular expression, e.g. ,\\s\\t;:)")
    import_mode = bpy.props.EnumProperty(items=[("MANUAL", "Manually using configs below", "")], default="MANUAL", # [Need Modify]
        description="Currently you can select only one option. (not implemented yet)")
    # import_mode = bpy.props.EnumProperty(items=[('MANUAL', "Manually using configs below", "manu"), ('AUTO', "Automatically using configs in file", "auto")], default='MANUAL')
    fcurve_configs = bpy.props.CollectionProperty(type=FCurveImportUIConfig)
    
    # data_path_candidates = bpy.props.CollectionProperty(type=DataPathCandidate) # [Gave Up]
    
def init_data_path_candidates():
    # note: NOT USE, gave up Data Path suggestion using CollectionProperty.
    
    # sec: set up data_path_candidates
    
    config_top = bpy.data.scenes[0].CONFIG_CsvFcurveImporter
    
    for index in range(len(config_top.data_path_candidates)): # clear data path menu items first
        config_top.data_path_candidates.remove(0)
        
    for name in ["location", "rotation_euler", "rotation_quaternion", # create data path menu items
                 "rotation_axis_angle", "scale", "dimensions"]:
        config_top.data_path_candidates.add()
        config_top.data_path_candidates[-1].name = name
        
class OBJECT_PT_CsvFcurveImporter(bpy.types.Panel):
    
    bl_label = "CSV F-Curve Importer"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        
        config_top = bpy.data.scenes[0].CONFIG_CsvFcurveImporter
        lay = self.layout
        col1 = lay.column()

        row2 = col1.row(align=True)
        row2.prop(config_top, "import_mode", text="")
        
#        row2 = col1.row()
#        row2.operator("scene.csv_fcurve_importer_???", icon="TEXT", text="Log") # [Need Modify]
#        row2.operator("scene.csv_fcurve_importer_???", icon="SCRIPT", text="Script") # [Need Modify]
        
        row2 = col1.row(align=True)
#        row2.operator("scene.csv_fcurve_importer_show_file_detail", icon='QUESTION', text="", emboss=False)
        row2.label(text=".csv File Path:")
        col1.prop(config_top, "file_path", text="")

        row2 = col1.row(align=True)
        row2.label(text="Delimiter:")
        row2 = col1.row(align=True)
        col3 = row2.row(align=True)
        col3.prop(config_top, "deli_comma")
        col3.prop(config_top, "deli_space")
        row2 = col1.row(align=True)
        col3 = row2.row(align=True)
        col3.prop(config_top, "deli_tab")
        col3.prop(config_top, "deli_else", text="Else")
        
        col1.label(text="Column and F-Curve Configurations:")
        if not config_top.fcurve_configs:
            col1.operator("scene.csv_fcurve_importer_create", icon="NONE", text="Add").index = 0
        
        for index, config in enumerate(config_top.fcurve_configs):
            
            box2 = col1.box()
            col3 = box2.column()
            
            row4 = col3.row(align=True)
            if config.is_collapsed:
                row4.operator("scene.csv_fcurve_importer_collapse", icon='GRAPH', text="", emboss=False).index = index
            else:
                row4.operator("scene.csv_fcurve_importer_collapse", icon='GRAPH', text="", emboss=False).index = index
            row4.label(text=config.get_name())
            row4.operator("scene.csv_fcurve_importer_copy", icon='DUPLICATE', text="").index = index
            row4.operator("scene.csv_fcurve_importer_remove", icon='TRASH', text="").index = index
            
            if config.is_collapsed:
                continue
            
            row4 = col3.row(align=True)
            row4.prop(config, "time_column", text="Time column")
            row4.prop(config, "data_column", text="Data column")

            row4 = col3.row()
            col5 = row4.column()
            col5.label(text="Action Name:", icon='NONE')
            row6 = col5.row(align=True)
            row6.prop(config, "action_name__use_suggestion", text="", icon='SYSTEM')
            if config.action_name__use_suggestion:
                row6.prop_search(config, "action_name", bpy.data, "actions", text="")
            else:
                row6.prop(config, "action_name", text="")
            
            col5 = row4.column()
            col5.label(text="Data Path:", icon='NONE')
            col6 = col5.column(align=True)
            row7 = col6.row(align=True)
            row7.prop(config, "data_path__use_suggestion", text="", icon='PLUGIN')
            if config.data_path__use_suggestion:
                # row7.prop_search(config, "data_path", config_top, "data_path_candidates", text="", icon='QUESTION') # [Gave Up]
                row7.prop(config, "data_path_candidates", text="")
            else:
                row7.prop(config, "data_path", text="")
            col6.prop(config, "data_path_index", text=self.__class__.get_data_path_index_text(config.data_path_index))
            
            
        col1.operator("scene.csv_fcurve_importer_import", text="Import")
        # WannaDo: [Need Modify]
        # +create/not action name
        # +create/not data path
        # +add detail extension button
        #  +radian/degree if necessary
        #  +object to import: selected/name, create/not
        #  +f-curve extrapolation, interpolation_type, handle_type
        #  +converter for time and data
        #  +thin down sampling
        # +output these configs to python code
        # +import automatically -> use "exec"
            
    @staticmethod
    def get_data_path_index_text(index):
         
        if index == 0:
            return "Index (X)"
        elif index == 1:
            return "Index (Y)"
        elif index == 2:
            return "Index (Z)"
        elif index == 3:
            return "Index (W)"
        else:
            return "Index"

class OBJECT_OP_CsvFcurveImporter_Import(bpy.types.Operator):
    
    bl_idname = "scene.csv_fcurve_importer_import"
    bl_label = "Import f-curves from .csv file (CSV F-Curve Importer (P))"
    bl_description = "Import f-curves from .csv file"
    
    def execute(self, context):
        
        config_top = bpy.data.scenes[0].CONFIG_CsvFcurveImporter
        
        print('Execute import at file path', config_top.file_path)
        reader = CsvLineReader(config_top.file_path)
        data = reader.readCsv()
        
        adder_logs = []
        # for config in config_top.fcurve_configs:
        config = config_top.fcurve_configs[0]

        activeObject = bpy.context.active_object
        print('active object', activeObject)
        accesser = ActionFCurveAccessor(bpy.context.active_object)
        print('accesser', accesser)
        # above: you can change "active_object" to a material instance to add animation to the material.
        print('action', accesser.get_or_create_action(config.action_name))

        data_path = config.data_path

        print('data_path', data_path, config.data_path_index)

        curve = accesser.get_or_create_fcurve(data_path, config.data_path_index)

        print('curve', curve)

        for line in data:
            addCurvePoint(curve, int(line[config.time_column]), int(line[config.data_column]))

        return {'FINISHED'}

class OBJECT_OP_CsvFcurveImporter_ShowFileDetail(bpy.types.Operator):
    
    bl_idname = "scene.csv_fcurve_importer_show_file_detail"
    bl_label = ""
    bl_description = ""

class OBJECT_OP_CsvFcurveImporter_Create(bpy.types.Operator):
    
    bl_idname = "scene.csv_fcurve_importer_create"
    bl_label = "Create an import configuration (CSV F-Curve Importer)"
    bl_description = "Create an import configuration"
    
    index = bpy.props.IntProperty(min = -1, default = -1)
    
    def execute(self, context):
        
        config_top = bpy.data.scenes[0].CONFIG_CsvFcurveImporter
        
        config_top.fcurve_configs.add()
        config_top.fcurve_configs.move(len(config_top.fcurve_configs) - 1, self.index + 1) # move to the end
        
        return {'FINISHED'}

class OBJECT_OP_CsvFcurveImporter_Copy(bpy.types.Operator):
    
    bl_idname = "scene.csv_fcurve_importer_copy"
    bl_label = "Copy an import configuration (CSV F-Curve Importer)"
    bl_description = "Copy an import configuration"
    
    index = bpy.props.IntProperty(min = -1, default = -1)
    
    def execute(self, context):
        
        config_top = bpy.data.scenes[0].CONFIG_CsvFcurveImporter
        
        config = config_top.fcurve_configs.add()
        config_orig = config_top.fcurve_configs[self.index]
        config.time_column = config_orig.time_column
        config.data_column = config_orig.data_column
        config.action_name = config_orig.action_name
        config.data_path = config_orig.data_path
        config.data_path_candidates = config_orig.data_path_candidates
        config.data_path_index = config_orig.data_path_index
        
        config_top.fcurve_configs.move(len(config_top.fcurve_configs) - 1, self.index + 1) # move below to the original config
        return {'FINISHED'}

class OBJECT_OP_CsvFcurveImporter_Remove(bpy.types.Operator):
    
    bl_idname = "scene.csv_fcurve_importer_remove"
    bl_label = "Remove the import configuration (CSV F-Curve Importer)"
    bl_description = "Remove the import configuration"

    index = bpy.props.IntProperty(min = -1, default = -1)
    
    def execute(self, context):

        config_top = bpy.data.scenes[0].CONFIG_CsvFcurveImporter
        
        config_top.fcurve_configs.remove(self.index)
        return {'FINISHED'}

class OBJECT_OP_CsvFcurveImporter_Collapse(bpy.types.Operator):
    
    bl_idname = "scene.csv_fcurve_importer_collapse"
    bl_label = "Collapse/Expand the import configuration (CSV F-Curve Importer)"
    bl_description = "Collapse/Expand the import configuration"
    
    index = bpy.props.IntProperty(min = -1, default = -1)
    
    def execute(self, context):

        config_top = bpy.data.scenes[0].CONFIG_CsvFcurveImporter

        config = config_top.fcurve_configs[self.index]
        config.is_collapsed = not config.is_collapsed
        return {'FINISHED'}
    
    
#---=== Register ===

classes = (
    FCurveImportUIConfig,
    DataPathCandidate,
    ImporterUIConfig,
    OBJECT_PT_CsvFcurveImporter,
    OBJECT_OP_CsvFcurveImporter_Import,
    OBJECT_OP_CsvFcurveImporter_ShowFileDetail,
    OBJECT_OP_CsvFcurveImporter_Create,
    OBJECT_OP_CsvFcurveImporter_Copy,
    OBJECT_OP_CsvFcurveImporter_Remove,
    OBJECT_OP_CsvFcurveImporter_Collapse,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.CONFIG_CsvFcurveImporter = bpy.props.PointerProperty(type=ImporterUIConfig)
    
    # init_data_path_candidates() # [Gave Up]
    # note: gave up Data Path suggestion using CollectionProperty.

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    if bpy.context.scene.get('CONFIG_CsvFcurveImporter') != None:
        del bpy.context.scene['CONFIG_CsvFcurveImporter']
    try:
        del bpy.types.Scene.CONFIG_CsvFcurveImporter
    except:
        pass

if __name__ == '__main__':
    register()
    # main() # run unit tests
