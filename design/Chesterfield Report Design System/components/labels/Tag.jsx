import React from 'react';

const STYLE_ID = 'cr-tag-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-tag {
    display: inline-flex; align-items: center; gap: 7px; cursor: pointer;
    font-family: var(--font-mono); font-size: var(--fs-2xs); letter-spacing: var(--ls-wide);
    color: var(--text-default); background: var(--surface-raised);
    border: var(--bw-1) solid var(--ink-400); border-radius: var(--radius-pill);
    padding: 6px 13px; transition: var(--transition-base); user-select: none;
  }
  .cr-tag:hover { border-color: var(--neon-teal); color: var(--text-strong); }
  .cr-tag--active { background: var(--teal-wash); border-color: var(--neon-teal); color: var(--neon-teal); box-shadow: var(--glow-sm-teal); }
  .cr-tag__hash { color: var(--neon-teal); opacity: .8; }
  .cr-tag__x { display: inline-flex; opacity: .6; }
  .cr-tag__x:hover { opacity: 1; color: var(--neon-magenta); }
  .cr-tag__x svg { width: 12px; height: 12px; }
  .cr-tag:focus-visible { outline: none; box-shadow: var(--ring); }
  `;
  document.head.appendChild(el);
}

/**
 * Tag — topic / filter chip. Use for selectable beats and removable filters.
 */
export function Tag({
  children,
  active = false,
  hash = true,
  onRemove,
  className = '',
  ...rest
}) {
  const cls = ['cr-tag', active ? 'cr-tag--active' : '', className].filter(Boolean).join(' ');
  return (
    <button type="button" className={cls} aria-pressed={active} {...rest}>
      {hash ? <span className="cr-tag__hash" aria-hidden="true">#</span> : null}
      {children}
      {onRemove ? (
        <span className="cr-tag__x" role="button" aria-label="Remove"
          onClick={(e) => { e.stopPropagation(); onRemove(e); }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </span>
      ) : null}
    </button>
  );
}
