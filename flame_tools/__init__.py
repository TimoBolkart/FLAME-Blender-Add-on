# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Tools",
    "author": "Joachim Tesch, Max Planck Institute for Intelligent Systems",
    "version": (2020, 9, 11),
    "blender": (2, 80, 0),
    "location": "Viewport > Right panel",
    "description": "FLAME Tools",
    "category": "FLAME"}

# FLAME globals
# Note: FLAME 2020 indices of hole closing faces are from sample OBJ and start at 1
flame_hole_faces = [(1595,1743,1863),(1595,1596,1743),(1596,1747,1743),(1747,1748,1743),(1743,1740,1863),(1740,1666,1831),(1863,1740,1831),(1666,1667,1836),(1667,3515,1853),(1836,1667,1853),(3515,2784,2942),(2784,2783,2934),(2783,2855,2931),(2855,2858,2946),(2858,2863,2862),(2862,2732,2858),(2732,2731,2858),(2731,2709,2946),(2709,2710,2944),(2946,2709,2944),(2946,2931,2855),(2931,2934,2783),(2934,2942,2784),(2942,3498,3515),(3498,1853,3515),(1836,1831,1666),(1863,1861,1573),(1861,1574,1573),(1573,1595,1863),(2731,2946,2858),(3323,3372,3331),(3257,3256,3261),(3256,3258,3261),(3258,3259,3290),(3286,3380,3360),(3380,3358,3357),(3258,3290,3261),(3290,3286,3261),(3219,3257,3262),(3227,3220,3273),(3220,3219,3229),(3273,3230,3274),(3229,3230,3220),(3220,3230,3273),(3262,3229,3219),(3257,3261,3262),(3380,3357,3360),(3357,3355,3360),(3355,3356,3360),(3356,3322,3361),(3322,3323,3330),(3356,3361,3360),(3323,3328,3372),(3372,3373,3331),(3331,3330,3323),(3330,3361,3322),(3360,3249,3286),(3249,3261,3286)]
flame_default_faces = 9976
flame_pose_length = 15

import bpy
import bmesh
from mathutils import Vector
from math import radians
import numpy as np
import os
import pickle

from bpy.props import ( BoolProperty, EnumProperty, FloatProperty, PointerProperty )
from bpy.types import ( PropertyGroup )


def rodrigues_from_pose(armature, bone_name):
    # Ensure that rotation mode is AXIS_ANGLE so the we get a correct readout of current pose
    armature.pose.bones[bone_name].rotation_mode = 'AXIS_ANGLE'
    axis_angle = armature.pose.bones[bone_name].rotation_axis_angle

    angle = axis_angle[0]

    rodrigues = Vector((axis_angle[1], axis_angle[2], axis_angle[3]))
    rodrigues.normalize()
    rodrigues = rodrigues * angle
    return rodrigues

# Called whenenver one of the FLAME pose sliders is moved
def update_pose(self, context):
    obj = context.object
    if (obj.type == 'ARMATURE'):
        armature = obj
    else:
        armature = obj.parent

    # Change rotation mode from AXIS_ANGLE to XYZ to see changes
    armature.pose.bones["neck"].rotation_mode = 'XYZ'
    armature.pose.bones["neck"].rotation_euler = (radians(self.flame_neck_pitch), radians(self.flame_neck_yaw), 0.0)

    armature.pose.bones["jaw"].rotation_mode = 'XYZ'
    armature.pose.bones["jaw"].rotation_euler = (radians(self.flame_jaw), 0.0, 0.0)

    if self.flame_corrective_poseshapes:
        # Update corrective poseshapes
        bpy.ops.object.flame_set_poseshapes('EXEC_DEFAULT')

def update_corrective_poseshapes(self, context):
    if self.flame_corrective_poseshapes:
        bpy.ops.object.flame_set_poseshapes('EXEC_DEFAULT')
    else:
        bpy.ops.object.flame_reset_poseshapes('EXEC_DEFAULT')

