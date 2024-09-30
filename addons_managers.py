import bpy
import addon_utils
import os

bl_info = {
    "name": "Advanced Addon Manager",
    "author": "eiku_jaime",
    "version": (1, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Addon Manager",
    "description": "Gestiona addons: habilitar, deshabilitar, desinstalar e instalar nuevos.",
    "category": "Development",
}

class AddonItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Nombre del Addon")
    is_enabled: bpy.props.BoolProperty(name="Habilitado")

class VIEW3D_PT_addon_manager(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Addon Manager"
    bl_label = "Gestión de Addons"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.operator("addon_manager.refresh_list", text="Actualizar Lista", icon='FILE_REFRESH')
        row.operator("addon_manager.install_addon", text="Instalar Addon", icon='IMPORT')

        layout.template_list("ADDON_UL_list", "", scene, "addon_list", scene, "addon_list_index")

        if len(scene.addon_list) > 0 and scene.addon_list_index >= 0:
            item = scene.addon_list[scene.addon_list_index]
            row = layout.row()
            row.prop(item, "is_enabled", text="Habilitado")
            row.operator("addon_manager.toggle_addon", text="Aplicar Cambios", icon='CHECKMARK')
            layout.operator("addon_manager.remove_addon", text="Eliminar Addon", icon='TRASH')

class ADDON_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name)
            layout.prop(item, "is_enabled", text="")

class ADDON_OT_refresh_list(bpy.types.Operator):
    bl_idname = "addon_manager.refresh_list"
    bl_label = "Actualizar Lista de Addons"
    bl_description = "Actualiza la lista de addons instalados"

    def execute(self, context):
        scene = context.scene
        scene.addon_list.clear()

        for mod in addon_utils.modules():
            item = scene.addon_list.add()
            item.name = mod.__name__
            item.is_enabled = addon_utils.check(mod.__name__)[0]

        return {'FINISHED'}

class ADDON_OT_install_addon(bpy.types.Operator):
    bl_idname = "addon_manager.install_addon"
    bl_label = "Instalar Addon"
    bl_description = "Instala un nuevo addon desde un archivo .py o .zip"
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        try:
            bpy.ops.preferences.addon_install(filepath=self.filepath)
            bpy.ops.addon_manager.refresh_list()
            self.report({'INFO'}, "Addon instalado correctamente")
        except Exception as e:
            self.report({'ERROR'}, f"Error instalando addon: {e}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ADDON_OT_remove_addon(bpy.types.Operator):
    bl_idname = "addon_manager.remove_addon"
    bl_label = "Eliminar Addon"
    bl_description = "Elimina el addon seleccionado"
    
    def execute(self, context):
        scene = context.scene
        if len(scene.addon_list) > 0 and scene.addon_list_index >= 0:
            addon_name = scene.addon_list[scene.addon_list_index].name
            try:
                addon_utils.disable(addon_name)
                bpy.ops.preferences.addon_remove(module=addon_name)
                bpy.ops.addon_manager.refresh_list()
                self.report({'INFO'}, f"Addon '{addon_name}' eliminado correctamente")
            except Exception as e:
                self.report({'ERROR'}, f"Error eliminando addon: {e}")
        else:
            self.report({'WARNING'}, "No hay addon seleccionado")
        return {'FINISHED'}

class ADDON_OT_toggle_addon(bpy.types.Operator):
    bl_idname = "addon_manager.toggle_addon"
    bl_label = "Aplicar Cambios al Addon"
    bl_description = "Habilita o deshabilita el addon seleccionado"

    def execute(self, context):
        scene = context.scene
        if len(scene.addon_list) > 0 and scene.addon_list_index >= 0:
            item = scene.addon_list[scene.addon_list_index]
            try:
                if item.is_enabled:
                    addon_utils.enable(item.name, default_set=True)
                    self.report({'INFO'}, f"Addon '{item.name}' habilitado")
                else:
                    addon_utils.disable(item.name)
                    self.report({'INFO'}, f"Addon '{item.name}' deshabilitado")
            except Exception as e:
                self.report({'ERROR'}, f"Error al cambiar el estado del addon: {e}")
        else:
            self.report({'WARNING'}, "No hay addon seleccionado")
        return {'FINISHED'}

classes = (
    AddonItem,
    VIEW3D_PT_addon_manager,
    ADDON_UL_list,
    ADDON_OT_refresh_list,
    ADDON_OT_install_addon,
    ADDON_OT_remove_addon,
    ADDON_OT_toggle_addon,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.addon_list = bpy.props.CollectionProperty(type=AddonItem)
    bpy.types.Scene.addon_list_index = bpy.props.IntProperty()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.addon_list
    del bpy.types.Scene.addon_list_index

if __name__ == "__main__":
    register()

# Función para actualizar la lista de addons
def update_addon_list(dummy):
    bpy.ops.addon_manager.refresh_list()

# Registrar la función de actualización para que se ejecute después de que Blender haya cargado completamente
bpy.app.timers.register(update_addon_list, first_interval=1.0)