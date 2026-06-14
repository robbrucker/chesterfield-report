import React from 'react';

const STYLE_ID = 'cr-iconbutton-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-iconbtn {
    display: inline-flex; align-items: center; justify-content: center;
    border: var(--bw-1) solid var(--ink-400); background: var(--surface-raised);
    color: var(--text-default); border-radius: var(--radius-sm); cursor: pointer;
    transition: var(--transition-base); padding: 0;
  }
  .cr-iconbtn svg { width: 1.15em; height: 1.15em; }
  .cr-iconbtn:hover { color: var(--neon-teal); border-color: var(--neon-teal); box-shadow: var(--glow-sm-teal); }
  .cr-iconbtn:active { transform: translateY(1px); }
  .cr-iconbtn:focus-visible { outline: none; box-shadow: var(--ring); }
  .cr-iconbtn[disabled] { opacity: .4; cursor: not-allowed; }
  .cr-iconbtn--sm { width: 30px; height: 30px; font-size: 14px; }
  .cr-iconbtn--md { width: 38px; height: 38px; font-size: 16px; }
  .cr-iconbtn--lg { width: 46px; height: 46px; font-size: 19px; }
  .cr-iconbtn--ghost { background: transparent; border-color: transparent; }
  .cr-iconbtn--ghost:hover { background: var(--surface-well); }
  `;
  document.head.appendChild(el);
}

/**
 * IconButton — square icon-only control (toolbar, card actions, nav).
 */
export function IconButton({
  children,
  label,
  size = 'md',
  variant = 'solid',
  className = '',
  ...rest
}) {
  const cls = [
    'cr-iconbtn',
    `cr-iconbtn--${size}`,
    variant === 'ghost' ? 'cr-iconbtn--ghost' : '',
    className,
  ].filter(Boolean).join(' ');
  return (
    <button type="button" className={cls} aria-label={label} title={label} {...rest}>
      {children}
    </button>
  );
}
