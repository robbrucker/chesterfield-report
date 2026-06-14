import * as React from 'react';

/**
 * Transient notification. Accent color + icon derive from tone.
 */
export interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Bold title line */
  title?: string;
  /** Secondary message (children) */
  children?: React.ReactNode;
  /** Tone. @default "info" */
  tone?: 'info' | 'success' | 'breaking' | 'civic';
  /** Show a dismiss button + handler */
  onClose?: () => void;
}

export function Toast(props: ToastProps): JSX.Element;
