import bpy
import math
import bmesh
from bpy.props import IntProperty, CollectionProperty, FloatVectorProperty
from bpy.types import Panel, UIList

image = None

class ColorList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(0.2)
        split.label(str(item.id))
        split.prop(item, "c", text="")

class PalettePanel(Panel):
    """Creates a Panel in the Object properties window"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "Palette"
    bl_idname = "OBJECT_FC_PALETTE"
    bl_context = "mesh_edit"
    bl_category = "Palette"

    def draw(self, context):
        layout = self.layout
        ob = context.object
        layout.operator("mesh.add_color", text="Add Color")
        layout.template_list("ColorList", "", ob, "palette", ob, "palette_selection")
        layout.operator("mesh.set_color", text="Set Color")

def color_update(self, context):
    draw_palette([self.id])

class PaletteColor(bpy.types.PropertyGroup):
    id = IntProperty()
    c = FloatVectorProperty(subtype='COLOR', default=[1.0,1.0,1.0], min=0.0, max=1.0, update=color_update)

class AddColorToPalette(bpy.types.Operator):
    bl_idname = "mesh.add_color"
    bl_label = "Add Color To Palette"
    bl_options = {"UNDO"}
    
    def invoke(self, context, event):
        ob = bpy.context.object
        item = ob.palette.add()
        item.id = len(ob.palette) - 1
        draw_palette([item.id])
        ob.palette_selection = item.id
        position_all_uv()
        return {"FINISHED"}

class SetFaceColor(bpy.types.Operator):
    bl_idname = "mesh.set_color"
    bl_label = "Set Face Color"
    bl_options = {"UNDO"}
    
    def invoke(self, context, event):
        position_selected_uv()
        return {"FINISHED"}

def draw_palette(update = []):
    global image
    if image is None:
        image = bpy.data.images.new('imagename',3,3)
        #bpy.context.object.data.uv_textures.new("uv")
        
    palette_list = [(p.id, p.c) for p in bpy.context.object.palette]
    amount = len(palette_list)
    
    if update == []:
        update = range(amount)
    
    x_size = 3 * amount
    y_size = 3
    
    image.generated_width = x_size
    image.generated_height = y_size
    
    for entry in palette_list:
        id = entry[0]
        color = entry[1]
        r = color.r
        g = color.g
        b = color.b
        a = 1.0
        pixel = 0  
          
        for y in range(3):
            pixel = (3 * id + (x_size * y)) * 4
            for x in range(3):
                image.pixels[pixel:pixel+4] = [r,g,b,a]
                pixel = pixel + 4

        
def position_selected_uv():
    global image
    selected_faces = []
    pal_i = bpy.context.object.palette_selection
    amount = len(bpy.context.object.palette)
    x_offset = 1 / amount / 2
    objdata = bpy.context.object.data
    bm = bmesh.from_edit_mesh(objdata)
    
    # Guarantee existing UV map and layer
    if len(objdata.uv_textures) == 0:
        bpy.context.object.data.uv_textures.new("uv")
    
    if len(objdata.uv_layers) == 0:
        bpy.context.object.data.uv_layer.new("uv")
    
    uv_layer = bm.loops.layers.uv[0]
    
    # Find selected faces
    for i, face in enumerate(bm.faces):
        if face.select:
            selected_faces.append(i)
    
    # Set UV image to be palette image
    bpy.ops.object.editmode_toggle()      
    for i in selected_faces:
        objdata.uv_textures[0].data[i].image = image
    bpy.ops.object.editmode_toggle()  
    
    # Place UV coords
    bm = bmesh.from_edit_mesh(objdata)
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv[0]
    for i in selected_faces:
        bpy.context.object.face_map[i] = pal_i
        print(bpy.context.object.face_map)
        for v in bm.faces[i].loops:
            v[uv_layer].uv = ((pal_i / amount) + x_offset, .5)

def position_all_uv():
    # Guarantee existing UV map and layer
    objdata = bpy.context.object.data
    if len(objdata.uv_textures) == 0:
        bpy.context.object.data.uv_textures.new("uv")
    
    if len(objdata.uv_layers) == 0:
        bpy.context.object.data.uv_layer.new("uv")
    
    obj = bpy.context.object
    amount = len(obj.palette)
    x_offset = 1 / amount / 2
    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv[0]
    
    for k,v in obj.face_map.items():
        for ve in bm.faces[k].loops:
            ve[uv_layer].uv = ((v / amount) + x_offset, .5) 

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Object.palette = CollectionProperty(type=PaletteColor)
    bpy.types.Object.palette_selection = IntProperty()
    bpy.types.Object.face_map = {}
    #bpy.utils.register_class(AddColorToPalette)

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Object.palette

if __name__ == "__main__":
    register()
    
    ob = bpy.context.object
    ob.palette.clear()
    
