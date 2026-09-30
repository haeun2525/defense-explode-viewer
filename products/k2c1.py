"""k2c1 — K2C1 소총 분해 씬: 통상 분해(야전분해) 수준 부품 + 도트사이트 속 회로.

실행: Blender -b --factory-startup --python products/k2c1.py -- [--look armory] [--render] [--frames 1,20,40,60]
+X 총구, +Z 위, -Y 가 총의 오른쪽. 전장 0.97m(개머리판 폈을 때). 하부 총몸이 기준(고정).
· 전자부품은 조준경(도트사이트)에만 있다 — 몸체가 올라간 뒤 LED·회로 기판·코인 배터리·반사 렌즈·다이얼이 흩어진다.
· 기계 부품은 공개 교범의 통상 분해 수준 덩어리까지만 (방아쇠 뭉치는 한 덩어리, 격발 구조는 만들지 않는다).
· 치수·배치는 실루엣 근사이며 실물 도면이 아니다.
분해 순서: 1 개머리판·탄창·조준경 몸체 → 2 총열·장전손잡이·조준경 속·탄창 속 → 3 상부 총몸
         → 4 노리쇠 뭉치·복좌 스프링·가스 피스톤 → 5 방아쇠 뭉치
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

CODE = "k2c1"
argv, get = ex.parse_args()
LOOK = get("--look", "armory")
OUT = ex.out_dir(HERE, CODE, LOOK)

# 치수 (m) — 전장 -0.485 ~ +0.485
BUTT_X, MUZZLE_X = -0.485, 0.485
REC_X0, REC_X1 = -0.140, 0.120          # 총몸 앞뒤
UP_Z0, UP_Z1, REC_W = 0.000, 0.045, 0.032
LOW_Z0 = -0.050
HG_X1 = 0.360                           # 총열덮개 끝
RAIL_Z = UP_Z1
HINGE = Vector((REC_X0, -0.020, 0.0))   # 개머리판 접힘축 (오른쪽 뒤 모서리)
T = Matrix.Translation

sc = ex.reset_scene()
coll = bpy.data.collections.new(CODE)
sc.collection.children.link(coll)
M = ex.standard_materials(CODE, ("black", "gunmetal", "olive", "glass", "pcb", "metal", "gold", "ceramic", "led"))
root = ex.make_root(CODE, coll, max_order=5)
root["stock_extend"] = 1.0
root.id_properties_ui("stock_extend").update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
                                             description="0 = 오른쪽으로 접힘, 1 = 폄")
parts = []


def add(name, bm, mat, direction, dist, order, label, desc="", **kw):
    ob = ex.part_object(f"{CODE}_{len(parts) + 1:02d}_{name}", bm, mat, coll, root, **kw)
    ex.set_meta(ob, direction, dist, order, label, desc)
    parts.append(ob)
    return ob


def add_to(name, bm, mat, offset, order, label, desc="", **kw):
    """분해했을 때 놓일 자리를 이동량(m)으로 준다 → 방향·거리로 바꿔 add."""
    v = Vector(offset)
    return add(name, bm, mat, tuple(v.normalized()), v.length, order, label, desc, **kw)


def rail(bm, x0, x1, z, width, idx):
    """피카티니 레일: 바닥 띠 + 일정 간격 이빨."""
    ex.set_mat(ex.bm_box(bm, (x1 - x0, width * 0.7, 0.004), T(((x0 + x1) / 2, 0, z + 0.002))), idx)
    n = int((x1 - x0) / 0.010)
    for i in range(n):
        x = x0 + 0.005 + i * 0.010
        ex.set_mat(ex.bm_box(bm, (0.005, width, 0.004), T((x, 0, z + 0.006))), idx)


def slanted_box(bm, p0, p1, w, h):
    """p0→p1 (XZ 평면) 방향으로 뻗은 막대."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    return ex.bm_box(bm, (d.length, w, h), T((p0 + p1) / 2) @ Matrix.Rotation(-math.atan2(d.z, d.x), 4, 'Y'))


