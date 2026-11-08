import { staticFile, continueRender, delayRender } from 'remotion';
import { useEffect, useState } from 'react';
const faces: [string, string, number | string][] = [
  ['Anton', 'Anton-Regular.ttf', 400], ['Inter', 'Inter-Regular.otf', 400], ['Inter', 'Inter-Medium.otf', 500], ['Inter', 'Inter-SemiBold.otf', 600],
  ['JBMono', 'JBMono-400.ttf', 400], ['JBMono', 'JBMono-700.ttf', 700], ['VT323', 'VT323-Regular.ttf', 400], ['Caveat', 'Caveat-Medium.ttf', 500],
  ['Cormorant', 'CormorantGaramond-Bold.ttf', 700], ['SairaStencil', 'SairaStencilOne-Regular.ttf', 400], ['PermanentMarker', 'PermanentMarker-Regular.ttf', 400],
];
let loaded = false;
export const useFonts = () => {
  const [h] = useState(() => (loaded ? null : delayRender('fonts')));
  useEffect(() => {
    if (loaded || h === null) return;
    Promise.all(faces.map(([fam, file, w]) => { const ff = new FontFace(fam, `url(${staticFile('fonts/' + file)})`, { weight: String(w) }); return ff.load().then((x) => document.fonts.add(x)); }))
      .then(() => { loaded = true; continueRender(h); }).catch(() => { loaded = true; continueRender(h); });
  }, []);
};
