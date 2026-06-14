import * as React from 'react';

/**
 * Square, icon-only control for toolbars, card actions and nav.
 * Always pass `label` for accessibility.
 */
export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Icon node (SVG or icon font glyph) */
  children: React.ReactNode;
  /** Accessible label (also used as title tooltip) */
  label: string;
  /** Size. @default "md" */
  size?: 'sm' | 'md' | 'lg';
  /** "solid" (bordered surface) or "ghost" (bare). @default "solid" */
  variant?: 'solid' | 'ghost';
}

export function IconButton(props: IconButtonProps): JSX.Element;
