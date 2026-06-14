Base surface panel for the dark HUD. Compose everything from it — article cards, the This Week digest, sidebar modules. Crisp corners, hairline border, optional neon accent bar and hover lift.

```jsx
<Card interactive accent tone="breaking" bracket>
  <Badge tone="breaking" dot>Breaking</Badge>
  <h3>County board approves riverfront rezoning</h3>
</Card>
```

Props: `accent` (top bar), `tone` (teal/breaking/civic/eco), `interactive` (hover lift + glow), `grad` (top wash), `bracket` (corner flourish), `pad` (default true).
