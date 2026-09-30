"""분해 애니메이션 공통 도구.

좌표 규칙: +X 전방, +Y 좌측, +Z 위. 단위 m. 원점 = 제품 중심.
폭발은 delta_location 드라이버로 움직이므로 location 은 자유롭게 손댈 수 있다.
  delta = explode_dir * explode_dist * smoothstep(s, s + w, explode_factor)
  s = (explode_order - 1) * explode_stagger,  w = explode_window   (root 프로퍼티)
"""
import math
import bmesh
import bpy
from mathutils import Matrix, Vector

WINDOW = 0.4  # 부품 하나가 움직이는 구간 (explode_factor 기준)


# ---------- 씬 ----------

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 1, 60
    return sc


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h):
    h = h.lstrip('#')
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)


# ---------- 재질 ----------

def _bsdf(m):
    m.use_nodes = True
    return m.node_tree.nodes["Principled BSDF"]


def make_material(code, name, hex_color, roughness=0.6, metallic=0.0, coat=0.0, specular=0.5):
    m = bpy.data.materials.new(f"mat_{code}_{name}")
    b = _bsdf(m)
    b.inputs["Base Color"].default_value = hex_rgba(hex_color)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Specular IOR Level"].default_value = specular
    b.inputs["Coat Roughness"].default_value = 0.08
    m.diffuse_color = hex_rgba(hex_color)
    _edge_wear(m, b, metallic)
    return m


def _edge_wear(m, b, metallic):
    """모서리를 살짝 밝히고 표면에 미세 요철 — 프리미티브가 '플라스틱 덩어리'로 안 보이게."""
    nt = m.node_tree
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 900.0
    n.inputs["Detail"].default_value = 4.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    # 거칠기에 얼룩
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 60.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    base_r = b.inputs["Roughness"].default_value
    mr.inputs["To Min"].default_value = base_r * 0.8
    mr.inputs["To Max"].default_value = min(1.0, base_r * 1.25)
    nt.links.new(n2.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])


def make_carbon(code, name="carbon", tint="#161719", scale=140.0):
    """카본 직조: 두 방향 띠를 체커로 번갈아 → 색·거칠기·요철. 위에 클리어코트."""
    m = bpy.data.materials.new(f"mat_{code}_{name}")
    b = _bsdf(m)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    chk = nt.nodes.new("ShaderNodeTexChecker")
    chk.inputs["Scale"].default_value = 1.0
    nt.links.new(mp.outputs["Vector"], chk.inputs["Vector"])
    wx = nt.nodes.new("ShaderNodeTexWave")
    wx.bands_direction = 'X'
    wy = nt.nodes.new("ShaderNodeTexWave")
    wy.bands_direction = 'Y'
    for w in (wx, wy):
        w.inputs["Scale"].default_value = 3.0
        w.inputs["Distortion"].default_value = 0.0
        nt.links.new(mp.outputs["Vector"], w.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'FLOAT'
    nt.links.new(chk.outputs["Fac"], mix.inputs["Factor"])
    nt.links.new(wx.outputs["Fac"], mix.inputs["A"])
    nt.links.new(wy.outputs["Fac"], mix.inputs["B"])
    weave = mix.outputs["Result"]

    col = nt.nodes.new("ShaderNodeMix")
    col.data_type = 'RGBA'
    col.inputs["A"].default_value = hex_rgba("#0B0C0D")
    col.inputs["B"].default_value = hex_rgba(tint)
    nt.links.new(weave, col.inputs["Factor"])
    nt.links.new(col.outputs["Result"], b.inputs["Base Color"])

    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.62
    rr.inputs["To Max"].default_value = 0.45
    nt.links.new(weave, rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Anisotropic"].default_value = 0.2

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    bump.inputs["Distance"].default_value = 0.0003
    nt.links.new(weave, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])

    b.inputs["Coat Weight"].default_value = 0.12  # 높이면 주변이 다 비쳐 은색 크롬처럼 보인다
    b.inputs["Coat Roughness"].default_value = 0.18
    b.inputs["Coat IOR"].default_value = 1.5
    m.diffuse_color = hex_rgba(tint)
    return m


def make_glass(code, name="glass", tint="#DDE6EE", roughness=0.03):
    m = bpy.data.materials.new(f"mat_{code}_{name}")
    b = _bsdf(m)
    b.inputs["Base Color"].default_value = hex_rgba(tint)
    b.inputs["IOR"].default_value = 1.45
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = roughness
    m.diffuse_color = hex_rgba(tint)[:3] + (0.3,)
    m.surface_render_method = 'DITHERED'  # EEVEE 뷰포트에서도 비쳐 보이게
    return m


def _emissive(m, hex_color, strength):
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = hex_rgba(hex_color)
    b.inputs["Emission Strength"].default_value = strength
    return m


def standard_materials(code, which=("olive", "black", "gunmetal", "glass")):
    spec = {
        "olive": lambda: make_material(code, "olive", "#2A2F0C", 0.85, specular=0.15),  # #4B5320 은 병기고 조명에서 연두로 뜬다 → 눌러서 화면에 #4B5320 근처로,
        "black": lambda: make_material(code, "black", "#0C0C0D", 0.55, specular=0.25),  # #1C1C1C 는 병기고 조명에서 배경 회색과 같아진다
        "gunmetal": lambda: make_material(code, "gunmetal", "#2A2D34", 0.55, 0.75),
        "glass": lambda: make_glass(code),
        "carbon": lambda: make_carbon(code),
        # 내부 전자부품용 — 이름 끝(_pcb, _gold …)으로 웹 뷰어가 재질을 고른다 (web/index.html MAT 와 같은 키)
        "pcb": lambda: make_material(code, "pcb", "#0B4A26", 0.4, coat=0.35, specular=0.4),       # 녹색 솔더마스크
        "metal": lambda: make_material(code, "metal", "#B8BCC2", 0.28, 1.0),                     # 은색 금속(차폐캔·나사)
        "gold": lambda: make_material(code, "gold", "#C9A34A", 0.25, 1.0),                       # 금도금 핀·패드
        "copper": lambda: make_material(code, "copper", "#B06A3B", 0.3, 1.0),                    # 코일·권선
        "ceramic": lambda: make_material(code, "ceramic", "#D9D2BE", 0.5, specular=0.3),         # 칩 부품·안테나
        "cell": lambda: make_material(code, "cell", "#1F4E79", 0.45, coat=0.3, specular=0.4),    # 배터리 셀 비닐
        "phosphor": lambda: make_material(code, "phosphor", "#3FA34D", 0.35, specular=0.4),      # 형광 스크린·표시부
        "led": lambda: _emissive(make_material(code, "led", "#FF3B30", 0.3, specular=0.4), "#FF2A1F", 3.0),  # 빨간 LED (스스로 빛남)
    }
    return {k: spec[k]() for k in which}


# ---------- 메시 (전부 bmesh 로 만들고 변환을 메시에 굽는다) ----------

def rot(axis_from_z):
    """Z축 기본 프리미티브를 X/Y/Z 축으로 눕히는 행렬."""
    return {
        'X': Matrix.Rotation(math.radians(90), 4, 'Y'),
        'Y': Matrix.Rotation(math.radians(-90), 4, 'X'),
        'Z': Matrix.Identity(4),
    }[axis_from_z]


def bm_box(bm, size, matrix=Matrix.Identity(4)):
    sx, sy, sz = size
    return bmesh.ops.create_cube(bm, size=1.0, matrix=matrix @ Matrix.Diagonal((sx, sy, sz, 1)))["verts"]


def bm_cyl(bm, r1, r2, depth, axis='Z', matrix=Matrix.Identity(4), segs=32, caps=True):
    return bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=segs,
                                 radius1=r1, radius2=r2, depth=depth,
                                 matrix=matrix @ rot(axis))["verts"]


