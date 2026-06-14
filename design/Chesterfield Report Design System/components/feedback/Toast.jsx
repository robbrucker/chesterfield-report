import React from 'react';

const STYLE_ID = 'cr-toast-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-toast {
    display: flex; align-items: flex-start; gap: 12px; max-width: 380px;
    background: var(--surface-raised); border: var(--bw-1) solid var(--ink-300);
    border-left: var(--bw-3) solid var(--toast-accent, var(--neon-teal));
    border-radius: var(--radius-sm); padding: 13px 14px; box-shadow: var(--shadow-lg);
    position: relative; overflow: hidden;
  }
  .cr-toast::before { content: ""; position: absolute; inset: 0; background: var(--tex-scanlines); opacity: .25; pointer-events: none; }
  .cr-toast__icon { color: var(--toast-accent, var(--neon-teal)); flex: none; display: flex; margin-top: 1px; }
  .cr-toast__icon svg { width: 18px; height: 18px; }
  .cr-toast__body { flex: 1; min-width: 0; }
  .cr-toast__title { font: var(--fw-semibold) var(--fs-sm)/1.3 var(--font-display); color: var(--text-strong); letter-spacing: var(--ls-wide); }
  .cr-toast__msg { font-size: var(--fs-2xs); color: var(--text-muted); margin-top: 3px; }
  .cr-toast__close { appearance: none; background: none; border: none; color: var(--text-faint); cursor: pointer; padding: 2px; display: flex; transition: color var(--dur-fast); }
  .cr-toast__close:hover { color: var(--neon-magenta); }
  .cr-toast__close svg { width: 14px; height: 14px; }
  `;
  document.head.appendChild(el);
}

const TOAST_ACCENT = {
  info: 'var(--neon-teal)',
  success: 'var(--neon-lime)',
  breaking: 'var(--neon-magenta)',
  civic: 'var(--neon-amber)',
};
const ICONS = {
  info: <path d="M12 16v-5M12 8h.01M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z"/>,
  success: <path d="M22 11.1V12a10 10 0 1 1-5.9-9.1M22 4 12 14.01l-3-3"/>,
  breaking: <path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>,
  civic: <path d="M3 21h18M5 21V8l7-5 7 5v13M9 21v-6h6v6"/>,
};

/**
 * Toast — transient notification. Pulls accent + icon from tone.
 */
export function Toast({ title, children, tone = 'info', onClose, className = '', ...rest }) {
  return (
    <div className={['cr-toast', className].filter(Boolean).join(' ')}
      style={{ '--toast-accent': TOAST_ACCENT[tone] || TOAST_ACCENT.info }}
      role="status" {...rest}>
      <span className="cr-toast__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">{ICONS[tone] || ICONS.info}</svg>
      </span>
      <div className="cr-toast__body">
        {title ? <div className="cr-toast__title">{title}</div> : null}
        {children ? <div className="cr-toast__msg">{children}</div> : null}
      </div>
      {onClose ? (
        <button type="button" className="cr-toast__close" aria-label="Dismiss" onClick={onClose}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      ) : null}
    </div>
  );
}