# Property group for UI sliders
class PG_FlameProperties(PropertyGroup):

    flame_gender: EnumProperty(
        name = "Gender",
        description = "FLAME model gender",
        items = [ ("female", "female", ""), ("generic", "generic", ""), ("male", "male", "") ]
    )

    flame_corrective_poseshapes: BoolProperty(
        name = "Corrective poseshapes",
        description = "Enable/disable corrective poseshapes of FLAME model",
        default = False,
        update = update_corrective_poseshapes
    )

    flame_neck_yaw: FloatProperty(
        name = "Set neck yaw",
        description = "Yaw rotation of FLAME neck joint",
        default = 0.0,
        min = -30,
        max = 30.0,
        update = update_pose
    )

    flame_neck_pitch: FloatProperty(
        name = "Set neck pitch",
        description = "Pitch rotation of FLAME neck joint",
        default = 0.0,
        min = -30,
        max = 30.0,
        update = update_pose
    )

    flame_jaw: FloatProperty(
        name = "Set jaw",
        description = "Pitch rotation of FLAME jaw joint",
        default = 0.0,
        min = 0,
        max = 30.0,
        update = update_pose
    )

class FlameAddGender(bpy.types.Operator):
    bl_idname = "scene.flame_add_gender"
    bl_label = "Add"
    bl_description = ("Add FLAME model of selected gender to scene")
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        gender = context.window_manager.flame_tool.flame_gender
        print("Adding gender: " + gender)

        path = os.path.dirname(os.path.realpath(__file__))
        objects_path = os.path.join(path, "data", "flame2020_%s.blend" % (gender), "Object")
        object_name = "FLAME-" + gender

        bpy.ops.wm.append(filename=object_name, directory=str(objects_path))

        # Select imported FACE mesh
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = bpy.data.objects[object_name]
        bpy.data.objects[object_name].select_set(True)

        return {'FINISHED'}


class FlameRandomShapes(bpy.types.Operator):
    bl_idname = "object.flame_random_shapes"
    bl_label = "Random shapes"
    bl_description = ("Sets all shape blend shape keys to a random value")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name.startswith("Shape"):
                key_block.value = np.random.normal(0.0, 1.0)

        bpy.ops.object.flame_update_joint_locations('EXEC_DEFAULT')

        return {'FINISHED'}

class FlameResetShapes(bpy.types.Operator):
    bl_idname = "object.flame_reset_shapes"
    bl_label = "Reset shapes"
    bl_description = ("Resets all blend shape keys for shape")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name.startswith("Shape"):
                key_block.value = 0.0

        bpy.ops.object.flame_update_joint_locations('EXEC_DEFAULT')

        return {'FINISHED'}

class FlameRandomExpressions(bpy.types.Operator):
    bl_idname = "object.flame_random_expressions"
    bl_label = "Random expressions"
    bl_description = ("Sets all expression blend shape keys to a random value")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name.startswith("Exp"):
                key_block.value = np.random.normal(0.0, 1.0)

        bpy.ops.object.flame_update_joint_locations('EXEC_DEFAULT')

        return {'FINISHED'}

class FlameResetExpressions(bpy.types.Operator):
    bl_idname = "object.flame_reset_expressions"
    bl_label = "Reset expressions"
    bl_description = ("Resets all blend shape keys for expressions")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name.startswith("Exp"):
                key_block.value = 0.0

        bpy.ops.object.flame_update_joint_locations('EXEC_DEFAULT')

        return {'FINISHED'}

