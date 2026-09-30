"""nvg — 야간투시경 (PVS-7형: 대물렌즈 1, 증폭관 1, 접안렌즈 2) 분해 씬 — 속까지.

실행: Blender -b --factory-startup --python products/nvg.py -- [--look armory] [--render] [--frames 1,20,40,60]
+X 전방(보는 쪽), -X 가 눈. 전장 약 0.16m.
하부 몸체가 기준(고정). 순서: ① 덮개(배터리실·마운트째)·대물 경통·접안렌즈가 빠지고
② 대물렌즈 알·건전지·전원 모듈·회로 기판·IR LED 가 드러나고 ③ 마지막에 증폭관 속 층들이 위로 들려
광축(X)을 따라 한 줄로 펼쳐진다 (빛 → 광음극 → MCP → 형광 스크린 → 광섬유 출력창 → 콜리메이터(상을 바로 세움) → 눈).
구성은 공개된 PVS-7 구조(증폭관 하나를 프리즘으로 두 눈에 나눔)를 따른 것이고, 실제 배치 그대로는 아니다.
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

CODE = "nvg"
argv, get = ex.parse_args()
LOOK = get("--look", "armory")
OUT = ex.out_dir(HERE, CODE, LOOK)

# 치수 (m)
BODY_X0, BODY_X1 = -0.030, 0.040             # 몸체 앞뒤
BODY_W, BODY_H = 0.100, 0.055
WALL = 0.003                                 # 몸체 벽 두께
OBJ_R, OBJ_L = 0.026, 0.050                  # 대물렌즈 경통
EYE_Y, EYE_R, EYE_L = 0.032, 0.017, 0.040    # 접안렌즈 (눈 간격 64mm)
TUBE_R, TUBE_X0, TUBE_X1 = 0.018, -0.012, 0.034   # 증폭관 외통 (뒤쪽은 프리즘 자리)
LIFT = (0.100, 0.070)                        # 증폭관 층들이 들리는 높이 — 번갈아 두 줄 (라벨이 안 겹치게)
BAT = (0.012, -0.005, BODY_H / 2 + 0.010)    # 배터리실 중심 (Y 방향 원통)
T = Matrix.Translation

sc = ex.reset_scene()
coll = bpy.data.collections.new(CODE)
sc.collection.children.link(coll)
M = ex.standard_materials(CODE, ("olive", "black", "gunmetal", "glass", "pcb", "metal", "gold", "ceramic",
                                 "cell", "phosphor"))
root = ex.make_root(CODE, coll, max_order=3)
parts = []


def add(name, bm, mat, direction, dist, order, label, desc="", **kw):
    ob = ex.part_object(f"{CODE}_{len(parts) + 1:02d}_{name}", bm, mat, coll, root, **kw)
    ex.set_meta(ob, direction, dist, order, label, desc)
    parts.append(ob)
    return ob


def shell(bm, z0, z1, floor_at):
    """몸체 반쪽: 바닥(또는 지붕) 판 + 네 벽. floor_at 은 판이 놓일 z."""
    cx, lx = (BODY_X0 + BODY_X1) / 2, BODY_X1 - BODY_X0
    h = z1 - z0
    ex.bm_box(bm, (lx, BODY_W, WALL), T((cx, 0, floor_at)))
    for sy in (+1, -1):
        ex.bm_box(bm, (lx, WALL, h), T((cx, sy * (BODY_W - WALL) / 2, (z0 + z1) / 2)))
    for x in (BODY_X0 + WALL / 2, BODY_X1 - WALL / 2):
        ex.bm_box(bm, (WALL, BODY_W - 2 * WALL, h), T((x, 0, (z0 + z1) / 2)))


def lift(dx, row):
    """증폭관 층: 위로 LIFT[row] 만큼 들리며 X 로 dx 만큼 벌어진다 → (방향, 거리)."""
    v = Vector((dx, 0, LIFT[row]))
    return tuple(v.normalized()), v.length


def lens(bm, r, x, t=0.0035):
    """볼록 렌즈 알 하나: 얇은 원판 양면에 납작한 반구."""
    ex.bm_cyl(bm, r, r, t, 'X', T((x, 0, 0)), segs=32)
    for s in (+1, -1):
        ex.bm_hemisphere(bm, r * 0.98, 'X', T((x + s * t / 2, 0, 0)) @
                         Matrix.Rotation(0 if s > 0 else math.pi, 4, 'Z') @ Matrix.Diagonal((0.18, 1, 1, 1)), segs=32)


# ───────── ① 껍데기 ─────────

# 01 하부 몸체 — 기준. 바닥 + 네 벽, 윗면이 열린 통
bm = bmesh.new()
shell(bm, -BODY_H / 2, 0, -BODY_H / 2 + WALL / 2)
add("lower_body", bm, M["olive"], (0, 0, -1), 0.0, 0, "하부 몸체",
    "부품을 담는 몸통의 아래쪽. 물에 1m·30분까지 견딘다 (이 모델은 설명을 위해 몸통을 위아래로 나눴다)", bevel=0.001, segments=2)

# 02 상부 덮개 — 지붕 + 네 벽. 배터리실·마운트와 한 덩어리로 위로 빠진다
bm = bmesh.new()
shell(bm, 0, BODY_H / 2, BODY_H / 2 - WALL / 2)
ex.set_mat(ex.bm_cyl(bm, 0.006, 0.006, 0.006, 'Z', T((-0.018, -0.030, BODY_H / 2 + 0.003)), segs=20), 1)  # 전원·IR 스위치 손잡이
add("top_cover", bm, [M["olive"], M["black"]], (0, 0, 1), 0.13, 1, "상부 덮개",
    "몸통의 위쪽 (설명을 위해 나눈 것). 실제 몸통에는 배터리실과 끔·켬·IR 스위치가 붙어 있다", bevel=0.001, segments=2)

# 03 배터리 하우징 — 덮개 위 가로 원통 + 캡 (덮개와 같이 움직인다)
bm = bmesh.new()
ex.bm_cyl(bm, 0.011, 0.011, 0.060, 'Y', T(BAT), segs=32)
ex.set_mat(ex.bm_cyl(bm, 0.013, 0.013, 0.010, 'Y', T((BAT[0], -0.040, BAT[2])), segs=32), 1)
add("battery_housing", bm, [M["olive"], M["black"]], (0, 0, 1), 0.13, 1, "배터리 하우징",
    "건전지를 넣는 칸 — AA 2개 또는 3V 리튬 전지(BA-5567) 1개. 뚜껑이 몸통에 달려 있다", bevel=0.0015)

# 04 헬멧 마운트 암 — 덮개 뒤쪽 위 판 + 도브테일 바 (덮개와 같이)
bm = bmesh.new()
ex.bm_box(bm, (0.012, 0.030, 0.040), T((-0.018, 0.015, BODY_H / 2 + 0.020)))
ex.bm_box(bm, (0.050, 0.022, 0.010), T((-0.005, 0.015, BODY_H / 2 + 0.043)))
ex.set_mat(ex.bm_box(bm, (0.030, 0.026, 0.004), T((0.005, 0.015, BODY_H / 2 + 0.050))), 1)
add("helmet_mount_arm", bm, [M["gunmetal"], M["black"]], (0, 0, 1), 0.13, 1, "헬멧 마운트 암",
    "머리띠(헤드 마운트)나 헬멧에 달아 두 손을 자유롭게 쓴다. 떼어 내면 저절로 꺼진다", bevel=0.0015)

# 05 대물렌즈 경통 — 앞 경통(초점링 널링) + 맨 앞 보호 유리. 속의 렌즈 알은 따로
bm = bmesh.new()
bx = BODY_X1 + OBJ_L / 2
ex.bm_cyl(bm, OBJ_R, OBJ_R, OBJ_L, 'X', T((bx, 0, 0)), segs=40)
for dx in (-0.012, -0.004, 0.004):                               # 초점링 널링
    ex.set_mat(ex.bm_cyl(bm, OBJ_R + 0.0015, OBJ_R + 0.0015, 0.004, 'X', T((bx + dx, 0, 0)), segs=40), 1)
ex.set_mat(ex.bm_cyl(bm, OBJ_R + 0.002, OBJ_R + 0.002, 0.006, 'X', T((BODY_X1 + OBJ_L - 0.003, 0, 0)), segs=40), 1)
ex.set_mat(ex.bm_cyl(bm, OBJ_R - 0.004, OBJ_R - 0.004, 0.002, 'X', T((BODY_X1 + OBJ_L + 0.0005, 0, 0)), segs=40), 2)
add("objective_barrel", bm, [M["olive"], M["black"], M["glass"]], (1, 0, 0), 0.16, 1, "대물렌즈 경통",
    "초점을 25cm 부터 무한대까지 맞춘다. 대물렌즈가 맺는 상은 위아래가 뒤집혀 있다", bevel=0.003, segments=3)

# 06/07 접안렌즈 — 경통 + 고무 아이컵(끝이 벌어짐)
for side, nm, lb in ((+1, "eyepiece_left", "접안렌즈(좌)"), (-1, "eyepiece_right", "접안렌즈(우)")):
    y = side * EYE_Y
    bm = bmesh.new()
    ex.set_mat(ex.bm_cyl(bm, EYE_R, EYE_R, 0.022, 'X', T((BODY_X0 - 0.011, y, 0)), segs=32), 1)
    ex.bm_cyl(bm, EYE_R + 0.005, EYE_R, 0.020, 'X', T((BODY_X0 - 0.030, y, 0)), segs=32)   # 아이컵
    add(nm, bm, [M["black"], M["gunmetal"]], (-1, 0, 0), 0.07, 1, lb,
        "콜리메이터가 보낸 영상을 눈으로 보는 렌즈. 시력(디옵터) +2 ~ −6 을 맞춘다. 배율은 1배", bevel=0.0015)

# ───────── ② 드러나는 속 부품 ─────────

# 08/09 렌즈 유리 — 접안렌즈 안쪽 끝 유리 2장. 뒤로 더 빠진다
for side, nm, lb in ((+1, "lens_glass_left", "렌즈 유리(좌)"), (-1, "lens_glass_right", "렌즈 유리(우)")):
    bm = bmesh.new()
    ex.bm_hemisphere(bm, EYE_R - 0.003, 'X', T((BODY_X0 - 0.024, side * EYE_Y, 0)) @
                     Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Diagonal((0.35, 1, 1, 1)), segs=32)
    add(nm, bm, M["glass"], (-1, 0, 0), 0.14, 2, lb, "접안렌즈 속 렌즈 알", bevel=0)

# 10~12 대물렌즈 알 3장 — 경통 속. 경통이 빠진 뒤 앞으로 조금씩 벌어진다
for i, (x, r, d, nm) in enumerate(((0.082, 0.022, 0.080, "앞"), (0.066, 0.021, 0.050, "가운데"),
                                   (0.051, 0.020, 0.020, "뒤"))):
    bm = bmesh.new()
    lens(bm, r, x)
    add(f"objective_lens_{i + 1}", bm, M["glass"], (1, 0, 0), d, 2, f"대물렌즈({nm})",
        "렌즈 여러 장이 희미한 빛을 모아 증폭관 앞면에 상을 맺는다 (장수는 모델마다 다름 — 여기선 3장으로 그렸다)", bevel=0)

# 13 건전지(AA 2개 또는 3V 리튬 1개 — 한 개만 그림) — 배터리실 속. 덮개가 들린 뒤 왼쪽 위(마운트 옆 빈자리)로 빠진다
bm = bmesh.new()
ex.bm_cyl(bm, 0.0071, 0.0071, 0.048, 'Y', T(BAT), segs=28)
ex.set_mat(ex.bm_cyl(bm, 0.0026, 0.0026, 0.0015, 'Y', T((BAT[0], BAT[1] - 0.0247, BAT[2])), segs=16), 1)   # + 단자
ex.set_mat(ex.bm_cyl(bm, 0.0068, 0.0068, 0.0006, 'Y', T((BAT[0], BAT[1] + 0.0243, BAT[2])), segs=28), 1)   # - 단자
add("aa_battery", bm, [M["cell"], M["metal"]], (-0.45, 0, 1), 0.17, 2, "건전지",
    "장비 전체의 전원. AA 2개(합쳐 3V) 또는 3V 리튬 1개를 쓴다 — 이 모델은 한 개만 그렸다", bevel=0.0004)

# 14 고전압 전원 모듈 — 증폭관 옆(+Y) 수지로 굳힌 덩어리(고압부) + 윗면 제어 기판 + 증폭관으로 가는 고압 리드
#    기판은 블록 위에 부품면을 위로 — 위에서 내려다보는 카메라에 칩이 보이게. 칩 구성은 일반적인 고압 전원 회로 예시.
HV = (0.012, 0.033, -0.004)
bm = bmesh.new()
ex.bm_box(bm, (0.030, 0.018, 0.022), T((HV[0], HV[1], HV[2] - 0.003)))                  # 포팅 블록 (위 z = HV+0.008)
hv_chips = ex.bm_pcb(bm, (0.030, 0.018, 0.0012), T((HV[0], HV[1], HV[2] + 0.0086)), chips=(
    (-0.0085, 0.002, 0.009, 0.009, 0.003, 'inductor', "고전압 트랜스포머(코일)",
     "건전지의 낮은 전압을 코일 감은 수 차이로 크게 끌어올린다"),
    (0.0010, 0.0045, 0.004, 0.004, 0.0009, 'qfn', "승압 컨버터 IC",
     "트랜스포머에 전류를 아주 빠르게 켜고 끊어 전압을 올리는 스위칭 칩"),
    (0.0010, -0.0045, 0.0022, 0.0012, 0.0007, 'passive', "전압 체배기(다이오드·커패시터)",
     "다이오드와 커패시터를 계단처럼 이어 수천 볼트로 올린다 — 광음극·MCP·형광 스크린에 각각 다른 전압을 준다"),
    (-0.0015, -0.0045, 0.0022, 0.0012, 0.0007, 'passive'), (0.0035, -0.0045, 0.0022, 0.0012, 0.0007, 'passive'),
    (0.0060, -0.0045, 0.0022, 0.0012, 0.0007, 'passive'),
    (0.0090, -0.0010, 0.005, 0.004, 0.0014, 'ic', "자동 밝기 제어(ABC) 회로",
     "형광 스크린 전류를 보고 MCP 전압을 낮춰, 주변이 밝아져도 화면 밝기를 일정하게 지킨다"),
    (0.0120, -0.0060, 0.0028, 0.0016, 0.0009, 'sot', "강한 빛 보호(BSP) 스위치",
     "광음극에 전류가 너무 많이 흐르면 광음극 전압을 낮추거나 켰다 껐다 해 관을 지킨다"),
    (0.0110, 0.0050, 0.0045, 0.0045, 0.0030, 'cap', "고압 출력 커패시터",
     "출력 전압의 떨림을 고르게 다듬어 영상이 깜빡이지 않게 한다"),
), mats=(1, 0, 2, 3))
for dz in (-0.006, 0.004):                                                                # 고압 리드
    ex.set_mat(ex.bm_cyl(bm, 0.0008, 0.0008, 0.010, 'Y', T((HV[0] - 0.008, HV[1] - 0.013, HV[2] + dz)), segs=8), 2)
ob = add("hv_power_supply", bm, [M["black"], M["pcb"], M["gold"], M["ceramic"]], (0.6, 0, -1), 0.13, 2,
         "고전압 전원 모듈", "건전지 3V 를 수천 볼트(형광 스크린 쪽은 약 6,000V)로 올려 증폭관에 건다. 밝기 자동 조절과 강한 빛 보호도 여기서 한다",
         bevel=0.0008, segments=1)                                    # 칩·핀이 많아 베벨 단계를 줄여 파일을 가볍게
ex.attach_chips(ob, hv_chips)

# 15 제어 회로 기판 — 증폭관 앞쪽(-Y) 아래. 스위치를 읽어 전원 모듈과 IR LED 를 켠다 (칩 구성은 일반적인 예시)
bm = bmesh.new()
ctrl_chips = ex.bm_pcb(bm, (0.046, 0.022, 0.0012), T((0.008, -0.033, -0.018)), chips=(
    (-0.0125, 0.0020, 0.006, 0.006, 0.0009, 'qfn', "제어 칩(예: 저전력 MCU)",
     "스위치(끔·켬·IR) 위치를 읽어 전원 모듈과 IR LED 를 켜고 끈다. 실제 회로 구성은 공개돼 있지 않아 예로 그렸다"),
    (-0.0040, 0.0065, 0.0040, 0.0020, 0.0010, 'crystal'),
    (0.0040, 0.0040, 0.0050, 0.0040, 0.0014, 'ic', "전압 레귤레이터",
     "건전지 전압을 회로가 쓰는 일정한 전압으로 바꿔 준다"),
    (0.0120, 0.0045, 0.0040, 0.0040, 0.0020, 'inductor'),
    (-0.0020, -0.0060, 0.0028, 0.0016, 0.0009, 'sot', "배터리 전압 감시 IC",
     "전압이 2.4V 까지 떨어지면 오른쪽 접안부의 표시등을 깜빡여 알린다 (약 30분 남음)"),
    (0.0080, -0.0060, 0.0028, 0.0016, 0.0009, 'sot', "LED 구동 트랜지스터",
     "MCU 신호를 받아 적외선 LED 에 큰 전류를 흘려 켠다"),
    (0.0140, -0.0060, 0.0020, 0.0012, 0.0007, 'passive'), (0.0030, -0.0060, 0.0020, 0.0012, 0.0007, 'passive'),
    (-0.0055, -0.0015, 0.0020, 0.0012, 0.0007, 'passive'),
    (0.0180, 0.0020, 0.0050, 0.0050, 0.0040, 'cap', "전해 커패시터",
     "전기를 잠깐 모아 두어 LED 를 켤 때 전압이 출렁이지 않게 한다"),
    (-0.0200, -0.0060, 0.0040, 0.0040, 0.0035, 'conn', "스위치 커넥터",
     "전원·IR 선택 스위치의 선이 꽂히는 자리"),
), mats=(0, 1, 2, 3))
ob = add("control_board", bm, [M["pcb"], M["black"], M["gold"], M["ceramic"]], (0, -1, 0.45), 0.07, 2,
         "제어 회로 기판", "스위치에 따라 전원 모듈·적외선 LED 를 켜고 끈다. 배터리 부족을 알리고, 마운트에서 떼거나 밝은 곳에 70초쯤 두면 저절로 끈다", bevel=0)
ex.attach_chips(ob, ctrl_chips)

# 16 적외선 조명 LED — 몸체 앞면 아래쪽 작은 창 + LED + 받침 기판
bm = bmesh.new()
ex.bm_cyl(bm, 0.0055, 0.0055, 0.006, 'X', T((BODY_X1 + 0.003, -0.036, -0.017)), segs=20)            # 창 테두리
ex.set_mat(ex.bm_hemisphere(bm, 0.0035, 'X', T((BODY_X1 + 0.006, -0.036, -0.017)), segs=16), 1)     # LED 렌즈
ex.set_mat(ex.bm_box(bm, (0.0012, 0.010, 0.010), T((BODY_X1 - 0.0006, -0.036, -0.017))), 2)         # 받침 기판
add("ir_led", bm, [M["black"], M["glass"], M["pcb"]], (1, -0.6, -0.2), 0.05, 2, "적외선 조명 LED",
    "아주 어두울 때 가까운 곳을 비추는 적외선. 사람 눈엔 안 보이지만 상대의 야간투시경에는 보인다", bevel=0.0003)

# ───────── ③ 증폭관 속 — 위로 들려 광축을 따라 한 줄 ─────────

# 17 증폭관 외통 — 진공 용기. 기준(몸체에 남는다), 층들이 위로 빠져나온다
bm = bmesh.new()
ex.bm_cyl(bm, TUBE_R, TUBE_R, TUBE_X1 - TUBE_X0, 'X', T(((TUBE_X0 + TUBE_X1) / 2, 0, 0)), segs=40)
for x in (TUBE_X0 + 0.008, TUBE_X1 - 0.010):                     # 전극 링
    ex.set_mat(ex.bm_cyl(bm, TUBE_R + 0.001, TUBE_R + 0.001, 0.004, 'X', T((x, 0, 0)), segs=40), 1)
add("tube_envelope", bm, [M["gunmetal"], M["gold"]], (0, 0, 1), 0.0, 0, "증폭관 외통",
    "속을 진공으로 만든 통. 전자가 공기에 막히지 않고 날아간다. PVS-7 에는 18mm 관(MX-10130 형)이 쓰인다", bevel=0.001)

# 18 광음극 — 맨 앞 유리창 안쪽 얇은 막 (빛 → 전자)
bm = bmesh.new()
ex.bm_cyl(bm, 0.0145, 0.0145, 0.004, 'X', T((0.028, 0, 0)), segs=36)
ex.set_mat(ex.bm_cyl(bm, 0.0125, 0.0125, 0.0008, 'X', T((0.0256, 0, 0)), segs=36), 1)            # 광음극 막
ex.set_mat(ex.bm_cyl(bm, 0.0155, 0.0155, 0.0015, 'X', T((0.028, 0, 0)), segs=36), 2)             # 금속 테
d, L = lift(0.090, 0)
add("photocathode", bm, [M["glass"], M["gold"], M["metal"]], d, L, 3, "광음극",
    "들어온 빛(광자)을 전자로 바꾸는 막. 3세대 관은 갈륨비소(GaAs)를 써서 별빛 정도의 빛도 잡는다", bevel=0.0002)

# 19 마이크로채널판(MCP) — 미세 구멍 판 (전자를 수천 배로)
bm = bmesh.new()
ex.set_mat(ex.bm_cyl(bm, 0.0140, 0.0140, 0.0016, 'X', T((0.018, 0, 0)), segs=36), 0)          # 판 (짙은 유리)
ex.set_mat(ex.bm_cyl(bm, 0.0152, 0.0152, 0.0008, 'X', T((0.018, 0, 0)), segs=36), 1)          # 전극 테 (판보다 얇게)
for ry in range(-4, 5):                                                                        # 구멍 격자 — 앞뒤 면에 점
    for rz in range(-4, 5):
        if (ry * ry + rz * rz) * 0.0026 ** 2 < 0.0118 ** 2:
            ex.set_mat(ex.bm_cyl(bm, 0.0007, 0.0007, 0.0020, 'X', T((0.018, ry * 0.0026, rz * 0.0026)), segs=6), 2)
d, L = lift(0.045, 1)
add("mcp", bm, [M["gunmetal"], M["gold"], M["black"]], d, L, 3, "마이크로채널판(MCP)",
    "머리카락보다 가는 구멍 수백만 개. 전자가 구멍 벽에 부딪힐 때마다 불어나 수천 배가 된다", bevel=0.0001, segments=1)

# 20 형광 스크린 — 불어난 전자가 부딪혀 초록 빛
bm = bmesh.new()
ex.bm_cyl(bm, 0.0135, 0.0135, 0.0015, 'X', T((0.0115, 0, 0)), segs=36)
ex.set_mat(ex.bm_cyl(bm, 0.0150, 0.0150, 0.0010, 'X', T((0.0110, 0, 0)), segs=36), 1)
d, L = lift(0.000, 0)
add("phosphor_screen", bm, [M["phosphor"], M["metal"]], d, L, 3, "형광 스크린",
    "전자가 부딪히면 빛을 낸다. PVS-7 관은 초록 형광체(P-43)라 화면이 초록이다 (요즘은 흰색 형광 관도 있다)", bevel=0.0001)

# 21 광섬유 출력창 — 형광 스크린이 입혀진 광섬유 창. PVS-7 의 MX-10130 관은 비반전형(상을 뒤집지 않는다)
#    → 상을 바로 세우는 건 뒤의 콜리메이터 (예전의 '광섬유 역상기'는 이 관에 맞지 않아 고쳤다)
bm = bmesh.new()
ex.bm_cyl(bm, 0.0120, 0.0120, 0.016, 'X', T((-0.002, 0, 0)), segs=36)
for x in (-0.009, 0.005):
    ex.set_mat(ex.bm_cyl(bm, 0.0130, 0.0130, 0.002, 'X', T((x, 0, 0)), segs=36), 1)
d, L = lift(-0.045, 1)
add("fiber_output_window", bm, [M["glass"], M["metal"]], d, L, 3, "광섬유 출력창",
    "형광 스크린이 입혀진 광섬유 창. 초록 영상을 뒤집지 않고 관 밖으로 내보낸다 (PVS-7 관은 비반전형)", bevel=0.0001)

# 22 프리즘·콜리메이터 — 관 뒤에서 영상을 두 눈으로 나눈다
bm = bmesh.new()
ex.bm_box(bm, (0.012, 0.030, 0.016), T((-0.021, 0, 0)))                                        # 가운데 분광 프리즘
for s in (+1, -1):
    ex.bm_box(bm, (0.010, 0.020, 0.014), T((-0.021, s * 0.028, 0)) @ Matrix.Rotation(s * math.radians(20), 4, 'Z'))
ex.set_mat(ex.bm_box(bm, (0.013, 0.070, 0.004), T((-0.021, 0, -0.010))), 1)                    # 받침 틀
d, L = lift(-0.090, 0)
add("prism_collimator", bm, [M["glass"], M["gunmetal"]], d, L, 3, "프리즘·콜리메이터",
    "릴레이 렌즈·프리즘 묶음. 뒤집힌 상을 바로 세우고, 관 하나의 영상을 두 접안렌즈로 나눠 보낸다 (두 눈으로 보지만 관은 하나)", bevel=0.0003)

for ob in parts:
    ex.add_explode_drivers(ob, root)
ex.key_explode(root, 1, 60)

# 카메라: 옆(-Y)에서 약간 앞·위 (조립 모습 기준. 분해하면 뷰어가 알아서 물러난다)
ex.apply_look(LOOK, dict(cam_loc=(0.20, -0.80, 0.34), target=(-0.005, 0, 0.040), lens=46), OUT)

# ---- 검증 ----
ex.verify_explode(parts)
dg = bpy.context.evaluated_depsgraph_get()


def world_bbox(o):
    ev = o.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def overlap(a, b, pad=0.0005):
    return all(a[0][i] + pad < b[1][i] and b[0][i] + pad < a[1][i] for i in range(3))


# 조립 상태: 속 부품이 몸체(하부+덮개) 안에 들어 있나
sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
inner = [o for o in parts if o["explode_order"] >= 2 and "lens_glass" not in o.name and "objective_lens" not in o.name
         and "battery" not in o.name and "ir_led" not in o.name]
lo_c = [BODY_X0, -BODY_W / 2, -BODY_H / 2]
hi_c = [BODY_X1, BODY_W / 2, BODY_H / 2]
bad = [o.name for o in inner if not all(lo_c[i] - 1e-4 <= world_bbox(o)[0][i] and world_bbox(o)[1][i] <= hi_c[i] + 1e-4
                                        for i in range(3))]
print("VERIFY inside-body", "OK" if not bad else bad)

# 완전 분해: 서로 겹치는 부품 짝 (경계상자 기준 — 원통끼리는 조금 보수적)
sc.frame_set(60)
dg = bpy.context.evaluated_depsgraph_get()
boxes = {o.name: world_bbox(o) for o in parts}
# 같이 붙어 움직이는 덩어리(덮개·배터리실·마운트)와 몸체 속 외통은 겹쳐도 정상
GROUP = ("top_cover", "battery_housing", "helmet_mount_arm")
same = lambda a, b: (any(g in a.name for g in GROUP) and any(g in b.name for g in GROUP)) or \
    {a["explode_dist"], b["explode_dist"]} == {0.0}
hits = [(a.name, b.name) for i, a in enumerate(parts) for b in parts[i + 1:]
        if not same(a, b) and overlap(boxes[a.name], boxes[b.name])]
print("VERIFY exploded-overlap", "OK" if not hits else hits)
sc.frame_set(1)

ex.report(CODE, parts, os.path.join(OUT, "parts.md"))
ex.save_and_render(OUT, argv, get)
