Monospace HUD data block — the brand's signature "data readout." Use for civic counters, dashboard figures, This Week stats.

```jsx
<StatReadout label="Stories this week" value="47" delta="+12" trend="up" />
<StatReadout label="Open FOIA requests" value="9" tone="amber" />
```

Tones `teal | magenta | amber | lime`. Pass `delta`+`trend` for the colored arrow line.
