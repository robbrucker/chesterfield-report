import * as React from 'react';

/**
 * Primary action control. Neon-teal fill for the main action; ghost/edge
 * variants for secondary, breaking (magenta) and civic (amber) contexts.
 *
 * @startingPoint section="Buttons" subtitle="Primary, secondary, ghost, breaking & civic actions" viewport="700x220"
 */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button label / content */
  children: React.ReactNode;
  /** Visual style. @default "primary" */
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'civic';
  /** Size. @default "md" */
  size?: 'sm' | 'md' | 'lg';
  /** Fill the container width. @default false */
  block?: boolean;
  /** Icon node placed before the label */
  iconLeft?: React.ReactNode;
  /** Icon node placed after the label */
  iconRight?: React.ReactNode;
  /** Render as another element/tag (e.g. "a"). @default "button" */
  as?: keyof JSX.IntrinsicElements;
}

export function Button(props: ButtonProps): JSX.Element;
