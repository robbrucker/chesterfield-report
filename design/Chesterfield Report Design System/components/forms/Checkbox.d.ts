import * as React from 'react';

/**
 * Boolean checkbox with neon-teal checked state and label.
 */
export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Text label beside the box */
  label?: React.ReactNode;
}

export function Checkbox(props: CheckboxProps): JSX.Element;
