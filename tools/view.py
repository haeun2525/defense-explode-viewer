"""GUI 로 .blend 를 열고 카메라 시점 + Rendered 미리보기로 바꾼다.
실행: Blender out/<code>/<code>.blend --python tools/view.py"""
import bpy


def apply():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                sp = area.spaces[0]
                sp.shading.type = 'RENDERED'
                sp.region_3d.view_perspective = 'CAMERA'
                sp.overlay.show_overlays = False
    return None


bpy.app.timers.register(apply, first_interval=1.0)
