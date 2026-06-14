import React from 'react';

const STYLE_ID = 'cr-tabs-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-tabs { display: flex; gap: 2px; border-bottom: var(--bw-1) solid var(--ink-400); }
  .cr-tab {
    appearance: none; background: none; border: none; cursor: pointer;
    font-family: var(--font-display); font-weight: var(--fw-semibold); font-size: var(--fs-sm);
    letter-spacing: var(--ls-wide); color: var(--text-muted); padding: 12px 16px;
    position: relative; transition: var(--transition-base); white-space: nowrap;
  }
  .cr-tab::after {
    content: ""; position: absolute; left: 12px; right: 12px; bottom: -1px; height: 2px;
    background: var(--neon-teal); transform: scaleX(0); transform-origin: left;
    transition: transform var(--dur-base) var(--ease-out); box-shadow: 0 0 10px var(--glow-teal);
  }
  .cr-tab:hover { color: var(--text-strong); }
  .cr-tab[aria-selected="true"] { color: var(--neon-teal); }
  .cr-tab[aria-selected="true"]::after { transform: scaleX(1); }
  .cr-tab:focus-visible { outline: none; box-shadow: var(--ring); border-radius: var(--radius-xs); }
  .cr-tab__count { font-family: var(--font-mono); font-size: var(--fs-3xs); margin-left: 6px; opacity: .7; }
  `;
  document.head.appendChild(el);
}

/**
 * Tabs — section navigation with an animated neon underline.
 */
export function Tabs({ items = [], value, onChange, className = '', ...rest }) {
  const active = value != null ? value : (items[0] && (items[0].value ?? items[0]));
  return (
    <div className={['cr-tabs', className].filter(Boolean).join(' ')} role="tablist" {...rest}>
      {items.map((it) => {
        const val = typeof it === 'string' ? it : it.value;
        const lbl = typeof it === 'string' ? it : it.label;
        const count = typeof it === 'object' ? it.count : undefined;
        return (
          <button key={val} role="tab" type="button"
            aria-selected={val === active}
            className="cr-tab"
            onClick={() => onChange && onChange(val)}>
            {lbl}
            {count != null ? <span className="cr-tab__count">{count}</span> : null}
          </button>
        );
      })}
    </div>
  );
}
