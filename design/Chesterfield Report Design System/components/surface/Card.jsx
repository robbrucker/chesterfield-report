import React from 'react';

const STYLE_ID = 'cr-card-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-card {
    position: relative; background: var(--surface-card);
    border: var(--bw-1) solid var(--ink-400); border-radius: var(--radius-card);
    transition: var(--transition-base); overflow: hidden;
  }
  .cr-card--pad { padding: var(--space-5); }
  .cr-card--grad::before {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background: var(--grad-panel); opacity: .8;
  }
  /* top accent bar */
  .cr-card--accent { border-top: var(--bw-3) solid var(--accent-color, var(--neon-teal)); }
  .cr-card--interactive { cursor: pointer; }
  .cr-card--interactive:hover {
    border-color: var(--accent-color, var(--neon-teal));
    box-shadow: var(--shadow-lg), 0 0 22px rgba(34,245,212,.12);
    transform: translateY(-2px);
  }
  .cr-card--interactive:active { transform: translateY(0); }
  .cr-card > * { position: relative; }
  /* corner bracket flourish */
  .cr-card--bracket::after {
    content: ""; position: absolute; top: 8px; right: 8px; width: 12px; height: 12px;
    border-top: 1px solid var(--neon-teal); border-right: 1px solid var(--neon-teal);
    opacity: .5; pointer-events: none;
  }
  `;
  document.head.appendChild(el);
}

const TONE_COLOR = {
  teal: 'var(--neon-teal)',
  breaking: 'var(--neon-magenta)',
  civic: 'var(--neon-amber)',
  eco: 'var(--river-green)',
};

/**
 * Card — base surface panel. Compose article cards, digests and HUD panels.
 */
export function Card({
  children,
  pad = true,
  accent = false,
  tone = 'teal',
  interactive = false,
  grad = false,
  bracket = false,
  className = '',
  style = {},
  ...rest
}) {
  const cls = [
    'cr-card',
    pad ? 'cr-card--pad' : '',
    accent ? 'cr-card--accent' : '',
    interactive ? 'cr-card--interactive' : '',
    grad ? 'cr-card--grad' : '',
    bracket ? 'cr-card--bracket' : '',
    className,
  ].filter(Boolean).join(' ');
  return (
    <div className={cls} style={{ '--accent-color': TONE_COLOR[tone] || TONE_COLOR.teal, ...style }} {...rest}>
      {children}
    </div>
  );
}
