/* webshot.mjs — 분해 뷰어(web/index.html) 검수 캡처. 헤드리스 크롬에 CDP 로 붙는다.

     node tools/webshot.mjs                 → 6개 제품 × 분해 0 / 0.5 / 1 (마우스 모드) → out/web/
     node tools/webshot.mjs quad nvg        → 고른 제품만
     FAKECAM=1 node tools/webshot.mjs sb300 → 가짜 카메라로 실제 시작 경로(카메라 열기·손 모델 로딩)까지
     HANDS=1 …                              → 가짜 손 좌표로 판정 확인 (펼침·가리키기·양손 확대)
     FOCUS="quad:배터리" …                   → 부품 보기 화면 (FOCUS_F=0 이면 조립 상태에서)
     SIM="k2c1" …                            → 작동 보기 단계별 화면 (SIM_AT=ms 단계 시작 후 찍는 시점)
     FOCUS_ZOOM=2.5 …                       → 부품 보기에서 그만큼 더 확대 (칩 이름표 확인용)
     SIZE=1280x720 …                        → 크기 (기본 1600x900)

   손 인식 결과 자체는 가짜 카메라(초록 패턴)로는 못 본다 — 배선만 확인된다.
*/
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'out', 'web');
const PORT = Number(process.env.PORT || 9433);   // 여러 개를 동시에 돌릴 때는 PORT 를 다르게
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PAGE = pathToFileURL(join(ROOT, 'web', 'index.html')).href;
const [W, H] = (process.env.SIZE || '1600x900').split('x').map(Number);
const FAKECAM = !!process.env.FAKECAM;
const ALL = ['sb300', 'quad', 'nvg', 'ugs', 'k2c1'];
const targets = process.argv.slice(2).length ? process.argv.slice(2) : ALL;
const sleep = ms => new Promise(r => setTimeout(r, ms));
mkdirSync(OUT, { recursive: true });

const chrome = spawn(CHROME, [
  '--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=/tmp/explode-web-${process.pid}`,
  `--window-size=${W},${H}`, '--hide-scrollbars', '--no-first-run', '--force-device-scale-factor=1',
  '--allow-file-access-from-files', '--enable-unsafe-swiftshader',
  ...(FAKECAM ? ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] : []),
  'about:blank',
], { stdio: 'ignore' });

let sock, msgId = 0;
const waiters = new Map();
const send = (method, params = {}) => {
  const id = ++msgId;
  sock.send(JSON.stringify({ id, method, params }));
  return new Promise(res => waiters.set(id, res));
};
const evaluate = async (expression) => {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};

async function connect() {
  for (let i = 0; i < 60; i++) {
    try {
      const page = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find(t => t.type === 'page');
      if (page) {
        sock = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((res, rej) => { sock.onopen = res; sock.onerror = rej; });
        sock.onmessage = e => {
          const m = JSON.parse(e.data);
          if (m.id && waiters.has(m.id)) { waiters.get(m.id)(m.result ?? m); waiters.delete(m.id); }
          if (m.method === 'Runtime.exceptionThrown') console.error('페이지 오류:', m.params.exceptionDetails.exception?.description);
          if (m.method === 'Runtime.consoleAPICalled' && ['error', 'warning'].includes(m.params.type))
            console.error(`콘솔 ${m.params.type}:`, m.params.args.map(a => a.description || a.value).join(' '));
        };
        return;
      }
    } catch {}
    await sleep(250);
  }
  throw new Error('크롬에 붙지 못했습니다');
}

