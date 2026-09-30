"""ugs — 무인 지상 감시 센서 (말뚝형) 분해 씬. 속 회로·부품까지.

실행: Blender -b --factory-startup --python products/ugs.py -- [--look armory] [--render] [--frames 1,20,40,60]
+Z 위. 전고 0.40m (말뚝 끝 → 안테나 끝). 말뚝과 본체 케이스가 기준(고정).
분해 순서: 안테나 → 태양전지 → 윗덮개 → 위쪽 부품(무선·GPS·충전·PIR·마이크) → 메인 보드 → 배터리·진동 케이스 → 지오폰.
속 부품은 케이스 좌우(화면 오른쪽 +X+Y / 왼쪽 −X−Y) 두 줄로 벌어져, 위로만 길게 늘어서지 않게 한다.
부품 구성은 공개된 일반 UGS 구조(지진동·적외선·음향 감지, 저전력 MCU, 메시 무선, GPS, 배터리+태양광)를
바탕으로 한 것이다 — 특정 제품의 실제 배치가 아니다.
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

CODE = "ugs"
argv, get = ex.parse_args()
LOOK = get("--look", "armory")
OUT = ex.out_dir(HERE, CODE, LOOK)

# 높이는 말뚝 끝 = 0 기준으로 적고, 전체를 -H/2 내려 제품 중심을 원점에 둔다.
H = 0.400
Z0 = -H / 2
CONE_TOP, THIN_TOP, STAKE_TOP = 0.080, 0.140, 0.200
BODY = (0.100, 0.080, 0.090)
BODY_TOP = STAKE_TOP + BODY[2]
WALL = 0.004                           # 케이스 벽 두께
LID_T = 0.006                          # 윗덮개 두께 (케이스 윗면에서 아래로)
PANEL_T = 0.006
ANT_X, ANT_Y = -0.038, 0.028
T = Matrix.Translation
RX90 = Matrix.Rotation(math.radians(90), 4, 'X')    # 기판을 세워 부품면이 −Y 를 보게


def Tz(x, y, z):
    return T((x, y, z + Z0))


sc = ex.reset_scene()
coll = bpy.data.collections.new(CODE)
sc.collection.children.link(coll)
M = ex.standard_materials(CODE, ("olive", "black", "gunmetal", "glass", "pcb", "metal", "gold", "copper",
                                 "ceramic", "cell"))
PCB_MATS = [M["pcb"], M["black"], M["metal"], M["ceramic"], M["gold"]]   # bm_pcb 기본 순서 + 4 = 금
root = ex.make_root(CODE, coll, max_order=7)
parts = []


def add(name, bm, mat, direction, dist, order, label, desc="", **kw):
    ob = ex.part_object(f"{CODE}_{len(parts) + 1:02d}_{name}", bm, mat, coll, root, **kw)
    ex.set_meta(ob, direction, dist, order, label, desc)
    parts.append(ob)
    return ob


# 분해 끝 자리(말뚝 끝 = 0 기준 좌표)를 적으면 방향·거리를 계산한다
U = 0.160 / math.sqrt(2)               # 좌우 줄: 케이스 중심에서 대각선으로 0.16m


def goto(start, end):
    d = Vector(end) - Vector(start)
    return tuple(d.normalized()), d.length


def add_to(name, bm, mat, start, end, order, label, desc, **kw):
    direction, dist = goto(start, end)
    return add(name, bm, mat, direction, dist, order, label, desc, **kw)


# 01 지면 말뚝 — 원뿔 끝 + 가는 원통 + 굵은 상단(센서 칸) + 발로 밟는 턱
bm = bmesh.new()
ex.bm_cyl(bm, 0.0015, 0.018, CONE_TOP, 'Z', Tz(0, 0, CONE_TOP / 2), segs=24)
ex.bm_cyl(bm, 0.018, 0.018, THIN_TOP - CONE_TOP, 'Z', Tz(0, 0, (CONE_TOP + THIN_TOP) / 2), segs=24)
ex.bm_cyl(bm, 0.028, 0.028, STAKE_TOP - THIN_TOP, 'Z', Tz(0, 0, (THIN_TOP + STAKE_TOP) / 2), segs=32)
ex.set_mat(ex.bm_box(bm, (0.070, 0.014, 0.008), Tz(0, 0, THIN_TOP + 0.004)), 1)        # 턱
for z in (0.100, 0.115):                                                              # 걸림 링
    ex.set_mat(ex.bm_cyl(bm, 0.0205, 0.0205, 0.004, 'Z', Tz(0, 0, z), segs=24), 1)
add("ground_stake", bm, [M["gunmetal"], M["black"]], (0, 0, -1), 0.0, 0, "지면 말뚝",
    "땅에 박아 센서를 세우고, 땅에 단단히 붙어 진동이 지오폰까지 잘 전해지게 한다", bevel=0.0012)

# 02 센서 본체 케이스 — 윗면이 열린 상자(바닥 + 벽 4장) + 옆 커넥터 + 앞 창 + 뒤 손잡이. 말뚝과 함께 고정.
bm = bmesh.new()
bx, by, bh = BODY[0], BODY[1], BODY[2] - LID_T
zc = STAKE_TOP + bh / 2
ex.bm_box(bm, (bx, by, WALL), Tz(0, 0, STAKE_TOP + WALL / 2))                          # 바닥
for s in (+1, -1):
    ex.bm_box(bm, (WALL, by, bh), Tz(s * (bx - WALL) / 2, 0, zc))                       # 앞·뒤 벽
    ex.bm_box(bm, (bx - 2 * WALL, WALL, bh), Tz(0, s * (by - WALL) / 2, zc))            # 옆 벽
ex.set_mat(ex.bm_cyl(bm, 0.009, 0.009, 0.012, 'Y', Tz(0.020, -by / 2 - 0.005, STAKE_TOP + 0.030)), 1)
ex.set_mat(ex.bm_box(bm, (0.004, 0.030, 0.012), Tz(bx / 2 + 0.001, 0, STAKE_TOP + 0.062)), 2)   # PIR 창
ex.set_mat(ex.bm_box(bm, (0.006, 0.060, 0.010), Tz(-bx / 2 - 0.002, 0, STAKE_TOP + 0.020)), 1)  # 뒤 손잡이
add("sensor_body", bm, [M["olive"], M["black"], M["glass"]], (0, 0, 1), 0.0, 0, "센서 본체 케이스",
    "전자부품을 물·먼지·충격에서 지키는 외함", bevel=0.0018, segments=2)

# 03 안테나 — 받침 + 가늘고 긴 원통 + 끝 캡. 끝이 전고 0.40m
ANT_BASE_H = 0.016
rod_len = H - (BODY_TOP + ANT_BASE_H) - 0.004
bm = bmesh.new()
ex.set_mat(ex.bm_cyl(bm, 0.008, 0.009, ANT_BASE_H, 'Z', Tz(ANT_X, ANT_Y, BODY_TOP + ANT_BASE_H / 2), segs=20), 1)
ex.bm_cyl(bm, 0.0028, 0.0022, rod_len, 'Z', Tz(ANT_X, ANT_Y, BODY_TOP + ANT_BASE_H + rod_len / 2), segs=12)
ex.bm_cyl(bm, 0.004, 0.004, 0.004, 'Z', Tz(ANT_X, ANT_Y, H - 0.002), segs=12)
add("antenna", bm, [M["black"], M["gunmetal"]], (0, 0, 1), 0.20, 1, "안테나",
    "감지 결과를 전파로 내보낸다 — 이웃 센서나 기지국으로", bevel=0.0006)

# 04 태양전지 패널 — 상판. 프레임 + 셀(유리 덮개) + 격자선. 안테나 자리는 비운다.
PX0, PX1 = -0.022, BODY[0] / 2          # 뒤쪽은 안테나 자리
pcx, pw = (PX0 + PX1) / 2, PX1 - PX0
bm = bmesh.new()
ex.bm_box(bm, (pw, BODY[1], PANEL_T), Tz(pcx, 0, BODY_TOP + PANEL_T / 2))
ex.set_mat(ex.bm_box(bm, (pw - 0.008, BODY[1] - 0.008, 0.0012), Tz(pcx, 0, BODY_TOP + PANEL_T + 0.0004)), 1)
for i in range(1, 3):
    ex.bm_box(bm, (0.0012, BODY[1] - 0.008, 0.0016), Tz(PX0 + 0.004 + i * (pw - 0.008) / 3, 0, BODY_TOP + PANEL_T + 0.0004))
ex.bm_box(bm, (pw - 0.008, 0.0012, 0.0016), Tz(pcx, 0, BODY_TOP + PANEL_T + 0.0004))
add("solar_panel", bm, [M["gunmetal"], M["glass"]], (0, 0, 1), 0.155, 2, "태양전지 패널",
    "햇빛으로 충전식 배터리를 채워, 현장에 더 오래 둘 수 있게 한다", bevel=0.0008)

# 05 윗덮개 — 케이스를 밀봉. 안테나 관통부(금속 링) + 가장자리 패킹(검정)
bm = bmesh.new()
ex.bm_box(bm, (BODY[0], BODY[1], LID_T), Tz(0, 0, BODY_TOP - LID_T / 2))
ex.set_mat(ex.bm_cyl(bm, 0.0045, 0.0045, LID_T + 0.001, 'Z', Tz(ANT_X, ANT_Y, BODY_TOP - LID_T / 2), segs=16), 1)
ex.set_mat(ex.bm_box(bm, (BODY[0] - 2 * WALL + 0.001, BODY[1] - 2 * WALL + 0.001, 0.0015),
                     Tz(0, 0, BODY_TOP - LID_T - 0.0006)), 2)
add("lid", bm, [M["olive"], M["gold"], M["black"]], (0, 0, 1), 0.11, 3, "윗덮개",
    "케이스를 물·먼지 없이 밀봉하고, 태양전지와 안테나를 받친다", bevel=0.0015, segments=2)

# ---- 케이스 속 (말뚝 끝 = 0 기준 z) ----
BAT_C = (-0.005, 0.0, 0.225)            # 배터리 팩: 바닥 위
MAIN_Z = 0.2468                         # 메인 보드 (배터리 위)

# 06 무선 통신 모듈 — 안테나 바로 아래. 작은 기판 + 차폐캔 + 금색 안테나 커넥터(U.FL)
RAD_C = (-0.028, 0.018, 0.2575)
bm = bmesh.new()
info = ex.bm_pcb(bm, (0.030, 0.020, 0.0010), Tz(*RAD_C),
                 chips=[(0.005, 0.001, 0.016, 0.014, 0.0028, 'can', "RF 트랜시버(메시)",
                         "차폐캔 속 무선 칩. 감지 신호를 전파로 바꿔 보내고, 이웃 센서의 신호도 받아 대신 넘겨 준다(중계)"),
                        (-0.010, -0.006, 0.0030, 0.0016, 0.0010, 'sot', "LDO 전원 레귤레이터",
                         "배터리 전압을 무선 칩이 쓰는 일정한 낮은 전압(보통 3.3V)으로 깨끗하게 낮춘다"),
                        (-0.010, 0.0065, 0.0032, 0.0020, 0.0008, 'crystal', "크리스털 발진기",
                         "무선 주파수를 정확히 맞추는 기준 박자를 만든다"),
                        (-0.005, -0.008, 0.0015, 0.0008, 0.0006, 'passive'),
                        (-0.005, 0.008, 0.0015, 0.0008, 0.0006, 'passive')])
ex.set_mat(ex.bm_cyl(bm, 0.0014, 0.0014, 0.0014, 'Z', Tz(RAD_C[0] - 0.011, RAD_C[1] + 0.001, RAD_C[2] + 0.0012),
                     segs=12), 4)
for dx in (-0.012, 0.012):                                                            # 받침 기둥
    ex.set_mat(ex.bm_cyl(bm, 0.0012, 0.0012, 0.009, 'Z', Tz(RAD_C[0] + dx, RAD_C[1] - 0.007, RAD_C[2] - 0.005),
                         segs=8), 2)
ob = add_to("radio_module", bm, PCB_MATS, RAD_C, (U, U, 0.335), 4, "무선 통신 모듈(메시)",
            "센서끼리 그물처럼 이어져, 옆 센서를 징검다리 삼아 멀리 있는 기지국까지 신호를 넘긴다", bevel=0.0002, segments=1)
ex.attach_chips(ob, info + [("안테나 커넥터(U.FL)", "위쪽 안테나 케이블을 꽂는 금도금 소형 동축 단자",
                              (RAD_C[0] - 0.011, RAD_C[1] + 0.001, RAD_C[2] + 0.0019 + Z0))])

# 07 GPS 모듈 — 하늘을 보도록 덮개 바로 밑. 기판 + 세라믹 패치 안테나(은색 면)
GPS_C = (0.020, -0.015, 0.2700)
bm = bmesh.new()
PX = GPS_C[0] - 0.004                                                                 # 패치 안테나 중심 (왼쪽으로)
info = ex.bm_pcb(bm, (0.024, 0.024, 0.0010), Tz(*GPS_C),
                 chips=[(0.0080, 0.0060, 0.0050, 0.0050, 0.0009, 'qfn', "GPS 수신 칩",
                         "여러 위성의 신호 도착 시간을 비교해 위치와 정확한 시각을 계산한다"),
                        (0.0085, -0.0015, 0.0030, 0.0016, 0.0010, 'sot', "저잡음 증폭기(LNA)",
                         "안테나가 받은 아주 약한 위성 신호를 잡음 없이 키운다"),
                        (0.0060, -0.0098, 0.0032, 0.0025, 0.0009, 'crystal', "TCXO(온도보상 발진기)",
                         "추위·더위에도 흔들리지 않는 기준 박자 — 위성 신호를 빨리 잡게 한다"),
                        (0.0105, 0.0100, 0.0016, 0.0008, 0.0006, 'passive'),
                        (-0.0080, 0.0100, 0.0016, 0.0008, 0.0006, 'passive')])
ex.set_mat(ex.bm_box(bm, (0.014, 0.014, 0.0040), Tz(PX, GPS_C[1], GPS_C[2] + 0.0025)), 3)               # 세라믹 패치
ex.set_mat(ex.bm_box(bm, (0.010, 0.010, 0.0003), Tz(PX, GPS_C[1], GPS_C[2] + 0.0047)), 2)               # 은 전극
ex.set_mat(ex.bm_cyl(bm, 0.0008, 0.0008, 0.0006, 'Z', Tz(PX + 0.002, GPS_C[1] + 0.002, GPS_C[2] + 0.0050),
                     segs=8), 4)
info.append(("세라믹 패치 안테나", "하늘을 향한 네모 세라믹 판. 위성에서 오는 약한 전파를 모은다",
             (PX, GPS_C[1] - 0.007, GPS_C[2] + 0.0020 + Z0)))                                   # 앞 옆면 가운데 (부품 이름표와 안 겹치게)
for dx, dy in ((-0.010, -0.010), (0.010, 0.010)):
    ex.set_mat(ex.bm_cyl(bm, 0.0012, 0.0012, 0.020, 'Z', Tz(GPS_C[0] + dx, GPS_C[1] + dy, GPS_C[2] - 0.0105),
                         segs=8), 2)
ob = add_to("gps_module", bm, PCB_MATS, GPS_C, (-U, -U, 0.345), 4, "GPS 모듈",
            "센서가 놓인 위치를 스스로 알아내, 어디서 감지됐는지 알 수 있게 한다", bevel=0.0002, segments=1)
ex.attach_chips(ob, info)

# 08 태양광 충전 기판 — 코일(인덕터) + 충전 IC + 커넥터
CHG_C = (0.015, 0.019, 0.2575)
bm = bmesh.new()
info = ex.bm_pcb(bm, (0.030, 0.022, 0.0010), Tz(*CHG_C),
                 chips=[(-0.006, 0.002, 0.007, 0.007, 0.0045, 'inductor', "전력 인덕터(코일)",
                         "전기를 잠깐 자기장으로 담았다 내놓으며 전압을 바꾼다 — 충전 회로의 핵심 부품"),
                        (0.0055, 0.0045, 0.0045, 0.0045, 0.0009, 'qfn', "충전 제어 IC(MPPT)",
                         "태양전지가 가장 많은 전기를 내는 전압을 찾아 맞추고(MPPT), 배터리가 다 차면 충전을 멈춘다"),
                        (0.0110, -0.0005, 0.0030, 0.0016, 0.0010, 'sot', "역류 방지 MOSFET",
                         "밤에 배터리 전기가 태양전지 쪽으로 거꾸로 새지 않게 막는 전자 스위치"),
                        (0.0115, 0.0065, 0.0035, 0.0035, 0.0045, 'cap', "입력 커패시터",
                         "충전 회로가 전기를 켰다 껐다 할 때 생기는 전압 출렁임을 받쳐 준다"),
                        (-0.011, -0.007, 0.006, 0.004, 0.0030, 'conn', "태양전지 입력 커넥터",
                         "덮개 위 태양전지 패널의 전선을 꽂는 단자"),
                        (0.0075, -0.0075, 0.0020, 0.0012, 0.0008, 'passive'),
                        (0.0110, -0.0075, 0.0020, 0.0012, 0.0008, 'passive')])
ex.set_mat(ex.bm_cyl(bm, 0.0033, 0.0033, 0.0012, 'Z', Tz(CHG_C[0] - 0.006, CHG_C[1] + 0.002, CHG_C[2] + 0.0055),
                     segs=16), 5)                                                     # 코일 권선이 보이게
for dx in (-0.012, 0.012):
    ex.set_mat(ex.bm_cyl(bm, 0.0012, 0.0012, 0.009, 'Z', Tz(CHG_C[0] + dx, CHG_C[1] - 0.008, CHG_C[2] - 0.005),
                         segs=8), 2)
ob = add_to("charge_board", bm, PCB_MATS + [M["copper"]], CHG_C, (U, U, 0.270), 4, "태양광 충전 기판",
            "태양전지의 들쭉날쭉한 전압을 배터리에 맞게 바꿔, 넘치지 않게 충전한다", bevel=0.0002, segments=1)
ex.attach_chips(ob, info)

# 09 적외선(PIR) 감지기 — 앞 창 뒤에 세운 기판 + 초전 센서(금속 캔) + 흰 프레넬 렌즈 돔. +X(앞)를 본다
PIR_C = (0.034, 0.0, 0.265)
bm = bmesh.new()
info = ex.bm_pcb(bm, (0.024, 0.024, 0.0012), Tz(*PIR_C) @ ex.rot('X'),
                 chips=[(-0.0080, -0.0060, 0.0045, 0.0035, 0.0012, 'ic', "초전 센서 증폭기",
                         "초전 센서의 아주 작은 전압 변화를 크게 키우고 잡음을 걸러 낸다"),
                        (-0.0080, 0.0070, 0.0030, 0.0016, 0.0010, 'sot', "비교기(감지 판정)",
                         "증폭된 신호가 기준을 넘으면 '움직임 있음' 신호를 메인 보드로 보낸다"),
                        (0.0095, 0.0085, 0.0020, 0.0012, 0.0008, 'passive'),
                        (0.0095, -0.0085, 0.0020, 0.0012, 0.0008, 'passive')])
ex.set_mat(ex.bm_cyl(bm, 0.0045, 0.0045, 0.004, 'X', Tz(PIR_C[0] + 0.0026, 0, 0.262)), 2)             # 초전 센서
ex.set_mat(ex.bm_hemisphere(bm, 0.0060, 'X', Tz(PIR_C[0] + 0.0046, 0, 0.262), segs=20), 3)          # 프레넬 렌즈
ob = add_to("pir_sensor", bm, PCB_MATS, PIR_C, (-U, -U, 0.290), 4, "적외선(PIR) 감지기",
            "사람 몸의 열(적외선)이 움직이면 반응하는 초전 센서. 흰 렌즈(프레넬 렌즈)가 넓은 범위의 적외선을 센서로 모아 준다",
            bevel=0.0002, segments=1)
ex.attach_chips(ob, info + [("초전(PIR) 센서", "금속 캔 속 결정이 열(적외선)의 변화를 받으면 전압을 낸다",
                              (PIR_C[0] + 0.0106, 0.0, 0.262 + Z0))])                                # 렌즈 돔 앞 끝

# 10 음향 마이크 — 옆 벽(−Y) 안쪽에 세운 작은 기판 + MEMS 마이크 + 증폭 IC
MIC_C = (-0.020, -0.0335, 0.265)
bm = bmesh.new()
info = ex.bm_pcb(bm, (0.020, 0.016, 0.0010), Tz(*MIC_C) @ RX90,
                 chips=[(-0.0045, 0.0015, 0.0040, 0.0030, 0.0012, 'can', "MEMS 마이크",
                         "작은 금속 캔 속 실리콘 막이 소리에 떨리며 전기 신호를 만든다"),
                        (0.0050, 0.0030, 0.0040, 0.0030, 0.0009, 'qfn', "마이크 증폭기(프리앰프)",
                         "작은 소리 신호를 키워, 엔진·발소리 구분에 쓸 만큼 또렷하게 만든다"),
                        (-0.0045, -0.0045, 0.0030, 0.0016, 0.0009, 'sot', "전원 필터 레귤레이터",
                         "마이크 전원의 잡음을 걸러 소리 신호에 섞이지 않게 한다"),
                        (0.0050, -0.0045, 0.0020, 0.0012, 0.0008, 'passive')])
ob = add_to("microphone", bm, PCB_MATS, MIC_C, (-U, -U, 0.235), 4, "음향 마이크",
            "엔진·발소리를 듣는다. 진동 신호와 함께 분석해 사람인지 차량인지 가려내는 데 쓴다", bevel=0.0002, segments=1)
ex.attach_chips(ob, info)

# 11 메인 제어 보드 — 저전력 MCU + 메모리 + 신호 증폭(ADC) + 크리스털 + 커넥터들
bm = bmesh.new()
info = ex.bm_pcb(bm, (0.084, 0.064, 0.0016), Tz(0, 0, MAIN_Z),
                 chips=[(0.004, 0.000, 0.010, 0.010, 0.0012, 'qfp', "저전력 MCU",
                         "센서 신호를 분석해 사람·차량을 가려내고 기록한다. 평소엔 저전력 대기로 전기를 아끼다가 신호가 오면 깨어난다 (예: 저전력 ARM Cortex-M 계열 — 실제 제품 부품 아님)"),
                        (-0.014, -0.016, 0.006, 0.004, 0.0010, 'ic', "플래시 메모리",
                         "전기가 끊겨도 지워지지 않게 감지 기록과 프로그램을 저장한다"),
                        (0.020, -0.016, 0.005, 0.005, 0.0009, 'qfn', "ADC(신호 변환기)",
                         "지오폰·마이크의 흔들리는 전압을 MCU가 읽을 수 있는 숫자로 바꾼다"),
                        (0.020, -0.003, 0.006, 0.004, 0.0010, 'ic', "저잡음 증폭기(지오폰용)",
                         "먼 발걸음처럼 아주 약한 땅 떨림 신호를 잡음 없이 키운다"),
                        (0.004, 0.013, 0.0045, 0.0020, 0.0010, 'crystal', "크리스털 발진기",
                         "MCU가 쓰는 일정한 시계 박자를 만든다"),
                        (-0.022, 0.016, 0.0030, 0.0016, 0.0010, 'sot', "전원 레귤레이터",
                         "배터리 전압을 칩들이 쓰는 일정한 전압(보통 3.3V)으로 맞춘다"),
                        (-0.022, 0.004, 0.0050, 0.0050, 0.0055, 'cap'),
                        (-0.036, 0.000, 0.004, 0.014, 0.0040, 'conn', "배터리 커넥터",
                         "아래 배터리 팩의 전선을 꽂는 단자"),
                        (0.036, -0.020, 0.004, 0.010, 0.0035, 'conn', "센서 커넥터",
                         "지오폰·PIR·마이크 기판을 메인 보드에 잇는 단자"),
                        (-0.012, 0.012, 0.0020, 0.0012, 0.0008, 'passive'), (-0.008, 0.012, 0.0020, 0.0012, 0.0008, 'passive'),
                        (0.014, 0.008, 0.0020, 0.0012, 0.0008, 'passive'), (0.028, 0.008, 0.0020, 0.0012, 0.0008, 'passive'),
                        (0.028, 0.013, 0.0020, 0.0012, 0.0008, 'passive')])
for x, y in ((-0.038, -0.028), (-0.038, 0.028), (0.038, -0.028), (0.038, 0.028)):    # 나사 구멍 링
    ex.set_mat(ex.bm_cyl(bm, 0.0022, 0.0022, 0.0018, 'Z', Tz(x, y, MAIN_Z), segs=12), 4)
ob = add_to("main_board", bm, PCB_MATS, (0, 0, MAIN_Z), (0, 0, 0.335), 5, "메인 제어 보드",
            "저전력 마이크로컨트롤러가 센서 신호를 분석해 사람·차량을 가려내고 기록한다. 평소엔 저전력 대기로 전기를 아낀다",
            bevel=0.0002, segments=1)
ex.attach_chips(ob, info)

# 12 배터리 팩 — 리튬 원통 셀 4개(2×2, X 방향으로 눕힘) + 검정 홀더 판 + 니켈 연결판
bm = bmesh.new()
cx, cy, cz = BAT_C
for sy in (-1, 1):
    for sz in (-1, 1):
        ex.bm_cyl(bm, 0.0088, 0.0088, 0.064, 'X', Tz(cx, cy + sy * 0.009, cz + sz * 0.009), segs=24)
for sx in (-1, 1):
    ex.set_mat(ex.bm_box(bm, (0.003, 0.038, 0.038), Tz(cx + sx * 0.0335, cy, cz)), 1)          # 홀더
    ex.set_mat(ex.bm_box(bm, (0.0006, 0.030, 0.030), Tz(cx + sx * 0.0353, cy, cz)), 2)         # 니켈판
ex.set_mat(ex.bm_box(bm, (0.004, 0.006, 0.006), Tz(cx + 0.037, cy + 0.010, cz + 0.010)), 1)    # 출력 단자 (홀더 옆)
add_to("battery_pack", bm, [M["cell"], M["black"], M["metal"]], BAT_C, (U, U, 0.198), 6, "배터리 팩(충전식 리튬)",
       "전기를 저장한다. 저전력 설계 덕분에 한 번 충전으로 수 주, 제품에 따라 1년 가까이 버티기도 한다", bevel=0.0008, segments=2)

# 13 지진동 센서 케이스 — 말뚝 상단 속. 지오폰을 감싸는 방수 통
SEI_C = (0, 0, STAKE_TOP - 0.024)
bm = bmesh.new()
ex.bm_box(bm, (0.030, 0.030, 0.036), Tz(*SEI_C))
ex.set_mat(ex.bm_cyl(bm, 0.008, 0.008, 0.006, 'Z', Tz(0, 0, STAKE_TOP - 0.004), segs=20), 1)   # 커넥터
add_to("seismic_case", bm, [M["olive"], M["gunmetal"]], SEI_C, (U, U, 0.140), 6, "지진동 센서 케이스",
       "속의 지오폰을 흙·물에서 지키고, 땅의 떨림이 잘 전해지도록 말뚝에 꽉 물린다", bevel=0.0015)

# 14 지오폰 — 가운데 자석 + 둘레 구리 코일 + 위아래 판스프링. 1축(위아래 진동)
GEO_C = (0, 0, SEI_C[2])
bm = bmesh.new()
ex.set_mat(ex.bm_cyl(bm, 0.0095, 0.0095, 0.012, 'Z', Tz(*GEO_C), segs=24), 0)                    # 코일
ex.set_mat(ex.bm_cyl(bm, 0.0050, 0.0050, 0.022, 'Z', Tz(*GEO_C), segs=16), 1)                    # 자석
for dz in (-0.0085, 0.0085):
    ex.set_mat(ex.bm_cyl(bm, 0.0090, 0.0090, 0.0006, 'Z', Tz(GEO_C[0], GEO_C[1], GEO_C[2] + dz), segs=24), 2)
add_to("geophone", bm, [M["copper"], M["gunmetal"], M["metal"]], GEO_C, (-U, -U, 0.160), 7, "지오폰(진동 감지 코일)",
       "스프링에 매달린 코일이 자석 옆에서 흔들리면 전기가 생긴다 — 발걸음·차량의 땅 떨림을 전기 신호로 바꾼다",
       bevel=0.0004, segments=1)

for ob in parts:
    ex.add_explode_drivers(ob, root)
ex.key_explode(root, 1, 60)

# 카메라: 위로 벌어지고 좌우로도 퍼지므로 약간 위에서 3/4, 넉넉히
ex.apply_look(LOOK, dict(cam_loc=(0.80, -0.80, 0.34), target=(0, 0, 0.12), lens=31), OUT)

# ---- 검증 ----
ex.verify_explode(parts)
sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()


def world_bbox(o):
    ev = o.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def by(name):
    return next(o for o in parts if o.name.endswith(name))


# 조립 상태: 속 부품이 케이스 안쪽(벽·바닥·덮개 사이)에 들어 있는가
inner_lo = [-BODY[0] / 2 + WALL - 1e-4, -BODY[1] / 2 + WALL - 1e-4, STAKE_TOP + WALL + Z0 - 1e-4]
inner_hi = [BODY[0] / 2 - WALL + 1e-4, BODY[1] / 2 - WALL + 1e-4, BODY_TOP - LID_T + Z0 + 1e-4]
bad = []
for nm in ("radio_module", "gps_module", "charge_board", "pir_sensor", "microphone", "main_board", "battery_pack"):
    a, b = world_bbox(by(nm))
    if not all(inner_lo[i] <= a[i] and b[i] <= inner_hi[i] for i in range(3)):
        bad.append((nm, [round(v, 4) for v in a], [round(v, 4) for v in b]))
print("VERIFY internals-inside-case", "OK" if not bad else bad)

# 조립 상태: 속 부품끼리 안 겹치는가 (바운딩박스)


def overlap(a, b, eps=-2e-4):
    (a0, a1), (b0, b1) = a, b
    return all(a0[i] < b1[i] + eps and b0[i] < a1[i] + eps for i in range(3))


# 메인 보드 위 부품들은 받침 기둥이 보드에 닿아 있으니 보드는 빼고, 대신 배터리가 보드 밑에 있는지 따로 본다
inner = [by(n) for n in ("radio_module", "gps_module", "charge_board", "pir_sensor", "microphone", "battery_pack")]
hits = [(p.name, q.name) for i, p in enumerate(inner) for q in inner[i + 1:] if overlap(world_bbox(p), world_bbox(q))]
print("VERIFY internals-no-overlap(frame1)", "OK" if not hits else hits)
print("VERIFY battery-under-board", "OK" if world_bbox(by("battery_pack"))[1][2] < world_bbox(by("main_board"))[0][2] else "FAIL")

lo, hi = world_bbox(parts[0])
for o in parts[1:]:
    a, b = world_bbox(o)
    lo, hi = [min(lo[i], a[i]) for i in range(3)], [max(hi[i], b[i]) for i in range(3)]
print("VERIFY height(m)", round(hi[2] - lo[2], 3), "center z", round((hi[2] + lo[2]) / 2, 3))

# 분해 끝: 어떤 두 부품도 바운딩박스가 겹치지 않는가 (말뚝·케이스 포함)
sc.frame_set(60)
dg = bpy.context.evaluated_depsgraph_get()
boxes = [(o.name, world_bbox(o)) for o in parts]
hits = [(a[0], b[0]) for i, a in enumerate(boxes) for b in boxes[i + 1:] if overlap(a[1], b[1])]
print("VERIFY no-overlap(frame60)", "OK" if not hits else hits)

ex.report(CODE, parts, os.path.join(OUT, "parts.md"))
ex.save_and_render(OUT, argv, get)
