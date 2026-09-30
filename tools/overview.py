"""6개 제품의 조립(1)·분해(60) 프레임을 한 장으로: 행 = 제품, 열 = 1 | 60. 절반 크기."""
import os, bpy, numpy as np
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
codes = ["sb300", "quad", "nvg", "ugs", "k2c1", "nu40"]
rows = []
for c in codes:
    row = []
    for f in (1, 60):
        im = bpy.data.images.load(os.path.join(d, f"{c}_armory", f"frame_{f:02d}.png"))
        im.scale(im.size[0] // 2, im.size[1] // 2)
        w, h = im.size
        row.append(np.array(im.pixels[:]).reshape(h, w, 4))
    rows.append(np.concatenate(row, 1))
sheet = np.concatenate(rows[::-1], 0)  # 픽셀은 아래부터 → 첫 제품이 맨 위
H, W = sheet.shape[:2]
out = bpy.data.images.new("overview", W, H, alpha=True)
out.pixels[:] = sheet.ravel()
out.filepath_raw = os.path.join(d, "overview.png")
out.file_format = "PNG"
out.save()
