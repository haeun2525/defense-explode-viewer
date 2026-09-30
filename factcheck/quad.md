# 사실 확인 — 정찰 쿼드콥터 (quad)

- 대상: `products/quad.py` 의 부품·칩 이름과 설명, `web/index.html` 의 `SCEN.quad` 작동 단계, 제목(NAMES)
- 기준: 특정 제품이 아니라 **일반적인 소형 정찰 드론 구성**이다. "소형 드론이라면 대체로 맞다"여야 통과이고, 구체적인 숫자는 출처가 있거나 표현을 누그러뜨렸다.
- 판정
  - **맞음**: 그대로 둠
  - **고침**: 틀렸거나 지나치게 단정해서 고침
  - **확인 불가**: 출처가 없어서 일반적인 표현으로 바꿈
- 반영: 부품·칩 문구는 `products/quad.py` 에 반영했다. 작동 단계는 `factcheck/quad-scen.json` 에 수정안만 적었다(index.html 은 건드리지 않음).

## 부품

| 항목 | 원래 문구 | 판정 | 고친 문구 | 근거(URL) |
|---|---|---|---|---|
| 하부 프레임·암 | 기체의 뼈대. 카본 암 네 개가 모터를 받치고, 안쪽에 보드와 배터리가 들어간다 | 맞음 | (그대로 — 이 모델의 모양 설명) | — |
| 프로펠러 | 모터가 돌려 양력을 만든다. 대각선끼리 같은 방향으로 돈다 | 고침 | 모터가 돌려 기체를 띄우는 힘(추력)을 만든다. 대각선끼리 같은 방향으로 돈다 | https://ardupilot.org/copter/docs/connect-escs-and-motors.html · https://en.wikipedia.org/wiki/Quadcopter |
| 모터 | 브러시리스 모터. 코일에 전류를 번갈아 흘려 바깥 캔(자석)을 돌린다 | 맞음 | — | https://blog.skyrc.com/how-brushless-motors-work/ |
| 모터 로터 | 바깥에서 도는 캔. 안쪽 벽에 영구자석이 붙어 있다 | 맞음 | — | https://www.x-teamrc.com/inrunner-vs-outrunner-brushless-motors/ |
| 모터 코일 | 구리선을 감은 고정자. ESC 가 전류 방향을 빠르게 바꿔 회전 자기장을 만든다 | 맞음 | — | https://blog.skyrc.com/how-brushless-motors-work/ |
| 배터리 팩 | 셀을 감싸는 케이스. 앞쪽 금속 단자로 배전 기판에 전기를 넘긴다 | 확인 불가 | 셀을 감싸는 케이스. 금속 단자로 기체에 전기를 넘긴다 | (단자 위치는 기체마다 다름) |
| 배터리 셀(3S) | 리튬이온 셀 3개를 직렬로 이어 약 11V. 위의 얇은 기판(BMS)이 과충전·과방전을 막는다 | 고침 | 예: 리튬이온 셀 3개를 직렬로 이으면 약 11V(셀당 약 3.6~3.7V). 위의 얇은 기판(BMS)이 과충전·과방전을 막는다 | https://www.batteryuniversity.com/article/bu-303-confusion-with-voltages/ |
| 짐벌(3축 모터) | 모터 세 개가 기체 흔들림을 반대로 상쇄해 카메라를 늘 수평으로 붙잡는다 | 고침 | … 카메라가 흔들리지 않게 붙잡는다 | ('늘 수평'은 과장 — 짐벌은 카메라를 기울여 아래를 보기도 함) |
| 카메라 하우징 | 렌즈·센서를 먼지와 빛샘에서 막는 알루미늄 몸통 | 확인 불가 | 렌즈·센서를 먼지와 빛샘에서 막는 단단한 몸통 | (재질 출처 없음) |
| 렌즈군 | 렌즈 여러 장이 빛을 모아 센서에 초점을 맺는다. 앞뒤로 움직여 줌·초점을 맞춘다 | 고침 | 렌즈 여러 장이 빛을 모아 센서에 상을 맺는다. 줌·초점용 렌즈는 앞뒤로 움직인다 | (렌즈 전체가 움직이는 게 아님) |
| 열상 코어 | 미세한 온도 차를 보는 적외선 센서(마이크로볼로미터). 밤이나 연기 속에서도 사람·차량의 열을 찾는다 | 고침(표현) | 물체가 내는 열(적외선)을 보는 센서(마이크로볼로미터). 빛이 없거나 연기가 낀 곳에서도 사람·차량의 열을 찾는다 | https://www.axiomoptics.com/products/infrared-cameras-and-solutions/lwir-cameras-and-cores/ · https://en.wikipedia.org/wiki/Forward-looking_infrared · https://oem.flir.com/about/news/innovating-the-most-sensitive-uncooled-thermal-camera-drone-payload-with-skydio/ |
| 이미지 센서 보드 | 렌즈가 모은 빛을 전기 신호로 바꾸는 CMOS 센서와 영상 처리 칩 | 맞음 | — | https://www.skydio.com/ja-jp/resources/datasheets/skydio-x2d-colorthermal |
| 상부 덮개 | 위쪽 껍데기. 보드를 비·먼지로부터 막고, 앞면에 항법 카메라 창이 뚫려 있다 | 맞음 | (이 모델의 모양 설명) | — |
| 항법 카메라 쌍 | 두 눈처럼 떨어진 카메라로 거리를 재서 장애물을 피하고, GPS 없이도 위치를 추정한다 | 맞음 | — | https://developer.nvidia.com/blog/skydio-2-jetson-tx2-drone/ · https://www.originofbots.com/robot/skydio-x2d-by-skydio-details-specifications-rating (GPS-denied navigation) |
| 자율비행 컴퓨터 | 카메라 영상으로 주변을 3D 로 그리고 경로를 스스로 짜는 AI 칩. 뜨거워서 방열판을 얹는다 | 맞음 | — | https://developer.nvidia.com/blog/skydio-2-jetson-tx2-drone/ |
| 데이터링크 무전 모듈 | 조종기와 영상·명령을 주고받는 암호화 무선. 안테나 두 개로 끊김을 줄인다 | 고침 | 조종기와 영상·명령을 주고받는 무선. 군용은 보통 암호화한다. 안테나를 두 개 쓰면 한쪽이 약할 때 다른 쪽이 받아 끊김이 준다 | https://www.originofbots.com/robot/skydio-x2d-by-skydio-details-specifications-rating · https://lectrosonics.com/comparing-diversity-reception-techniques/ |
| GPS·나침반 모듈 | 위성 신호로 위치를, 지자기 센서로 기체가 향한 방향을 잰다 | 맞음 | — | https://content.u-blox.com/sites/default/files/products/documents/GNSS-Antennas_AppNote_(UBX-15030289).pdf |
| 비행 컨트롤러 | 두뇌. IMU(기울기·회전)와 기압계(고도)를 1초에 수천 번 읽어 네 모터 세기를 정한다 | 고침 | 두뇌. IMU(기울기·회전)는 1초에 수백~수천 번, 기압계(고도)는 그보다 드물게 읽어 네 모터 세기를 정한다 | https://oscarliang.com/best-looptime-flight-controller/ · https://betaflight.com/docs/wiki/app/configuration-tab |
| 4-in-1 ESC | 비행 컨트롤러의 명령대로 배터리 전력을 잘게 끊어 모터 네 개에 보낸다 | 맞음 | — | https://oscarliang.com/best-blheli-32-settings/ |
| 배전 기판 | 배터리 전원을 받아 ESC 로 보내고, 보드들이 쓰는 5V·3.3V 를 만든다 | 맞음 | — | (일반 구성) |