class FlameUpdateJointLocations(bpy.types.Operator):
    bl_idname = "object.flame_update_joint_locations"
    bl_label = "Update joint locations"
    bl_description = ("Update joint locations after shape/expression changes")
    bl_options = {'REGISTER', 'UNDO'}

    j_regressor = None

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return ((context.object.type == 'MESH') and (context.object.parent.type == 'ARMATURE'))
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        if self.j_regressor is None:
            path = os.path.dirname(os.path.realpath(__file__))
            regressor_path = os.path.join(path, "data", "flame2020_joint_regressor.npz")
            with np.load(regressor_path) as data:
                self.j_regressor = data['joint_regressor']


        # Store current bone rotations
        armature = obj.parent

        bone_rotations = {}
        for pose_bone in armature.pose.bones:
            pose_bone.rotation_mode = 'AXIS_ANGLE'
            axis_angle = pose_bone.rotation_axis_angle
            bone_rotations[pose_bone.name] = (axis_angle[0], axis_angle[1], axis_angle[2], axis_angle[3])

        # Set model in default pose
        for bone in armature.pose.bones:
            bpy.ops.object.flame_reset_poseshapes('EXEC_DEFAULT')
            bone.rotation_mode = 'AXIS_ANGLE'
            bone.rotation_axis_angle = (0, 0, 1, 0)

        # Reset corrective poseshapes if used
        if context.window_manager.flame_tool.flame_corrective_poseshapes:
            bpy.ops.object.flame_reset_poseshapes('EXEC_DEFAULT')

        # Get vertices with applied skin modifier
        depsgraph = context.evaluated_depsgraph_get()
        object_eval = obj.evaluated_get(depsgraph)
        mesh_from_eval = object_eval.to_mesh()

        # Get Blender vertices as numpy matrix
        vertices_np = np.zeros((len(mesh_from_eval.vertices)*3), dtype=np.float)
        mesh_from_eval.vertices.foreach_get("co", vertices_np)
        vertices_matrix = np.reshape(vertices_np, (len(mesh_from_eval.vertices), 3))
        object_eval.to_mesh_clear() # Remove temporary mesh

        joint_locations = self.j_regressor @ vertices_matrix

        # Set new bone joint locations
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        for index, bone in enumerate(armature.data.edit_bones):

            if index == 0:
                continue # ignore root bone
            bone.head = (0.0, 0.0, 0.0)
            bone.tail = (0.0, 0.0, 0.01)

            bone_start = Vector(joint_locations[index])
            bone.translate(bone_start)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = obj

        # Restore pose
        for pose_bone in armature.pose.bones:
            pose_bone.rotation_mode = 'AXIS_ANGLE'
            pose_bone.rotation_axis_angle = bone_rotations[pose_bone.name]

        # Restore corrective poseshapes if used
        if context.window_manager.flame_tool.flame_corrective_poseshapes:
            bpy.ops.object.flame_set_poseshapes('EXEC_DEFAULT')

        return {'FINISHED'}

class FlameSetPoseshapes(bpy.types.Operator):
    bl_idname = "object.flame_set_poseshapes"
    bl_label = "Set poseshapes"
    bl_description = ("Sets corrective poseshapes for current pose")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object and parent is armature
            return ( ((context.object.type == 'MESH') and (context.object.parent.type == 'ARMATURE')) or (context.object.type == 'ARMATURE'))
        except: return False

    # https://github.com/gulvarol/surreal/blob/master/datageneration/main_part1.py
    # Computes rotation matrix through Rodrigues formula as in cv2.Rodrigues
    def rodrigues_to_mat(self, rotvec):
        theta = np.linalg.norm(rotvec)
        r = (rotvec/theta).reshape(3, 1) if theta > 0. else rotvec
        cost = np.cos(theta)
        mat = np.asarray([[0, -r[2], r[1]],
                        [r[2], 0, -r[0]],
                        [-r[1], r[0], 0]])
        return(cost*np.eye(3) + (1-cost)*r.dot(r.T) + np.sin(theta)*mat)

    # https://github.com/gulvarol/surreal/blob/master/datageneration/main_part1.py
    # Calculate weights of pose corrective blend shapes
    def rodrigues_to_posecorrective_weight(self, pose):
        rod_rots = np.asarray(pose).reshape(5, 3)
        mat_rots = [self.rodrigues_to_mat(rod_rot) for rod_rot in rod_rots]
        bshapes = np.concatenate([(mat_rot - np.eye(3)).ravel() for mat_rot in mat_rots[1:]])
        return(bshapes)

    def execute(self, context):
        obj = bpy.context.object

        # Get armature pose in rodrigues representation
        if obj.type == 'ARMATURE':
            armature = obj
            obj = bpy.context.object.children[0]
        else:
            armature = obj.parent

        neck = rodrigues_from_pose(armature, "neck")
        jaw = rodrigues_from_pose(armature, "jaw")

        pose = [0.0] * flame_pose_length
        pose[3] = neck[0]
        pose[4] = neck[1]
        pose[5] = neck[2]

        pose[6] = jaw[0]
        pose[7] = jaw[1]
        pose[8] = jaw[2]

        # print("Current pose: " + str(pose))

        poseweights = self.rodrigues_to_posecorrective_weight(pose)

        # Set weights for pose corrective shape keys
        for index, weight in enumerate(poseweights):
            if index >= 18:
                break
            obj.data.shape_keys.key_blocks["Pose%d" % (index+1)].value = weight

        # Set checkbox without triggering update function
        context.window_manager.flame_tool["flame_corrective_poseshapes"] = True

        return {'FINISHED'}