# 01 총열 + 총열덮개 (일체) — 사각 레일 덮개 + 총열 + 소염기
bm = bmesh.new()
hg_cx = (REC_X1 + HG_X1) / 2
ex.bm_box(bm, (HG_X1 - REC_X1, 0.046, 0.050), T((hg_cx, 0, 0.020)))
rail(bm, REC_X1 + 0.005, HG_X1 - 0.005, 0.045, 0.022, 0)
for x in (REC_X1 + 0.05, REC_X1 + 0.12, REC_X1 + 0.19):              # 방열 구멍 느낌의 홈
    ex.set_mat(ex.bm_box(bm, (0.030, 0.047, 0.008), T((x, 0, 0.012))), 1)
ex.set_mat(ex.bm_cyl(bm, 0.0095, 0.0095, MUZZLE_X - 0.045 - REC_X1, 'X',
                     T(((REC_X1 + MUZZLE_X - 0.045) / 2, 0, 0.018)), segs=24), 1)
ex.set_mat(ex.bm_cyl(bm, 0.012, 0.012, 0.045, 'X', T((MUZZLE_X - 0.0225, 0, 0.018)), segs=24), 1)   # 소염기
add("barrel_handguard", bm, [M["black"], M["gunmetal"]], (1, 0, 0), 0.16, 2, "총열·총열덮개",
    "안쪽 강선으로 탄이 회전을 얻는 총열과, 그 위를 감싸 손을 보호하는 덮개(부착용 레일 포함)", bevel=0.0015)

# 02 상부 총몸 — 박스 + 상단 레일 + 배출구 덮개
bm = bmesh.new()
ex.bm_box(bm, (REC_X1 - REC_X0, REC_W, UP_Z1 - UP_Z0), T(((REC_X0 + REC_X1) / 2, 0, (UP_Z0 + UP_Z1) / 2)))
rail(bm, REC_X0 + 0.010, REC_X1 - 0.005, RAIL_Z, 0.022, 0)
ex.set_mat(ex.bm_box(bm, (0.060, 0.002, 0.018), T((0.020, -REC_W / 2 - 0.001, 0.024))), 1)
upper = add("upper_receiver", bm, [M["gunmetal"], M["black"]], (0, 0, 1), 0.08, 3, "상부 총몸",
             "노리쇠 뭉치가 앞뒤로 움직이는 윗몸체. 위에 조준경을 다는 피카티니 레일이 있다", bevel=0.002)

# 03 하부 총몸 — 몸체 + 탄창 멈치 턱 + 방아쇠울 + 권총손잡이
bm = bmesh.new()
ex.bm_box(bm, (REC_X1 - REC_X0 - 0.020, REC_W - 0.002, UP_Z0 - LOW_Z0),
          T(((REC_X0 + REC_X1) / 2 - 0.010, 0, (LOW_Z0 + UP_Z0) / 2)))
ex.bm_box(bm, (0.070, REC_W, 0.020), T((0.060, 0, LOW_Z0 - 0.008)))           # 탄창 삽입구
ex.bm_box(bm, (0.060, 0.010, 0.006), T((-0.010, 0, LOW_Z0 - 0.024)))           # 방아쇠울 바닥
ex.bm_box(bm, (0.006, 0.010, 0.024), T((0.018, 0, LOW_Z0 - 0.012)))            # 방아쇠울 앞
slanted_box(bm, (-0.045, 0, LOW_Z0 + 0.005), (-0.080, 0, LOW_Z0 - 0.105), 0.030, 0.032)   # 권총손잡이
add("lower_receiver", bm, M["black"], (0, 0, -1), 0.0, 0, "하부 총몸",
    "방아쇠 뭉치·탄창 삽입구·손잡이가 붙는 아랫몸체 (기준 부품)", bevel=0.002)