## 칩 이름표

| 기판 · 칩 | 원래 문구 | 판정 | 고친 문구 | 근거(URL) |
|---|---|---|---|---|
| BMS · 배터리 보호 IC | 셀마다 전압을 지켜보다가 너무 차거나 비면 전류를 끊으라고 MOSFET 에 알린다 | 맞음 | — | https://www.ablic.com/en/semicon/products/power-management-ic/lithium-ion-battery-protection-ic/s-821a-821b/ |
| BMS · 보호 MOSFET | 보호 IC 의 신호를 받아 배터리 전류 길을 열고 닫는 전자 스위치 | 맞음 | — | 같은 곳 |
| BMS · 온도 센서(NTC) | 셀이 뜨거워지면 저항값이 바뀌어, 과열되기 전에 충전·방전을 멈추게 한다 | 맞음 | — | https://www.ablic.com/en/semicon/datasheets/power-management-ic/lithium-ion-battery-protection-ic/s-82d1a/ |
| BMS · 밸런스 커넥터 | 셀 하나하나의 전압을 충전기로 이어, 셀끼리 고르게 충전되게 한다 | 맞음 | — | https://www.batterypkcell.com/news/lithium-battery-voltage-chart-li-ion-vs-lifepo4-from-1s-to-4s/ |
| 이미지 센서 · 이미지 센서(CMOS) | 렌즈가 모은 빛을 수백만 개의 화소가 받아 전기 신호로 바꾼다 — 카메라의 눈 | 맞음 | — | https://www.skydio.com/ja-jp/resources/datasheets/skydio-x2d-colorthermal (12MP) |
| 이미지 센서 · 영상 처리 칩(ISP) | 센서 신호의 색·밝기·잡음을 다듬고 영상을 압축해 넘긴다 | 고침 | 센서 신호의 색·밝기·잡음을 다듬어 영상으로 만든다 | (압축은 보통 주 프로세서·인코더가 함) |
| 이미지 센서 · 전원 레귤레이터 | 센서가 쓰는 1.2V·2.8V 같은 깨끗한 전압을 만든다 | 확인 불가 | 센서가 쓰는 여러 가지 낮은 전압을 깨끗하게 만든다 | (구체 전압은 센서마다 다름) |
| 이미지 센서 · 크리스털 발진기 | 화소를 읽어 내는 박자(클럭)를 정확하게 맞춘다 | 맞음 | — | (일반 구성) |
| 자율비행 · AI 프로세서(SoC) | 예: NVIDIA Jetson 계열 모듈 — 영상으로 장애물·지형을 알아보고 갈 길을 계산한다 | 맞음 | — ('예:' 유지) | https://developer.nvidia.com/blog/skydio-2-jetson-tx2-drone/ |
| 자율비행 · LPDDR 메모리 | AI 칩이 영상과 지도를 계산하는 동안 잠깐 담아 두는 고속 메모리 | 맞음 | — | (일반 구성) |
| 자율비행 · eMMC 저장장치 | 운영체제와 AI 모델, 비행 기록을 전원이 꺼져도 남게 저장한다 | 고침 | 운영체제와 AI 프로그램을 전원이 꺼져도 남게 저장한다 | (비행 기록 저장 위치는 확인 불가) |
| 자율비행 · 전원 관리 칩(PMIC) | 여러 전압을 정해진 순서로 켜서 AI 칩에 안정적인 전원을 준다 | 맞음 | — | (일반 구성) |
| 자율비행 · 카메라 입력 커넥터(MIPI) | 항법 카메라 영상을 AI 칩으로 받아들이는 고속 단자 | 맞음 | — | (일반 구성) |
| 자율비행 · 방열판 | AI 칩에서 나는 열을 얇은 핀 여러 장으로 퍼뜨려 공기로 식힌다 | 맞음 | — | — |
| 무전 · RF 모듈(차폐캔) | 캔 속의 RF 트랜시버·증폭기가 영상·명령을 전파로 바꾼다. 금속 캔이 잡음을 막는다 | 맞음 | — | (일반 구성) |
| 무전 · 안테나 커넥터 | 작은 동축 단자. 여기서 안테나 선을 따라 전파가 나간다 | 맞음 | — | — |
| 무전 · 암호화 칩 | 주고받는 데이터를 암호로 바꿔 도청이나 가로채기를 막는다 | 고침 | 예시 — 데이터를 암호로 바꿔 엿들어도 내용을 알 수 없게 한다 (무전 칩 안에서 하기도 한다) | (별도 칩 여부 확인 불가 · '가로채기를 막는다'는 과장) |
| 무전 · 전원 레귤레이터 / 크리스털 발진기 | (전압 낮추기 / 기준 박자) | 맞음 | — | — |
| GPS · GPS 수신 칩 | 위성 여러 개의 신호가 도착한 시간 차로 지금 위치와 정확한 시각을 계산한다 | 고침 | 위성 신호가 오는 데 걸린 시간으로 거리를 재서, 위성 4개 이상이면 위치와 정확한 시각을 계산한다 | https://content.u-blox.com/sites/default/files/products/documents/GNSS-Antennas_AppNote_(UBX-15030289).pdf |
| GPS · 지자기 센서(나침반) | 지구 자기장을 재서 기체 머리가 어느 쪽을 향하는지 알려 준다 | 맞음 | — | — |
| GPS · TCXO | 추위·더위에도 흔들리지 않는 박자를 만들어 위성 신호를 빨리 잡게 한다 | 고침(표현) | 온도가 바뀌어도 거의 흔들리지 않는 박자를 만들어 약한 위성 신호를 잡는 걸 돕는다 | https://content.u-blox.com/sites/default/files/MAX-TCXO-to-Crystal-MigrationGuide_AppNote_UBX-20056846.pdf |
| GPS · 저잡음 증폭기(LNA) | 안테나로 들어온 아주 약한 위성 신호를 잡음 없이 키운다 | 맞음 | — | https://www.gpsworld.com/u-blox-gnss-antenna-module-supports-all-satellites/ |
| GPS · 세라믹 패치 안테나 | 하늘을 향한 네모난 세라믹 판. 우주에서 오는 아주 약한 GPS 전파를 받는다 | 맞음 | — | 같은 곳 |
| 비행 컨트롤러 · MCU | 예: STM32 계열 — … 모터 4개의 세기를 1초에 수천 번 정한다 | 고침 | … 1초에 수백~수천 번 정한다 | https://oscarliang.com/best-looptime-flight-controller/ |
| 비행 컨트롤러 · IMU | … 흔들림이 적은 보드 가운데 쪽에 둔다 | 고침 | … 비행 컨트롤러는 기체 무게중심 가까이 두는 게 좋다 | https://ardupilot.org/copter/docs/common-mounting-the-flight-controller.html |
| 비행 컨트롤러 · 기압계 | … 금속 뚜껑의 구멍으로 공기가 들어간다 | 고침 | … 바람의 영향을 줄이려 스펀지를 덮기도 한다 | https://ardupilot.org/copter/docs/common-mounting-the-flight-controller.html |
| 비행 컨트롤러 · 블랙박스 메모리(플래시) | 비행 중 센서 값과 명령을 기록해, 사고가 나면 원인을 찾게 한다 | 맞음 | — | https://betaflight.com/docs/wiki/guides/current/Black-Box-logging-and-usage |
| 비행 컨트롤러 · 전원 레귤레이터(3.3V) / 크리스털 / ESC 커넥터 | — | 맞음 | — | (일반 구성) |
| ESC · ESC 제어 MCU / 게이트 드라이버 / 전해 커패시터 | — | 맞음 | — | https://oscarliang.com/best-blheli-32-settings/ |
| ESC · 전류 센서 | 모터로 흐르는 전류를 재서 과부하가 걸리면 줄이게 한다 | 고침(표현) | 모터로 흐르는 전류를 재서 너무 많이 흐르면 줄일 수 있게 한다 | (전류 제한은 설정에 따라 다름) |
| ESC · 파워 MOSFET | 배터리 전기를 1초에 수만 번 켰다 껐다 해 … 귀퉁이마다 모터 하나씩 | 고침 | … 모터마다 여러 개가 한 조 | https://oscarliang.com/best-blheli-32-settings/ (PWM 24~96kHz) |
| 배전 · 전류 센서 | 배터리에서 나가는 전류를 재서 남은 비행 시간을 계산하게 한다 | 고침(표현) | 배터리에서 나가는 전류를 재서, 쓴 전기량으로 남은 배터리를 추정하게 한다 | (일반 구성) |
| 배전 · 5V 스위칭 레귤레이터 | 11V 배터리 전압을 카메라·컴퓨터가 쓰는 5V 로 효율 좋게 낮춘다 | 고침(표현) | 배터리 전압(예: 약 11V)을 … | (셀 수는 예시) |
| 배전 · 배터리 입력 단자 / 역전압 보호 MOSFET / 3.3V 레귤레이터 / 전해 커패시터 | — | 맞음 | — | (일반 구성) |

