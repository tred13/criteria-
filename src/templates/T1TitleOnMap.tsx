import React from 'react';
import {AbsoluteFill, Img, cancelRender, continueRender, delayRender, interpolate, staticFile, useCurrentFrame} from 'remotion';

/**
 * T1 — عنوان نصّي متحرك فوق خريطة قمرية.
 * 720x1280 @ 30fps، 68 إطارًا (0-67). كل أرقام الحركة مأخوذة من قياس الفيديو المرجعي
 * (انظر TEMPLATE-T1.md)؛ لا يُنسخ منه أي نص أو صورة.
 */
export type T1Props = {
  titleWord: string; // الجزء الأبيض من العنوان
  titleNumeral: string; // الجزء الأصفر (رقم أو كلمة قصيرة)
  subtitles: {text: string; from: number; to: number}[]; // العبارات ونطاقها بالإطارات
  background: string; // مسار داخل public/
};

export const t1Defaults: T1Props = {
  titleWord: 'MARCH',
  titleNumeral: '14',
  subtitles: [
    {text: 'Temporary sample line one', from: 3, to: 30},
    {text: 'second line shows the timing', from: 32, to: 54},
    {text: 'text is not final content', from: 56, to: 68},
  ],
  background: 'assets/bg_map_placeholder.jpg',
};

const W = 720;
const H = 1280;

// ---------- أدوات ----------
const lin = (f: number, xs: number[], ys: number[]) =>
  interpolate(f, xs, ys, {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
const logLin = (f: number, xs: number[], ys: number[]) => Math.exp(lin(f, xs, ys.map((v) => Math.log(v))));

// ---------- مفاتيح الحركة المقيسة ----------
// مركز العنوان (نسبة من العرض/الارتفاع) — من صندوق العنوان المقيس في كل إطارين
const CX_F = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 58, 67];
const CX_V = [-7.95, 0.45, 12.65, 22.05, 27.15, 31.15, 34.45, 38.05, 40.75, 43.35, 45.25, 46.95, 48.25, 49.05, 49.75, 50.15, 50.75, 51.25, 51.85, 52.35, 52.95, 53.5, 54.2, 54.95, 55.6, 56.0, 56.0, 55.5, 55.5, 55.5];
const CY_F = [0, 4, 12, 16, 22, 26, 67];
const CY_V = [49.1, 49.9, 50.0, 50.3, 50.6, 50.65, 50.65];
// التكبير (1.0 ثم تكبير تدريجي من الإطار 40، وبعد 54 من ارتفاع الصندوق)
const SC_F = [0, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 67];
const SC_V = [1, 1, 1.006, 1.014, 1.035, 1.073, 1.138, 1.242, 1.331, 1.38, 1.52, 1.7, 2.1, 3.2, 4.1, 4.6, 4.9];
// ميل العنوان (درجات، موجب = هبوط نحو اليمين)
const ROT_F = [0, 12, 28, 36, 44, 67];
const ROT_V = [6.0, 6.0, 5.36, 4.4, 3.6, 3.6];
// تمويه (بكسل): دخول من اليسار ثم خروج بالتكبير — تقريبي (لم يُقس نصف القطر)
const BL_F = [0, 4, 8, 12, 16, 46, 48, 52, 56, 60, 64, 67];
const BL_V = [12, 9, 5, 2, 0, 0, 1, 3, 7, 13, 22, 28];
// الخريطة الخلفية: تحويل تشابهي نسبةً للإطار 5 (مقيس بـORB حتى 52، وما بعده تقدير مُخفَّف)
const BG_F = [0, 5, 15, 25, 35, 45, 52, 67];
const BG_S = [1, 1, 0.9452, 0.9508, 0.9533, 0.973, 0.9933, 1.015];
const BG_R = [0, 0, -2.14, -2.87, -4.87, -5.95, -6.99, -8.0];
const BG_TX = [0, 0, 46.2, 40.2, 22.5, 1.1, -10.3, -20];
const BG_TY = [0, 0, 50.5, 60.1, 74.8, 71.4, 44.1, 5];
const BG_OX = 490; // تموضع الصورة الأكبر (1700x2400) بحيث تغطي الإطار بهامش
const BG_OY = 560;

// ---------- الخطوط (محلية، بلا CDN) ----------
const useFonts = () => {
  const [handle] = React.useState(() => delayRender('t1-fonts'));
  React.useEffect(() => {
    const faces = [
      new FontFace('T1Serif', `url(${staticFile('fonts/playfair-display-latin-800-normal.woff2')})`, {weight: '800'}),
      new FontFace('T1Sans', `url(${staticFile('fonts/roboto-latin-700-normal.woff2')})`, {weight: '700'}),
    ];
    Promise.all(faces.map((f) => f.load()))
      .then((loaded) => {
        loaded.forEach((f) => (document.fonts as unknown as {add: (face: FontFace) => void}).add(f));
        continueRender(handle);
      })
      .catch((e) => cancelRender(e));
  }, [handle]);
};

export const T1TitleOnMap: React.FC<T1Props> = ({titleWord, titleNumeral, subtitles, background}) => {
  useFonts();
  const frame = useCurrentFrame();

  // الخلفية
  const s = lin(frame, BG_F, BG_S);
  const th = (lin(frame, BG_F, BG_R) * Math.PI) / 180;
  const tx = lin(frame, BG_F, BG_TX);
  const ty = lin(frame, BG_F, BG_TY);
  const bgMatrix = `matrix(${s * Math.cos(th)}, ${s * Math.sin(th)}, ${-s * Math.sin(th)}, ${s * Math.cos(th)}, ${tx}, ${ty})`;

  // العنوان
  const cx = (lin(frame, CX_F, CX_V) / 100) * W;
  const cy = (lin(frame, CY_F, CY_V) / 100) * H;
  const sc = logLin(frame, SC_F, SC_V);
  const rot = lin(frame, ROT_F, ROT_V);
  const blur = lin(frame, BL_F, BL_V);

  return (
    <AbsoluteFill style={{backgroundColor: '#093D4F', overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: W, height: H, transformOrigin: '0 0', transform: bgMatrix}}>
        <Img src={staticFile(background)} style={{position: 'absolute', left: -BG_OX, top: -BG_OY, width: 1700, height: 2400}} />
      </div>

      <div
        style={{
          position: 'absolute',
          left: cx,
          top: cy,
          transform: `translate(-50%, -50%) rotate(${rot}deg) scale(${sc})`,
          filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
          whiteSpace: 'nowrap',
          fontFamily: 'T1Serif, Georgia, serif',
          fontWeight: 800,
          fontSize: 71.5,
          lineHeight: 1,
          letterSpacing: 0,
          color: '#FDFDFD',
          textShadow: '3px 5px 8px rgba(0,0,0,0.55)',
        }}
      >
        {titleWord} <span style={{color: '#F9F722'}}>{titleNumeral}</span>
      </div>

      {subtitles.map((sub, i) => {
        const o = interpolate(frame, [sub.from, sub.from + 2, sub.to - 2, sub.to], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        return o > 0 ? (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 0,
              width: W,
              top: 0.713 * H - 15,
              height: 30,
              lineHeight: '30px',
              textAlign: 'center',
              fontFamily: 'T1Sans, Arial, sans-serif',
              fontWeight: 700,
              fontSize: 33,
              color: '#FAFFFF',
              opacity: o,
              textShadow: '0 2px 4px rgba(0,0,0,0.45)',
              whiteSpace: 'nowrap',
            }}
          >
            {sub.text}
          </div>
        ) : null;
      })}
    </AbsoluteFill>
  );
};
