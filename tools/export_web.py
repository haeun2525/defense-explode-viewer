"""out/<code>_armory/*.blend → web/models/<code>.js (glb 를 base64 로 담은 일반 스크립트).

실행: Blender -b --python tools/export_web.py -- sb300 quad nvg ugs k2c1 nu40
file:// 로 열리게 fetch 없이 <script> 로 싣는다. 좌표는 JS 에서 Blender(Z-up) → three(Y-up) 로 바꾼다.
각 부품 extras: explode_dir / explode_dist / explode_order / label_ko (+ sb300 날개: fold_pivot / fold_angle)
"""
import base64
import json
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
codes = sys.argv[sys.argv.index("--") + 1:]
os.makedirs(os.path.join(ROOT, "web", "models"), exist_ok=True)

# sb300 날개 접힘: Blender Z축 회전. products/sb300.py 의 fold_drivers 와 같은 규칙.
SB300_FOLD = {  # 이름 끝 → (피벗 x, 접힌 각도 부호: 주날개 +side, 꼬리 -side)
    "wing_left": (0.060, +1), "wing_right": (0.060, -1),
    "tail_left": (-0.120, -1), "tail_right": (-0.120, +1),
}

for code in codes:
    path = os.path.join(ROOT, "out", f"{code}_armory", f"{code}_armory.blend")
    bpy.ops.wm.open_mainfile(filepath=path)
    sc = bpy.context.scene
    root = bpy.data.objects[f"{code}_root"]
    root.animation_data_clear()                     # 키프레임 대신 JS 가 움직인다
    root["explode_factor"] = 0.0
    if "wing_deploy" in root:
        root["wing_deploy"] = 1.0                   # 펼친 모습이 기준 자세, 접힘은 JS 에서
    if "stock_extend" in root:
        root["stock_extend"] = 1.0
    sc.frame_set(1)
    bpy.context.view_layer.update()

    parts = [o for o in root.children]
    for o in parts:
        for key, (px, sign) in SB300_FOLD.items():
            if code == "sb300" and o.name.endswith(key):
                o["fold_pivot"] = (px, 0.0, 0.0)
                o["fold_angle"] = sign * math.pi / 2

    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    for o in parts:
        o.select_set(True)
    glb = os.path.join(ROOT, "out", f"{code}_armory", f"{code}.glb")
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True,
                              export_apply=True, export_extras=True, export_animations=False,
                              export_cameras=False, export_lights=False, export_yup=True)

    cam = sc.camera
    fwd = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    hfov = 2 * math.atan(18.0 / cam.data.lens)
    meta = {
        "code": code,
        "stagger": root["explode_stagger"], "window": root["explode_window"],
        "cam": {"pos": list(cam.location), "fwd": list(fwd),
                "vfov": math.degrees(2 * math.atan(math.tan(hfov / 2) * 9 / 16))},
        "parts": len(parts),
    }
    with open(glb, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    js = os.path.join(ROOT, "web", "models", f"{code}.js")
    with open(js, "w") as f:
        f.write("window.MODELS = window.MODELS || {};\n")
        f.write(f"window.MODELS[{json.dumps(code)}] = {{meta: {json.dumps(meta)}, glb: \"{b64}\"}};\n")
    print("EXPORT", code, len(parts), "parts", round(os.path.getsize(js) / 1024), "KB")
