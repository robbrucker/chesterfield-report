import * as React from 'react';

type Option = string | { value: string; label: string };

/**
 * Native select styled for the dark HUD surface, with neon chevron.
 */
export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  /** Mono uppercase label above the field */
  label?: string;
  /** Options as strings or {value,label}. Ignored if children passed. */
  options?: Option[];
}

export function Select(props: SelectProps): JSX.Element;
