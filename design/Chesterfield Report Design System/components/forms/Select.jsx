import React from 'react';

const STYLE_ID = 'cr-select-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-select-wrap { position: relative; display: flex; flex-direction: column; gap: 6px; }
  .cr-select-wrap__inner { position: relative; display: flex; align-items: center; }
  .cr-select {
    appearance: none; width: 100%; font: var(--text-body-r); font-size: var(--fs-sm);
    color: var(--text-strong); background: var(--surface-raised);
    border: var(--bw-1) solid var(--ink-400); border-radius: var(--radius-sm);
    padding: 11px 36px 11px 13px; cursor: pointer; transition: var(--transition-base);
  }
  .cr-select:hover { border-color: var(--ink-300); }
  .cr-select:focus { outline: none; border-color: var(--neon-teal); box-shadow: var(--glow-sm-teal); }
  .cr-select:disabled { opacity: .5; cursor: not-allowed; }
  .cr-select-wrap__chevron { position: absolute; right: 12px; pointer-events: none; color: var(--neon-teal); display: flex; }
  .cr-select-wrap__chevron svg { width: 14px; height: 14px; }
  .cr-select option { background: var(--ink-700); color: var(--text-strong); }
  `;
  document.head.appendChild(el);
}

/**
 * Select — native dropdown styled for the dark HUD surface.
 */
export function Select({
  label,
  options = [],
  id,
  className = '',
  children,
  ...rest
}) {
  const fieldId = id || (label ? 'cr-sel-' + label.toLowerCase().replace(/\s+/g, '-') : undefined);
  return (
    <div className="cr-select-wrap">
      {label ? <label className="cr-field__label" htmlFor={fieldId}>{label}</label> : null}
      <div className="cr-select-wrap__inner">
        <select id={fieldId} className={['cr-select', className].filter(Boolean).join(' ')} {...rest}>
          {children || options.map((o) => {
            const val = typeof o === 'string' ? o : o.value;
            const lbl = typeof o === 'string' ? o : o.label;
            return <option key={val} value={val}>{lbl}</option>;
          })}
        </select>
        <span className="cr-select-wrap__chevron" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </span>
      </div>
    </div>
  );
}
