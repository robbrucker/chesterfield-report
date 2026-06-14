import * as React from 'react';

/**
 * Base surface panel — compose article cards, digests and HUD panels.
 * @startingPoint section="Surface" subtitle="HUD panel with accent bar, gradient & corner bracket" viewport="700x220"
 */
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  /** Apply default padding. @default true */
  pad?: boolean;
  /** Show top accent bar in the tone color */
  accent?: boolean;
  /** Accent / hover color. @default "teal" */
  tone?: 'teal' | 'breaking' | 'civic' | 'eco';
  /** Hover lift + glow (use for clickable cards) */
  interactive?: boolean;
  /** Subtle top gradient wash */
  grad?: boolean;
  /** Cyber corner-bracket flourish */
  bracket?: boolean;
}

export function Card(props: CardProps): JSX.Element;
