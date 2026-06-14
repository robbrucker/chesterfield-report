import * as React from 'react';

/**
 * Topic / filter chip. Selectable beats and removable active filters.
 */
export interface TagProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onRemove'> {
  children: React.ReactNode;
  /** Active/selected styling */
  active?: boolean;
  /** Show the leading "#". @default true */
  hash?: boolean;
  /** When provided, renders a remove "×" affordance */
  onRemove?: (e: React.MouseEvent) => void;
}

export function Tag(props: TagProps): JSX.Element;
