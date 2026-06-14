// This Week digest view. -> window.CRWeek
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const { Card, Badge, Button, StatReadout } = DS;
  const { SectionHead, ListRow } = window.CRParts;
  const I = window.CRIcons;
  const { thisWeek, stories } = window.CR_DATA;

  function Week({ onOpen, onNav }) {
    return (
      <div className="cr-week">
        <div className="cr-week__hero cr-scanlines">
          <span className="cr-week__kicker">// Digest \u00b7 Week of June 8\u201314, 2026</span>
          <h1 className="cr-week__title">This Week in Chesterfield</h1>
          <p className="cr-week__dek">Everything the county decided, scheduled, or set in motion \u2014 one scan.</p>
          <div className="cr-week__stats">
            <StatReadout label="Public meetings" value="5" />
            <StatReadout label="Decisions logged" value="11" tone="amber" delta="+4" trend="up" />
            <StatReadout label="Days to budget vote" value="04" tone="magenta" />
          </div>
        </div>

        <SectionHead kicker="// The schedule" title="On the county calendar" />
        <div className="cr-week__rail">
          {thisWeek.map((d, i) => (
            <Card key={i} accent tone={d.tone} bracket className="cr-week__day">
              <span className="cr-week__dayname">{d.day}</span>
              <Badge tone={d.tone}>{d.label}</Badge>
              <div className="cr-week__daytitle">{d.title}</div>
            </Card>
          ))}
        </div>

        <SectionHead kicker="// In case you missed it" title="The week's biggest files"
          action={<Button variant="secondary" size="sm" iconRight={<I.Arrow />} onClick={() => onNav('home')}>Back to feed</Button>} />
        <div className="cr-week__list">
          {stories.slice(0, 4).map((s) => <ListRow key={s.id} story={s} onOpen={onOpen} />)}
        </div>
      </div>
    );
  }

  window.CRWeek = { Week };
})();
