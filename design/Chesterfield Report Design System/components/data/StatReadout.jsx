import React from 'react';

const STYLE_ID = 'cr-statreadout-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-stat {
    display: flex; flex-direction: column; gap: 4px; padding: 14px 16px;
    background: var(--surface-card); border: var(--bw-1) solid var(--ink-400);
    border-radius: var(--radius-sm); position: relative; overflow: hidden; min-width: 120px;
  }
  .cr-stat::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 2px; background: var(--stat-accent, var(--neon-teal)); box-shadow: 0 0 10px var(--stat-accent, var(--neon-teal)); }
  .cr-stat__label { font: var(--fw-bold) var(--fs-3xs)/1 var(--font-mono); letter-spacing: var(--ls-wider); text-transform: uppercase; color: var(--text-muted); }
  .cr-stat__value { font: var(--fw-bold) var(--fs-2xl)/1 var(--font-mono); color: var(--stat-accent, var(--neon-teal)); font-variant-numeric: tabular-nums; text-shadow: 0 0 14px var(--stat-glow, var(--glow-teal)); }
  .cr-stat__delta { font-family: var(--font-mono); font-size: var(--fs-3xs); color: var(--text-faint); display: flex; align-items: center; gap: 4px; }
  .cr-stat__delta--up { color: var(--neon-lime); }
  .cr-stat__delta--down { color: var(--neon-magenta); }
  `;
  document.head.appendChild(el);
}

const STAT = {
  teal: ['var(--neon-teal)', 'var(--glow-teal)'],
  magenta: ['var(--neon-magenta)', 'var(--glow-magenta)'],
  amber: ['var(--neon-amber)', 'var(--glow-amber)'],
  lime: ['var(--neon-lime)', 'rgba(141,255,94,.4)'],
};

/**
 * StatReadout — mono HUD data block (label, big value, optional delta).
 */
export function StatReadout({ label, value, delta, trend, tone = 'teal', className = '', ...rest }) {
  const [c, g] = STAT[tone] || STAT.teal;
  return (
    <div className={['cr-stat', className].filter(Boolean).join(' ')}
      style={{ '--stat-accent': c, '--stat-glow': g }} {...rest}>
      <span className="cr-stat__label">{label}</span>
      <span className="cr-stat__value">{value}</span>
      {delta != null ? (
        <span className={['cr-stat__delta', trend === 'up' ? 'cr-stat__delta--up' : trend === 'down' ? 'cr-stat__delta--down' : ''].filter(Boolean).join(' ')}>
          {trend === 'up' ? '▲' : trend === 'down' ? '▼' : '·'} {delta}
        </span>
      ) : null}
    </div>
  );
}
