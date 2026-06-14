import React from 'react';

const STYLE_ID = 'cr-badge-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-badge {
    display: inline-flex; align-items: center; gap: 6px;
    font: var(--fw-bold) var(--fs-3xs)/1 var(--font-mono); letter-spacing: var(--ls-wider);
    text-transform: uppercase; padding: 5px 9px; border-radius: var(--radius-xs);
    border: var(--bw-1) solid transparent; white-space: nowrap;
  }
  .cr-badge--solid { background: var(--neon-teal); color: var(--text-on-neon); }
  .cr-badge--teal   { color: var(--neon-teal);   border-color: rgba(34,245,212,.4);  background: var(--teal-wash); }
  .cr-badge--breaking { color: var(--neon-magenta); border-color: rgba(255,46,136,.5); background: var(--magenta-wash); }
  .cr-badge--civic  { color: var(--neon-amber);  border-color: rgba(255,210,63,.45); background: var(--amber-wash); }
  .cr-badge--eco    { color: var(--neon-lime);   border-color: rgba(141,255,94,.4);  background: rgba(141,255,94,.08); }
  .cr-badge--neutral{ color: var(--text-muted);  border-color: var(--ink-400);       background: var(--surface-raised); }
  .cr-badge__dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
  .cr-badge--live .cr-badge__dot { animation: cr-pulse 1.4s var(--ease-in-out) infinite; }
  @keyframes cr-pulse { 0%,100% { opacity: 1; } 50% { opacity: .25; } }
  `;
  document.head.appendChild(el);
}

/**
 * Badge — compact status / category label (breaking, live, civic, beat tag).
 */
export function Badge({
  children,
  tone = 'teal',
  dot = false,
  live = false,
  className = '',
  ...rest
}) {
  const cls = [
    'cr-badge',
    `cr-badge--${tone}`,
    live ? 'cr-badge--live' : '',
    className,
  ].filter(Boolean).join(' ');
  return (
    <span className={cls} {...rest}>
      {(dot || live) ? <span className="cr-badge__dot" aria-hidden="true"></span> : null}
      {children}
    </span>
  );
}
