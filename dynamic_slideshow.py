bl_info = {
    "name": "Dynamic Slideshow",
    "author": "Philipp (Hapit) Hemmer",
    "version": (0, 2),
    "blender": (2, 72, 0),
    "location": "View3D > Tool shelf > Slideshow (Tab)",
    "description": "Inspired by a CG Cookie Tutorial, this addon creates cameras and sequences for a slideshow. It uses the 'images as planes' addon for adding pictures.",
    #"warning": "",
    #"wiki_url": "",
    "category": "Animation"}


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

def get_first_free_vse_channel():
    if bpy.context.scene.sequence_editor == None:
        return 1
    else:
        first_free_channel = 1
        for seq in bpy.context.scene.sequence_editor.sequences:
            if first_free_channel <= seq.channel:
                first_free_channel = seq.channel + 1
        return first_free_channel

def is_vse_empty():
    if bpy.context.scene.sequence_editor == None:
        return True
    elif len(bpy.context.scene.sequence_editor.sequences) == 0:
        return True
    return False
    

################### Operators

class InitCamerasOperator(bpy.types.Operator):
    """Init Cameras"""
    bl_idname = "dyn_slideshow.init_cameras"
    bl_label = "Init Cameras"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
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
                    # default draw_type to 'WIRE'
                    #obj.draw_type = 'WIRE'

            scene_meshes.sort(key=lambda mesh: mesh.location.x)
            
            last_mesh = camera_image_mesh
            for obj in scene_meshes:
                if obj.type == 'MESH':
                    if obj == camera_image_mesh:
                        print('image_plane already has first camera: '+str(obj))
                        
                    else:
                        camera_offset_x = obj.location.x - last_mesh.location.x
                        camera_offset_y = obj.location.y - last_mesh.location.y
                        
                        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate = {"linked":False})
                        newObj = bpy.context.active_object
                        
                        newObj.delta_location[0] += camera_offset_x
                        newObj.delta_location[1] += camera_offset_y
                        
                        last_mesh = obj
                        
                else:
                    print('ERROR: type is '+obj.type)
                    
        else:
            msg = 'Please add and position camera in scene.'
            if cameraCount > 1:
                msg = 'More than one camera in scene.'
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        
        return {'FINISHED'}


class InitSequencesOperator(bpy.types.Operator):
    """Init Sequences"""
    bl_idname = "dyn_slideshow.init_sequences"
    bl_label = "Init Sequences"
    bl_options = {'REGISTER', 'UNDO'}
    
    scene_sequence_name = 'scene'
    effect_sequence_name = 'effect'
    effect_type = 'CROSS' # 'CROSS' or ‘GAMMA_CROSS’ or ‘WIPE’
    
    def execute(self, context):
        wm = context.window_manager
        # variables
        channel_toggle = True
        channel_a = get_first_free_vse_channel()
        channel_b = channel_a + 1
        effect_channel = channel_b + 1
        seq_channel = channel_a
        sequence_index = 0
        effect_index = 0
        effect_count_on_seq = 1
        last_sequence = None
        
        # create sequences for each camera
        bpy.context.scene.sequence_editor_create()

        # list of all cameras in scene
        scene_cameras = []
        for obj in bpy.context.scene.objects:
            if obj.type == 'CAMERA':
                scene_cameras.append(obj)

        scene_cameras.sort(key=lambda camera: camera.delta_location[0])
        
        for camera in scene_cameras:
            if sequence_index > 0:
                effect_index = sequence_index-1
            seq_start_frame = wm.ds_start_frame + sequence_index*wm.ds_sequence_length + effect_index*wm.ds_effect_length
            
            # toggle sequence channel
            if channel_toggle:
                seq_channel = channel_a
            else:
                seq_channel = channel_b
            channel_toggle = not channel_toggle
            
            new_sequence = bpy.context.scene.sequence_editor.sequences.new_scene(name=self.scene_sequence_name+'_'+str(camera.name), scene=bpy.context.scene, channel=seq_channel, frame_start=seq_start_frame)
            new_sequence.frame_final_duration = wm.ds_sequence_length + effect_count_on_seq * wm.ds_effect_length
            new_sequence.scene_camera = camera

            if last_sequence != None:
                new_effect_sequence = bpy.context.scene.sequence_editor.sequences.new_effect(name=self.effect_sequence_name, type = self.effect_type, channel=effect_channel, frame_start=seq_start_frame, frame_end=seq_start_frame + wm.ds_effect_length, seq1=last_sequence, seq2=new_sequence)
            
            sequence_index = sequence_index+1
            effect_index = effect_index+1
            effect_count_on_seq = 2
            last_sequence = new_sequence

        new_sequence.frame_final_end = new_sequence.frame_final_end - wm.ds_effect_length
        return {'FINISHED'}


class DeleteAllSequencesOperator(bpy.types.Operator):
    """Delete all sequences in the VSE"""
    bl_idname = "dyn_slideshow.clear_vse"
    bl_label = "Delete all sequences"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.context.scene.sequence_editor_clear()
        
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return not is_vse_empty()


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
        box.prop(wm, 'ds_start_frame', text="Start frame")
        box.prop(wm, 'ds_sequence_length', text="Length")
        box.prop(wm, 'ds_effect_length', text="Effect length")
        box.operator("dyn_slideshow.init_sequences", 'Create sequences')
        box.operator(DeleteAllSequencesOperator.bl_idname, 'Delete all sequences')


def register():
    bpy.utils.register_module(__name__)
    
    bpy.types.WindowManager.ds_sequence_length = IntProperty(min = 1, default = 100)
    bpy.types.WindowManager.ds_effect_length = IntProperty(min = 1, default = 25)
    bpy.types.WindowManager.ds_start_frame = IntProperty(min = 1, default = 1)

def unregister():
    bpy.utils.unregister_module(__name__)
    
    try:
        del bpy.types.WindowManager.ds_sequence_length
        del bpy.types.WindowManager.ds_effect_length
        
    except:
        pass

if __name__ == "__main__":
    register()