## 작동 단계 (SCEN.quad) — 수정안은 `quad-scen.json`

| 단계 | 원래 문구 | 판정 | 고친 문구 | 근거(URL) |
|---|---|---|---|---|
| 1 | 배터리 셀 3개(약 11V)의 전기가 배전 기판으로 들어가 … | 고침(표현) | 배터리 셀(예: 3개, 약 11V)의 전기가 … | https://www.batteryuniversity.com/article/bu-303-confusion-with-voltages/ |
| 2 | 비행 컨트롤러가 IMU·기압계를 1초에 수천 번 읽어 기울기와 높이를 잰다 | 고침 | 비행 컨트롤러가 IMU 로 기울기·회전을 1초에 수백~수천 번, 기압계로 높이를 재서 자세를 계산한다 | https://oscarliang.com/best-looptime-flight-controller/ |
| 3 | 명령을 받은 4-in-1 ESC 가 모터 코일에 전류를 번갈아 흘려 모터 네 개를 돌린다 | 맞음 | — | https://blog.skyrc.com/how-brushless-motors-work/ |
| 4 | GPS·나침반 모듈이 위치와 방향을, 항법 카메라 쌍이 장애물까지 거리를 재서 자율비행 컴퓨터로 보낸다 | 고침 | GPS·나침반 모듈은 위치와 방향을 비행 컨트롤러로, 항법 카메라는 장애물까지 거리를 자율비행 컴퓨터로 보낸다. 흐름 선도 GPS → 비행 컨트롤러로 바꾸길 권함 | https://ardupilot.org/dev/docs/companion-computers.html |
| 5 | 자율비행 컴퓨터가 주변을 3D 로 그려 안전한 경로를 짜고, 비행 컨트롤러에 갈 방향을 준다 | 맞음 | — | https://developer.nvidia.com/blog/skydio-2-jetson-tx2-drone/ · https://ardupilot.org/dev/docs/mavlink-commands.html |
| 6 | 짐벌이 흔들림을 상쇄해 카메라를 수평으로 붙잡고, 렌즈군·이미지 센서·열상 코어가 영상을 만든다 | 맞음 | — | — |
| 7 | 영상은 데이터링크 무전 모듈의 안테나 두 개로 조종기에 실시간으로 전송된다 | 고침 | 영상은 데이터링크 무전 모듈을 통해 조종기로 실시간 전송된다 — 군용은 보통 암호화한다 | (안테나 개수 확인 불가) |

