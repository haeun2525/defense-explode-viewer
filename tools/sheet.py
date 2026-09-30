"""out/<code>/frame_*.png 4장을 2x2 로 묶어 sheet.png. 실행: Blender -b --python tools/sheet.py -- <code>"""
import os, sys
import bpy, numpy as np
code = sys.argv[sys.argv.index("--") + 1]
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", code)
ims = [bpy.data.images.load(os.path.join(d, f"frame_{f:02d}.png")) for f in (1, 20, 40, 60)]
w, h = ims[0].size
px = [np.array(i.pixels[:]).reshape(h, w, 4) for i in ims]
sheet = np.concatenate([np.concatenate([px[2], px[3]], 1), np.concatenate([px[0], px[1]], 1)], 0)  # 픽셀은 아래부터
out = bpy.data.images.new("sheet", 2 * w, 2 * h, alpha=True)
out.pixels[:] = sheet.ravel()
out.filepath_raw = os.path.join(d, "sheet.png")
out.file_format = "PNG"
out.save()
