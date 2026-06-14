import React from 'react';

const STYLE_ID = 'cr-button-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-btn {
    --_fg: var(--text-on-neon);
    display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2);
    font-family: var(--font-display); font-weight: var(--fw-semibold);
    letter-spacing: var(--ls-wide); line-height: 1; white-space: nowrap;
    border: var(--bw-1) solid transparent; border-radius: var(--radius-sm);
    cursor: pointer; text-decoration: none; position: relative;
    transition: var(--transition-base);
    -webkit-tap-highlight-color: transparent; user-select: none;
  }
  .cr-btn:focus-visible { outline: none; box-shadow: var(--ring); }
  .cr-btn:active { transform: translateY(1px); }
  .cr-btn[disabled], .cr-btn[aria-disabled="true"] {
    opacity: 0.4; cursor: not-allowed; pointer-events: none;
  }
  /* sizes */
  .cr-btn--sm { font-size: var(--fs-2xs); padding: 7px 12px; }
  .cr-btn--md { font-size: var(--fs-xs); padding: 10px 18px; }
  .cr-btn--lg { font-size: var(--fs-sm); padding: 14px 26px; }
  /* primary — neon teal fill */
  .cr-btn--primary { background: var(--neon-teal); color: var(--text-on-neon); border-color: var(--neon-teal); box-shadow: 0 0 0 1px rgba(34,245,212,.0), 0 0 18px rgba(34,245,212,.0); }
  .cr-btn--primary:hover { box-shadow: var(--glow-md-teal); }
  .cr-btn--primary:active { background: var(--neon-teal-dim); }
  /* secondary — ghost with neon edge */
  .cr-btn--secondary { background: transparent; color: var(--neon-teal); border-color: var(--ink-300); }
  .cr-btn--secondary:hover { border-color: var(--neon-teal); color: var(--text-strong); box-shadow: var(--glow-sm-teal); }
  /* ghost — bare */
  .cr-btn--ghost { background: transparent; color: var(--text-default); border-color: transparent; }
  .cr-btn--ghost:hover { background: var(--surface-well); color: var(--text-strong); }
  /* danger / breaking — magenta */
  .cr-btn--danger { background: transparent; color: var(--neon-magenta); border-color: var(--neon-magenta-dim); }
  .cr-btn--danger:hover { color: var(--text-strong); box-shadow: var(--glow-md-magenta); border-color: var(--neon-magenta); }
  /* civic — amber */
  .cr-btn--civic { background: transparent; color: var(--neon-amber); border-color: var(--neon-amber-dim); }
  .cr-btn--civic:hover { color: var(--text-strong); box-shadow: var(--glow-md-amber); border-color: var(--neon-amber); }
  .cr-btn--block { display: flex; width: 100%; }
  `;
  document.head.appendChild(el);
}

/**
 * Button — primary action control for The Chesterfield Report.
 */
export function Button({
  children,
  variant = 'primary',
  size = 'md',
  block = false,
  iconLeft = null,
  iconRight = null,
  as = 'button',
  className = '',
  ...rest
}) {
  const Tag = as;
  const cls = [
    'cr-btn',
    `cr-btn--${variant}`,
    `cr-btn--${size}`,
    block ? 'cr-btn--block' : '',
    className,
  ].filter(Boolean).join(' ');
  return (
    <Tag className={cls} {...rest}>
      {iconLeft ? <span className="cr-btn__icon" aria-hidden="true">{iconLeft}</span> : null}
      <span>{children}</span>
      {iconRight ? <span className="cr-btn__icon" aria-hidden="true">{iconRight}</span> : null}
    </Tag>
  );
}
