bl_info = {
    "name": "Dynamic Slideshow",
    "author": "Philipp (Hapit) Hemmer",
    "version": (0, 3),
    "blender": (2, 72, 0),
    "location": "View3D > Tool shelf > Slideshow (Tab)",
    "description": "Addon for creating dynamic slideshows. Inspired by a CG Cookie Tutorial, this addon creates cameras and sequences for a slideshow. It uses the 'images as planes' addon for adding pictures.",
    #"warning": "",
    "wiki_url": "https://github.com/hapit/blender_addon_dynamic_slideshow/wiki/Documentation",
    'tracker_url': 'https://github.com/hapit/blender_addon_dynamic_slideshow/issues',
    'support': 'COMMUNITY',
    "category": "Animation"}


import bpy
from math import sqrt
from bpy.props import *
from bpy.app.handlers import persistent
from mathutils import Vector

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

def set_3d_viewport_shade(shade):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.viewport_shade = shade

def set_all_mesh_draw_type(draw_type):
    for mesh_obj in bpy.context.scene.objects:
        if mesh_obj.type == 'MESH':
            mesh_obj.draw_type = draw_type

def get_sequences_for_frame():
    seq_list = []
    for seq in bpy.context.scene.sequence_editor.sequences:
        cur_frame = bpy.context.scene.frame_current
        if seq.frame_final_start <= cur_frame and seq.frame_final_end >= cur_frame and seq.type == 'SCENE':
            seq_list.append(seq)
    return seq_list

def get_sorted_scene_cameras_list():
    # list of all cameras in scene
    scene_cameras = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'CAMERA':
            scene_cameras.append(obj)
    scene_cameras.sort(key=lambda cam: cam.location.x+cam.delta_location.x)
    return scene_cameras

def is_camera_count_zero():
    for obj in bpy.context.scene.objects:
        if obj.type == 'CAMERA':
            return False
    return True

def has_multiple_cameras():
    cam_count = 0
    for obj in bpy.context.scene.objects:
        if obj.type == 'CAMERA':
            cam_count += 1
            if cam_count > 1:
                return True
    return False

def has_camera_navigation():
    if not has_multiple_cameras():
        return False
    else:
        for cam in get_sorted_scene_cameras_list():
            if cam['picture_mesh'] == None or cam['picture_mesh'] == '':
                return False
    return True
    
def get_prev_camera():
    cameras = get_sorted_scene_cameras_list()
    current_cam = bpy.context.scene.camera
    last_cam = None
    for cam in cameras:
        if cam == current_cam:
            if last_cam == None:
                return current_cam
            else:
                return last_cam
        else:
            last_cam = cam
    return current_cam

def get_next_camera():
    cameras = get_sorted_scene_cameras_list()
    current_cam = bpy.context.scene.camera
    cam_found = False
    for cam in cameras:
        if cam_found:
            return cam
        if cam == current_cam:
            cam_found = True
    return current_cam

def is_draw_type_handling():
    if __name__ == "__main__":
        return True
    user_preferences = bpy.context.user_preferences
    addon_prefs = user_preferences.addons[__name__].preferences

    return addon_prefs.draw_type_handling

def move_action_on_x(action, x_movement):
    for fcurve in action.fcurves:
        for point in fcurve.keyframe_points:
            point.co.x += x_movement
            point.handle_left.x += x_movement
            point.handle_right.x += x_movement

def has_sequence():
    se = bpy.context.scene.sequence_editor
    if se == None:
        return False
    if len(se.sequences) == 0:
        return False
    return True

