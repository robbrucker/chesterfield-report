import * as React from 'react';

/**
 * Mono HUD data block — label, big neon value, optional delta/trend.
 * @startingPoint section="Data" subtitle="Monospace counter readouts with trend deltas" viewport="700x140"
 */
export interface StatReadoutProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Mono uppercase label */
  label: string;
  /** Big numeric / string value */
  value: React.ReactNode;
  /** Optional delta text (e.g. "+12 this week") */
  delta?: string;
  /** Delta direction (colors + arrow) */
  trend?: 'up' | 'down' | 'flat';
  /** Accent tone. @default "teal" */
  tone?: 'teal' | 'magenta' | 'amber' | 'lime';
}

export function StatReadout(props: StatReadoutProps): JSX.Element;