# 04 노리쇠 뭉치 — 상부 총몸 속 원통형 블록. 상부 총몸이 올라간 뒤 뒤로 빠진다.
bm = bmesh.new()
ex.bm_cyl(bm, 0.0115, 0.0115, 0.140, 'X', T((-0.020, 0, 0.022)), segs=24)
ex.set_mat(ex.bm_cyl(bm, 0.007, 0.007, 0.022, 'X', T((0.061, 0, 0.022)), segs=20), 1)      # 노리쇠 머리
bcg = add("bolt_carrier", bm, [M["gunmetal"], M["black"]], (-1, 0, 0), 0.20, 4, "노리쇠 뭉치",
          "앞뒤로 움직이며 탄을 약실에 밀어 넣고, 쏜 뒤 탄피를 빼내는 부품", bevel=0.0012)

# 05 장전손잡이 — 오른쪽 옆 손잡이
bm = bmesh.new()
ex.bm_box(bm, (0.012, 0.018, 0.008), T((0.050, -REC_W / 2 - 0.009, 0.026)))
ex.bm_cyl(bm, 0.006, 0.006, 0.012, 'Y', T((0.050, -REC_W / 2 - 0.022, 0.026)), segs=16)
add("charging_handle", bm, M["gunmetal"], (0, -1, 0.5), 0.10, 2, "장전손잡이",
    "노리쇠를 손으로 당겨 첫 탄을 장전할 때 잡는 손잡이", bevel=0.001)

# 06 개머리판 (접이식) — 위 받침대 + 비스듬한 아래 받침대 + 개머리 판
bm = bmesh.new()
ex.bm_box(bm, (REC_X0 - BUTT_X - 0.030, 0.024, 0.026), T(((REC_X0 + BUTT_X + 0.030) / 2, 0, 0.012)))
slanted_box(bm, (REC_X0 - 0.010, 0, -0.035), (BUTT_X + 0.030, 0, -0.080), 0.022, 0.018)
ex.bm_box(bm, (0.030, 0.036, 0.140), T((BUTT_X + 0.015, 0, -0.035)))
ex.bm_box(bm, (0.012, REC_W, 0.050), T((REC_X0 - 0.006, 0, -0.005)))              # 접힘 경첩 블록
stock = add("folding_stock", bm, M["black"], (-1, 0, 0), 0.18, 1, "개머리판(신축·접이식)",
            "어깨에 대고 반동을 받치는 부분. 길이를 여러 단으로 조절하고, 옆으로 접을 수 있다", bevel=0.002)

# 07 탄창 몸통 — 앞으로 휘는 곡선 탄창 (바닥판·스프링·탄창판은 아래 17~19 에서 따로)
bm = bmesh.new()
MAG_H, MAG_TOP = 0.180, LOW_Z0 - 0.012
MAG_X0, MAG_BEND = 0.062, 0.045


def mag_x(z):
    """탄창 중심선: 아래로 갈수록 앞(+X)으로 기운다 (몸통이 꼭짓점 8개 상자라 선형으로 맞춘다)."""
    t = (MAG_TOP - z) / MAG_H
    return MAG_X0 + MAG_BEND * t


vs = ex.bm_box(bm, (0.062, 0.022, MAG_H), T((MAG_X0, 0, MAG_TOP - MAG_H / 2)))
for v in vs:
    v.co.x += mag_x(v.co.z) - MAG_X0
add("magazine", bm, M["olive"], (0, 0, -1), 0.14, 1, "탄창",
    "탄을 담아 두는 통(20·30발). 속의 스프링이 탄을 위로 밀어 올려 한 발씩 공급한다", bevel=0.0015)