def select_single_object(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select = True
    bpy.context.scene.objects.active = obj

@persistent
def frame_change_handler(scene):
    if is_draw_type_handling() and has_sequence():
        set_all_mesh_draw_type('WIRE')
        for seq in get_sequences_for_frame():
            bpy.data.objects[seq.scene_camera['picture_mesh']].draw_type = 'TEXTURED'

################### Operators

class InitSceneOperator(bpy.types.Operator):
    """Init scene for slideshow"""
    bl_idname = "dyn_slideshow.init_scene"
    bl_label = "Init Scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)
        bpy.context.scene.render.engine = 'BLENDER_RENDER'
        
        bpy.context.space_data.viewport_shade = 'WIREFRAME'
        bpy.context.scene.game_settings.material_mode = 'GLSL'
        bpy.context.space_data.show_textured_solid = True
        
        # N-Panel Screen Preview/Render
        bpy.context.scene.render.use_sequencer_gl_preview = True
        bpy.context.scene.render.sequencer_gl_preview = 'SOLID'
        bpy.context.scene.render.use_sequencer_gl_textured_solid = True
        
        return {'FINISHED'}


class AddCameraOperator(bpy.types.Operator):
    """Add Camera"""
    
    bl_idname = "dyn_slideshow.add_cameras"
    bl_label = "Add Camera"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        wm = context.window_manager
        
        bpy.ops.object.camera_add(location=(0,0,2),rotation=(0,0,0))
        
        if is_draw_type_handling():
            for mesh_obj in bpy.context.scene.objects:
                if mesh_obj.type == 'MESH':
                    for mat_slot in mesh_obj.material_slots:
                        mat_slot.material.use_shadeless = True
                    mesh_obj.draw_type = 'WIRE'
                    if mesh_obj.location == Vector((0.0, 0.0, 0.0)):
                        mesh_obj.draw_type = 'SOLID'
        
        bpy.context.space_data.viewport_shade = 'SOLID'
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return is_camera_count_zero()


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
            select_single_object(cameraObj)
            bpy.context.scene.camera = cameraObj
            
            # list of all meshes in scene
            scene_meshes = []
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    scene_meshes.append(obj)
            
            # get image_plane under camera
            camera_image_mesh = None
            for mesh_obj in scene_meshes:
                if mesh_obj.type == 'MESH':
                    if camera_image_mesh == None:
                        camera_image_mesh = mesh_obj
                    elif get_distance(cameraObj, mesh_obj) < get_distance(cameraObj, camera_image_mesh):
                        camera_image_mesh = mesh_obj
                        
            scene_meshes.sort(key=lambda mesh: mesh.location.x)
            if is_draw_type_handling():
                camera_image_mesh.draw_type = 'TEXTURED'
            
            last_mesh = camera_image_mesh
            for mesh_obj in scene_meshes:
                if mesh_obj.type == 'MESH':
                    if mesh_obj == camera_image_mesh:
                        print('image_plane already has first camera: '+str(mesh_obj))
                        cameraObj['picture_mesh'] = camera_image_mesh.name
                    else:
                        camera_offset_x = mesh_obj.location.x - last_mesh.location.x
                        camera_offset_y = mesh_obj.location.y - last_mesh.location.y
                        
                        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate = {"linked":False})
                        newObj = bpy.context.active_object
                        
                        newObj.delta_location[0] += camera_offset_x
                        newObj.delta_location[1] += camera_offset_y
                        
                        newObj['picture_mesh'] = mesh_obj.name
                        
                        last_mesh = mesh_obj
                        
                else:
                    print('ERROR: type is '+mesh_obj.type)
            
                    
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
        
        scene_cameras = get_sorted_scene_cameras_list()
        scene_cameras.sort(key=lambda camera: camera.location[0]+camera.delta_location[0])
        
        # resize scene length
        bpy.context.scene.frame_end = len(scene_cameras)*wm.ds_sequence_length + (len(scene_cameras)-1)*wm.ds_effect_length
        
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
            
            # set offset in strip
            seqDuration = new_sequence.frame_final_duration
            new_sequence.animation_offset_start = seq_start_frame
            new_sequence.frame_final_duration = seqDuration
            
            # move animation to strip frames
            if camera.animation_data != None:
                move_action_on_x(camera.animation_data.action, seq_start_frame)
            
            new_sequence.scene_camera = camera

            if last_sequence != None:
                new_effect_sequence = bpy.context.scene.sequence_editor.sequences.new_effect(name=self.effect_sequence_name, type = self.effect_type, channel=effect_channel, frame_start=seq_start_frame, frame_end=seq_start_frame + wm.ds_effect_length, seq1=last_sequence, seq2=new_sequence)
            
            sequence_index = sequence_index+1
            effect_index = effect_index+1
            effect_count_on_seq = 2
            last_sequence = new_sequence

        new_sequence.frame_final_end = new_sequence.frame_final_end - wm.ds_effect_length
        
        return {'FINISHED'}


