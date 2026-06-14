Section navigation with an animated neon underline. Use for switching beats / feed views.

```jsx
const [tab, setTab] = React.useState('this-week');
<Tabs value={tab} onChange={setTab} items={[
  { value: 'this-week', label: 'This Week' },
  { value: 'growth', label: 'Growth', count: 12 },
  { value: 'schools', label: 'Schools', count: 5 },
]} />
```

Items accept a plain string or `{value,label,count}`. Controlled via `value`/`onChange`.
