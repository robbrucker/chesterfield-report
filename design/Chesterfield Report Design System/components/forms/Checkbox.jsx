import React from 'react';

const STYLE_ID = 'cr-checkbox-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-check { display: inline-flex; align-items: center; gap: 10px; cursor: pointer; user-select: none; font-size: var(--fs-sm); color: var(--text-default); }
  .cr-check input { position: absolute; opacity: 0; width: 0; height: 0; }
  .cr-check__box {
    width: 18px; height: 18px; flex: none; border: var(--bw-1) solid var(--ink-300);
    border-radius: var(--radius-xs); background: var(--surface-raised);
    display: grid; place-items: center; transition: var(--transition-base);
  }
  .cr-check__box svg { width: 12px; height: 12px; opacity: 0; transform: scale(.5); transition: var(--transition-base); color: var(--text-on-neon); }
  .cr-check:hover .cr-check__box { border-color: var(--neon-teal); }
  .cr-check input:checked + .cr-check__box { background: var(--neon-teal); border-color: var(--neon-teal); box-shadow: var(--glow-sm-teal); }
  .cr-check input:checked + .cr-check__box svg { opacity: 1; transform: scale(1); }
  .cr-check input:focus-visible + .cr-check__box { box-shadow: var(--ring); }
  .cr-check input:disabled ~ * { opacity: .45; }
  `;
  document.head.appendChild(el);
}

/**
 * Checkbox — boolean toggle with label.
 */
export function Checkbox({ label, id, className = '', ...rest }) {
  const fieldId = id || (label ? 'cr-cb-' + String(label).toLowerCase().replace(/\s+/g, '-') : undefined);
  return (
    <label className={['cr-check', className].filter(Boolean).join(' ')} htmlFor={fieldId}>
      <input type="checkbox" id={fieldId} {...rest} />
      <span className="cr-check__box" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
      </span>
      {label ? <span>{label}</span> : null}
    </label>
  );
}
