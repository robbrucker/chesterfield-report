// Home feed view. -> window.CRHome
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const { Card, Badge, Button, StatReadout, Tag } = DS;
  const { StoryCard, ListRow, SectionHead, MetaRow, PhotoFrame } = window.CRParts;
  const I = window.CRIcons;
  const { lead, stories, thisWeek } = window.CR_DATA;

  function HeroLead({ onOpen }) {
    return (
      <Card interactive accent tone="breaking" bracket pad={false}
        className="cr-hero" onClick={() => onOpen(lead)}>
        <PhotoFrame photo={lead.photo} ratio="21 / 9" label="PHOTO \u00b7 APPOMATTOX RIVERFRONT">
          <div className="cr-hero__overlay">
            <Badge tone="breaking" dot>Breaking \u00b7 {lead.kicker}</Badge>
            <h1 className="cr-hero__title">{lead.title}</h1>
            <p className="cr-hero__dek">{lead.dek}</p>
            <MetaRow time={lead.time} date={lead.date} read={lead.read} author={lead.author} />
          </div>
        </PhotoFrame>
      </Card>
    );
  }

  function ThisWeekRail({ onNav }) {
    return (
      <Card grad className="cr-twrail" pad={false}>
        <div className="cr-twrail__head">
          <span className="cr-twrail__kicker">// This Week in Chesterfield</span>
          <button className="cr-twrail__all" onClick={() => onNav('thisweek')}>Full digest <I.ArrowUpRight /></button>
        </div>
        <ul className="cr-twrail__list">
          {thisWeek.map((d, i) => (
            <li key={i} className="cr-twrail__item">
              <span className={'cr-twrail__day cr-twrail__day--' + d.tone}>{d.day}</span>
              <div>
                <div className="cr-twrail__label">{d.label}</div>
                <div className="cr-twrail__title">{d.title}</div>
              </div>
            </li>
          ))}
        </ul>
      </Card>
    );
  }

  function Newsletter({ onNav }) {
    return (
      <Card grad bracket className="cr-nl">
        <span className="cr-nl__kicker">// Sunday 7am</span>
        <h3 className="cr-nl__title">The week, decoded.</h3>
        <p className="cr-nl__dek">One email. Every decision the county made, in plain language.</p>
        <Button variant="primary" size="sm" block iconRight={<I.Send />} onClick={() => onNav('tip')}>Get This Week</Button>
      </Card>
    );
  }

  function Home({ onOpen, onNav }) {
    const grid = stories.slice(0, 4);
    const list = stories.slice(2);
    return (
      <div className="cr-home">
        <div className="cr-home__main">
          <HeroLead onOpen={onOpen} />
          <SectionHead kicker="// The feed" title="Across the county"
            action={<Button variant="secondary" size="sm" iconRight={<I.Arrow />} onClick={() => onNav('topics')}>Filter beats</Button>} />
          <div className="cr-home__grid">
            {grid.map((s) => <StoryCard key={s.id} story={s} onOpen={onOpen} />)}
          </div>
          <SectionHead kicker="// Latest" title="As it files in" />
          <div className="cr-home__list">
            {list.map((s) => <ListRow key={s.id} story={s} onOpen={onOpen} />)}
          </div>
        </div>
        <aside className="cr-home__side">
          <div className="cr-home__stats">
            <StatReadout label="Stories this week" value="47" delta="+12" trend="up" />
            <StatReadout label="Board votes tracked" value="216" tone="amber" delta="3 pending" trend="flat" />
          </div>
          <ThisWeekRail onNav={onNav} />
          <Newsletter onNav={onNav} />
          <Card className="cr-trend" grad>
            <span className="cr-twrail__kicker">// Trending tags</span>
            <div className="cr-trend__tags">
              {['Zoning','Route 10','School calendar','Swift Creek','Budget','Midlothian'].map((t) => (
                <Tag key={t} onClick={() => onNav('topics')}>{t}</Tag>
              ))}
            </div>
          </Card>
        </aside>
      </div>
    );
  }

  window.CRHome = { Home };
})();
