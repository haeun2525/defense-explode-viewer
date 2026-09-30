"""quad — 정찰 쿼드콥터 (Skydio X2 급) 분해 씬. 껍데기를 열면 속 전자부품까지 나온다.

실행: Blender -b --factory-startup --python products/quad.py -- [--look armory] [--render] [--frames 1,20,40,60]
+X 전방. 모터 대각 거리 약 0.45m, 프롭 포함 전폭 약 0.5m.
내부 배치는 소형 정찰 드론의 공개된 일반 구성(비행 컨트롤러·ESC·자율비행 컴퓨터·GPS·데이터링크·항법 카메라)을
바탕으로 한 것이다. 실제 제품의 기판 배치가 아니다.

분해 순서
  1 프로펠러 → 2 모터·배터리 팩·짐벌 카메라 하우징 → 3 상부 덮개 → 4 위층 보드·항법 카메라·렌즈군
  → 5 아래층 보드·배터리 셀·열상 코어·센서 보드 → 6 배전 기판
하부 프레임(암 포함)과 짐벌은 움직이지 않는 기준이다.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))

import bmesh
import bpy
from mathutils import Matrix, Vector
import explode_common as ex

CODE = "quad"
argv, get = ex.parse_args()
LOOK = get("--look", "armory")
OUT = ex.out_dir(HERE, CODE, LOOK)

# 치수 (m)
BODY = (0.200, 0.100, 0.060)          # 중앙 바디 X×Y×Z (원점 중심, z −0.03 ~ +0.03)
SEAM = 0.008                          # 하부 프레임과 상부 덮개가 맞닿는 높이
WALL = 0.003                          # 껍데기 두께
MOTOR_XY = 0.160                      # 모터 중심 (±, ±) → 대각 0.45m
ARM_W, ARM_T = 0.022, 0.014
MOTOR_R, MOTOR_H = 0.018, 0.022
PROP_R = 0.090                        # 7인치급
T = Matrix.Translation
BX, BY, BZ = BODY[0] / 2, BODY[1] / 2, BODY[2] / 2

sc = ex.reset_scene()
coll = bpy.data.collections.new(CODE)
sc.collection.children.link(coll)
M = ex.standard_materials(CODE, ("olive", "carbon", "gunmetal", "glass", "black",
                                 "pcb", "metal", "gold", "ceramic", "cell", "copper"))
root = ex.make_root(CODE, coll, max_order=6)
parts = []
PCB = [M["pcb"], M["black"], M["metal"], M["ceramic"]]   # ex.bm_pcb 의 mats=(0,1,2,3) 순서 — 칩 핀·차폐캔은 은색(주석 도금)


def add(name, bm, mat, direction, dist, order, label, desc="", **kw):
    ob = ex.part_object(f"{CODE}_{len(parts) + 1:02d}_{name}", bm, mat, coll, root, **kw)
    ex.set_meta(ob, direction, dist, order, label, desc)
    parts.append(ob)
    return ob


def walls(bm, x0, x1, y0, y1, z0, z1, skip_rear=False, rear_gap=0.0):
    """위아래가 뚫린 네 벽. skip_rear 면 뒷벽 가운데를 rear_gap 폭만큼 비운다(배터리 슬롯)."""
    zc, h = (z0 + z1) / 2, z1 - z0
    ex.bm_box(bm, (WALL, y1 - y0, h), T((x1 - WALL / 2, (y0 + y1) / 2, zc)))          # 앞
    ex.bm_box(bm, (x1 - x0, WALL, h), T(((x0 + x1) / 2, y1 - WALL / 2, zc)))          # 왼
    ex.bm_box(bm, (x1 - x0, WALL, h), T(((x0 + x1) / 2, y0 + WALL / 2, zc)))          # 오른
    if not skip_rear:
        ex.bm_box(bm, (WALL, y1 - y0, h), T((x0 + WALL / 2, (y0 + y1) / 2, zc)))
    else:
        side = ((y1 - y0) - rear_gap) / 2
        for s in (+1, -1):
            ex.bm_box(bm, (WALL, side, h), T((x0 + WALL / 2, s * (rear_gap / 2 + side / 2), zc)))


CORNERS = (("front_left", +1, +1, "앞 왼쪽"), ("front_right", +1, -1, "앞 오른쪽"),
           ("rear_left", -1, +1, "뒤 왼쪽"), ("rear_right", -1, -1, "뒤 오른쪽"))
motor_z = ARM_T / 2 + MOTOR_H / 2

# ─────────── 기준: 하부 프레임 + 암 네 개 (카본 암이 프레임에 박혀 있다) ───────────
bm = bmesh.new()
ex.bm_box(bm, (BODY[0], BODY[1], WALL), T((0, 0, -BZ + WALL / 2)))                  # 바닥판
walls(bm, -BX, BX, -BY, BY, -BZ + WALL, SEAM, skip_rear=True, rear_gap=0.074)      # 벽 (뒤는 배터리 슬롯)
for nm, sx, sy, lb in CORNERS:
    root_pt = Vector((sx * 0.070, sy * 0.035, 0))
    tip = Vector((sx * MOTOR_XY, sy * MOTOR_XY, 0))
    d = tip - root_pt
    vs = ex.bm_box(bm, (d.length, ARM_W, ARM_T))
    for v in vs:                                        # +X 쪽(모터 쪽) 폭을 줄인다
        if v.co.x > 0:
            v.co.y *= 0.7
    bmesh.ops.transform(bm, verts=vs, matrix=T((root_pt + tip) / 2) @
                        Matrix.Rotation(math.atan2(d.y, d.x), 4, 'Z'))
    ex.set_mat(vs, 1)
    ex.set_mat(ex.bm_cyl(bm, MOTOR_R + 0.003, MOTOR_R + 0.003, ARM_T, 'Z', T(tip)), 1)   # 모터 받침
add("frame", bm, [M["olive"], M["carbon"]], (0, 0, -1), 0.0, 0, "하부 프레임·암",
    "기체의 뼈대. 카본 암 네 개가 모터를 받치고, 안쪽에 보드와 배터리가 들어간다", bevel=0.002)

# ─────────── 1 프로펠러 2엽 — 끝이 좁은 블레이드, 피치 12도 ───────────
prop_z = motor_z + MOTOR_H / 2 + 0.010
for i, (nm, sx, sy, lb) in enumerate(CORNERS):
    c = Vector((sx * MOTOR_XY, sy * MOTOR_XY, prop_z))
    yaw = math.radians((12, -18, 168, 198)[i])  # 옆 카메라에서 날이 가로로 보이게
    bm = bmesh.new()
    ex.set_mat(ex.bm_cyl(bm, 0.009, 0.009, 0.008, 'Z', T(c)), 1)
    for s in (+1, -1):
        vs = ex.bm_box(bm, (PROP_R - 0.008, 0.016, 0.0025))
        for v in vs:
            if v.co.x > 0:
                v.co.y *= 0.5
        bmesh.ops.transform(bm, verts=vs, matrix=T(c) @ Matrix.Rotation(yaw + (0 if s > 0 else math.pi), 4, 'Z') @
                            T(((PROP_R + 0.008) / 2, 0, 0)) @ Matrix.Rotation(math.radians(12), 4, 'X'))
    add(f"prop_{nm}", bm, [M["carbon"], M["gunmetal"]], (sx * 0.45, sy * 0.45, 1), 0.19, 1, f"프로펠러({lb})",
        "모터가 돌려 기체를 띄우는 힘(추력)을 만든다. 대각선끼리 같은 방향으로 돈다", bevel=0.0008)

# ─────────── 2 모터 — 금속 캔 + 카본 냉각 띠. 앞 오른쪽 하나는 캔(자석)과 코일로 나눠 속을 보여 준다 ───────────
for nm, sx, sy, lb in CORNERS:
    c = Vector((sx * MOTOR_XY, sy * MOTOR_XY, motor_z))
    split = nm == "front_right"
    bm = bmesh.new()
    ex.bm_cyl(bm, MOTOR_R, MOTOR_R * 0.9, MOTOR_H, 'Z', T(c))
    ex.set_mat(ex.bm_cyl(bm, MOTOR_R + 0.001, MOTOR_R + 0.001, 0.005, 'Z', T(c - Vector((0, 0, 0.004)))), 1)
    ex.bm_cyl(bm, 0.003, 0.003, 0.008, 'Z', T(c + Vector((0, 0, MOTOR_H / 2 + 0.004))), segs=12)  # 축
    if not split:
        add(f"motor_{nm}", bm, [M["gunmetal"], M["carbon"]], (sx * 0.3, sy * 0.3, 1), 0.09, 2, f"모터({lb})",
            "브러시리스 모터. 코일에 전류를 번갈아 흘려 바깥 캔(자석)을 돌린다")
        continue
    add(f"motor_bell_{nm}", bm, [M["gunmetal"], M["carbon"]], (sx * 0.3, sy * 0.3, 1), 0.12, 2,
        f"모터 로터({lb})", "바깥에서 도는 캔. 안쪽 벽에 영구자석이 붙어 있다")
    # 고정자: 구리 권선을 감은 12 톱니 + 가운데 베어링 관. 캔 안에 쏙 들어간다
    bm = bmesh.new()
    zc = c.z - 0.002
    ex.set_mat(ex.bm_cyl(bm, 0.006, 0.006, MOTOR_H - 0.006, 'Z', T((c.x, c.y, zc))), 1)
    for k in range(12):
        a = k * math.tau / 12
        m = T((c.x + math.cos(a) * 0.011, c.y + math.sin(a) * 0.011, zc)) @ Matrix.Rotation(a, 4, 'Z')
        ex.bm_box(bm, (0.008, 0.0045, MOTOR_H - 0.008), m)
    add(f"motor_stator_{nm}", bm, [M["copper"], M["metal"]], (sx * 0.3, sy * 0.3, 1), 0.035, 2,
        f"모터 코일({lb})", "구리선을 감은 고정자. ESC 가 전류 방향을 빠르게 바꿔 회전 자기장을 만든다", bevel=0.0004)

# ─────────── 2 배터리 팩 껍데기 / 5 셀 — 뒤에서 밀어 넣는 팩, 끝이 바디 뒤로 10mm 나와 있다 ───────────
BAT_C = Vector((-BX + 0.035, 0, -0.008))
BAT = (0.090, 0.070, 0.028)
bm = bmesh.new()
bx0, bx1 = BAT_C.x - BAT[0] / 2, BAT_C.x + BAT[0] / 2
by, bz0, bz1 = BAT[1] / 2, BAT_C.z - BAT[2] / 2, BAT_C.z + BAT[2] / 2
ex.bm_box(bm, (BAT[0], BAT[1], 0.002), T((BAT_C.x, 0, bz0 + 0.001)))                  # 바닥
ex.bm_box(bm, (BAT[0], BAT[1], 0.002), T((BAT_C.x, 0, bz1 - 0.001)))                  # 뚜껑
for s in (+1, -1):
    ex.bm_box(bm, (BAT[0], 0.002, BAT[2]), T((BAT_C.x, s * (by - 0.001), BAT_C.z)))
for x in (bx0 + 0.001, bx1 - 0.001):
    ex.bm_box(bm, (0.002, BAT[1], BAT[2]), T((x, 0, BAT_C.z)))
ex.set_mat(ex.bm_box(bm, (0.006, 0.030, 0.012), T((bx0 - 0.003, 0, BAT_C.z))), 1)         # 손잡이 탭
ex.set_mat(ex.bm_box(bm, (0.004, 0.018, 0.006), T((bx1 + 0.002, 0, BAT_C.z))), 2)         # 앞쪽 전원 단자
add("battery_pack", bm, [M["carbon"], M["gunmetal"], M["gold"]], (-1, 0.4, -0.1), 0.18, 2, "배터리 팩",
    "셀을 감싸는 케이스. 금속 단자로 기체에 전기를 넘긴다", bevel=0.002)

bm = bmesh.new()
for k, y in enumerate((-0.021, 0.0, 0.021)):                                               # 18650 셀 3개 (3S)
    ex.bm_cyl(bm, 0.0092, 0.0092, 0.066, 'X', T((BAT_C.x, y, BAT_C.z)))
    for sx in (-1, 1):
        ex.set_mat(ex.bm_cyl(bm, 0.004, 0.004, 0.0015, 'X', T((BAT_C.x + sx * 0.0335, y, BAT_C.z)), segs=16), 1)
chips = ex.bm_pcb(bm, (0.066, 0.050, 0.0012), T((BAT_C.x, 0, BAT_C.z + 0.0098)),        # 셀 보호 회로(BMS)
                  chips=[(-0.012, 0.010, 0.003, 0.003, 0.0008, 'qfn', "배터리 보호 IC",
                          "셀마다 전압을 지켜보다가 너무 차거나 비면 전류를 끊으라고 MOSFET 에 알린다"),
                         (0.004, 0.010, 0.005, 0.004, 0.0010, 'ic', "보호 MOSFET",
                          "보호 IC 의 신호를 받아 배터리 전류 길을 열고 닫는 전자 스위치"),
                         (0.011, 0.010, 0.005, 0.004, 0.0010, 'ic'),
                         (-0.022, -0.012, 0.002, 0.0012, 0.0008, 'passive', "온도 센서(NTC)",
                          "셀이 뜨거워지면 저항값이 바뀌어, 과열되기 전에 충전·방전을 멈추게 한다"),
                         (0.024, -0.013, 0.010, 0.005, 0.0030, 'conn', "밸런스 커넥터",
                          "셀 하나하나의 전압을 충전기로 이어, 셀끼리 고르게 충전되게 한다"),
                         (-0.004, -0.004, 0.002, 0.001, 0.0006, 'passive'), (0.000, -0.004, 0.002, 0.001, 0.0006, 'passive'),
                         (0.004, -0.004, 0.002, 0.001, 0.0006, 'passive')], mats=(2, 3, 1, 4))
ob = add("battery_cells", bm, [M["cell"], M["metal"], M["pcb"], M["black"], M["ceramic"]], (-1, -0.2, 0.6), 0.10, 5,
         "배터리 셀(3S)", "예: 리튬이온 셀 3개를 직렬로 이으면 약 11V(셀당 약 3.6~3.7V). 위의 얇은 기판(BMS)이 과충전·과방전을 막는다", bevel=0.0005)
ex.attach_chips(ob, chips)

# ─────────── 2 짐벌 카메라 하우징 / 기준 짐벌 / 4~5 카메라 속 ───────────
gx, gz = 0.070, -BZ - 0.028
bm = bmesh.new()
ex.bm_box(bm, (0.030, 0.050, 0.008), T((gx, 0, -BZ - 0.004)))                            # 마운트 판
ex.set_mat(ex.bm_cyl(bm, 0.010, 0.010, 0.006, 'Z', T((gx, 0, -BZ - 0.011))), 1)           # 요(yaw) 모터
for s in (+1, -1):
    ex.bm_box(bm, (0.012, 0.005, 0.030), T((gx, s * 0.022, gz + 0.008)))                  # 요크 팔
    ex.set_mat(ex.bm_cyl(bm, 0.008, 0.008, 0.005, 'Y', T((gx, s * 0.0265, gz))), 1)        # 피치·롤 모터
add("gimbal", bm, [M["gunmetal"], M["black"]], (0, 0, -1), 0.0, 0, "짐벌(3축 모터)",
    "모터 세 개가 기체 흔들림을 반대로 상쇄해 카메라가 흔들리지 않게 붙잡는다", bevel=0.001)

bm = bmesh.new()
ex.bm_cyl(bm, 0.017, 0.017, 0.036, 'Y', T((gx, 0, gz)))                                   # 몸통(가로 원통)
ex.set_mat(ex.bm_cyl(bm, 0.0072, 0.0072, 0.004, 'X', T((gx + 0.0165, 0.009, gz))), 1)     # 열상 창 테
add("camera_housing", bm, [M["gunmetal"], M["black"]], (0.6, 0, -1), 0.13, 2, "카메라 하우징",
    "렌즈·센서를 먼지와 빛샘에서 막는 단단한 몸통", bevel=0.001)

bm = bmesh.new()                                                                          # 컬러 카메라 렌즈군
ly = -0.007
ex.bm_cyl(bm, 0.009, 0.009, 0.016, 'X', T((gx + 0.019, ly, gz)))                          # 경통
for k, (x, r) in enumerate(((gx + 0.010, 0.0060), (gx + 0.016, 0.0070), (gx + 0.022, 0.0075))):
    ex.set_mat(ex.bm_cyl(bm, r, r, 0.0018, 'X', T((x, ly, gz))), 1)                       # 렌즈 알 3장
ex.set_mat(ex.bm_hemisphere(bm, 0.0072, 'X', T((gx + 0.027, ly, gz)), segs=24), 1)
add("lens_group", bm, [M["black"], M["glass"]], (1, 0, 0), 0.20, 4, "렌즈군",
    "렌즈 여러 장이 빛을 모아 센서에 상을 맺는다. 줌·초점용 렌즈는 앞뒤로 움직인다", bevel=0.0004)

bm = bmesh.new()                                                                          # 열상 코어 + 게르마늄 렌즈
ex.bm_box(bm, (0.013, 0.012, 0.012), T((gx + 0.004, 0.009, gz)))
ex.set_mat(ex.bm_cyl(bm, 0.0055, 0.0055, 0.004, 'X', T((gx + 0.0125, 0.009, gz))), 1)
ex.set_mat(ex.bm_cyl(bm, 0.0048, 0.0048, 0.0014, 'X', T((gx + 0.0152, 0.009, gz))), 2)
add("thermal_core", bm, [M["gunmetal"], M["black"], M["gunmetal"]], (0.2, 0, -1), 0.16, 5, "열상 코어",
    "물체가 내는 열(적외선)을 보는 센서(마이크로볼로미터). 빛이 없거나 연기가 낀 곳에서도 사람·차량의 열을 찾는다",
    bevel=0.0005)

bm = bmesh.new()                                                                          # 이미지 센서 보드 (세운 기판)
chips = ex.bm_pcb(bm, (0.024, 0.020, 0.0016), T((gx - 0.006, -0.004, gz)) @ Matrix.Rotation(math.radians(90), 4, 'Y'),
                  chips=[(0, 0, 0.009, 0.009, 0.0016, 'bga', "이미지 센서(CMOS)",
                          "렌즈가 모은 빛을 수백만 개의 화소가 받아 전기 신호로 바꾼다 — 카메라의 눈"),
                         (-0.0075, -0.0065, 0.005, 0.004, 0.0012, 'bga', "영상 처리 칩(ISP)",
                          "센서 신호의 색·밝기·잡음을 다듬어 영상으로 만든다"),
                         (0.008, -0.007, 0.0025, 0.0015, 0.0010, 'sot', "전원 레귤레이터",
                          "센서가 쓰는 여러 가지 낮은 전압을 깨끗하게 만든다"),
                         (0.008, 0.007, 0.003, 0.002, 0.0008, 'crystal', "크리스털 발진기",
                          "화소를 읽어 내는 박자(클럭)를 정확하게 맞춘다"),
                         (0.0075, 0.0025, 0.002, 0.001, 0.0006, 'passive'), (-0.008, 0.006, 0.002, 0.001, 0.0006, 'passive'),
                         (-0.008, 0.0025, 0.002, 0.001, 0.0006, 'passive')], mats=(0, 1, 2, 3))
ob = add("image_sensor", bm, PCB, (-0.2, 0, -1), 0.16, 5, "이미지 센서 보드",
         "렌즈가 모은 빛을 전기 신호로 바꾸는 CMOS 센서와 영상 처리 칩", bevel=0)
ex.attach_chips(ob, chips)

# ─────────── 3 상부 덮개 — 뚜껑 + 네 벽 + 윗면 능선. 뒤는 배터리 슬롯 ───────────
bm = bmesh.new()
ex.bm_box(bm, (BODY[0], BODY[1], WALL), T((0, 0, BZ - WALL / 2)))
walls(bm, -BX, BX, -BY, BY, SEAM, BZ - WALL, skip_rear=True, rear_gap=0.050)
ex.bm_box(bm, (WALL, 0.050, BZ - WALL - 0.014), T((-BX + WALL / 2, 0, (0.014 + BZ - WALL) / 2)))  # 슬롯 위 뒷벽
ex.bm_box(bm, (0.12, 0.05, 0.008), T((-0.01, 0, BZ + 0.003)))                            # 윗면 능선
add("top_cover", bm, M["olive"], (0, 0, 1), 0.18, 3, "상부 덮개",
    "위쪽 껍데기. 보드를 비·먼지로부터 막고, 앞면에 항법 카메라 창이 뚫려 있다", bevel=0.003, segments=3)

# ─────────── 4 항법 카메라 쌍 — 앞면 안쪽에 붙은 스테레오 카메라 ───────────
bm = bmesh.new()
ex.bm_box(bm, (0.004, 0.080, 0.012), T((BX - 0.007, 0, 0.018)))                          # 두 카메라를 잇는 막대
for s in (+1, -1):
    ex.bm_box(bm, (0.008, 0.014, 0.014), T((BX - 0.008, s * 0.030, 0.018)))
    ex.set_mat(ex.bm_cyl(bm, 0.0045, 0.0045, 0.006, 'X', T((BX - 0.001, s * 0.030, 0.018)), segs=20), 1)
add("nav_cameras", bm, [M["black"], M["glass"]], (1, 0, 1), 0.12, 4, "항법 카메라 쌍",
    "두 눈처럼 떨어진 카메라로 거리를 재서 장애물을 피하고, GPS 없이도 위치를 추정한다", bevel=0.0005)

# ─────────── 4 자율비행 컴퓨터 — 방열판을 얹은 AI 모듈 ───────────
bm = bmesh.new()
chips = ex.bm_pcb(bm, (0.060, 0.050, 0.0016), T((0.045, 0, 0.013)),
                  chips=[(-0.021, 0.012, 0.008, 0.007, 0.0012, 'bga', "LPDDR 메모리",
                          "AI 칩이 영상과 지도를 계산하는 동안 잠깐 담아 두는 고속 메모리"),
                         (-0.021, -0.010, 0.008, 0.006, 0.0012, 'bga', "eMMC 저장장치",
                          "운영체제와 AI 프로그램을 전원이 꺼져도 남게 저장한다"),
                         (-0.021, 0.001, 0.005, 0.005, 0.0009, 'qfn', "전원 관리 칩(PMIC)",
                          "여러 전압을 정해진 순서로 켜서 AI 칩에 안정적인 전원을 준다"),
                         (-0.027, 0.001, 0.003, 0.003, 0.0015, 'inductor'),
                         (0.025, -0.020, 0.005, 0.006, 0.0030, 'conn', "카메라 입력 커넥터(MIPI)",
                          "항법 카메라 영상을 AI 칩으로 받아들이는 고속 단자"),
                         (-0.012, 0.021, 0.003, 0.002, 0.0008, 'crystal'),
                         (-0.015, 0.006, 0.002, 0.001, 0.0006, 'passive'), (-0.015, -0.004, 0.002, 0.001, 0.0006, 'passive'),
                         (-0.027, 0.012, 0.002, 0.001, 0.0006, 'passive'), (-0.027, -0.010, 0.002, 0.001, 0.0006, 'passive')],
                  mats=(0, 1, 2, 3))
chips += [("AI 프로세서(SoC)", "예: NVIDIA Jetson 계열 모듈 — 영상으로 장애물·지형을 알아보고 갈 길을 계산한다. 방열판 바로 아래에 있다",
           (0.049, 0.004, 0.0245)),
          ("방열판", "AI 칩에서 나는 열을 얇은 핀 여러 장으로 퍼뜨려 공기로 식힌다", (0.064, -0.0155, 0.0245))]
ex.set_mat(ex.bm_box(bm, (0.030, 0.030, 0.0025), T((0.049, 0, 0.0151))), 4)               # SoC 모듈
ex.set_mat(ex.bm_box(bm, (0.034, 0.034, 0.0015), T((0.049, 0, 0.01715))), 5)               # 방열판 바닥
for k in range(7):
    ex.set_mat(ex.bm_box(bm, (0.034, 0.0012, 0.0065), T((0.049, -0.0155 + k * 0.00516, 0.02115))), 5)
ob = add("ai_computer", bm, PCB + [M["gunmetal"], M["metal"]], (0, 0, 1), 0.12, 4, "자율비행 컴퓨터",
         "카메라 영상으로 주변을 3D 로 그리고 경로를 스스로 짜는 AI 칩. 뜨거워서 방열판을 얹는다", bevel=0)
ex.attach_chips(ob, chips)

# ─────────── 4 데이터링크 무전 모듈 + 안테나 2개 — 배터리 위, 안테나는 덮개 위로 나온다 ───────────
bm = bmesh.new()
RX = -0.070
chips = ex.bm_pcb(bm, (0.040, 0.050, 0.0016), T((RX, 0, 0.012)),
                  chips=[(0.004, 0, 0.022, 0.030, 0.0025, 'can', "RF 모듈(차폐캔)",
                          "캔 속의 RF 트랜시버·증폭기가 영상·명령을 전파로 바꾼다. 금속 캔이 잡음을 막는다"),
                         (-0.014, 0.017, 0.005, 0.006, 0.0015, 'conn', "안테나 커넥터",
                          "작은 동축 단자. 여기서 안테나 선을 따라 전파가 나간다"),
                         (-0.014, -0.017, 0.005, 0.006, 0.0015, 'conn'),
                         (-0.013, 0.004, 0.004, 0.004, 0.0009, 'qfn', "암호화 칩",
                          "예시 — 데이터를 암호로 바꿔 엿들어도 내용을 알 수 없게 한다 (무전 칩 안에서 하기도 한다)"),
                         (-0.013, -0.006, 0.0025, 0.0015, 0.0010, 'sot', "전원 레귤레이터",
                          "배터리 전압을 무선 회로가 쓰는 깨끗한 전압으로 낮춘다"),
                         (-0.013, 0.011, 0.003, 0.002, 0.0008, 'crystal', "크리스털 발진기",
                          "무선 주파수를 정확히 맞추는 기준 박자를 만든다"),
                         (-0.0175, 0.000, 0.002, 0.001, 0.0006, 'passive'), (-0.0085, 0.000, 0.002, 0.001, 0.0006, 'passive'),
                         (-0.0175, -0.010, 0.002, 0.001, 0.0006, 'passive')], mats=(0, 1, 2, 3))
for s in (+1, -1):                                                                        # 동축선 + 안테나 막대
    ex.set_mat(ex.bm_cyl(bm, 0.0012, 0.0012, 0.012, 'X', T((RX - 0.021, s * 0.017, 0.0145)), segs=10), 1)
    ex.set_mat(ex.bm_cyl(bm, 0.0022, 0.0018, 0.046, 'Z', T((RX - 0.027, s * 0.017, 0.037)), segs=14), 1)
ob = add("datalink_radio", bm, PCB, (-1, 0, 0.5), 0.14, 4, "데이터링크 무전 모듈",
         "조종기와 영상·명령을 주고받는 무선. 군용은 보통 암호화한다. 안테나를 두 개 쓰면 한쪽이 약할 때 다른 쪽이 받아 끊김이 준다", bevel=0)
ex.attach_chips(ob, chips)

# ─────────── 5 GPS·나침반 모듈 — 덮개 바로 밑, 세라믹 패치 안테나가 하늘을 본다 ───────────
bm = bmesh.new()
GPS_C = Vector((-0.025, 0, 0.016))
chips = ex.bm_pcb(bm, (0.026, 0.026, 0.0016), T(GPS_C),
                  chips=[(0.0085, 0.006, 0.005, 0.005, 0.0009, 'qfn', "GPS 수신 칩",
                          "위성 신호가 오는 데 걸린 시간으로 거리를 재서, 위성 4개 이상이면 위치와 정확한 시각을 계산한다"),
                         (0.0085, -0.0025, 0.002, 0.002, 0.0008, 'qfn', "지자기 센서(나침반)",
                          "지구 자기장을 재서 기체 머리가 어느 쪽을 향하는지 알려 준다"),
                         (0.0085, -0.0085, 0.0025, 0.002, 0.0008, 'crystal', "TCXO(온도보상 발진기)",
                          "온도가 바뀌어도 거의 흔들리지 않는 박자를 만들어 약한 위성 신호를 잡는 걸 돕는다"),
                         (-0.003, -0.0105, 0.0025, 0.0015, 0.0010, 'sot', "저잡음 증폭기(LNA)",
                          "안테나로 들어온 아주 약한 위성 신호를 잡음 없이 키운다"),
                         (0.0035, -0.0105, 0.002, 0.001, 0.0006, 'passive'), (0.0035, 0.0105, 0.002, 0.001, 0.0006, 'passive'),
                         (-0.0095, 0.0105, 0.002, 0.001, 0.0006, 'passive')], mats=(0, 1, 2, 3))
PATCH = GPS_C + Vector((-0.003, 0, 0.0008))                                              # 세라믹 패치 안테나 (하늘을 본다)
ex.set_mat(ex.bm_box(bm, (0.014, 0.014, 0.004), T(PATCH + Vector((0, 0, 0.002)))), 3)
ex.set_mat(ex.bm_box(bm, (0.011, 0.011, 0.0001), T(PATCH + Vector((0, 0, 0.00405)))), 2)
ex.set_mat(ex.bm_cyl(bm, 0.0006, 0.0006, 0.0003, 'Z', T(PATCH + Vector((0.002, 0.002, 0.0042))), segs=10), 2)
chips.append(("세라믹 패치 안테나", "하늘을 향한 네모난 세라믹 판. 우주에서 오는 아주 약한 GPS 전파를 받는다",
              tuple(PATCH + Vector((0, 0, 0.004)))))
ob = add("gps_compass", bm, PCB, (-0.4, 0, 1), 0.14, 5, "GPS·나침반 모듈",
         "위성 신호로 위치를, 지자기 센서로 기체가 향한 방향을 잰다", bevel=0)
ex.attach_chips(ob, chips)

# ─────────── 5 비행 컨트롤러 — MCU·IMU·기압계. 방진 스탠드오프 위에 떠 있다 ───────────
bm = bmesh.new()
chips = ex.bm_pcb(bm, (0.045, 0.040, 0.0016), T((0.040, 0, 0.001)),
                  chips=[(0, 0, 0.010, 0.010, 0.0015, 'qfp', "MCU(마이크로컨트롤러)",
                          "예: STM32 계열 — 센서 값을 읽어 자세를 계산하고, 모터 4개의 세기를 1초에 수백~수천 번 정한다"),
                         (-0.013, 0.010, 0.003, 0.003, 0.0009, 'qfn', "IMU(자이로·가속도)",
                          "기체가 얼마나 기울고 얼마나 빨리 도는지 잰다. 비행 컨트롤러는 기체 무게중심 가까이 두는 게 좋다"),
                         (-0.013, -0.010, 0.003, 0.003, 0.0010, 'can', "기압계",
                          "공기 압력의 아주 작은 변화로 높이를 잰다. 바람의 영향을 줄이려 스펀지를 덮기도 한다"),
                         (0.013, 0.011, 0.005, 0.004, 0.0012, 'ic', "블랙박스 메모리(플래시)",
                          "비행 중 센서 값과 명령을 기록해, 사고가 나면 원인을 찾게 한다"),
                         (0.013, -0.004, 0.0025, 0.0015, 0.0010, 'sot', "전원 레귤레이터(3.3V)",
                          "5V 를 칩들이 쓰는 깨끗한 3.3V 로 낮춘다"),
                         (0.008, -0.0125, 0.0032, 0.0025, 0.0008, 'crystal', "크리스털 발진기",
                          "MCU 의 박자(클럭)를 정확하게 맞춘다"),
                         (0.017, -0.014, 0.006, 0.003, 0.0025, 'conn', "ESC 연결 커넥터",
                          "모터 명령 신호를 아래의 ESC 보드로 내보낸다"),
                         (-0.006, 0.0135, 0.002, 0.001, 0.0006, 'passive'), (-0.002, 0.0135, 0.002, 0.001, 0.0006, 'passive'),
                         (0.007, 0.0075, 0.002, 0.001, 0.0006, 'passive'), (-0.018, 0.002, 0.002, 0.001, 0.0006, 'passive'),
                         (-0.018, -0.004, 0.002, 0.001, 0.0006, 'passive'), (0.0035, -0.0085, 0.002, 0.001, 0.0006, 'passive')],
                  mats=(0, 1, 2, 3))
for (cx, cy) in ((0.021, 0.018), (0.021, -0.018), (0.059, 0.018), (0.059, -0.018)):        # 방진 스탠드오프
    ex.set_mat(ex.bm_cyl(bm, 0.0022, 0.0022, 0.004, 'Z', T((cx, cy, -0.0018)), segs=12), 4)
ob = add("flight_controller", bm, PCB + [M["black"]], (0.2, 0, 1), 0.09, 5, "비행 컨트롤러",
         "두뇌. IMU(기울기·회전)는 1초에 수백~수천 번, 기압계(고도)는 그보다 드물게 읽어 네 모터 세기를 정한다", bevel=0)
ex.attach_chips(ob, chips)

# ─────────── 5 4-in-1 ESC — 모터 넷을 구동하는 전력 보드 ───────────
bm = bmesh.new()
esc_chips = [(0, 0, 0.005, 0.005, 0.0009, 'qfn', "ESC 제어 MCU",
               "비행 컨트롤러의 명령을 받아 모터 코일에 전기를 넣을 순서와 세기를 정한다"),
              (-0.009, 0, 0.004, 0.004, 0.0009, 'qfn', "게이트 드라이버",
               "작은 제어 신호를 MOSFET 을 빠르게 켜고 끌 만큼 센 신호로 키운다"),
              (0.0085, 0, 0.0025, 0.0015, 0.0010, 'sot', "전류 센서",
               "모터로 흐르는 전류를 재서 너무 많이 흐르면 줄일 수 있게 한다"),
              (0.018, 0, 0.008, 0.008, 0.010, 'cap', "전해 커패시터",
               "모터 네 개가 한꺼번에 전기를 당길 때 전압이 출렁이지 않게 받쳐 준다")]
MOSFET = ("파워 MOSFET", "배터리 전기를 1초에 수만 번 켰다 껐다 해 모터 코일에 보내는 전자 스위치. 모터마다 여러 개가 한 조")
for sx in (-1, 1):                                                                        # 모터마다 MOSFET 두 개 (네 귀퉁이)
    for sy in (-1, 1):
        for k, dx in enumerate((-0.003, 0.003)):
            named = MOSFET if (sx > 0 and sy > 0 and k == 0) else ()                      # 이름표는 하나만
            esc_chips.append((sx * 0.0125 + dx, sy * 0.013, 0.005, 0.004, 0.0012, 'ic') + named)   # SO-8 형
esc_chips += [(-0.004, 0.006, 0.002, 0.001, 0.0006, 'passive'), (0.004, 0.006, 0.002, 0.001, 0.0006, 'passive'),
              (-0.004, -0.006, 0.002, 0.001, 0.0006, 'passive'), (0.004, -0.006, 0.002, 0.001, 0.0006, 'passive')]
chips = ex.bm_pcb(bm, (0.045, 0.045, 0.0016), T((0.040, 0, -0.012)), chips=esc_chips, mats=(0, 1, 2, 3))
ob = add("esc_4in1", bm, PCB + [M["gunmetal"]], (0.7, 0, 1), 0.16, 5, "4-in-1 ESC(모터 구동 보드)",
         "비행 컨트롤러의 명령대로 배터리 전력을 잘게 끊어 모터 네 개에 보낸다", bevel=0)
ex.attach_chips(ob, chips)

# ─────────── 6 배전 기판 — 바닥, 배터리 단자에서 전원을 나눈다 ───────────
bm = bmesh.new()
chips = ex.bm_pcb(bm, (0.060, 0.060, 0.0016), T((0.040, 0, -0.024)),
                  chips=[(-0.024, 0, 0.006, 0.012, 0.004, 'conn', "배터리 입력 단자",
                          "배터리 팩의 금속 단자가 여기에 꽂혀 전기가 들어온다"),
                         (-0.010, -0.012, 0.005, 0.004, 0.0012, 'ic', "역전압 보호 MOSFET",
                          "배터리를 거꾸로 꽂아도 회로가 타지 않게 전류를 막는다"),
                         (-0.008, 0.012, 0.005, 0.004, 0.0012, 'ic', "전류 센서",
                          "배터리에서 나가는 전류를 재서, 쓴 전기량으로 남은 배터리를 추정하게 한다"),
                         (0.010, 0.017, 0.004, 0.004, 0.0009, 'qfn', "5V 스위칭 레귤레이터",
                          "배터리 전압(예: 약 11V)을 카메라·컴퓨터가 쓰는 5V 로 효율 좋게 낮춘다"),
                         (0.018, 0.017, 0.005, 0.005, 0.0030, 'inductor'),
                         (0.010, -0.012, 0.0025, 0.0015, 0.0010, 'sot', "3.3V 레귤레이터",
                          "센서와 작은 칩들이 쓰는 3.3V 를 만든다"),
                         (0.020, -0.017, 0.006, 0.006, 0.008, 'cap', "전해 커패시터",
                          "전압이 순간적으로 떨어지지 않게 전기를 모아 두었다 내준다"),
                         (0.004, 0.004, 0.002, 0.001, 0.0006, 'passive'), (0.004, -0.004, 0.002, 0.001, 0.0006, 'passive'),
                         (0.016, 0.006, 0.002, 0.001, 0.0006, 'passive'), (0.016, -0.006, 0.002, 0.001, 0.0006, 'passive')],
                  mats=(0, 1, 2, 3))
for s in (+1, -1):
    ex.set_mat(ex.bm_box(bm, (0.050, 0.004, 0.0006), T((0.040, s * 0.024, -0.0229))), 2)   # 굵은 구리 전원선 패드
ob = add("power_board", bm, PCB, (0, 0, 1), 0.05, 6, "배전 기판",
         "배터리 전원을 받아 ESC 로 보내고, 보드들이 쓰는 5V·3.3V 를 만든다", bevel=0)
ex.attach_chips(ob, chips)

for ob in parts:
    ex.add_explode_drivers(ob, root)
ex.key_explode(root, 1, 60)

# 카메라: 옆(-Y)에서 내려다본다. 3/4 로 보면 한쪽 암이 카메라를 향해 막대처럼 보인다.
ex.apply_look(LOOK, dict(cam_loc=(0.12, -1.05, 0.80), target=(-0.01, 0, 0.04), lens=42), OUT)

# ---- 검증 ----
ok = ex.verify_explode(parts)
dg = bpy.context.evaluated_depsgraph_get()


def world_bbox(o):
    ev = o.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


by_name = {o.name.split("_", 2)[2]: o for o in parts}
INSIDE = ("ai_computer", "gps_compass", "flight_controller", "esc_4in1", "power_board", "battery_cells")
sc.frame_set(1)
lo_b, hi_b = (-BX - 0.001, -BY - 0.001, -BZ - 0.001), (BX + 0.001, BY + 0.001, BZ + 0.001)
bad = [n for n in INSIDE if not all(lo_b[i] <= world_bbox(by_name[n])[0][i] and
                                     world_bbox(by_name[n])[1][i] <= hi_b[i] for i in range(3))]
print("VERIFY internals-inside-body", "OK" if not bad else bad)

# 완전 분해에서 부품끼리 경계상자가 겹치지 않는가 (같은 모터의 로터·코일, 기준 부품끼리는 뺀다)
sc.frame_set(60)
dg = bpy.context.evaluated_depsgraph_get()
boxes = {o.name: world_bbox(o) for o in parts}
over = []
names = list(boxes)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        if {a.split("_", 2)[2], b.split("_", 2)[2]} <= {"frame", "gimbal"}:
            continue
        (la, ha), (lb, hb) = boxes[a], boxes[b]
        if all(la[k] < hb[k] - 0.001 and lb[k] < ha[k] - 0.001 for k in range(3)):
            over.append((a, b))
print("VERIFY exploded-no-overlap", "OK" if not over else over)
sc.frame_set(1)

ex.report(CODE, parts, os.path.join(OUT, "parts.md"))
ex.save_and_render(OUT, argv, get)
