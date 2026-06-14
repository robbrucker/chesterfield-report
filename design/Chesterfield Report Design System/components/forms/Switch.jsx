import React from 'react';

const STYLE_ID = 'cr-switch-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-switch { display: inline-flex; align-items: center; gap: 10px; cursor: pointer; user-select: none; font-size: var(--fs-sm); color: var(--text-default); }
  .cr-switch input { position: absolute; opacity: 0; width: 0; height: 0; }
  .cr-switch__track {
    width: 40px; height: 22px; flex: none; border-radius: var(--radius-pill);
    background: var(--ink-500); border: var(--bw-1) solid var(--ink-300);
    position: relative; transition: var(--transition-base);
  }
  .cr-switch__thumb {
    position: absolute; top: 2px; left: 2px; width: 16px; height: 16px;
    border-radius: 50%; background: var(--fog); transition: var(--transition-base);
  }
  .cr-switch:hover .cr-switch__track { border-color: var(--neon-teal); }
  .cr-switch input:checked + .cr-switch__track { background: var(--neon-teal); border-color: var(--neon-teal); box-shadow: var(--glow-sm-teal); }
  .cr-switch input:checked + .cr-switch__track .cr-switch__thumb { transform: translateX(18px); background: var(--text-on-neon); }
  .cr-switch input:focus-visible + .cr-switch__track { box-shadow: var(--ring); }
  .cr-switch input:disabled ~ * { opacity: .45; }
  `;
  document.head.appendChild(el);
}

/**
 * Switch — on/off toggle for settings and live filters.
 */
export function Switch({ label, id, className = '', ...rest }) {
  const fieldId = id || (label ? 'cr-sw-' + String(label).toLowerCase().replace(/\s+/g, '-') : undefined);
  return (
    <label className={['cr-switch', className].filter(Boolean).join(' ')} htmlFor={fieldId}>
      <input type="checkbox" role="switch" id={fieldId} {...rest} />
      <span className="cr-switch__track" aria-hidden="true"><span className="cr-switch__thumb"></span></span>
      {label ? <span>{label}</span> : null}
    </label>
  );
}
