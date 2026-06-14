import * as React from 'react';

/**
 * On/off switch for settings and live filters (role="switch").
 */
export interface SwitchProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Text label beside the switch */
  label?: React.ReactNode;
}

export function Switch(props: SwitchProps): JSX.Element;