def bm_hemisphere(bm, r, axis='X', matrix=Matrix.Identity(4), segs=32):
    tmp = bmesh.new()
    bmesh.ops.create_uvsphere(tmp, u_segments=segs, v_segments=segs // 2, radius=r)
    bmesh.ops.delete(tmp, geom=[v for v in tmp.verts if v.co.z < -1e-6], context='VERTS')
    bmesh.ops.holes_fill(tmp, edges=[e for e in tmp.edges if e.is_boundary])
    bmesh.ops.transform(tmp, matrix=matrix @ rot(axis), verts=tmp.verts)
    me = bpy.data.meshes.new("tmp")
    tmp.to_mesh(me)
    tmp.free()
    before = set(bm.verts)
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return [v for v in bm.verts if v not in before]


def bm_pcb(bm, size, matrix=Matrix.Identity(4), chips=(), mats=(0, 1, 2, 3)):
    """기판 한 장 + 올린 부품. size=(가로 x, 세로 y, 두께 z), 기판 중심이 원점이고 부품면은 +z.
    matrix 로 기판째 옮기거나 세운다 (예: T(c) @ rot('X')).
    chips: (x, y, w, h, 높이, 종류[, 이름, 설명]) — 이름을 주면 뷰어의 부품 보기에서 칩 이름표가 뜬다.
      종류  'qfp'    검정 몸통 + 네 변 금속 핀 (MCU·큰 칩)       'ic'   검정 몸통 + 두 변 핀 (SOIC: 메모리·드라이버)
            'qfn'    얇은 검정 몸통 + 옆면 패드 + 1번 핀 점      'bga'  기판색 받침 위 검정 칩 (프로세서·AI 칩)
            'sot'    작은 검정 + 다리 3개 (트랜지스터·레귤레이터) 'crystal' 금속 타원 캔 (발진기)
            'cap'    원통 전해 커패시터 (금속 윗면)             'passive'  세라믹 칩부품 + 양끝 금속 전극
            'inductor' 짙은 정사각 코일                         'can'  금속 차폐캔 (무선 모듈)
            'conn'   검정 커넥터 + 윗면 금 핀줄                 'block' 검정 덩어리 (모듈)
    mats = (기판, 검정, 금속·금, 세라믹) 의 material_index.
    돌려주는 값: 이름 있는 칩들의 [(이름, 설명, 윗면 중심 좌표(bm 좌표))] → attach_chips 로 부품에 붙인다."""
    pcb_i, black_i, metal_i, cer_i = mats
    t = size[2]
    T = Matrix.Translation
    top0 = t / 2
    set_mat(bm_box(bm, size, matrix), pcb_i)
    info = []

    def box(sz, c, idx):
        set_mat(bm_box(bm, sz, matrix @ T(c)), idx)

    for chip in chips:
        x, y, w, h, z, kind = chip[:6]
        mid = top0 + z / 2
        if kind == 'qfp' or kind == 'ic':
            box((w, h, z), (x, y, mid), black_i)
            sides = ((1, 0), (-1, 0), (0, 1), (0, -1)) if kind == 'qfp' else ((0, 1), (0, -1))
            for sx, sy in sides:
                length = h if sx else w
                n = max(2, int(length / 0.0008))
                for i in range(n):
                    p = -length / 2 + (i + 0.5) * length / n
                    if sx:
                        box((0.0009, length / n * 0.45, 0.0004), (x + sx * (w / 2 + 0.0004), y + p, top0 + 0.0002), metal_i)
                    else:
                        box((length / n * 0.45, 0.0009, 0.0004), (x + p, y + sy * (h / 2 + 0.0004), top0 + 0.0002), metal_i)
            box((min(w, h) * 0.08,) * 2 + (0.0001,), (x - w / 2 + min(w, h) * 0.15, y + h / 2 - min(w, h) * 0.15, top0 + z + 0.00005), metal_i)
        elif kind == 'qfn':
            box((w, h, z), (x, y, mid), black_i)
            for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                length = h if sx else w
                n = max(2, int(length / 0.0006))
                for i in range(n):
                    p = -length / 2 + (i + 0.5) * length / n
                    c = (x + sx * w / 2, y + p, top0 + z * 0.25) if sx else (x + p, y + sy * h / 2, top0 + z * 0.25)
                    box((0.00025, length / n * 0.5, z * 0.5) if sx else (length / n * 0.5, 0.00025, z * 0.5), c, metal_i)
            box((min(w, h) * 0.1,) * 2 + (0.0001,), (x - w / 2 + min(w, h) * 0.18, y + h / 2 - min(w, h) * 0.18, top0 + z + 0.00005), metal_i)
        elif kind == 'bga':
            box((w * 1.12, h * 1.12, 0.0006), (x, y, top0 + 0.0003), pcb_i)
            box((w, h, z - 0.0006), (x, y, top0 + 0.0006 + (z - 0.0006) / 2), black_i)
        elif kind == 'sot':
            box((w, h, z), (x, y, top0 + 0.0002 + z / 2), black_i)
            for (dx, dy) in ((-w * 0.3, -1), (w * 0.3, -1), (0, 1)):
                box((w * 0.18, 0.0008, 0.0003), (x + dx, y + dy * (h / 2 + 0.0003), top0 + 0.00015), metal_i)
        elif kind == 'crystal':
            set_mat(bm_cyl(bm, h / 2, h / 2, z, 'Z', matrix @ T((x, y, mid)) @ Matrix.Diagonal((w / h, 1, 1, 1)), segs=20), metal_i)
        elif kind == 'cap':
            r = min(w, h) / 2
            set_mat(bm_cyl(bm, r, r, z * 0.92, 'Z', matrix @ T((x, y, top0 + z * 0.46)), segs=20), black_i)
            set_mat(bm_cyl(bm, r * 0.96, r * 0.96, z * 0.08, 'Z', matrix @ T((x, y, top0 + z * 0.96)), segs=20), metal_i)
        elif kind == 'passive':
            box((w * 0.6, h, z), (x, y, mid), cer_i)
            for sx in (1, -1):
                box((w * 0.2, h, z), (x + sx * w * 0.4, y, mid), metal_i)
        elif kind == 'inductor':
            box((w, h, z), (x, y, mid), black_i)
            box((w * 0.7, h * 0.7, 0.0001), (x, y, top0 + z + 0.00005), metal_i)
        elif kind == 'conn':
            box((w, h, z), (x, y, mid), black_i)
            n = max(2, int(w / 0.0013))
            for i in range(n):
                box((0.0005, 0.0005, 0.0003), (x - w / 2 + (i + 0.5) * w / n, y, top0 + z + 0.00015), metal_i)
        elif kind == 'can':
            box((w, h, z), (x, y, mid), metal_i)
        else:  # 'block'
            box((w, h, z), (x, y, mid), black_i)
        if len(chip) > 6 and chip[6]:
            info.append((chip[6], chip[7] if len(chip) > 7 else "", tuple(matrix @ Vector((x, y, top0 + z)))))
    return info


def attach_chips(ob, info):
    """bm_pcb 가 돌려준 칩 목록을 부품 좌표로 바꿔 ob["chips"] 에 JSON 으로 담는다 (glTF extras → 뷰어).
    part_object 가 메시를 가운데로 옮기고 그만큼 location 을 줬으니, 부품 좌표 = bm 좌표 − location."""
    import json
    prev = json.loads(ob.get("chips", "[]"))
    for name, desc, pos in info:
        local = Vector(pos) - ob.location
        prev.append({"name": name, "desc": desc, "pos": [round(c, 5) for c in local]})
    ob["chips"] = json.dumps(prev, ensure_ascii=False)


def set_mat(verts, idx):
    """방금 만든 도형(verts)의 면에 재질 슬롯 번호를 준다."""
    vs = set(verts)
    for v in vs:
        for f in v.link_faces:
            if all(fv in vs for fv in f.verts):
                f.material_index = idx


def part_object(name, bm, material, coll, root, bevel=0.0015, segments=3, smooth=True):
    """bmesh → 오브젝트. origin 을 바운딩박스 중심으로 옮기고 root 자식으로 건다.
    material 은 하나 또는 리스트(면의 material_index 순서)."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    xs = [v.co for v in me.vertices]
    center = Vector(tuple((min(c[i] for c in xs) + max(c[i] for c in xs)) / 2 for i in range(3)))
    me.transform(Matrix.Translation(-center))
    if smooth:
        me.shade_smooth()
    for mat in (material if isinstance(material, (list, tuple)) else [material]):
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.location = center
    ob.parent = root
    if bevel > 0:
        mod = ob.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(35)
        mod.harden_normals = True
    return ob


# ---------- 루트 / 메타데이터 ----------

def make_root(code, coll, max_order):
    root = bpy.data.objects.new(f"{code}_root", None)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = 0.05
    coll.objects.link(root)
    root["explode_factor"] = 0.0
    root.id_properties_ui("explode_factor").update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
                                                   description="0 = 조립, 1 = 완전 분해")
    root["explode_window"] = WINDOW
    root["explode_stagger"] = (1.0 - WINDOW) / max(max_order - 1, 1)
    return root


def set_meta(ob, direction, dist, order, label_ko, desc_ko=""):
    """desc_ko: 뷰어의 부품 보기에서 이름 아래 뜨는 한 줄 설명 (무슨 일을 하는 부품인지)."""
    d = Vector(direction)
    d = d.normalized() if d.length > 0 else Vector((0, 0, 1))
    ob["explode_dir"] = tuple(round(c, 6) for c in d)
    ob.id_properties_ui("explode_dir").update(subtype='XYZ')
    ob["explode_dist"] = float(dist)
    ob["explode_order"] = int(order)
    ob["label_ko"] = label_ko
    if desc_ko:
        ob["desc_ko"] = desc_ko


def _var(drv, name, ob, path):
    v = drv.variables.new()
    v.name = name
    v.type = 'SINGLE_PROP'
    v.targets[0].id_type = 'OBJECT'
    v.targets[0].id = ob
    v.targets[0].data_path = path
    return v


def add_explode_drivers(ob, root):
    """delta_location 에 폭발 드라이버. Python 함수 없이 simple expression 만 써서
    auto-run 스크립트가 꺼진 환경에서도 그대로 동작한다."""
    for i in range(3):
        fc = ob.driver_add("delta_location", i)
        drv = fc.driver
        drv.type = 'SCRIPTED'
        _var(drv, "f", root, '["explode_factor"]')
        _var(drv, "k", root, '["explode_stagger"]')
        _var(drv, "w", root, '["explode_window"]')
        _var(drv, "o", ob, '["explode_order"]')
        _var(drv, "L", ob, '["explode_dist"]')
        _var(drv, "d", ob, f'["explode_dir"][{i}]')
        drv.expression = "d*L*smoothstep((o-1)*k, (o-1)*k+w, f)"
        assert drv.is_simple_expression, ob.name


def key_explode(root, f0=1, f1=60):
    root["explode_factor"] = 0.0
    root.keyframe_insert('["explode_factor"]', frame=f0)
    root["explode_factor"] = 1.0
    root.keyframe_insert('["explode_factor"]', frame=f1)
    _linear_keys(root)


def _linear_keys(ob):
    act = ob.animation_data.action
    fcurves = getattr(act, "fcurves", None)
    if fcurves is None:  # 4.4+ layered action
        fcurves = [fc for layer in act.layers for strip in layer.strips
                   for bag in strip.channelbags for fc in bag.fcurves]
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'


# ---------- 우주 배경 연출 (제품 컬렉션 밖) ----------

def _space_world():
    """별(밝기 편차 큰 두 겹) + 옅은 성운. 방향 벡터 기반이라 카메라가 돌아도 무한히 먼 하늘."""
    w = bpy.data.worlds.new("space")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    dirv = tc.outputs["Generated"]

    def star_layer(scale, radius, sharp, gain):
        vo = nt.nodes.new("ShaderNodeTexVoronoi")
        vo.inputs["Scale"].default_value = scale
        vo.inputs["Randomness"].default_value = 1.0
        nt.links.new(dirv, vo.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")          # 점 모양: 중심 1 → radius 에서 0
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = radius
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.0
        nt.links.new(vo.outputs["Distance"], mr.inputs["Value"])
        sep = nt.nodes.new("ShaderNodeSeparateColor")    # 별마다 무작위 밝기, 대부분 어둡게
        nt.links.new(vo.outputs["Color"], sep.inputs["Color"])
        pw = nt.nodes.new("ShaderNodeMath")
        pw.operation = 'POWER'
        pw.inputs[1].default_value = sharp
        nt.links.new(sep.outputs["Red"], pw.inputs[0])
        m1 = nt.nodes.new("ShaderNodeMath")
        m1.operation = 'MULTIPLY'
        nt.links.new(mr.outputs["Result"], m1.inputs[0])
        nt.links.new(pw.outputs["Value"], m1.inputs[1])
        m2 = nt.nodes.new("ShaderNodeMath")
        m2.operation = 'MULTIPLY'
        m2.inputs[1].default_value = gain
        nt.links.new(m1.outputs["Value"], m2.inputs[0])
        return m2.outputs["Value"]

    s1 = star_layer(300.0, 0.10, 16.0, 45.0)   # 드문드문 밝은 별
    s2 = star_layer(800.0, 0.12, 14.0, 3.0)     # 촘촘한 잔별
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = 'ADD'
    nt.links.new(s1, add.inputs[0])
    nt.links.new(s2, add.inputs[1])

    # 성운: 저주파 노이즈 → 남보라/청록 램프, 다른 노이즈로 가려 띠처럼
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 10.0
    nz.inputs["Roughness"].default_value = 0.62
    nt.links.new(dirv, nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.45, (0, 0, 0, 1)
    cr.elements[1].position, cr.elements[1].color = 0.78, hex_rgba("#5B3FA8")
    e = cr.elements.new(0.62)
    e.color = hex_rgba("#1B3A6B")
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    neb = nt.nodes.new("ShaderNodeMix")
    neb.data_type = 'RGBA'
    neb.blend_type = 'MULTIPLY'
    neb.inputs["Factor"].default_value = 1.0
    neb.inputs["B"].default_value = (0.6, 0.6, 0.6, 1)
    nt.links.new(ramp.outputs["Color"], neb.inputs["A"])

    total = nt.nodes.new("ShaderNodeMix")
    total.data_type = 'RGBA'
    total.blend_type = 'ADD'
    total.inputs["Factor"].default_value = 1.0
    nt.links.new(neb.outputs["Result"], total.inputs["A"])
    star_rgb = nt.nodes.new("ShaderNodeCombineColor")
    for ch in ("Red", "Green", "Blue"):
        nt.links.new(add.outputs["Value"], star_rgb.inputs[ch])
    nt.links.new(star_rgb.outputs["Color"], total.inputs["B"])
    nt.links.new(total.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    return w


def _planet(coll, cam, sun_dir, radius=150.0, dist=320.0, down_deg=33.0, side_deg=-12.0):
    """화면 아래쪽에 걸친 거대한 행성 호 + 대기 글로우."""
    q = cam.rotation_euler.to_quaternion()
    fwd, up, right = q @ Vector((0, 0, -1)), q @ Vector((0, 1, 0)), q @ Vector((1, 0, 0))
    d = (Matrix.Rotation(math.radians(-down_deg), 3, right) @
         Matrix.Rotation(math.radians(side_deg), 3, up) @ fwd)
    center = Vector(cam.location) + d * dist

    me = bpy.data.meshes.new("planet")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=128, v_segments=64, radius=radius)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    ob = bpy.data.objects.new("bg_planet", me)
    ob.location = center
    coll.objects.link(ob)

    m = bpy.data.materials.new("bg_planet")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 12.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].color = hex_rgba("#03080F")
    cr.elements[1].color = hex_rgba("#16283A")
    cr.elements.new(0.55).color = hex_rgba("#0A1624")
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    # 대기: 가장자리(Facing)로 갈수록 파란 발광
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.12
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 5.0
    nt.links.new(lw.outputs["Facing"], pw.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = hex_rgba("#4FA3FF")
    em.inputs["Strength"].default_value = 5.0
    add = nt.nodes.new("ShaderNodeAddShader")
    mixs = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(pw.outputs["Value"], mixs.inputs["Fac"])
    nt.links.new(b.outputs["BSDF"], mixs.inputs[1])
    nt.links.new(em.outputs["Emission"], mixs.inputs[2])
    out = nt.nodes["Material Output"]
    nt.links.new(mixs.outputs["Shader"], out.inputs["Surface"])
    me.materials.append(m)
    ob.visible_shadow = False
    return ob


def studio(cam_loc, target=(0, 0, 0), lens=50, res=(1280, 720), samples=160):
    """우주 배경 + 태양광(하드) + 청색 림. Cycles(Metal GPU)."""
    sc = bpy.context.scene
    coll = bpy.data.collections.new("scene_setup")
    sc.collection.children.link(coll)

    cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    cam.data.lens = lens
    cam.data.clip_start = 0.01
    cam.data.clip_end = 2000
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(cam)
    sc.camera = cam

    sun_dir = Vector((-0.55, 0.35, -0.75)).normalized()  # 빛이 향하는 방향
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN'))
    sun.data.energy = 4.0
    sun.data.angle = math.radians(1.5)
    sun.data.color = (1.0, 0.96, 0.9)
    sun.rotation_euler = sun_dir.to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(sun)

    def area(name, loc, energy, size, color):
        l = bpy.data.lights.new(name, 'AREA')
        l.energy, l.size, l.color = energy, size, color
        o = bpy.data.objects.new(name, l)
        o.location = loc
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        coll.objects.link(o)

    # 림은 윗면 정반사 경로(카메라를 수평면에 비친 방향) 밖에 둔다 — 안 그러면 날개가 흰 막대가 된다
    area("rim", (-1.1, 0.35, 1.2), 90, 0.6, (0.45, 0.65, 1.0))      # 뒤에서 청색 윤곽
    area("fill", (0.6, -1.3, -0.4), 18, 2.0, (0.6, 0.65, 0.8))      # 그림자 속 디테일
    area("key", (0.35, -1.2, 1.3), 55, 0.7, (1.0, 0.92, 0.82))    # 앞쪽 따뜻한 주광 — 카본 결이 보이게              # 윗면 반사 띠

    sc.world = _space_world()
    _planet(coll, cam, sun_dir)

    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception:
        sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 12
    sc.cycles.transmission_bounces = 12
    sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'

    # 하이라이트 번짐 (컴포지터)
    sc.use_nodes = True
    ct = sc.node_tree
    rl, comp = ct.nodes["Render Layers"], ct.nodes["Composite"]
    gl = ct.nodes.new("CompositorNodeGlare")
    gl.glare_type = 'FOG_GLOW'
    gl.quality = 'HIGH'
    gl.threshold = 1.2
    gl.mix = -0.75
    gl.size = 8
    ct.links.new(rl.outputs["Image"], gl.inputs["Image"])
    ct.links.new(gl.outputs["Image"], comp.inputs["Image"])
    return cam


def open_in_camera_view():
    """.blend 를 열면 바로 카메라 시점 + 렌더 미리보기(우주 배경·재질)가 보이게."""
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'
                    space.region_3d.view_perspective = 'CAMERA'


# ---------- 홀로그램 룩 (자비스 스타일) ----------

def _frame_driver(sock, expr):
    fc = sock.driver_add("default_value")
    fc.driver.type = 'SCRIPTED'
    fc.driver.expression = expr
    assert fc.driver.is_simple_expression, expr


def make_holo(code, name, hex_color, gain=1.0, sweep_period=45):
    """윤곽(Fresnel) + 와이어 + 가로 스캔라인 + 앞뒤로 훑는 스캔 빔. 빛만 더하고 뒤가 비친다."""
    m = bpy.data.materials.new(f"mat_{code}_{name}")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    N = nt.nodes.new
    L = nt.links.new

    def math_node(op, a, b=None):
        n = N("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]

    lw = N("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    edge = math_node('POWER', lw.outputs["Facing"], 2.2)

    wire = N("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 0.9

    geo = N("ShaderNodeNewGeometry")
    sep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs["Vector"])

    wave = N("ShaderNodeTexWave")               # 가로 스캔라인 (위로 흐름)
    wave.bands_direction = 'Z'
    wave.inputs["Scale"].default_value = 60.0
    L(geo.outputs["Position"], wave.inputs["Vector"])
    _frame_driver(wave.inputs["Phase Offset"], "-frame*0.35")
    scan = math_node('POWER', wave.outputs["Fac"], 10.0)

    beam_x = N("ShaderNodeValue")               # X 축을 훑는 빔 위치
    _frame_driver(beam_x.outputs[0], f"-0.45 + 0.9*(frame/{sweep_period} - floor(frame/{sweep_period}))")
    d = math_node('ABSOLUTE', math_node('SUBTRACT', sep.outputs["X"], beam_x.outputs[0]))
    beam = math_node('POWER', math_node('MAXIMUM', math_node('SUBTRACT', 1.0, math_node('DIVIDE', d, 0.035)), 0.0), 2.0)

    strength = math_node('ADD', 0.12, math_node('MULTIPLY', edge, 2.2))
    strength = math_node('ADD', strength, math_node('MULTIPLY', wire.outputs["Fac"], 1.4))
    strength = math_node('ADD', strength, math_node('MULTIPLY', scan, 0.35))
    strength = math_node('ADD', strength, math_node('MULTIPLY', beam, 2.0))
    strength = math_node('MULTIPLY', strength, gain)

    em = N("ShaderNodeEmission")
    em.inputs["Color"].default_value = hex_rgba(hex_color)
    L(strength, em.inputs["Strength"])
    tr = N("ShaderNodeBsdfTransparent")
    add = N("ShaderNodeAddShader")
    L(tr.outputs[0], add.inputs[0])
    L(em.outputs[0], add.inputs[1])
    L(add.outputs[0], out.inputs["Surface"])
    m.diffuse_color = hex_rgba(hex_color)[:3] + (0.4,)
    m.surface_render_method = 'BLENDED'
    return m


def apply_holo(code, parts, faint=(), accent=()):
    """모든 부품 재질을 홀로그램으로 교체. faint = 흐리게(튜브), accent = 주황 강조(핵심 부품)."""
    M = {"main": make_holo(code, "holo", "#35D0FF"),
         "faint": make_holo(code, "holo_faint", "#35D0FF", gain=0.1),
         "accent": make_holo(code, "holo_accent", "#FF8A3D", gain=0.55)}
    for ob in parts:
        key = "faint" if ob in faint else "accent" if ob in accent else "main"
        ob.data.materials.clear()
        ob.data.materials.append(M[key])
        for poly in ob.data.polygons:
            poly.material_index = 0
    return M


def studio_holo(cam_loc, target=(0, 0, 0), lens=50, res=(1280, 720), samples=64):
    """검은 화면 + 강한 글로우. 조명 없음(재질이 스스로 빛난다)."""
    sc = bpy.context.scene
    coll = bpy.data.collections.new("scene_setup")
    sc.collection.children.link(coll)
    cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    cam.data.lens = lens
    cam.data.clip_start = 0.01
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(cam)
    sc.camera = cam

    w = bpy.data.worlds.new("black")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    sc.world = w

    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception:
        sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.transparent_max_bounces = 64
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'

    sc.use_nodes = True
    ct = sc.node_tree
    rl, comp = ct.nodes["Render Layers"], ct.nodes["Composite"]
    prev = rl.outputs["Image"]
    for kind, thr, mix, size in (('FOG_GLOW', 0.25, 0.1, 9), ('FOG_GLOW', 0.6, -0.4, 6)):
        gl = ct.nodes.new("CompositorNodeGlare")
        gl.glare_type = kind
        gl.quality = 'HIGH'
        gl.threshold, gl.mix, gl.size = thr, mix, size
        ct.links.new(prev, gl.inputs["Image"])
        prev = gl.outputs["Image"]
    ct.links.new(prev, comp.inputs["Image"])
    return cam


# ---------- 흰 스튜디오 (제품 사진 룩) ----------

def studio_white(cam_loc, target=(0, 0, 0), lens=50, res=(1280, 720), samples=160, floor_z=-0.25):
    """순백 배경 + 바닥 그림자만. 흰 환경이 검은 클리어코트에 비쳐 형태가 읽힌다."""
    sc = bpy.context.scene
    coll = bpy.data.collections.new("scene_setup")
    sc.collection.children.link(coll)
    cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    cam.data.lens = lens
    cam.data.clip_start = 0.01
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(cam)
    sc.camera = cam

    def area(name, loc, energy, size, aim=target):
        l = bpy.data.lights.new(name, 'AREA')
        l.energy, l.size = energy, size
        o = bpy.data.objects.new(name, l)
        o.location = loc
        o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        coll.objects.link(o)

    area("softbox_top", (0.2, -0.2, 1.4), 180, 1.6)       # 큰 윗 소프트박스 — 부드러운 그림자
    area("key", (1.1, -0.9, 0.6), 60, 1.0)                # 앞쪽 주광
    area("strip_left", (-1.0, -0.7, 0.3), 45, 0.5)        # 옆 스트립 — 검은 몸통 가장자리에 흰 띠
    area("rim", (-0.6, 1.2, 0.8), 70, 0.8)                # 뒤 윤곽

    me = bpy.data.meshes.new("floor")                     # 그림자만 받는 바닥
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6.0)
    bm.to_mesh(me)
    bm.free()
    fl = bpy.data.objects.new("shadow_floor", me)
    fl.location = (0, 0, floor_z)
    fl.is_shadow_catcher = True
    coll.objects.link(fl)

    w = bpy.data.worlds.new("white")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    sc.world = w

    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception:
        sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 12
    sc.cycles.transmission_bounces = 12
    sc.render.film_transparent = True                     # 배경은 컴포지터에서 순백으로 깐다
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'

    sc.use_nodes = True
    ct = sc.node_tree
    rl, comp = ct.nodes["Render Layers"], ct.nodes["Composite"]
    ao = ct.nodes.new("CompositorNodeAlphaOver")
    ao.inputs[1].default_value = (1, 1, 1, 1)
    ct.links.new(rl.outputs["Image"], ao.inputs[2])
    ct.links.new(ao.outputs["Image"], comp.inputs["Image"])
    return cam


# ---------- 병기고 룩 (게임 무기 선택 화면) ----------

def armory_background(path, w, h, cell=26.0):
    """회색 방사 그라데이션 + 음각 육각 타일 + 옅은 연기 + 비네트 → PNG. numpy 로 픽셀 직접 계산."""
    import numpy as np
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    # 방사 그라데이션 (중앙 약간 위가 밝다)
    cx, cy = w * 0.5, h * 0.42
    r = np.sqrt(((x - cx) / (w * 0.62)) ** 2 + ((y - cy) / (h * 0.75)) ** 2)
    base = 0.36 - 0.24 * np.clip(r, 0, 1.4) ** 1.6
    # 육각 타일: 두 격자 중 가까운 중심 → 육각 거리
    p = np.stack([x / cell, y / cell], -1)
    R = np.array([1.0, math.sqrt(3)])
    H = R * 0.5
    a = np.mod(p, R) - H
    b = np.mod(p - H, R) - H
    gv = np.where((np.linalg.norm(a, axis=-1) < np.linalg.norm(b, axis=-1))[..., None], a, b)
    q = np.abs(gv)
    hd = np.maximum((q * np.array([0.5, math.sqrt(3) / 2])).sum(-1), q[..., 0])   # 0(중심)~0.5(모서리)
    groove = np.clip((hd - 0.44) / 0.06, 0, 1) ** 2                                 # 모서리 홈
    lit = np.clip((gv[..., 1] + gv[..., 0] * 0.3) * -2.0, 0, 1) * np.clip((hd - 0.30) / 0.14, 0, 1)
    tile = -0.055 * groove + 0.018 * lit
    # 연기: 여러 배율 무작위 격자를 부드럽게 키워 합침
    rng = np.random.default_rng(7)
    smoke = np.zeros((h, w))
    for k, amp in ((6, 0.5), (12, 0.3), (24, 0.2)):
        g = rng.random((k + 2, int(k * w / h) + 2))
        gy, gx = y / h * k, x / h * k
        i0, j0 = gy.astype(int), gx.astype(int)
        fy, fx = gy - i0, gx - j0
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        v = (g[i0, j0] * (1 - fx) + g[i0, j0 + 1] * fx) * (1 - fy) + \
            (g[i0 + 1, j0] * (1 - fx) + g[i0 + 1, j0 + 1] * fx) * fy
        smoke += amp * v
    val = base + tile * (1 - 0.6 * np.clip(r, 0, 1)) + (smoke - 0.5) * 0.07 * (1 - np.clip(r, 0, 1))
    val = np.clip(val, 0, 1)
    rgb = np.stack([val * 0.97, val * 0.99, val * 1.04], -1).clip(0, 1)   # 살짝 푸른 회색
    img = bpy.data.images.new("armory_bg", w, h, alpha=False)
    rgba = np.concatenate([rgb, np.ones((h, w, 1))], -1)[::-1]          # Blender 픽셀은 아래부터
    img.pixels[:] = rgba.ravel()
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    return img


def studio_armory(cam_loc, target=(0, 0, 0), lens=50, res=(1280, 720), samples=160, bg_path=None):
    """회색 육각 배경(합성) + 강한 주광 + 양옆 윤곽광. 검은 부품의 테두리가 선다."""
    sc = bpy.context.scene
    coll = bpy.data.collections.new("scene_setup")
    sc.collection.children.link(coll)
    cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    cam.data.lens = lens
    cam.data.clip_start = 0.01
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(cam)
    sc.camera = cam

    def area(name, loc, energy, size, color=(1, 1, 1)):
        l = bpy.data.lights.new(name, 'AREA')
        l.energy, l.size, l.color = energy, size, color
        o = bpy.data.objects.new(name, l)
        o.location = loc
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        coll.objects.link(o)

    area("key", (0.5, -1.0, 1.1), 70, 0.9)                        # 위-앞 주광: 윗면에 넓은 반사
    area("rim_front", (1.4, 0.3, 0.35), 90, 0.4, (0.8, 0.88, 1.0))  # 앞쪽 윤곽 (차가운 색)
    area("rim_back", (-1.4, 0.3, 0.35), 90, 0.4, (0.8, 0.88, 1.0))  # 뒤쪽 윤곽
    area("under", (0.0, -0.6, -0.9), 12, 1.5)                     # 아랫면이 뭉개지지 않게

    w = bpy.data.worlds.new("gray")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = hex_rgba("#3A3D42")
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12  # 높이면 카본이 은색 크롬이 된다
    sc.world = w

    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception:
        sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 12
    sc.cycles.transmission_bounces = 12
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'   # 배경 PNG 톤이 그대로 나오게

    bg = armory_background(bg_path, *res)
    sc.use_nodes = True
    ct = sc.node_tree
    rl, comp = ct.nodes["Render Layers"], ct.nodes["Composite"]
    im = ct.nodes.new("CompositorNodeImage")
    im.image = bg
    ao = ct.nodes.new("CompositorNodeAlphaOver")
    ct.links.new(im.outputs["Image"], ao.inputs[1])
    ct.links.new(rl.outputs["Image"], ao.inputs[2])
    ct.links.new(ao.outputs["Image"], comp.inputs["Image"])
    return cam


# ---------- 제품 스크립트 공통 마무리 ----------

def parse_args():
    import sys
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda n, d: argv[argv.index(n) + 1] if n in argv else d
    return argv, get


def out_dir(here, code, look):
    import os
    d = os.path.join(here, "..", "out", code if look == "real" else f"{code}_{look}")
    os.makedirs(d, exist_ok=True)
    return d


def apply_look(look, cam, out):
    """cam = dict(cam_loc, target, lens). 룩별 배경·조명."""
    import os
    if look == "armory":
        return studio_armory(bg_path=os.path.join(out, "bg.png"), **cam)
    if look == "white":
        return studio_white(**cam)
    return studio(**cam)


def verify_explode(parts, frame=60):
    """프레임 60 에서 월드 위치 - location = delta_location 이 dir*dist 인가 (부모가 원점일 때)."""
    bpy.context.scene.frame_set(frame)
    bad = []
    for o in parts:
        moved = o.matrix_world.translation - o.location
        want = Vector(o["explode_dir"]) * o["explode_dist"]
        if (moved - want).length > 1e-4:
            bad.append((o.name, tuple(round(c, 4) for c in moved), tuple(round(c, 4) for c in want)))
    print("VERIFY explode", "OK" if not bad else bad)
    return not bad


def save_and_render(out, argv, get):
    import os
    sc = bpy.context.scene
    sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, os.path.basename(os.path.normpath(out)) + ".blend"))
    if "--render" in argv:
        sc.render.resolution_percentage = int(get("--pct", "100"))
        for fr in (int(f) for f in get("--frames", "1,20,40,60").split(",")):
            sc.frame_set(fr)
            sc.render.filepath = os.path.join(out, f"frame_{fr:02d}.png")
            bpy.ops.render.render(write_still=True)


# ---------- 보고 ----------

def report(code, parts, path):
    rows = ["| 이름 | label_ko | 재질 | order | dir | dist(m) | 치수 X×Y×Z (mm) |",
            "|---|---|---|---|---|---|---|"]
    for ob in parts:
        d = ob.dimensions
        mats = "+".join(m.name.replace(f"mat_{code}_", "") for m in ob.data.materials)
        rows.append("| {} | {} | {} | {} | ({:+.2f}, {:+.2f}, {:+.2f}) | {:.3f} | {:.0f}×{:.0f}×{:.0f} |".format(
            ob.name, ob["label_ko"], mats,
            ob["explode_order"], *ob["explode_dir"], ob["explode_dist"],
            d.x * 1000, d.y * 1000, d.z * 1000))
    text = "\n".join(rows)
    with open(path, "w") as f:
        f.write(text + "\n")
    print(text)
