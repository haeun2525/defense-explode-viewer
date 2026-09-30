"""sb300 — Switchblade 300 배회탄약 분해 씬.

사실 확인(2026-09-30): 문구는 factcheck/sb300.md 의 출처 기준. 내부 배치·칩은 예시(개념도)다.

실행: Blender -b --factory-startup --python products/sb300.py -- [--render] [--frames 1,20,40,60] [--pct 100]
+X 전방. 전장 약 0.49m(튜브 제외), 동체 폭 0.08m. 외형 레퍼런스: 카본 동체 + 앞/뒤 긴 날개 X 배치.
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

CODE = "sb300"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
LOOK = argv[argv.index("--look") + 1] if "--look" in argv else "real"   # real | holo | white | armory
OUT = os.path.join(HERE, "..", "out", CODE if LOOK == "real" else f"{CODE}_{LOOK}")
os.makedirs(OUT, exist_ok=True)


def arg(name, default):
    return argv[argv.index(name) + 1] if name in argv else default


# 치수 (m)
BODY_R, BODY_RR, BODY_L, BODY_FLAT = 0.040, 0.032, 0.360, 0.72  # 앞 반경, 뒤 반경, 길이, 세로 납작 비
BODY_HZ = BODY_R * BODY_FLAT                                     # 동체 반높이 0.029
TUBE_R, TUBE_L = 0.070, 0.620
WING_CHORD, WING_SPAN, WING_T, WING_TIP = 0.036, 0.260, 0.004, 0.028
WING_PIVOT_X = 0.060
TAIL_CHORD, TAIL_SPAN, TAIL_T = 0.030, 0.220, 0.004
TAIL_PIVOT_X = -0.120

sc = ex.reset_scene()
coll = bpy.data.collections.new(CODE)
sc.collection.children.link(coll)
M = ex.standard_materials(CODE, ("carbon", "gunmetal", "glass", "olive",   # glass 는 렌즈에만
                                  "black", "pcb", "metal", "gold", "ceramic", "copper", "cell"))
root = ex.make_root(CODE, coll, max_order=6)
root["wing_deploy"] = 1.0
root.id_properties_ui("wing_deploy").update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
                                            description="0 = 접힘(튜브 안), 1 = 펼침 — 주날개·꼬리날개 공통")
T = Matrix.Translation
parts = []


def add(name, bm, mat, direction, dist, order, label, desc="", **kw):
    ob = ex.part_object(f"{CODE}_{len(parts) + 1:02d}_{name}", bm, mat, coll, root, **kw)
    ex.set_meta(ob, direction, dist, order, label, desc)
    parts.append(ob)
    return ob


def flatten(verts, k=BODY_FLAT):
    for v in verts:
        v.co.z *= k


# 01 발사 튜브 — 원통 + 양 끝 보강 링
bm = bmesh.new()
ex.bm_cyl(bm, TUBE_R, TUBE_R, TUBE_L, 'X', T((-0.010, 0, 0)), segs=64, caps=False)
for x in (-0.010 - TUBE_L / 2 + 0.012, -0.010 + TUBE_L / 2 - 0.012):
    ex.set_mat(ex.bm_cyl(bm, TUBE_R + 0.0045, TUBE_R + 0.0045, 0.024, 'X', T((x, 0, 0)), segs=64, caps=False), 1)
# 무광 올리브 복합재 통. 분해가 시작되면 위로 화면 밖까지 빠지며 드론을 드러낸다.
tube = add("launch_tube", bm, [M["olive"], M["carbon"]], (0, 0, 1), 0.60, 1, "발사 튜브",
           "운반·발사용 통. 공압(압축 공기)으로 기체를 밀어내고, 그 뒤 접혀 있던 날개가 펼쳐진다", bevel=0)
sol = tube.modifiers.new("Solidify", 'SOLIDIFY')
sol.thickness, sol.offset = 0.004, -1
tube.visible_shadow = False  # 통이 빠지는 동안 안쪽 드론이 그림자에 묻히지 않게

# 02 동체(하부) — 뒤로 좁아지는 납작 타원을 z=0 에서 갈라 아래 반쪽만 + 하부 수직핀.
#    속이 빈 껍데기(Solidify)라 덮개를 열면 안쪽 전자장비가 보인다. 안테나는 데이터링크 부품으로 옮겼다.
def body_half(keep_top):
    bm = bmesh.new()
    flatten(ex.bm_cyl(bm, BODY_RR, BODY_R, BODY_L, 'X', segs=40))
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 0, 1),
                           clear_outer=not keep_top, clear_inner=keep_top)
    return bm


bm = body_half(False)
ex.bm_box(bm, (0.026, 0.004, 0.030), T((-0.168, 0, -BODY_HZ - 0.012)))
body = add("body", bm, M["carbon"], (0, 0, 1), 0.0, 0, "동체(하부)",
           "탄두·배터리·전자장비를 담는 원통형 몸통 (이 모델은 속을 보이려고 위아래로 나눴다)", bevel=0.001)
sol = body.modifiers.new("Solidify", 'SOLIDIFY')
sol.thickness, sol.offset = 0.0022, -1


def long_wing(bm, side, span, chord, t, tip, z):
    """피벗(루트)이 원점인 평판 날개 + 끝이 아래로 꺾인 윙팁. 피벗 기준 +side 방향으로 뻗는다."""
    ex.bm_box(bm, (chord, span - tip, t), T((0, side * (span - tip) / 2, z)))
    hinge = Vector((0, side * (span - tip), z))
    R = Matrix.Rotation(math.radians(-side * 25), 4, 'X')
    ex.bm_box(bm, (chord * 0.9, tip, t), T(hinge) @ R @ T((0, side * tip / 2, 0)))


# 03/04 주날개 — 동체 상면. 좌우 높이를 엇갈려 접힘 시 겹치지 않게.
wing_z = {+1: BODY_HZ + 0.003, -1: BODY_HZ + 0.009}
for side, nm, lb in ((+1, "wing_left", "주날개(좌)"), (-1, "wing_right", "주날개(우)")):
    bm = bmesh.new()
    long_wing(bm, side, WING_SPAN, WING_CHORD, WING_T, WING_TIP, wing_z[side])
    bmesh.ops.translate(bm, vec=(WING_PIVOT_X, 0, 0), verts=bm.verts)
    add(nm, bm, M["carbon"], (0, side, 0), 0.16, 3, lb, "앞뒤 두 쌍 날개(탠덤) 중 앞날개. 튜브 안에서 접혀 있다가 발사 직후 스프링 힘으로 펴진다",
        bevel=0.0012)

# 05/06 꼬리날개 — 동체 하면 후방, 앞으로 접힌다.
tail_z = {+1: -BODY_HZ - 0.003, -1: -BODY_HZ - 0.009}
for side, nm, lb in ((+1, "tail_left", "꼬리날개(좌)"), (-1, "tail_right", "꼬리날개(우)")):
    bm = bmesh.new()
    long_wing(bm, side, TAIL_SPAN, TAIL_CHORD, TAIL_T, 0.02, tail_z[side])
    bmesh.ops.translate(bm, vec=(TAIL_PIVOT_X, 0, 0), verts=bm.verts)
    add(nm, bm, M["carbon"], (0, side * 0.8, -0.6), 0.12, 4, lb, "탠덤 날개 중 뒷날개. 튜브 안에서 접혀 있다가 발사 직후 펴져 양력과 안정을 준다",
        bevel=0.0012)

# 07 카메라 헤드 — 둥근 돔 + 렌즈 3개 (금속 링, 검은 조리개, 유리)
HX, HR, HLX = BODY_L / 2, 0.042, 1.2     # 돔 시작 x, 반경, 앞쪽 늘림
bm = bmesh.new()
dome = ex.bm_hemisphere(bm, HR, 'X', T((HX, 0, 0)), segs=40)
for v in dome:
    v.co.x = HX + (v.co.x - HX) * HLX
    v.co.z *= 0.8
for ly, lz, lr in ((0.012, 0.006, 0.011), (-0.016, 0.009, 0.006), (-0.012, -0.012, 0.005)):
    sx = HX + HR * HLX * math.sqrt(max(0.0, 1 - (ly / HR) ** 2 - (lz / (HR * 0.8)) ** 2))
    ex.set_mat(ex.bm_cyl(bm, lr, lr, 0.012, 'X', T((sx, ly, lz)), segs=32), 1)
    ex.set_mat(ex.bm_cyl(bm, lr * 0.72, lr * 0.72, 0.002, 'X', T((sx + 0.0055, ly, lz)), segs=32), 0)
    ex.set_mat(ex.bm_hemisphere(bm, lr * 0.7, 'X', T((sx + 0.0062, ly, lz)), segs=24), 2)
add("camera_head", bm, [M["carbon"], M["gunmetal"], M["glass"]], (1, 0, 0), 0.12, 2, "카메라 헤드",
    "주간(EO)·열상(IR) 카메라가 들어가는 부분. Block 20 은 카메라가 앞쪽에서 왼쪽까지 돌아가며 본다(패닝)", bevel=0.0006)

# 08 모터 블록 — 원뿔대 + 냉각 링 3줄
MX = -BODY_L / 2 - 0.020
bm = bmesh.new()
ex.bm_cyl(bm, 0.016, 0.025, 0.040, 'X', T((MX, 0, 0)))
for i, dx in enumerate((-0.010, 0.0, 0.010)):
    r = 0.0205 + dx * 0.45
    ex.set_mat(ex.bm_cyl(bm, r + 0.0025, r + 0.0025, 0.003, 'X', T((MX + dx, 0, 0))), 1)
add("motor_block", bm, [M["gunmetal"], M["carbon"]], (-1, 0, 0), 0.08, 5, "모터 블록",
    "배터리 전기로 프로펠러를 돌리는 전기 모터 — 소리가 작다")

# 09 프로펠러 2엽 — 끝이 좁아지는 블레이드, 피치 22도 + 스피너
PX = MX - 0.020 - 0.008
bm = bmesh.new()
ex.set_mat(ex.bm_cyl(bm, 0.011, 0.011, 0.012, 'X', T((PX, 0, 0))), 1)
ex.set_mat(ex.bm_hemisphere(bm, 0.011, 'X', T((PX - 0.006, 0, 0)) @ Matrix.Rotation(math.pi, 4, 'Z')), 1)
for s in (+1, -1):
    vs = ex.bm_box(bm, (0.003, 0.056, 0.016))
    for v in vs:
        if v.co.y > 0:
            v.co.z *= 0.55
    bmesh.ops.transform(bm, verts=vs, matrix=T((PX, s * 0.037, 0)) @
                        Matrix.Rotation(math.radians(90 - 90 * s), 4, 'X') @
                        Matrix.Rotation(math.radians(22), 4, 'Y'))
add("propeller", bm, [M["gunmetal"], M["carbon"]], (-1, 0, 0), 0.17, 2, "프로펠러",
    "꼬리에서 기체를 앞으로 밀어 주는 추진 프로펠러", bevel=0.0008)

# 10 탄두 블록 — 동체 내부 전방, 금속 원통 + 앞쪽 원뿔
bm = bmesh.new()
ex.bm_cyl(bm, 0.024, 0.024, 0.070, 'X', T((0.095, 0, 0)))
ex.bm_cyl(bm, 0.024, 0.012, 0.018, 'X', T((0.139, 0, 0)))
ex.set_mat(ex.bm_cyl(bm, 0.0255, 0.0255, 0.006, 'X', T((0.075, 0, 0))), 1)
add("warhead", bm, [M["gunmetal"], M["carbon"]], (0, 0, -1), 0.13, 6, "탄두",
    "교체식 탄두 — 파편형(대인)이나 관통형(EFP, 경장갑) 중 골라 넣는다. 내부는 다루지 않고 덩어리로만 표현")

# ─── 내부 장비 ───────────────────────────────────────────────────────────────
# 공개된 일반 구성(카메라·비행제어·데이터링크·배터리·모터 구동기)을 바탕으로 한 배치. 실제 설계도 아님.
# 앞에서부터: 카메라 헤드 속 [영상처리 보드 · 주간 카메라 · 열상 센서] | 탄두 | 날개 전개 장치 / 안전·장전 장치
#            | 데이터링크 | 비행제어 컴퓨터(배터리 위) · 배터리 | 모터 구동기 | 모터
# 동체 안쪽 반높이는 앞 0.027, 뒤 0.021 정도 (껍데기 두께 제외). 덮개가 열린 뒤(order 4) 마지막(order 6)에 빠져나온다.
PCB_MATS = [M["pcb"], M["black"], M["metal"], M["ceramic"]]      # 칩 다리·차폐캔은 은색 주석 도금

# 11 동체 덮개 — 위쪽 반쪽 껍데기. 날개가 옆으로 빠진 다음(order 4) 위로 들린다.
bm = body_half(True)
hatch = add("body_hatch", bm, M["carbon"], (0, 0, 1), 0.16, 4, "동체 덮개",
            "속을 보이려고 이 모델에서 만든 위쪽 덮개. 실제 기체가 이렇게 열리는 것은 아니다", bevel=0.001)
sol = hatch.modifiers.new("Solidify", 'SOLIDIFY')
sol.thickness, sol.offset = 0.0022, -1

# 12 비행제어 컴퓨터 — 배터리 위 기판. 칩 이름은 기능 기준 (예시 계열은 설명에만, 실제 부품이라는 뜻 아님)
FC_C = Vector((-0.080, 0, 0.011))
bm = bmesh.new()
fc_chips = ex.bm_pcb(bm, (0.058, 0.040, 0.0016), T(FC_C), chips=(
    (0.004, 0.000, 0.012, 0.012, 0.0014, 'qfp', "MCU(마이크로컨트롤러)",
     "센서 값을 모아 자세·경로를 계산하고 조종면·모터에 명령을 내리는 주 연산 칩 (예시 부품. 예: STM32 계열)"),
    (-0.006, -0.012, 0.004, 0.004, 0.0009, 'qfn', "IMU(자이로·가속도)",
     "기체가 얼마나 기울고 도는지를 아주 빠르게 반복해 잰다 (예시 부품)"),
    (0.001, -0.013, 0.003, 0.003, 0.0008, 'qfn', "기압 고도계",
     "공기 압력 변화로 지금 높이를 잰다 (예시 부품)"),
    (-0.017, -0.004, 0.013, 0.012, 0.0025, 'can', "GPS 수신 모듈",
     "위성 신호로 현재 위치와 정확한 시각을 알아낸다 (예시 부품). 위의 네모난 세라믹이 패치 안테나"),
    (0.020, 0.004, 0.005, 0.004, 0.0011, 'ic', "플래시 메모리",
     "비행 기록과 임무 설정을 전원이 꺼져도 저장한다 (예시 부품)"),
    (-0.017, 0.007, 0.003, 0.0016, 0.0009, 'sot', "전원 레귤레이터",
     "배터리 전압을 칩들이 쓰는 낮은 전압(예: 3.3V)으로 일정하게 맞춘다"),
    (0.013, -0.004, 0.0032, 0.0015, 0.0008, 'crystal', "크리스털 발진기",
     "MCU 의 시계 — 일정한 박자를 만들어 모든 계산 타이밍을 맞춘다"),
    (0.022, -0.012, 0.008, 0.005, 0.003, 'conn', "서보·ESC 커넥터",
     "조종면을 움직이는 장치와 모터 구동기로 명령을 보내는 선을 꽂는 단자 (예시)"),
    # 뒤쪽 줄(+y)은 이름 없는 부품만 — 부품 보기에서 기판 라벨이 뒤 가장자리 위에 붙으니 이름표가 겹치지 않게
    (0.024, 0.014, 0.003, 0.003, 0.004, 'cap'),                  # 전원 안정용 전해 커패시터
    (-0.010, 0.015, 0.003, 0.003, 0.004, 'cap'),
    (0.008, 0.016, 0.002, 0.001, 0.0006, 'passive'),
    (0.012, 0.016, 0.002, 0.001, 0.0006, 'passive'),
    (-0.002, 0.016, 0.002, 0.001, 0.0006, 'passive'),
    (-0.022, 0.015, 0.002, 0.001, 0.0006, 'passive'),
    (0.009, -0.013, 0.002, 0.001, 0.0006, 'passive'),
), mats=(0, 1, 2, 3))
ex.set_mat(ex.bm_box(bm, (0.009, 0.009, 0.0018), T(FC_C + Vector((-0.017, -0.004, 0.0008 + 0.0025 + 0.0009)))), 3)  # GPS 패치 안테나
fc = add("flight_computer", bm, PCB_MATS, (0, 0, 1), 0.06, 6, "비행제어 컴퓨터",
         "GPS 로 위치를, 자세 센서로 기울기를 알아내 조종면과 모터를 움직이는 두뇌. 칩 구성은 이런 장치의 일반적인 예시", bevel=0.0002, segments=1)   # 칩 다리 수백 개라 모서리는 1단만
ex.attach_chips(fc, fc_chips)

# 13 데이터링크 무전 모듈 + 안테나 — 무선 기판(RF 부분은 차폐캔), 위로 동체를 뚫고 나가는 막대 안테나
bm = bmesh.new()
dl_chips = ex.bm_pcb(bm, (0.046, 0.034, 0.0016), T((-0.006, 0, 0.000)), chips=(
    (0.006, 0.006, 0.016, 0.014, 0.003, 'can', "RF 트랜시버(차폐캔 속)",
     "데이터를 무선 신호로 바꿔 보내고 받는다. 캔은 전파 간섭을 막는다 (예시 부품)"),
    (0.010, -0.010, 0.004, 0.004, 0.0009, 'qfn', "전력 증폭기(PA)",
     "보낼 신호를 세게 키워 멀리 있는 조종기까지 닿게 한다 (예시 부품)"),
    (-0.008, -0.006, 0.007, 0.007, 0.0014, 'bga', "암호화 프로세서",
     "영상·명령을 암호화한다 — 제조사는 AES-256 암호화를 지원한다고 밝힘. 칩 자체는 예시"),
    (-0.008, 0.009, 0.0032, 0.0025, 0.0009, 'crystal', "정밀 발진기(TCXO)",
     "온도가 바뀌어도 무선 주파수가 흔들리지 않게 잡아 준다 (예시 부품)"),
    (-0.019, 0.010, 0.005, 0.006, 0.003, 'conn', "안테나 커넥터",
     "안테나 선을 꽂는 작은 고주파 단자"),
    (-0.019, -0.008, 0.003, 0.0016, 0.0009, 'sot', "전원 레귤레이터",
     "무선 칩이 쓰는 깨끗한 전압을 만든다 (예시 부품)"),
    (0.018, -0.012, 0.002, 0.001, 0.0006, 'passive'),
    (0.018, -0.008, 0.002, 0.001, 0.0006, 'passive'),
    (-0.013, 0.014, 0.002, 0.001, 0.0006, 'passive'),
    (0.003, -0.013, 0.0025, 0.0025, 0.0012, 'inductor'),          # RF 정합용 코일
), mats=(0, 1, 2, 3))
ex.set_mat(ex.bm_cyl(bm, 0.0015, 0.0015, 0.050, 'Z', T((0.012, 0, 0.030)), segs=12), 2)   # 안테나 막대
ex.set_mat(ex.bm_cyl(bm, 0.0030, 0.0030, 0.006, 'Z', T((0.012, 0, 0.008)), segs=16), 1)   # 안테나 받침
dl = add("datalink", bm, PCB_MATS, (0.3, 0, 1), 0.08, 6, "데이터링크 무전 모듈",
         "주파수를 바꿔 가며(호핑) 조종기와 영상·명령을 주고받는 암호화 디지털 데이터링크와 안테나. 칩 구성은 예시", bevel=0.0002, segments=1)   # 칩 다리 수백 개라 모서리는 1단만
ex.attach_chips(dl, dl_chips + [("막대 안테나", "전파를 공중으로 내보내고 받는다. 동체 위로 튀어나와 가려지지 않게 한다",
                                 (0.012, 0, 0.055))])

# 14 리튬 배터리 팩 — 원통 셀 3개를 나란히, 양 끝에 니켈 연결판, 수축 필름 대신 셀이 보이게 둔다
bm = bmesh.new()
for cy in (-0.0175, 0.0, 0.0175):
    ex.set_mat(ex.bm_cyl(bm, 0.0085, 0.0085, 0.066, 'X', T((-0.080, cy, -0.006)), segs=24), 0)
    ex.set_mat(ex.bm_cyl(bm, 0.0035, 0.0035, 0.0012, 'X', T((-0.0466, cy, -0.006)), segs=16), 1)   # + 단자
for x in (-0.1135, -0.0460):
    ex.set_mat(ex.bm_box(bm, (0.0008, 0.050, 0.010), T((x, 0, -0.006))), 1)                    # 니켈 연결판
ex.set_mat(ex.bm_box(bm, (0.010, 0.006, 0.004), T((-0.118, 0.012, 0.004))), 2)                 # 배선 커넥터
add("battery", bm, [M["cell"], M["metal"], M["black"]], (0, -1, 0.5), 0.09, 6, "리튬 배터리 팩",
    "모터와 전자장비에 전기를 대는 리튬이온 전지 묶음. 셀 수·배치는 예시", bevel=0.0005)

# 15 모터 구동기(ESC) — 모터 바로 앞 작은 기판: 파워 MOSFET 6개(3상 × 위/아래) + 제어 칩 + 굵은 모터 선 단자
bm = bmesh.new()
chips = []
for i in range(6):
    x, y = (-0.0065, 0.0005, 0.0075)[i % 3], (-0.008, 0.008)[i // 3]
    chips.append((x, y, 0.005, 0.006, 0.001, 'qfn') + (("파워 MOSFET(×6)",
                  "배터리 전류를 아주 빠르게 켰다 껐다 해 모터 코일에 번갈아 전기를 준다 (예시 부품)") if i == 0 else ()))
chips += [
    (0.0045, 0.0, 0.004, 0.004, 0.0009, 'qfn', "모터 제어 MCU",
     "모터가 지금 어느 각도인지 추정해 어느 코일에 전기를 줄지 정한다 (예시 부품)"),
    (-0.0035, 0.0, 0.0035, 0.0035, 0.0009, 'qfn', "게이트 드라이버",
     "MCU 의 약한 신호를 MOSFET 을 여닫을 만큼 센 전압으로 키운다 (예시 부품)"),
    (0.0125, 0.0, 0.005, 0.005, 0.006, 'cap', "입력 커패시터",
     "모터가 순간적으로 큰 전류를 당길 때 전압이 출렁이지 않게 받쳐 준다 (예시)"),
    (-0.0135, 0.0, 0.0025, 0.014, 0.004, 'conn', "모터 선 단자",
     "모터로 가는 굵은 선 3가닥이 연결되는 곳"),
    (0.0125, -0.0145, 0.003, 0.0015, 0.0006, 'passive'),          # 전류 감지 저항
    (0.0125, 0.0145, 0.002, 0.001, 0.0006, 'passive'),
]
esc_chips = ex.bm_pcb(bm, (0.032, 0.036, 0.0016), T((-0.140, 0, -0.004)), chips=chips, mats=(0, 1, 2, 3))
for cy in (-0.008, 0.0, 0.008):                                                                # 모터 선 3가닥
    ex.set_mat(ex.bm_cyl(bm, 0.0012, 0.0012, 0.012, 'X', T((-0.161, cy, -0.002)), segs=10), 4)
esc = add("esc", bm, PCB_MATS + [M["copper"]], (-0.3, 0, 1), 0.07, 6, "모터 구동기(ESC)",
          "배터리 전기로 전기 모터의 회전 속도를 조절하는 회로. 이런 소형 기체는 보통 브러시리스 모터와 이런 구동기를 쓴다 (일반 구성)", bevel=0.0002, segments=1)   # 칩 다리 수백 개라 모서리는 1단만
ex.attach_chips(esc, esc_chips)

# 16 날개 전개 장치 — 주날개 피벗 바로 뒤: 걸쇠 블록 + 비틀림 스프링(구리색 코일 두 개)
bm = bmesh.new()
ex.set_mat(ex.bm_box(bm, (0.022, 0.030, 0.008), T((0.042, 0, 0.012))), 0)
for cy in (-0.009, 0.009):
    ex.set_mat(ex.bm_cyl(bm, 0.0045, 0.0045, 0.010, 'Y', T((0.042, cy, 0.0205)), segs=16), 1)
ex.set_mat(ex.bm_box(bm, (0.006, 0.006, 0.006), T((0.050, 0, 0.005))), 2)                     # 해제 솔레노이드
add("wing_actuator", bm, [M["gunmetal"], M["copper"], M["black"]], (1, 0, 1.2), 0.11, 6, "날개 전개 장치",
    "날개는 스프링식이라 튜브를 빠져나오면 펴진다. 이 부품의 모양·구조는 개념도", bevel=0.0004)

# 17 안전·장전 장치 — 탄두 바로 뒤 아래쪽 밀봉 원통 (내부 구조 없음)
bm = bmesh.new()
ex.bm_cyl(bm, 0.013, 0.013, 0.018, 'X', T((0.043, 0, -0.010)), segs=24)
ex.set_mat(ex.bm_box(bm, (0.004, 0.006, 0.004), T((0.032, 0, -0.010))), 1)                     # 배선 단자
add("safe_arm", bm, [M["gunmetal"], M["black"]], (0, 0, -1), 0.07, 6, "안전·장전 장치",
    "유도탄에 보통 들어가는 안전 장치 개념 — 정해진 조건 전에는 탄두가 작동하지 못하게 막는다. 실제 구조는 공개되지 않음", bevel=0.0005)

# 18~20 카메라 헤드 속 — 돔(07)이 앞으로 빠지면 드러난다. 렌즈 창 위치에 맞춰 둔다.
#    돔: x 0.18 ~ 0.23, 반경 y 0.042 · z 0.034
bm = bmesh.new()                    # 돔 안에 앞을 보게 세운 기판 (기판 x → 세계 −z, y → 세계 y). 앞 카메라와 안 닿게 칩은 얇게
vb_chips = ex.bm_pcb(bm, (0.040, 0.050, 0.0016), T((0.1825, 0, 0)) @ ex.rot('X'), chips=(
    (0.004, -0.008, 0.010, 0.010, 0.0012, 'bga', "영상처리 SoC",
     "영상을 압축해 무전기로 넘기고, 고른 목표를 계속 따라가게 계산한다 (예시 부품)"),
    (-0.010, 0.012, 0.008, 0.006, 0.0011, 'bga', "메모리(DRAM)",
     "영상을 처리하는 동안 화면 여러 장을 잠시 담아 두는 작업 공간 (예시 부품)"),
    (0.010, 0.014, 0.005, 0.004, 0.0010, 'ic', "플래시 메모리",
     "영상 처리 프로그램(펌웨어)을 저장한다 (예시 부품)"),
    (-0.011, -0.010, 0.004, 0.004, 0.0009, 'qfn', "전원 관리 칩(PMIC)",
     "SoC 에 필요한 여러 전압을 정해진 순서대로 켜 준다 (예시 부품)"),
    (0.012, 0.004, 0.0032, 0.0025, 0.0008, 'crystal', "크리스털 발진기",
     "영상 칩의 기준 박자를 만든다 (예시 부품)"),
    (0.000, 0.021, 0.010, 0.003, 0.0012, 'conn', "카메라 커넥터",
     "카메라 영상 신호 케이블이 꽂히는 납작한 단자 (예시)"),
    (-0.004, 0.004, 0.002, 0.001, 0.0006, 'passive'),
    (-0.001, 0.004, 0.002, 0.001, 0.0006, 'passive'),
    (0.015, -0.016, 0.002, 0.001, 0.0006, 'passive'),
    (-0.016, 0.001, 0.0025, 0.0025, 0.0010, 'inductor'),          # PMIC 전원 코일
), mats=(0, 1, 2, 3))
vb = add("video_board", bm, PCB_MATS, (0, 0, 1), 0.05, 6, "영상처리 보드",
         "카메라 영상을 압축해 무전기로 보내고, 고른 목표를 계속 따라가게 돕는다(목표 추적 보조). 보드 구성은 예시", bevel=0.0002, segments=1)   # 칩 다리 수백 개라 모서리는 1단만
ex.attach_chips(vb, vb_chips)

bm = bmesh.new()                                                     # 큰 렌즈(0.012, 0.006) 뒤
eo_chips = ex.bm_pcb(bm, (0.018, 0.018, 0.0016), T((0.1865, 0.012, 0.006)) @ ex.rot('X'), chips=(   # 센서 기판 (렌즈 쪽이 앞)
    (0.0, 0.0, 0.009, 0.009, 0.0012, 'bga', "이미지 센서(CMOS)",
     "렌즈가 모은 빛을 화소 하나하나가 전기 신호로 바꾼다 (예시 부품)"),
    (0.0065, -0.0065, 0.0025, 0.0015, 0.0008, 'sot'),             # 센서 전원
    (-0.0065, 0.0065, 0.002, 0.001, 0.0006, 'passive'),
), mats=(3, 1, 4, 5))
ex.bm_cyl(bm, 0.0085, 0.0085, 0.016, 'X', T((0.198, 0.012, 0.006)), segs=24)                    # 렌즈 경통
ex.set_mat(ex.bm_cyl(bm, 0.0065, 0.0065, 0.001, 'X', T((0.2065, 0.012, 0.006)), segs=24), 2)    # 앞 렌즈
eo = add("eo_camera", bm, [M["gunmetal"], M["black"], M["glass"], M["pcb"], M["metal"], M["ceramic"]],
         (0.4, 1, 0), 0.05, 6, "주간(EO) 카메라", "낮에 쓰는 컬러 카메라 — 렌즈와 이미지 센서. 모양은 개념도", bevel=0.0003, segments=1)
ex.attach_chips(eo, eo_chips + [("렌즈 경통", "렌즈가 빛을 모아 이미지 센서 위에 상을 맺는다 (예시)",
                                 (0.206, 0.012, 0.0145))])

bm = bmesh.new()                                                     # 작은 렌즈들(-0.016, 0.009)·(-0.012, -0.012) 뒤
ex.bm_box(bm, (0.018, 0.016, 0.016), T((0.196, -0.014, -0.002)))                               # 열상 코어(차폐 몸통)
ex.set_mat(ex.bm_cyl(bm, 0.0055, 0.0055, 0.004, 'X', T((0.207, -0.014, 0.004)), segs=20), 1)    # 게르마늄 렌즈(검게)
ex.set_mat(ex.bm_box(bm, (0.004, 0.012, 0.012), T((0.1865, -0.014, -0.002))), 1)                 # 뒤 판독 기판
ir = add("ir_sensor", bm, [M["metal"], M["black"]], (0.4, -1, 0), 0.05, 6, "열상(IR) 센서",
         "열을 보는 적외선 카메라 — 어둠 속에서도 사람·차량의 열을 볼 수 있다. 모양은 개념도", bevel=0.0003)
ex.attach_chips(ir, [
    ("마이크로볼로미터 코어", "소형 열상 카메라에 흔히 쓰는 센서(예시) — 열을 받으면 저항이 바뀌는 작은 판들이 온도 차를 그림으로 만든다", (0.196, -0.014, 0.006)),
    ("게르마늄 렌즈", "보통 유리는 열상용 적외선을 잘 통과시키지 못해, 열상 카메라 렌즈는 흔히 게르마늄으로 만든다 (예시)", (0.209, -0.014, 0.0095)),
    ("판독 회로(ROIC)", "센서 판 하나하나의 신호를 차례로 읽어 영상 신호로 보낸다 (예시)", (0.1865, -0.014, 0.004)),
])

for ob in parts:
    ex.add_explode_drivers(ob, root)


def fold_drivers(ob, side, px, h, direction):
    """피벗 (px, 0) 을 축으로 th = (1-dep)·90° 회전해 접는다. direction -1 = 뒤로, +1 = 앞으로.
    location = pivot + R·(0, side·h, 0),  rotation_z = direction·side·th 의 부호 규칙"""
    exprs = {
        ("location", 0): f"{px} + {direction}*{h}*sin((1-dep)*pi/2)",
        ("location", 1): f"{side}*{h}*cos((1-dep)*pi/2)",
        ("rotation_euler", 2): f"{-direction * side}*(1-dep)*pi/2",
    }
    for (path, idx), e in exprs.items():
        drv = ob.driver_add(path, idx).driver
        drv.type = 'SCRIPTED'
        ex._var(drv, "dep", root, '["wing_deploy"]')
        drv.expression = e
        assert drv.is_simple_expression, e


# 날개 origin 은 바운딩 중심이라 피벗에서 (span/2 근처) 떨어져 있다 → 실제 중심 거리로 계산
for ob, side, px, direction in ((parts[2], +1, WING_PIVOT_X, -1), (parts[3], -1, WING_PIVOT_X, -1),
                                (parts[4], +1, TAIL_PIVOT_X, +1), (parts[5], -1, TAIL_PIVOT_X, +1)):
    h = abs(ob.location.y)
    assert abs(ob.location.x - px) < 1e-6, ob.name
    fold_drivers(ob, side, px, h, direction)

# 키프레임: 1 조립 → 60 완전 분해 (순서별 시차는 드라이버가 처리)
ex.key_explode(root, 1, 60)
# 조립 상태는 튜브 안에 날개가 접힌 모습. 튜브가 빠지는 동안 펼친다.
for fr, v in ((1, 0.0), (12, 0.0), (26, 1.0)):
    root["wing_deploy"] = v
    root.keyframe_insert('["wing_deploy"]', frame=fr)

txt = bpy.data.texts.new("explode_tools.py")
txt.write('''import bpy

def set_explode(code, factor, wing=None):
    """explode_factor(0~1) 로 전 부품을 이동. 키프레임이 있으면 현재 프레임 값이 덮어쓴다."""
    root = bpy.data.objects[f"{code}_root"]
    root["explode_factor"] = max(0.0, min(1.0, factor))
    if wing is not None and "wing_deploy" in root:
        root["wing_deploy"] = max(0.0, min(1.0, wing))
    bpy.context.view_layer.update()

def parts(code):
    return sorted((o for o in bpy.data.objects if o.name.startswith(code + "_") and "explode_dir" in o),
                  key=lambda o: o.name)
''')

CAM = dict(cam_loc=(1.20, -1.30, 0.50), target=(-0.03, 0, 0.03), lens=55)
if LOOK == "holo":
    ex.apply_holo(CODE, parts, faint=[parts[0]], accent=[parts[9]])  # 튜브는 흐리게, 탄두(10번째)는 주황
    ex.studio_holo(**CAM)
elif LOOK == "armory":
    # 옆모습에 가깝게(약간 앞·위) 꽉 차게. 좌우로 벌어지는 날개가 보이도록 완전 측면은 피한다.
    ex.studio_armory(cam_loc=(0.55, -1.45, 0.55), target=(-0.03, 0, 0.02), lens=50,
                     bg_path=os.path.join(OUT, "bg.png"))
elif LOOK == "white":
    ex.studio_white(**CAM)
else:
    ex.studio(**CAM)

# ---- 검증 1: 프레임 60 에서 각 부품의 폭발 이동량이 dir*dist 인가 ----
sc.frame_set(60)
bad = []
for o in parts:
    moved = o.matrix_world.translation - o.location  # 부모가 원점 → 월드 - location = delta_location
    want = Vector(o["explode_dir"]) * o["explode_dist"]
    if (moved - want).length > 1e-4:
        bad.append((o.name, tuple(round(c, 4) for c in moved), tuple(round(c, 4) for c in want)))
print("VERIFY explode", "OK" if not bad else bad)

# ---- 검증 2: 접힌 상태(프레임 1)에서 모든 부품이 튜브 안(반경 TUBE_R)에 들어가는가 ----
sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
out = []
for o in parts[1:]:
    ev = o.evaluated_get(dg)
    mw = ev.matrix_world
    rmax = max(math.hypot(*(mw @ v.co).yz) for v in ev.data.vertices)
    if rmax > TUBE_R - 0.002:
        out.append((o.name, round(rmax, 4)))
print("VERIFY in-tube", "OK" if not out else out)

ex.report(CODE, parts, os.path.join(OUT, "parts.md"))
sc.frame_set(1)
ex.open_in_camera_view()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, os.path.basename(OUT) + ".blend"))

if "--render" in argv:
    sc.render.resolution_percentage = int(arg("--pct", "100"))
    for fr in (int(f) for f in arg("--frames", "1,20,40,60").split(",")):
        sc.frame_set(fr)
        sc.render.filepath = os.path.join(OUT, f"frame_{fr:02d}.png")
        bpy.ops.render.render(write_still=True)
