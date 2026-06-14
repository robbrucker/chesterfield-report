import React from 'react';

const STYLE_ID = 'cr-input-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-field { display: flex; flex-direction: column; gap: 6px; }
  .cr-field__label { font: var(--fw-bold) var(--fs-3xs)/1 var(--font-mono); letter-spacing: var(--ls-wider); text-transform: uppercase; color: var(--text-muted); }
  .cr-input-wrap { position: relative; display: flex; align-items: center; }
  .cr-input-wrap__icon { position: absolute; left: 12px; color: var(--text-muted); display: flex; pointer-events: none; }
  .cr-input-wrap__icon svg { width: 16px; height: 16px; }
  .cr-input {
    width: 100%; font: var(--text-body-r); font-size: var(--fs-sm); color: var(--text-strong);
    background: var(--surface-raised); border: var(--bw-1) solid var(--ink-400);
    border-radius: var(--radius-sm); padding: 11px 13px; transition: var(--transition-base);
  }
  .cr-input--has-icon { padding-left: 36px; }
  .cr-input::placeholder { color: var(--text-faint); }
  .cr-input:hover { border-color: var(--ink-300); }
  .cr-input:focus { outline: none; border-color: var(--neon-teal); box-shadow: var(--glow-sm-teal); background: var(--ink-700); }
  .cr-input[aria-invalid="true"] { border-color: var(--neon-magenta); }
  .cr-input[aria-invalid="true"]:focus { box-shadow: var(--glow-md-magenta); }
  .cr-input:disabled { opacity: .5; cursor: not-allowed; }
  .cr-field__hint { font-size: var(--fs-2xs); color: var(--text-faint); }
  .cr-field__hint--error { color: var(--neon-magenta); }
  `;
  document.head.appendChild(el);
}

/**
 * Input — single-line text field with optional label, leading icon and hint.
 */
export function Input({
  label,
  hint,
  error,
  icon = null,
  id,
  className = '',
  ...rest
}) {
  const fieldId = id || (label ? 'cr-' + label.toLowerCase().replace(/\s+/g, '-') : undefined);
  return (
    <div className="cr-field">
      {label ? <label className="cr-field__label" htmlFor={fieldId}>{label}</label> : null}
      <div className="cr-input-wrap">
        {icon ? <span className="cr-input-wrap__icon">{icon}</span> : null}
        <input
          id={fieldId}
          className={['cr-input', icon ? 'cr-input--has-icon' : '', className].filter(Boolean).join(' ')}
          aria-invalid={error ? 'true' : undefined}
          {...rest}
        />
      </div>
      {error ? <span className="cr-field__hint cr-field__hint--error">{error}</span>
        : hint ? <span className="cr-field__hint">{hint}</span> : null}
    </div>
  );
}