class FlameResetPoseshapes(bpy.types.Operator):
    bl_idname = "object.flame_reset_poseshapes"
    bl_label = "Reset poseshapes"
    bl_description = ("Resets corrective poseshapes for current pose")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object and parent is armature
            return ( ((context.object.type == 'MESH') and (context.object.parent.type == 'ARMATURE')) or (context.object.type == 'ARMATURE'))
        except: return False

    def execute(self, context):
        obj = bpy.context.object

        if obj.type == 'ARMATURE':
            obj = bpy.context.object.children[0]

#        bpy.ops.object.mode_set(mode='OBJECT')
        for key_block in obj.data.shape_keys.key_blocks:
            if key_block.name.startswith("Pose"):
                key_block.value = 0.0

        return {'FINISHED'}

class FlameWritePose(bpy.types.Operator):
    bl_idname = "object.flame_write_pose"
    bl_label = "Write pose"
    bl_description = ("Writes flame pose to Blender console window")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        armature = obj.parent

        # Get armature pose in rodrigues representation
        armature = obj.parent
        neck = rodrigues_from_pose(armature, "neck")
        jaw = rodrigues_from_pose(armature, "jaw")
        left_eye = rodrigues_from_pose(armature, "left_eye")
        right_eye = rodrigues_from_pose(armature, "right_eye")

        pose = [0.0] * flame_pose_length
        pose[3] = neck[0]
        pose[4] = neck[1]
        pose[5] = neck[2]

        pose[6] = jaw[0]
        pose[7] = jaw[1]
        pose[8] = jaw[2]

        pose[9] = left_eye[0]
        pose[10] = left_eye[1]
        pose[11] = left_eye[2]

        pose[12] = right_eye[0]
        pose[13] = right_eye[1]
        pose[14] = right_eye[2]

        print("pose = " + str(pose))

        return {'FINISHED'}

class FlameResetPose(bpy.types.Operator):
    bl_idname = "object.flame_reset_pose"
    bl_label = "Reset pose"
    bl_description = ("Resets pose to default zero pose")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object
        armature = obj.parent

        for bone in armature.pose.bones:
            bone.rotation_mode = 'AXIS_ANGLE'
            bone.rotation_axis_angle = (0, 0, 1, 0)

        # Reset sliders without updating pose
        context.window_manager.flame_tool["flame_neck_yaw"] = 0.0
        context.window_manager.flame_tool["flame_neck_pitch"] = 0.0
        context.window_manager.flame_tool["flame_jaw"] = 0.0

        # Reset corrective pose shapes
        bpy.ops.object.flame_reset_poseshapes('EXEC_DEFAULT')

        return {'FINISHED'}

class FlameCloseMesh(bpy.types.Operator):
    bl_idname = "object.flame_close_mesh"
    bl_label = "Close mesh"
    bl_description = ("Closes all open holes in the FLAME mesh")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object

        # Get a bmesh representation
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        if len(bm.faces) > flame_default_faces:
            print("FLAME: Holes are already filled")
        else:
            bm.verts.ensure_lookup_table()

            for (i0, i1, i2) in flame_hole_faces:
                bm.faces.new((bm.verts[i0-1], bm.verts[i1-1], bm.verts[i2-1]))

        # Write the modified bmesh back to the mesh
        bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)

        bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}