# 08 조준경 몸체 — 레일 위 도트사이트: 마운트 + 원통 + 뒤 창 + 위 조절 노브 + 옆 배터리 포탑.
#    몸체가 먼저 올라가고(1), 속 부품(09~13)이 몸체 둘레로 흩어진다(2).
OX, OZ = -0.010, RAIL_Z + 0.038
OPT_UP = 0.14                                                                  # 몸체가 올라가는 거리
bm = bmesh.new()
ex.bm_box(bm, (0.040, 0.026, 0.020), T((OX, 0, RAIL_Z + 0.018)))
ex.bm_cyl(bm, 0.019, 0.019, 0.075, 'X', T((OX, 0, OZ)), segs=32)
ex.bm_cyl(bm, 0.008, 0.008, 0.010, 'Z', T((OX, 0, OZ + 0.022)), segs=16)     # 위: 조준점 상하 조절
ex.bm_cyl(bm, 0.012, 0.012, 0.010, 'Y', T((OX, -0.022, OZ)), segs=24)        # 옆: 배터리 포탑
ex.set_mat(ex.bm_cyl(bm, 0.016, 0.016, 0.002, 'X', T((OX - 0.038, 0, OZ)), segs=32), 1)   # 뒤 창
add("optic_housing", bm, [M["black"], M["glass"]], (0, 0, 1), OPT_UP, 1, "조준경 몸체",
    "도트사이트 몸체(일반적인 구조 예시). 레일에 물려 총에 고정한다", bevel=0.0012)

# 09 반사 렌즈 — 앞쪽 코팅 렌즈. 몸체 앞으로
bm = bmesh.new()
ex.set_mat(ex.bm_cyl(bm, 0.016, 0.016, 0.003, 'X', T((OX + 0.038, 0, OZ)), segs=32), 0)
ex.set_mat(ex.bm_cyl(bm, 0.0175, 0.0175, 0.002, 'X', T((OX + 0.0405, 0, OZ)), segs=32), 1)   # 렌즈 테
add_to("reflex_lens", bm, [M["glass"], M["black"]], (0.080, 0, OPT_UP), 2, "반사 렌즈",
       "LED 빛을 눈 쪽으로 되비춰, 표적 위에 빨간 점이 떠 보이게 하는 코팅 렌즈", bevel=0.0003)

# 10 LED 발광부 — 원통 뒤쪽 아래, 앞(반사 렌즈)을 향한다. 몸체 뒤로
bm = bmesh.new()
led = Vector((OX - 0.026, 0, OZ - 0.011))
ex.set_mat(ex.bm_box(bm, (0.008, 0.008, 0.005), T(led)), 0)                                  # 받침
ex.set_mat(ex.bm_cyl(bm, 0.0022, 0.0022, 0.003, 'X', T(led + Vector((0.0055, 0, 0.0005))), segs=16), 1)  # LED 칩
for sy in (+1, -1):                                                                          # 다리
    ex.set_mat(ex.bm_box(bm, (0.001, 0.0008, 0.006), T(led + Vector((-0.002, sy * 0.002, -0.005)))), 2)
ob = add_to("led_emitter", bm, [M["black"], M["led"], M["gold"]], (-0.080, 0, OPT_UP - 0.004), 2, "LED 발광부",
            "빨간 점을 만드는 작은 LED. 앞쪽 반사 렌즈를 향해 빛을 쏜다 (일반적인 도트사이트 원리)", bevel=0.0002)
ex.attach_chips(ob, [("빨간 LED 칩", "전기를 받으면 빨간 빛을 내는 반도체. 아주 작은 점 모양 빛을 만든다",
                      tuple(led + Vector((0.0070, 0, 0.0005))))])