let shots = 0;
try {
  await connect();
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  const q = FAKECAM ? '?test' : '?test&nocam';
  await send('Page.navigate', { url: `${PAGE}${q}&p=${targets[0]}` });
  for (let i = 0; i < 80 && !(await evaluate('!!(window.APP && APP.ready)').catch(() => false)); i++) await sleep(250);
  console.log('webgl:', await evaluate(`(() => { const g = document.getElementById('gl').getContext('webgl2');
    const d = g && g.getExtension('WEBGL_debug_renderer_info'); return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'n/a'; })()`));

  if (FAKECAM) {
    await sleep(Number(process.env.LOAD || 12000));
    console.log('상태:', await evaluate(`JSON.stringify({ status: document.getElementById('status').textContent,
      video: [video.videoWidth, video.videoHeight], camOff: document.getElementById('cam').classList.contains('off') })`));
  }

  if (process.env.HANDS) {
    // 가짜 손 좌표를 실제 판정 함수(APP.feed)에 넣어 본다. 시각은 가짜로 33ms(30fps)씩 흐르게 한다.
    // hand(cx, cy, r, ix, mid): r = 네 손가락 펼침비, ix = 검지만, mid = 중지·약지·새끼만 (없으면 r)
    const out = await evaluate(`(() => {
      const hand = (cx, cy, r, ix = r, mid = r) => {
        const L = Array.from({ length: 21 }, () => ({ x: cx, y: cy + 0.12 }));
        L[0] = { x: cx, y: cy + 0.12 }; L[5] = { x: cx - 0.05, y: cy }; L[9] = { x: cx, y: cy };
        L[17] = { x: cx + 0.05, y: cy + 0.01 };
        [[8, -0.04], [12, 0], [16, 0.03], [20, 0.06]].forEach(([i, dx]) =>
          (L[i] = { x: cx + dx, y: cy + 0.12 - (i === 8 ? ix : mid) * 0.12 }));
        return L;
      };
      let t = 1e6;
      const S = APP.state, V = APP.view, out = [];
      const feed = (L, n = 1) => { for (let i = 0; i < n; i++) APP.feed(L, undefined, t += 33); };
      const st = () => 'f=' + S.fTarget.toFixed(2) + ' yaw=' + S.yawT.toFixed(2) + ' pitch=' + S.pitchT.toFixed(2)
        + ' 확대=' + (1 / V.userT).toFixed(2) + ' 커서=' + (APP.pointer.on ? '켜짐' : '꺼짐') + ' 라벨=' + APP.labelOpacity().toFixed(2);
      APP.set(0, 0, 0);
      feed([hand(0.5, 0.5, 2.0)], 30);            out.push('한 손 활짝 1초 → ' + st());
      feed([hand(0.5, 0.5, 0.95)], 30);           out.push('주먹 1초 → ' + st());
      feed([hand(0.5, 0.5, 1.5)], 30);            out.push('반쯤 1초 → ' + st());
      feed([hand(0.5, 0.5, 2.0)], 30); feed([hand(0.5, 0.5, 1.4)], 30);
      out.push('활짝 뒤 반쯤 오므림 → ' + st() + ' (f 1 유지)');
      feed([hand(0.5, 0.5, 0.95)], 10);           out.push('주먹 0.33초 → ' + st() + ' (f 1 유지)');
      feed([hand(0.5, 0.5, 2.0)], 30);
      feed([hand(0.5, 0.5, 0.95)], 30);           out.push('주먹 1초 → ' + st() + ' (f 0)');
      feed([hand(0.5, 0.5, 2.0)], 6); feed([hand(0.5, 0.5, 0.95)], 5);
      out.push('주먹에서 0.2초만 폈다 다시 쥠 → ' + st() + ' (f 0 이어야 — 실수로 편 건 무시)');
      feed([hand(0.5, 0.5, 1.5)], 30);            out.push('다시 반쯤 → ' + st());
      feed([hand(0.5, 0.5, 2.0)], 30);
      for (let i = 1; i <= 10; i++) feed([hand(0.5 + 0.025 * i, 0.5, 2.0)]);   // 카메라 기준 오른쪽 = 사용자 왼쪽(거울)
      feed([hand(0.75, 0.5, 2.0)], 20);           out.push('펼친 채 화면 폭 1/4 이동 → ' + st() + ' (yaw 기대 -0.65)');
      for (let i = 1; i <= 10; i++) feed([hand(0.75, 0.5 - 0.01 * i, 2.0)]);
      feed([hand(0.75, 0.4, 2.0)], 20);           out.push('위로 높이 1/10 → ' + st() + ' (pitch 기대 -0.18)');
      // 손바닥 → 검지: 중지·약지·새끼가 2.0 → 1.6 → 1.45 → 1.0 으로 접힌다 (검지는 그대로)
      const y0 = S.yawT;
      feed([hand(0.75, 0.4, 2.0, 2.0, 1.6)], 2); feed([hand(0.75, 0.4, 2.0, 2.0, 1.45)], 2);
      feed([hand(0.75, 0.4, 1.0, 1.2, 1.0)], 3);     // 접는 중 0.1초 동안 검지까지 굽어 진짜 주먹처럼 보임
      feed([hand(0.75, 0.4, 2.0, 2.0, 1.0)], 20); out.push('손바닥 → 검지 전환 → ' + st() + ' (f 1 유지, 라벨 1 — 중간에 0.1초 주먹처럼 보여도)');
      feed([hand(0.75, 0.4, 2.0)], 30);           out.push('다시 손바닥 → ' + st());
      // 양손 확대 후 한 손만 남기기 (남은 손은 다른 자리)
      feed([hand(0.35, 0.5, 1.8), hand(0.65, 0.5, 1.8)], 12);
      for (let i = 1; i <= 10; i++) feed([hand(0.35 - 0.015 * i, 0.5, 1.8), hand(0.65 + 0.015 * i, 0.5, 1.8)]);
      feed([hand(0.2, 0.5, 1.8), hand(0.8, 0.5, 1.8)], 10); out.push('양손 0.3 → 0.6 벌림 → ' + st() + ' (확대 기대 ' + (2 ** 0.8).toFixed(2) + ')');
      const yb = S.yawT, pb = S.pitchT;
      feed([hand(0.2, 0.65, 1.8)], 30);           out.push('한 손만 남김(다른 자리) → yaw 변화 ' + (S.yawT - yb).toFixed(2) + ', pitch 변화 ' + (S.pitchT - pb).toFixed(2) + ' (0 이면 안 튐)');
      // 손을 0.2초 놓쳤다가 다시: 기준을 새로 잡지 않고 바로 이어 돈다
      feed([hand(0.4, 0.5, 2.0)], 20); const y1 = S.yawT;
      for (let i = 0; i < 6; i++) APP.noHands(t += 33);
      feed([hand(0.5, 0.5, 2.0)], 3);            out.push('손 0.2초 놓친 뒤 오른쪽으로 0.1 → yaw 변화 ' + (S.yawT - y1).toFixed(2) + ' (0 이 아니어야 — 바로 반응)');
      // 손이 오래(1초) 사라졌다 들어오면: 0.12초만 기다리고 반응
      for (let i = 0; i < 30; i++) APP.noHands(t += 33);
      feed([hand(0.5, 0.5, 2.0)], 5); const y2 = S.yawT;
      feed([hand(0.6, 0.5, 2.0)], 3);            out.push('손 새로 들어와 0.17초 뒤 움직임 → yaw 변화 ' + (S.yawT - y2).toFixed(2) + ' (0 이 아니어야)');
      // 주먹 흔들기: 좌우 ±0.06 을 0.2초마다 → 작동 보기 켜짐, 조립(주먹 0.5초)은 안 됨
      APP.set(1, 0, 0);
      feed([hand(0.5, 0.5, 2.0)], 15);
      const fistAt = (x, n) => feed([hand(x, 0.5, 0.95)], n);
      fistAt(0.5, 5); const yawBefore = S.yawT;
      for (let k = 0; k < 4; k++) { fistAt(0.56, 3); fistAt(0.44, 3); }
      out.push('주먹 좌우로 흔들기 → 작동 보기 ' + (APP.sim.on ? '켜짐' : '꺼짐') + ' (켜짐), 회전 변화 ' + (S.yawT - yawBefore).toFixed(2) + ' (0)');
      fistAt(0.5, 50);
      for (let k = 0; k < 4; k++) { fistAt(0.56, 3); fistAt(0.44, 3); }
      out.push('작동 보기 중 다시 흔들기 → ' + (APP.sim.on ? '켜짐' : '꺼짐') + ' (꺼짐), 분해 f=' + S.fTarget.toFixed(2) + ' (켜기 전 1 로 복귀)');
      APP.set(1, 0, 0); feed([hand(0.5, 0.5, 2.0)], 15);
      fistAt(0.5, 30);                              out.push('주먹 가만히 1초 → f=' + S.fTarget.toFixed(2) + ', 작동 보기 ' + (APP.sim.on ? '켜짐' : '꺼짐') + ' (f 0, 꺼짐)');
      fistAt(0.5, 3); fistAt(0.52, 3); fistAt(0.5, 3);   out.push('주먹 살짝 떨림 → 작동 보기 ' + (APP.sim.on ? '켜짐' : '꺼짐') + ' (꺼짐이어야)');
      if (APP.sim.on) APP.simStop();
      APP.pointer.on = false; V.userT = 1; APP.set(1, 0, 0);
      return out.join(' | ');
    })()`);
    console.log(out.split(' | ').join('\n'));
  }

  if (process.env.FOCUS) {
    // 부품 보기: FOCUS="quad:배터리,nvg:이미지 증폭관" → out/web/<code>-focus-<n>.png
    for (const [i, item] of process.env.FOCUS.split(',').entries()) {
      const [code, label] = item.split(':');
      await evaluate(`APP.show('${code}')`);
      await evaluate(`APP.set(${process.env.FOCUS_F ?? 1}, 0, 0)`);
      await evaluate(`APP.focusLabel(${JSON.stringify(label)})`);
      if (process.env.FOCUS_ZOOM) await evaluate(`APP.view.userT = APP.view.user = 1 / ${Number(process.env.FOCUS_ZOOM)}`);
      await sleep(500);
      const { data } = await send('Page.captureScreenshot', { format: 'png' });
      const file = join(OUT, `${code}-focus-${i}.png`);
      writeFileSync(file, Buffer.from(data, 'base64'));
      console.log(`  ${code} 부품 보기 "${label}" → ${file}`);
      await evaluate('APP.unfocus(); APP.view.userT = APP.view.user = 1');
    }
  }

  if (process.env.SIM) {
    // 작동 보기: SIM="k2c1,nvg" → 단계마다 SIM_AT(ms, 기본 1500) 지난 화면 → out/web/<code>-sim-<n>.png
    for (const code of process.env.SIM.split(',')) {
      await evaluate(`APP.show('${code}')`);
      await evaluate('APP.set(0, 0.35, 0.12)');
      await evaluate('APP.simStart()');
      const n = await evaluate(`APP.SCEN['${code}'].steps.length`);
      for (let i = 0; i < n; i++) {
        await evaluate(`APP.simGo(${i})`);
        await sleep(Number(process.env.SIM_AT || 1500));
        const { data } = await send('Page.captureScreenshot', { format: 'png' });
        const file = join(OUT, `${code}-sim-${i + 1}.png`);
        writeFileSync(file, Buffer.from(data, 'base64'));
        console.log(`  ${code} 작동 ${i + 1}/${n} → ${file}`);
      }
      await evaluate('APP.simStop(); APP.set(0, 0, 0)');
    }
  }

  for (const code of targets) {
    await evaluate(`APP.show('${code}')`);
    for (const f of [0, 0.5, 1]) {
      await evaluate(`APP.set(${f}, 0, 0)`);
      await sleep(350);
      const counts = await evaluate(`JSON.stringify({ parts: APP.products['${code}'].parts.length,
        tags: [...document.querySelectorAll('.tag')].length })`);
      const { data } = await send('Page.captureScreenshot', { format: 'png' });
      const file = join(OUT, `${code}-f${Math.round(f * 100)}.png`);
      writeFileSync(file, Buffer.from(data, 'base64'));
      shots++;
      console.log(`  ${code} f=${f} ${counts} → ${file}`);
    }
  }
} finally {
  sock?.close();
  chrome.kill();
  console.log(`찍은 장수: ${shots} / 예정 ${targets.length * 3}`);
}