## 영상에서 말하면 안 되는 것

- "Skydio X2(D) 안에 이게 들어 있다" — 스크립트 주석의 "Skydio X2 급"은 크기 기준일 뿐이다. 부품 배치·칩·보드 구성은 실제 제품과 다르다.
- "이 드론은 STM32 / NVIDIA Jetson 을 쓴다" — 둘 다 **예시**다. 참고로 Skydio 2 는 Jetson TX2 를 썼다는 공개 자료가 있지만, 신형은 다른 칩을 쓴다.
- 배터리 3S·약 11V, 안테나 2개, 모터 4개당 MOSFET 수 같은 **구체 수치를 이 기체의 사양처럼** 말하는 것
- "암호화 칩이 가로채기를 막는다" 같은 단정 — 암호화는 **내용을 못 읽게** 할 뿐, 전파를 가로채는 것 자체를 막지는 못한다.
- "비행 컨트롤러가 모든 센서를 1초에 수천 번 읽는다" — 기압계는 훨씬 느리다.
- 모든 소형 드론에 자율비행 AI 컴퓨터가 있다는 식의 일반화 — 일부 고급 기체에만 있다.

## 제목 "정찰 쿼드콥터"

일반 명칭이라 써도 된다. 다만 화면이나 영상 자막에 "일반적인 구성 예시(특정 제품 아님)"를 함께 표시하길 권한다.
