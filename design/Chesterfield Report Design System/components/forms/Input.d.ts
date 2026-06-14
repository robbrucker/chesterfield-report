import * as React from 'react';

/**
 * Single-line text field with optional mono label, leading icon, hint and error.
 * @startingPoint section="Forms" subtitle="Text field with label, icon, hint & error states" viewport="700x140"
 */
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Mono uppercase label above the field */
  label?: string;
  /** Helper text below the field */
  hint?: string;
  /** Error message (sets invalid styling, magenta) */
  error?: string;
  /** Leading icon node */
  icon?: React.ReactNode;
}

export function Input(props: InputProps): JSX.Element;
