// Topic filter view. -> window.CRTopics
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const { Card, Tag, Select, StatReadout, Switch } = DS;
  const { ListRow, SectionHead } = window.CRParts;
  const { stories, beats } = window.CR_DATA;

  function Topics({ onOpen }) {
    const allBeats = beats.filter((b) => b !== 'This Week');
    const [active, setActive] = React.useState({});
    const [live, setLive] = React.useState(true);
    const sel = Object.keys(active).filter((k) => active[k]);
    const toggle = (b) => setActive((s) => ({ ...s, [b]: !s[b] }));

    const filtered = stories.filter((s) => {
      if (sel.length === 0) return true;
      return sel.some((b) => s.beat === b || b.startsWith(s.beat) || s.beat.startsWith(b));
    });

    return (
      <div className="cr-topics">
        <div className="cr-topics__hero cr-grid-bg">
          <span className="cr-week__kicker">// Filter the county</span>
          <h1 className="cr-week__title">Follow the beats that matter to you</h1>
          <div className="cr-topics__tags">
            {allBeats.map((b) => (
              <Tag key={b} active={!!active[b]} hash onClick={() => toggle(b)}>{b}</Tag>
            ))}
          </div>
        </div>

        <div className="cr-topics__bar">
          <div className="cr-topics__count">
            <StatReadout label={sel.length ? 'Matching ' + sel.length + ' beat' + (sel.length > 1 ? 's' : '') : 'All stories'} value={String(filtered.length).padStart(2, '0')} />
          </div>
          <div className="cr-topics__controls">
            <Switch label="Live updates" checked={live} onChange={(e) => setLive(e.target.checked)} />
            <Select aria-label="Sort" options={['Newest first', 'Most read', 'Oldest first']} />
          </div>
        </div>

        <div className="cr-topics__list">
          {filtered.map((s) => <ListRow key={s.id} story={s} onOpen={onOpen} />)}
          {filtered.length === 0 ? (
            <Card className="cr-topics__empty">No stories match those beats yet. Try fewer filters.</Card>
          ) : null}
        </div>
      </div>
    );
  }

  window.CRTopics = { Topics };
})();