# 11 밝기 조절 회로 기판 — 마운트 속. 몸체 위 오른쪽으로 (09~13 은 라벨이 안 겹치게 몸체 둘레에 넓게 둔다)
bm = bmesh.new()
# 칩 이름은 이런 장치에 흔히 쓰이는 종류일 뿐, 실제 제품의 부품이 아니다
chips = ex.bm_pcb(bm, (0.030, 0.018, 0.0012), T((OX, 0, RAIL_Z + 0.016)), chips=[
    (-0.005, 0.003, 0.005, 0.005, 0.0009, 'qfn', "예: 저전력 MCU",
     "밝기 입력을 읽고 LED 밝기를 정하는 작은 두뇌 (구조 예시 — 실제 제품 회로는 공개되지 않았다)"),
    (0.003, 0.005, 0.0029, 0.0016, 0.0010, 'sot', "예: LED 구동 회로",
     "LED 에 흐르는 전류를 조절해 점 밝기를 일정하게 지킨다"),
    (0.009, 0.004, 0.003, 0.003, 0.0009, 'qfn', "예: 가속도 센서(일부 제품)",
     "일부 도트사이트는 움직임을 감지해 자동으로 켜고 끈다. 모든 제품에 있는 기능은 아니다"),
    (0.012, -0.003, 0.0029, 0.0016, 0.0010, 'sot', "예: 밝기 입력 감지",
     "다이얼이나 버튼으로 고른 밝기 단계를 읽어 MCU 에 알려 준다"),
    (0.004, -0.004, 0.0029, 0.0016, 0.0010, 'sot', "예: 전원 스위치 트랜지스터",
     "MCU 의 명령으로 LED 쪽 전기를 켜고 끄는 전자 스위치"),
    (-0.005, -0.004, 0.0032, 0.0015, 0.0008, 'crystal', "예: 크리스털",
     "일정한 박자를 만들어 MCU 의 시계와 절전 타이머를 맞춘다"),
    (0.009, -0.006, 0.003, 0.003, 0.0022, 'cap'),                          # 전원 안정용 커패시터
    (-0.0005, 0.000, 0.0016, 0.0008, 0.0005, 'passive'),
    (0.0015, 0.0010, 0.0016, 0.0008, 0.0005, 'passive'),
    (-0.0005, -0.0065, 0.0016, 0.0008, 0.0005, 'passive'),
    (0.0075, 0.0005, 0.0016, 0.0008, 0.0005, 'passive'),
    (-0.0115, -0.004, 0.005, 0.004, 0.0025, 'conn', "배선 커넥터",
     "전지와 LED 로 가는 전선을 잇는 자리"),
])
ob = add_to("control_board", bm, [M["pcb"], M["black"], M["gold"], M["ceramic"]], (0.140, 0, OPT_UP + 0.068), 2,
            "밝기 조절 회로 기판", "밝기 단계에 맞춰 LED 를 켜는 회로 (구조 예시)",
            bevel=0.0001)
ex.attach_chips(ob, chips)

# 12 코인 배터리(CR2032) — 옆 포탑 속. 몸체 바로 위로
bm = bmesh.new()
ex.bm_cyl(bm, 0.010, 0.010, 0.0032, 'Y', T((OX, -0.024, OZ)), segs=32)
add_to("coin_battery", bm, M["metal"], (0.0, 0, OPT_UP + 0.075), 2, "전지",
       "LED 와 회로에 전원을 주는 전지. 전지 종류는 조준경 기종마다 다르다 (그림은 동전형 예시)", bevel=0.0004)

# 13 밝기 조절 다이얼 — 옆 포탑 뚜껑 겸 다이얼 (톱니 테). 몸체 위 왼쪽으로
bm = bmesh.new()
ex.bm_cyl(bm, 0.0125, 0.0125, 0.005, 'Y', T((OX, -0.0295, OZ)), segs=32)
for i in range(18):                                                                           # 미끄럼 방지 톱니
    a = i / 18 * 2 * math.pi
    ex.bm_box(bm, (0.0016, 0.004, 0.0016), T((OX + 0.013 * math.cos(a), -0.0295, OZ + 0.013 * math.sin(a))))
add_to("brightness_dial", bm, M["gunmetal"], (-0.140, 0, OPT_UP + 0.068), 2, "밝기 조절 다이얼",
       "점 밝기를 바꾸는 조작부 (구조 예시)", bevel=0.0004)

# 14 복좌 스프링·가이드 — 상부 총몸 속 노리쇠 뭉치 위. 노리쇠보다 높이, 뒤로
bm = bmesh.new()
SP_X0, SP_X1, SP_Z = -0.135, -0.025, 0.038
ex.set_mat(ex.bm_cyl(bm, 0.0015, 0.0015, SP_X1 - SP_X0 + 0.012, 'X', T(((SP_X0 + SP_X1) / 2 + 0.006, 0, SP_Z)), segs=12), 1)
for i in range(22):                                                                           # 감긴 코일 (고리)
    x = SP_X0 + i * (SP_X1 - SP_X0) / 21
    ex.set_mat(ex.bm_cyl(bm, 0.0045, 0.0045, 0.0012, 'X', T((x, 0, SP_Z)), segs=14, caps=False), 0)
