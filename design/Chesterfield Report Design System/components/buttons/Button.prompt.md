Primary action control for The Chesterfield Report — neon-teal fill for the main action, edge/ghost variants for everything else. Use for any user action; pick the variant by intent, not decoration.

```jsx
<Button variant="primary" size="md" onClick={save}>Save story</Button>
<Button variant="secondary" iconLeft={<PlusIcon/>}>Follow beat</Button>
<Button variant="danger">Breaking alert</Button>
```

Variants: `primary` (teal fill — one per view), `secondary` (neon edge), `ghost` (bare, low-priority), `danger` (magenta — breaking/destructive), `civic` (amber — government/official actions). Sizes `sm | md | lg`. Pass `as="a"` with `href` to render a link. `block` makes it full-width.
