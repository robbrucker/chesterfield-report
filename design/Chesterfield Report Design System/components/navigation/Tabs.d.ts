import * as React from 'react';

type TabItem = string | { value: string; label: string; count?: number };

/**
 * Section navigation with animated neon underline.
 * @startingPoint section="Navigation" subtitle="Beat tabs with animated neon underline" viewport="700x80"
 */
export interface TabsProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  /** Tabs as strings or {value,label,count} */
  items: TabItem[];
  /** Controlled active value */
  value?: string;
  /** Change handler */
  onChange?: (value: string) => void;
}

export function Tabs(props: TabsProps): JSX.Element;