add_to("recoil_spring", bm, [M["metal"], M["gunmetal"]], (-0.160, 0, 0.100), 4, "복좌 스프링·가이드",
       "뒤로 밀려난 노리쇠 뭉치를 다시 앞으로 밀어 되돌리는 스프링과 그 축", bevel=0)

# 15 가스 피스톤·가스 조절기 — 총열덮개 속 총열 위. 총열덮개가 빠진 뒤 위로
bm = bmesh.new()
GP_Z = 0.034
ex.bm_cyl(bm, 0.0045, 0.0045, 0.200, 'X', T((0.200, 0, GP_Z)), segs=16)                       # 피스톤 막대
ex.bm_cyl(bm, 0.0065, 0.0065, 0.012, 'X', T((0.296, 0, GP_Z)), segs=20)                        # 피스톤 머리
ex.set_mat(ex.bm_cyl(bm, 0.008, 0.008, 0.020, 'X', T((0.315, 0, GP_Z)), segs=24), 1)          # 가스 조절기
ex.set_mat(ex.bm_box(bm, (0.006, 0.004, 0.006), T((0.315, -0.009, GP_Z))), 1)                  # 조절 레버
add_to("gas_piston", bm, [M["gunmetal"], M["black"]], (0, 0, 0.120), 4, "가스 피스톤·조절기",
       "총열에서 빠져나온 가스의 힘을 받아 노리쇠 뭉치를 뒤로 미는 긴 피스톤(롱 스트로크). 가스 조절기로 가스 양을 맞춘다", bevel=0.0006)

# 16 방아쇠 뭉치 — 하부 총몸 속 한 덩어리 (격발 구조는 만들지 않는다) + 방아쇠 날. 오른쪽(카메라 쪽)으로 빼서 뒤·위로
bm = bmesh.new()
ex.bm_box(bm, (0.057, 0.022, 0.034), T((-0.0165, 0, LOW_Z0 + 0.025)))
ex.set_mat(ex.bm_cyl(bm, 0.0035, 0.0035, 0.024, 'Y', T((-0.030, 0, LOW_Z0 + 0.030)), segs=16), 1)   # 조정간 축
slanted_box(bm, (0.002, 0, LOW_Z0 + 0.008), (0.006, 0, LOW_Z0 - 0.016), 0.005, 0.006)             # 방아쇠
add_to("trigger_group", bm, [M["gunmetal"], M["black"]], (-0.060, -0.070, 0.070), 5, "방아쇠 뭉치",
       "방아쇠와 격발 장치를 한 덩어리로 묶은 부분. 조정간으로 안전·단발·3점사·연발을 고른다", bevel=0.0008)

# 17 탄창판 — 탄창 맨 위, 스프링 위에서 탄을 받친다. 탄창 앞쪽으로
bm = bmesh.new()
FZ = MAG_TOP - 0.010
ex.bm_box(bm, (0.052, 0.018, 0.008), T((mag_x(FZ), 0, FZ)))
ex.bm_box(bm, (0.020, 0.010, 0.004), T((mag_x(FZ) - 0.010, 0.003, FZ + 0.006)))              # 한쪽 턱 (탄을 엇갈려 받침)
add_to("follower", bm, M["black"], (0.120, 0, -0.040), 2, "탄창판",
       "스프링 위에서 탄을 받쳐, 두 줄로 엇갈려 쌓인 탄을 가지런히 올려 주는 판", bevel=0.0008)

# 18 탄창 스프링 — 사각으로 감긴 스프링 (휜 탄창을 따라 고리를 쌓는다)
bm = bmesh.new()
n = 13
for i in range(n):
    z = MAG_TOP - 0.022 - i * (MAG_H - 0.034) / (n - 1)
    x = mag_x(z) + (0.004 if i % 2 else -0.004)                                              # 지그재그로 감긴 느낌
    for (w, h, dx, dy) in ((0.044, 0.002, 0, 0.007), (0.044, 0.002, 0, -0.007), (0.002, 0.016, 0.022, 0), (0.002, 0.016, -0.022, 0)):
        ex.bm_box(bm, (w, h, 0.002), T((x + dx, dy, z)))