class FlameRestoreMesh(bpy.types.Operator):
    bl_idname = "object.flame_restore_mesh"
    bl_label = "Restore mesh"
    bl_description = ("Restores all open holes in the FLAME mesh")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            # Enable button only if mesh is active object
            return context.object.type == 'MESH'
        except: return False

    def execute(self, context):
        obj = bpy.context.object

        # Get a bmesh representation
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        if len(bm.faces) == flame_default_faces:
            print("FLAME: Mesh already restored to default state")
        else:
            bm.faces.ensure_lookup_table()

            faces_delete = bm.faces[flame_default_faces:]
            bmesh.ops.delete(bm, geom=faces_delete, context='FACES') # EDGES_FACES

        # Write the modified bmesh back to the mesh
        bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)

        bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}

class FLAME_PT_Tools(bpy.types.Panel):
    bl_label = "FLAME"
    bl_category = "FLAME"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    flame_neck_yaw: FloatProperty(
        name = "Neck Yaw",
        description = "Yaw rotation of FLAME neck joint",
        default = 0.0,
        min = -30,
        max = 30.0,
        update = update_pose
    )

    flame_neck_pitch: FloatProperty(
        name = "Neck Pitch",
        description = "Pitch rotation of FLAME neck joint",
        default = 0.0,
        min = -30,
        max = 30.0,
        update = update_pose
    )

    def draw(self, context):

        try:
            ob = context.object
            mode = ob.mode
            name = ob.name
        except:
            ob = None
            mode = None
            name = ''

        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("ed.undo", icon='LOOP_BACK')
        row.operator("ed.redo", icon='LOOP_FORWARDS')
        col.separator()

        row = col.row(align=True)
        col.prop(context.window_manager.flame_tool, "flame_gender")
        col.operator("scene.flame_add_gender", text="Add to scene")
        col.separator()
        col.separator()

        col.label(text="Blend Shapes:")
        row = col.row(align=True)
        split = row.split(factor=0.75, align=True)
        split.operator("object.flame_random_shapes", text="Random head shape")
        split.operator("object.flame_reset_shapes", text="Reset")
        col.separator()
        row = col.row(align=True)
        split = row.split(factor=0.75, align=True)
        split.operator("object.flame_random_expressions", text="Random facial expression")
        split.operator("object.flame_reset_expressions", text="Reset")
        col.separator()

        col.label(text="Joints:")
        col.operator("object.flame_update_joint_locations", text="Update joint locations")
        col.separator()

        col.label(text="Pose:")
        col.prop(context.window_manager.flame_tool, "flame_corrective_poseshapes")
        col.separator()
        col.operator("object.flame_set_poseshapes", text="Set poseshapes for current pose")
        col.separator()
        col.separator()
        col.prop(context.window_manager.flame_tool, "flame_neck_yaw", slider=True)
        col.prop(context.window_manager.flame_tool, "flame_neck_pitch", slider=True)
        col.prop(context.window_manager.flame_tool, "flame_jaw", slider=True)
        row = col.row(align=True)
        split = row.split(factor=0.75, align=True)
        split.operator("object.flame_write_pose", text="Write pose to console")
        split.operator("object.flame_reset_pose", text="Reset")
        col.separator()

        col.label(text="Misc Tools:")
        row = col.row(align=True)
        row.operator("object.flame_close_mesh", text="Close mesh")
        row.operator("object.flame_restore_mesh", text="Open mesh")
        col.separator()
        export_button = col.operator("export_scene.obj", text="Export OBJ [mm]", icon='EXPORT')
        export_button.global_scale = 1000.0
        export_button.use_selection = True
        col.separator()
        (year, month, day) = bl_info["version"]
        col.label(text="Version: %s-%s-%s" % (year, month, day))

classes = [
    PG_FlameProperties,
    FlameAddGender,
    FlameRandomShapes,
    FlameResetShapes,
    FlameRandomExpressions,
    FlameResetExpressions,
    FlameUpdateJointLocations,
    FlameSetPoseshapes,
    FlameResetPoseshapes,
    FlameWritePose,
    FlameResetPose,
    FlameCloseMesh,
    FlameRestoreMesh,
    FLAME_PT_Tools
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        bpy.utils.register_class(cls)

    # Store properties under WindowManager (not Scene) so that they are not saved in .blend files and always show default values after loading
    bpy.types.WindowManager.flame_tool = PointerProperty(type=PG_FlameProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.flame_tool

if __name__ == "__main__":
    register()
