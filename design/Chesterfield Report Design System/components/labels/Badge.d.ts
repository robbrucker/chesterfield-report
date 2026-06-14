import * as React from 'react';

/**
 * Compact status / category label — breaking, live, civic, eco, beat.
 * @startingPoint section="Labels" subtitle="Status & category badges incl. live pulse" viewport="700x120"
 */
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
  /** Color tone. @default "teal" */
  tone?: 'solid' | 'teal' | 'breaking' | 'civic' | 'eco' | 'neutral';
  /** Show a leading status dot */
  dot?: boolean;
  /** Animate the dot (live indicator). Implies dot. */
  live?: boolean;
}

export function Badge(props: BadgeProps): JSX.Element;