add_to("mag_spring", bm, M["metal"], (0.135, 0, -0.100), 2, "탄창 스프링",
       "눌려 있다가 펴지며 탄을 한 발씩 위로 밀어 올리는 스프링", bevel=0)

# 19 탄창 바닥판·멈치판 — 바닥을 막는 판 + 그 위 금속 멈치판
bm = bmesh.new()
BZ = MAG_TOP - MAG_H - 0.004
ex.bm_box(bm, (0.072, 0.026, 0.008), T((mag_x(MAG_TOP - MAG_H) + 0.0, 0, BZ)))
ex.set_mat(ex.bm_box(bm, (0.050, 0.016, 0.003), T((mag_x(MAG_TOP - MAG_H), 0, BZ + 0.0055))), 1)
add_to("floor_plate", bm, [M["black"], M["metal"]], (0.135, 0, -0.175), 2, "탄창 바닥판·멈치판",
       "탄창 아래를 막는 판과, 그 판이 빠지지 않게 걸어 두는 멈치판", bevel=0.0008)

for ob in parts:
    ex.add_explode_drivers(ob, root)

# 개머리판 접힘 드라이버: 경첩(HINGE) 을 축으로 th = -(1-ext)·180° 회전 → 오른쪽 옆에 붙는다.
c = stock.location - HINGE
exprs = {
    ("location", 0): f"{HINGE.x} + {c.x}*cos(-(1-e)*pi) - {c.y}*sin(-(1-e)*pi)",
    ("location", 1): f"{HINGE.y} + {c.x}*sin(-(1-e)*pi) + {c.y}*cos(-(1-e)*pi) - 0.022*(1-e)",
    ("rotation_euler", 2): "-(1-e)*pi",
}
for (path, idx), e in exprs.items():
    drv = stock.driver_add(path, idx).driver
    drv.type = 'SCRIPTED'
    ex._var(drv, "e", root, '["stock_extend"]')
    drv.expression = e
    assert drv.is_simple_expression, e

ex.key_explode(root, 1, 60)

# 카메라: 길쭉한 총은 옆(오른쪽, -Y)에서. 장전손잡이가 이쪽으로 나온다.
ex.apply_look(LOOK, dict(cam_loc=(0.10, -1.55, 0.38), target=(-0.02, 0, 0.0), lens=35), OUT)

# ---- 검증 ----
ex.verify_explode(parts)
sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()


def world_bbox(o):
    ev = o.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


a, b = world_bbox(bcg)
c_, d = world_bbox(upper)
print("VERIFY bcg-inside-upper", "OK" if all(c_[i] < a[i] and b[i] < d[i] for i in range(3)) else (a, b, c_, d))
lo, hi = world_bbox(parts[0])
for o in parts[1:]:
    a, b = world_bbox(o)
    lo, hi = [min(lo[i], a[i]) for i in range(3)], [max(hi[i], b[i]) for i in range(3)]
print("VERIFY length(m)", round(hi[0] - lo[0], 3), "parts", len(parts))

# 완전 분해(프레임 60)에서 부품끼리 경계상자가 겹치는지 — 겹치면 이름을 찍는다 (휜·비스듬한 부품은 거짓 경보일 수 있다)
sc.frame_set(60)
dg = bpy.context.evaluated_depsgraph_get()
boxes = [(o.name, *world_bbox(o)) for o in parts]
hits = [(n1, n2) for i, (n1, a1, b1) in enumerate(boxes) for (n2, a2, b2) in boxes[i + 1:]
        if all(a1[k] < b2[k] - 0.0005 and a2[k] < b1[k] - 0.0005 for k in range(3))]
print("VERIFY exploded-overlap", "OK" if not hits else hits)

ex.report(CODE, parts, os.path.join(OUT, "parts.md"))
ex.save_and_render(OUT, argv, get)