class ActivateSecuenceCameraOperator(bpy.types.Operator):
    """Acivate sequence camera"""
    bl_idname = "dyn_slideshow.activate_sequence_camera"
    bl_label = "Activate camera from active sequence"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        se = bpy.context.scene.sequence_editor
        print(se)
        if se == None:
            return {'CANCELLED'}
        act_seq = se.active_strip
        print(act_seq)
        if act_seq.type == 'SCENE':
            if is_draw_type_handling():
                bpy.data.objects[bpy.context.scene.camera['picture_mesh']].draw_type = 'WIRE'
            bpy.context.scene.camera = act_seq.scene_camera
            select_single_object(bpy.context.scene.camera)
            if is_draw_type_handling():
                bpy.data.objects[act_seq.scene_camera['picture_mesh']].draw_type = 'TEXTURED'
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        se = bpy.context.scene.sequence_editor
        if se == None:
            return False
        act_seq = se.active_strip
        if act_seq == None:
            return False
        return act_seq.type == 'SCENE' and act_seq.scene_camera != None


class ActivateNextCameraOperator(bpy.types.Operator):
    """Acivate sequence camera"""
    bl_idname = "dyn_slideshow.activate_next_camera"
    bl_label = "Activate camera from active sequence"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if bpy.context.scene.camera == None:
            return {'CANCELLED'}
        if is_draw_type_handling():
            bpy.data.objects[bpy.context.scene.camera['picture_mesh']].draw_type = 'WIRE'
        bpy.context.scene.camera = get_next_camera()
        select_single_object(bpy.context.scene.camera)
        
        if is_draw_type_handling():
            bpy.data.objects[bpy.context.scene.camera['picture_mesh']].draw_type = 'TEXTURED'
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return has_camera_navigation()

class ActivatePreviousCameraOperator(bpy.types.Operator):
    """Acivate previous camera"""
    bl_idname = "dyn_slideshow.activate_previous_camera"
    bl_label = "Activate previous camera"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if bpy.context.scene.camera == None:
            return {'CANCELLED'}
        if is_draw_type_handling():
            bpy.data.objects[bpy.context.scene.camera['picture_mesh']].draw_type = 'WIRE'
        #bpy.context.scene.camera.select = False
        bpy.context.scene.camera = get_prev_camera()
        select_single_object(bpy.context.scene.camera)
        
        if is_draw_type_handling():
            bpy.data.objects[bpy.context.scene.camera['picture_mesh']].draw_type = 'TEXTURED'
        return {'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return has_camera_navigation()

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
        
        layout.operator(InitSceneOperator.bl_idname, 'Init scene')
        
        if 'io_import_images_as_planes' in bpy.context.user_preferences.addons.keys():
            layout.operator("import_image.to_plane", ' Images as Planes', icon='TEXTURE')
        else:
            layout.label("Activate 'Images as Planes'")
        
        layout.operator(AddCameraOperator.bl_idname, 'Add camera')
        
        layout.operator(InitCamerasOperator.bl_idname, 'Duplicate cameras')
        
        box = layout.box()
        box.prop(wm, 'ds_start_frame', text="Start frame")
        box.prop(wm, 'ds_sequence_length', text="Length")
        box.prop(wm, 'ds_effect_length', text="Effect length")
        box.operator(InitSequencesOperator.bl_idname, 'Create sequences')
        
        layout.label('Camera navigation:')
        layout.operator(ActivateSecuenceCameraOperator.bl_idname, 'Activate camera from active sequence')
        
        col = layout.row(align=True)
        col.operator(ActivatePreviousCameraOperator.bl_idname, 'Previous')
        col.operator(ActivateNextCameraOperator.bl_idname, 'Next')

# Addon Preferences

class DynSlideshowPref(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    draw_type_handling = bpy.props.BoolProperty(name='Advanced draw type handling for performance with many images.', default=True, description='Only displays acive planes as textured.')
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "draw_type_handling")


def register():
    bpy.utils.register_module(__name__)
    
    bpy.app.handlers.frame_change_pre.append(frame_change_handler)
    
    bpy.types.WindowManager.ds_sequence_length = IntProperty(min = 1, default = 100, description='Sequence length without effect length')
    bpy.types.WindowManager.ds_effect_length = IntProperty(min = 1, default = 25, description='Sequence effect length, added to sequence length')
    bpy.types.WindowManager.ds_start_frame = IntProperty(min = 1, default = 1, description='Frame the first sequence starts')


def unregister():
    bpy.utils.unregister_module(__name__)
    
    bpy.app.handlers.frame_change_pre.remove(frame_change_handler)
    
    try:
        del bpy.types.WindowManager.ds_sequence_length
        del bpy.types.WindowManager.ds_effect_length
        del bpy.types.WindowManager.ds_start_frame
        
    except:
        pass

if __name__ == "__main__":
    register()
