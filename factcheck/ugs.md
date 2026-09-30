# 사실 확인 — 무인 지상 감시 센서(UGS)

대상: `products/ugs.py`의 부품 이름·설명·칩 이름표, `web/index.html`의 `SCEN.ugs` 작동 단계 (2026-09-30).

이 모델은 특정 제품이 아니라 **일반 UGS**예요. 그래서 판정 기준은 "UGS에서 일반적으로 맞는가"예요. 부품 배치·크기·셀 개수·칩 종류는 개념도로 만든 것이라 사실 확인 대상이 아니에요.

판정 결과는 맞음 25 · 고침 23 · 확인 불가 0이에요(부품 설명 15, 칩 28, 작동 단계 6). 확인이 안 된 것은 모두 일반적인 표현으로 고치거나 빼서 "고침"에 넣었어요.

## 부품 설명

| 항목 | 원래 문구 | 판정 | 고친 문구 | 근거 |
|---|---|---|---|---|
| 지면 말뚝 | 땅에 박아 센서를 세우고, 땅의 진동을 속의 지오폰까지 전해 준다 | 고침 | 땅에 박아 센서를 세우고, 땅에 단단히 붙어 진동이 지오폰까지 잘 전해지게 한다 | 스파이크로 지면과 밀착(커플링): [GB2450789A](https://patents.google.com/patent/GB2450789A/en), [SEG Geophone ground coupling](https://library.seg.org/doi/10.1190/1.1441700). UGS 스파이크 설치: [Exensor Mini Mk3](https://www.exensor.com/products/flexnet-flexible-network-of-sensors/unattended-ground-sensors-ugs/mini-mk3/) |
| 센서 본체 케이스 | 전자부품을 담는 방수 외함. 옆 커넥터로 외부 센서·충전 케이블을 잇는다 | 고침 | 전자부품을 물·먼지·충격에서 지키는 외함 | 외부 커넥터 구성은 제품마다 달라 일반화 불가 → 삭제 |
| 안테나 | 감지 결과를 전파로 내보낸다 — 이웃 센서·중계기·지휘소로 | 고침 | … — 이웃 센서나 기지국으로 | 메시 노드 → 기지국(base station): [Exensor Mini Mk3](https://www.exensor.com/products/flexnet-flexible-network-of-sensors/unattended-ground-sensors-ugs/mini-mk3/) |
| 태양전지 패널 | 햇빛으로 배터리를 채워, 몇 달씩 사람 손 없이 현장에 둘 수 있게 한다 | 고침 | 햇빛으로 충전식 배터리를 채워, 현장에 더 오래 둘 수 있게 한다 | 태양전지로 충전하는 UGS: [EP2664945A1](https://patents.google.com/patent/EP2664945A1/en). "몇 달"은 제품마다 달라 뺌 |
| 윗덮개 | 케이스를 물·먼지 없이 밀봉하고, 태양전지와 안테나를 받친다 | 맞음 | — | 이 모델 구조를 설명하는 문구(개념도) |
| 무선 통신 모듈(메시) | 옆 센서를 거쳐 징검다리처럼 신호를 넘겨, 멀리 있는 지휘소까지 알린다 | 고침 | 센서끼리 그물처럼 이어져, 옆 센서를 징검다리 삼아 멀리 있는 기지국까지 신호를 넘긴다 | "각 센서가 메시 노드로 다른 센서의 데이터를 기지국까지 중계": [Exensor Mini Mk3](https://www.exensor.com/products/flexnet-flexible-network-of-sensors/unattended-ground-sensors-ugs/mini-mk3/) |
| GPS 모듈 | 센서가 있는 위치와 정확한 시각을 알아내 감지 기록에 붙인다 | 고침 | 센서가 놓인 위치를 스스로 알아내, 어디서 감지됐는지 알 수 있게 한다 | GPS는 자기 위치 파악용: [Exensor Flexnet](https://www.exensor.com/products/flexnet-flexible-network-of-sensors/). 시각을 기록에 붙이는지는 확인 못함 |
| 태양광 충전 기판 | 태양전지의 들쭉날쭉한 전압을 배터리에 맞게 바꿔, 넘치지 않게 충전한다 | 맞음 | — | [AltE: 충전 컨트롤러](https://www.altestore.com/pages/how-does-a-solar-charge-controller-work) |
| 적외선(PIR) 감지기 | 사람 몸의 열이 움직이면 반응하는 초전 센서. 흰 렌즈가 넓은 범위의 열을 모아 준다 | 고침 (보강) | 사람 몸의 열(적외선)이 움직이면 … 흰 렌즈(프레넬 렌즈)가 넓은 범위의 적외선을 센서로 모아 준다 | [Adafruit: How PIRs work](https://learn.adafruit.com/pir-passive-infrared-proximity-motion-sensor/how-pirs-work), [Wikipedia: PIR](https://en.wikipedia.org/wiki/Passive_infrared_sensor) |
| 음향 마이크 | 엔진·발소리를 들어, 진동 신호와 함께 사람인지 차량인지 가려내는 데 쓴다 | 맞음 (문장만 다듬음) | 엔진·발소리를 듣는다. 진동 신호와 함께 분석해 사람인지 차량인지 가려내는 데 쓴다 | 지오폰 + 마이크로 사람·차량 분류: [Exensor Mini Mk3](https://www.exensor.com/products/flexnet-flexible-network-of-sensors/unattended-ground-sensors-ugs/mini-mk3/) |
| 메인 제어 보드 | … 사람·차량을 가려내고 기록한다. 평소엔 거의 잠들어 전기를 아낀다 | 고침 | … 평소엔 저전력 대기로 전기를 아낀다 | 저전력 감시 모드 → 신호가 오면 처리 시작: [US8019549 (Event-based power management for seismic sensors)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8019549), [ThinkDefence UGS](https://www.thinkdefence.co.uk/2024/11/unattended-ground-sensors-ugs/) |
| 배터리 팩 이름 | 배터리 팩(리튬 셀 4개) | 고침 | 배터리 팩(충전식 리튬) | "셀 4개"는 모델에서 정한 숫자일 뿐 근거 없음 |
| 배터리 팩 설명 | 전기를 저장한다. 보드가 대부분 잠들어 있어 한 번 충전으로 오래 버틴다 | 고침 | 전기를 저장한다. 저전력 설계 덕분에 한 번 충전으로 수 주, 제품에 따라 1년 가까이 버티기도 한다 | Mini Mk3: "충전식 배터리로 30일, 옵션으로 1년": [Exensor Mini Mk3](https://www.exensor.com/products/flexnet-flexible-network-of-sensors/unattended-ground-sensors-ugs/mini-mk3/) |
| 지진동 센서 케이스 | 속의 지오폰을 흙·물에서 지키고, 땅의 떨림이 잘 전해지도록 말뚝에 꽉 물린다 | 맞음 | — | 지면에 밀착해야 진동이 잘 전해짐: [SEG](https://library.seg.org/doi/10.1190/1.1441700) |
| 지오폰 | 스프링에 매달린 코일이 자석 옆에서 흔들리면 전기가 생긴다 — 발걸음·차량의 땅 떨림을 전기 신호로 바꾼다 | 맞음 | — | "스프링에 매단 코일 + 자석, 전압이 진동 속도에 비례": [Wikipedia: Geophone](https://en.wikipedia.org/wiki/Geophone), [ScienceDirect](https://www.sciencedirect.com/topics/engineering/geophone) |

## 칩 이름표

모든 칩은 "이런 장치에 흔히 쓰는 종류"를 보여 주는 예시예요. 실제 제품에 들어간 부품이 아니에요.

| 기판 | 칩 | 판정 | 고친 문구 / 메모 | 근거 |
|---|---|---|---|---|
| 무선 | RF 트랜시버(메시) | 고침 | 차폐캔 속 무선 칩. 감지 신호를 전파로 바꿔 보내고, 이웃 센서의 신호도 받아 대신 넘겨 준다(중계) | [Exensor](https://www.exensor.com/products/flexnet-flexible-network-of-sensors/unattended-ground-sensors-ugs/mini-mk3/) |
| 무선 | LDO 전원 레귤레이터 | 고침 | "3.3V" → "일정한 낮은 전압(보통 3.3V)" | 전압은 설계마다 다름 |
| 무선 | 크리스털 발진기 | 맞음 | — | 일반 전자 상식 |
| 무선 | 안테나 커넥터(U.FL) | 맞음 | — | U.FL은 소형 동축 커넥터 |
| GPS | GPS 수신 칩 | 맞음 | 위성 신호 도착 시간 비교 → 위치·시각 계산 | GNSS 기본 원리 |
| GPS | 저잡음 증폭기(LNA) | 맞음 | — | GNSS 수신기 기본 구성 |
| GPS | TCXO | 맞음 | 온도가 바뀌어도 주파수가 안정적 → 위성 신호를 빨리 잡음 | 일반 GNSS 설계 상식 |
| GPS | 세라믹 패치 안테나 | 맞음 | — | 일반 GNSS 모듈 구성 |
| 충전 | 전력 인덕터 | 맞음 | — | 스위칭 컨버터 기본 |
| 충전 | 충전 제어 IC(MPPT) | 고침 (정확히) | 태양전지가 가장 많은 전기를 내는 전압을 찾아 맞추고(MPPT), 배터리가 다 차면 충전을 멈춘다 | [AltE](https://www.altestore.com/pages/how-does-a-solar-charge-controller-work), [EcoFlow: MPPT](https://www.ecoflow.com/us/blog/what-is-an-mppt-solar-charge-controller) |
| 충전 | 역류 방지 MOSFET | 맞음 | 밤에 배터리 → 태양전지로 역류하는 것을 막음 | [AltE](https://www.altestore.com/pages/how-does-a-solar-charge-controller-work) |
| 충전 | 입력 커패시터 | 고침 | "구름이 지날 때 전압을 받쳐 준다"는 틀림(커패시터는 느린 변화를 못 막음) → "충전 회로가 켰다 껐다 할 때 생기는 전압 출렁임을 받쳐 준다" | 스위칭 컨버터 입력 커패시터 역할 |
| 충전 | 태양전지 입력 커넥터 | 맞음 | — | 모델 구조 |
| PIR | 초전 센서 증폭기 | 고침 | "수천 배" → "크게" (배율은 설계마다 다름) | — |
| PIR | 비교기(감지 판정) | 맞음 | — | 일반 PIR 회로 구성 |
| PIR | 초전(PIR) 센서 | 맞음 | 결정이 적외선 변화를 받으면 전압을 냄 | [Adafruit](https://learn.adafruit.com/pir-passive-infrared-proximity-motion-sensor/how-pirs-work) |
| 마이크 | MEMS 마이크 | 맞음 | — | 일반 MEMS 마이크 구조 |
| 마이크 | 마이크 증폭기 | 맞음 | — | — |
| 마이크 | 전원 필터 레귤레이터 | 고침 | "'웅' 소리" 삭제 → "소리 신호에 섞이지 않게" | 과장된 표현 정리 |
| 메인 | 저전력 MCU | 고침 | 평소엔 저전력 대기, 신호가 오면 깨어난다 + "(예: 저전력 ARM Cortex-M 계열 — 실제 제품 부품 아님)" | [US8019549](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8019549) |
| 메인 | 플래시 메모리 | 맞음 | — | — |
| 메인 | ADC(신호 변환기) | 맞음 | — | — |
| 메인 | 저잡음 증폭기(지오폰용) | 맞음 | — | 지오폰 출력은 약한 신호라 증폭이 필요 |
| 메인 | 크리스털 발진기 | 고침 | "감지 시각 기록의 기준" 삭제 (확인 못함) | — |
| 메인 | 전원 레귤레이터 | 고침 | "3.3V" → "일정한 전압(보통 3.3V)" | — |
| 메인 | 배터리 커넥터, 센서 커넥터 | 맞음 | — | 모델 구조 |

## 작동 보기 (SCEN.ugs)

`index.html`은 이 작업에서 고치지 않았어요. 고칠 문구는 `factcheck/ugs-scen.json`에 정리해 뒀어요.

| 단계 | 판정 | 요지 |
|---|---|---|
| 1 태양광 충전 | 맞음 | 부품 이름이 바뀌었으니 lit·flow 두 곳을 `배터리 팩(충전식 리튬)`으로 바꿔야 함 |
| 2 대기 | 고침 | "거의 잠든 채" → "저전력 대기 상태로" |
| 3 땅 떨림 → 지오폰 | 맞음 | — |
| 4 PIR·마이크 | 고침 | "오경보를 줄인다"(단정) → "여러 센서를 함께 쓰면 오경보를 줄일 수 있다". 근거: [ARL: 지진동 + PIR 센서](https://www.mobilityengineeringtech.com/component/content/article/14881-arl-0147) |
| 5 판별 + GPS | 고침 | "GPS가 위치·시각을 붙인다" → "GPS로 알아 둔 센서 위치를 함께 보낸다" |
| 6 메시 경보 | 고침 | "지휘소" → "기지국" |

## 영상에서 말하면 안 되는 것

- **특정 실제 제품의 내부라고 말하기.** 이 모델은 일반 UGS 개념도예요. 부품 배치·크기·셀 개수·칩 종류는 예시예요.
- **"몇 달씩 / 1년 동안 사람 손 없이 동작한다"고 단정하기.** 제품마다 달라요. 예를 들어 Exensor Mini Mk3는 충전식 배터리로 30일, 옵션 배터리로 1년이에요.
- **"센서 여러 개를 쓰니 오경보가 없다"고 말하기.** 줄이는 데 도움이 될 뿐이에요.
- **"GPS가 감지 시각을 기록한다", "지휘소로 바로 보낸다"처럼 구체적인 운용 방식.** 확인하지 못했어요. 자료상 표현은 "기지국까지 중계"예요.
- **칩 이름표의 예시 계열(ARM Cortex-M 등)을 실제 부품처럼 소개하기.**
- 전압 수치(3.3V)와 증폭 배율은 설계마다 달라요. "보통 이 정도"로만 말하세요.
