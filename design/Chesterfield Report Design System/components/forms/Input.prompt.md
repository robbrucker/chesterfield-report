Single-line text field with a mono uppercase label, optional leading icon, hint text and error state. Use for all text entry — search, newsletter signup, tip submission.

```jsx
<Input label="Email" type="email" placeholder="you@chesterfield.gov" icon={<MailIcon/>} />
<Input label="Headline" error="Headline is required" />
```

Pass `error` to flip the field to the magenta invalid state (overrides `hint`). Pairs with `Select`, `Checkbox` and `Switch` in the same group.
