bl_info = {
    "name": "Dynamic Slideshow",
    "author": "Philipp (Hapit) Hemmer",
    "version": (0, 1),
    "blender": (2, 72, 0),
    "location": "View3D > Object > Dynamic Slideshow",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "category": "Object"}


import bpy
from math import sqrt
from bpy.props import *


################### Functions

def get_distance(obj1, obj2):
    """
    return: float. Distance of the two objects
    """
    l = []  # we store the loacation vector of each object
    l.append(obj1.location)
    l.append(obj2.location)
    
    distance = sqrt( (l[0][0] - l[1][0])**2 + (l[0][1] - l[1][1])**2 + (l[0][2] - l[1][2])**2)
    return distance

################### Operators

class InitCamerasOperator(bpy.types.Operator):
    """Init Cameras"""
    bl_idname = "dyn_slideshow.init_cameras"
    bl_label = "Init Cameras"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # check if only one camera
        cameraCount = 0
        cameraObj = None
        for obj in bpy.context.scene.objects:
            if obj.type == 'CAMERA':
                cameraCount += 1
                cameraObj = obj

        if cameraCount == 1:    
            # deselect everything
            bpy.ops.object.select_all(action='DESELECT')
            
            # select the camera
            cameraObj.select = True
            bpy.context.scene.objects.active = cameraObj
            bpy.context.scene.camera = cameraObj
            
            # list of all meshes in scene
            scene_meshes = []
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    scene_meshes.append(obj)
            
            # get image_plane under camera
            camera_image_mesh = None
            for obj in scene_meshes:
                if obj.type == 'MESH':
                    if camera_image_mesh == None:
                        camera_image_mesh = obj
                    elif get_distance(cameraObj, obj) < get_distance(cameraObj, camera_image_mesh):
                        camera_image_mesh = obj

            scene_meshes.sort(key=lambda mesh: mesh.location.x)
            
            last_mesh = camera_image_mesh
            for obj in scene_meshes:
                if obj.type == 'MESH':
                    if obj == camera_image_mesh:
                        print('image_plane already has first camera: '+str(obj))
                    else:
                        camera_offset_x = obj.location.x - last_mesh.location.x
                        camera_offset_y = obj.location.y - last_mesh.location.y
                        
                        print('doing')
                        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate = {"linked":False})
                        newObj = bpy.context.active_object
                        
                        newObj.delta_location[0] += camera_offset_x
                        newObj.delta_location[1] += camera_offset_y
                        
                        last_mesh = obj
                else:
                    print('ERROR: type is '+obj.type)
        else:
            return {'CANCELLED'}
        return {'FINISHED'}


class InitSequencesOperator(bpy.types.Operator):
    """Init Sequences"""
    bl_idname = "dyn_slideshow.init_sequences"
    bl_label = "Init Sequences"
    bl_options = {'REGISTER', 'UNDO'}
    
    # variables
    start_frame = 1
    channel_toggle = True
    channel_a = 1
    channel_b = 2
    effect_channel = channel_b + 1
    if channel_a > channel_b:
        effect_channel = channel_a +1
    seq_channel = channel_a
    scene_sequence_name = 'scene'
    effect_sequence_name = 'effect'
    effect_type = 'CROSS' # 'CROSS' or ‘GAMMA_CROSS’ or ‘WIPE’
    
    def execute(self, context):
        wm = context.window_manager
        # create sequences for each camera
        bpy.context.scene.sequence_editor_create()

        # list of all cameras in scene
        scene_cameras = []
        for obj in bpy.context.scene.objects:
            if obj.type == 'CAMERA':
                scene_cameras.append(obj)

        scene_cameras.sort(key=lambda camera: camera.delta_location[0])
        
        sequence_index = 0
        effect_index = 0
        effect_count_on_seq = 1
        last_sequence = None
        
        for camera in scene_cameras:
            if sequence_index > 0:
                effect_index = sequence_index-1
            seq_start_frame = self.start_frame + sequence_index*wm.ds_sequence_length + effect_index*wm.ds_effect_length
            if self.channel_toggle:
                seq_channel = self.channel_a
            else:
                seq_channel = self.channel_b
            self.channel_toggle = not self.channel_toggle
            
            new_sequence = bpy.context.scene.sequence_editor.sequences.new_scene(name=self.scene_sequence_name+'_'+str(camera.name), scene=bpy.context.scene, channel=seq_channel, frame_start=seq_start_frame)
            new_sequence.frame_final_duration = wm.ds_sequence_length + effect_count_on_seq * wm.ds_effect_length
            new_sequence.scene_camera = camera

            if last_sequence != None:
                new_effect_sequence = bpy.context.scene.sequence_editor.sequences.new_effect(name=self.effect_sequence_name, type = self.effect_type, channel=self.effect_channel, frame_start=seq_start_frame, frame_end=seq_start_frame + wm.ds_effect_length, seq1=last_sequence, seq2=new_sequence)
            
            sequence_index = sequence_index+1
            effect_index = effect_index+1
            effect_count_on_seq = 2
            last_sequence = new_sequence

        new_sequence.frame_final_end = new_sequence.frame_final_end - wm.ds_effect_length
        return {'FINISHED'}


class DynamicSlideshowPanel(bpy.types.Panel):
    """UI panel for the Remesh and Boolean buttons"""
    bl_label = "Dyn. slideshow"
    bl_idname = "OBJECT_PT_dynamic_slideshow"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Slideshow"

    def draw(self, context):
        layout = self.layout
        edit = context.user_preferences.edit
        wm = context.window_manager
        
        if 'io_import_images_as_planes' in bpy.context.user_preferences.addons.keys():
            layout.operator("import_image.to_plane", ' Images as Planes', icon='TEXTURE')
        else:
            layout.label("Activate 'Images as Planes'")
        
        layout.operator("dyn_slideshow.init_cameras", 'Duplicate cameras')
        
        box = layout.box()
        box.prop(wm, 'ds_sequence_length', text="Length")
        box.prop(wm, 'ds_effect_length', text="Effect length")
        box.operator("dyn_slideshow.init_sequences", 'Create sequences')


def register():
    bpy.utils.register_class(InitCamerasOperator)
    bpy.utils.register_class(InitSequencesOperator)
    bpy.utils.register_class(DynamicSlideshowPanel)
    
    bpy.types.WindowManager.ds_sequence_length = IntProperty(min = 1, default = 100)
    bpy.types.WindowManager.ds_effect_length = IntProperty(min = 1, default = 25)

def unregister():
    bpy.utils.unregister_class(InitCamerasOperator)
    bpy.utils.unregister_class(InitSequencesOperator)
    bpy.utils.unregister_class(DynamicSlideshowPanel)

if __name__ == "__main__":
    register()
