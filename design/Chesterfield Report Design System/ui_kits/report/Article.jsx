// Single article view. -> window.CRArticle
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const { Card, Badge, Button, IconButton, Tag, StatReadout } = DS;
  const { PhotoFrame, MetaRow, StoryCard, SectionHead } = window.CRParts;
  const I = window.CRIcons;
  const { stories } = window.CR_DATA;

  const BODY = [
    'After three hours of public comment, the Chesterfield County Board of Supervisors voted 4\u20131 Wednesday night to approve a mixed-use rezoning of 220 acres along the Appomattox River, clearing the way for what developers call a \u201criverfront district\u201d of housing, retail and a public greenway.',
    'The approval carries a 40-foot setback from the regulatory floodplain and requires the developer to fund a pedestrian bridge connecting the site to the existing trail network. Supervisor Lena Hargrove cast the lone dissenting vote, citing traffic on Route 10.',
    'Opponents, organized as Keep the Appomattox Wild, pledged within minutes to gather signatures for a referendum. \u201cThis isn\u2019t over,\u201d said spokesperson Dale Whitford. \u201cThe county just traded a floodplain for a tax base.\u201d',
    'County planners estimate the project will generate $3.2 million in annual tax revenue at build-out, projected for 2031. Construction on the first phase \u2014 320 townhomes \u2014 could begin as early as next spring.',
  ];

  function Article({ story, onOpen, onNav }) {
    const s = story || stories[0];
    const related = stories.filter((x) => x.id !== s.id).slice(0, 3);
    return (
      <article className="cr-article">
        <button className="cr-article__back" onClick={() => onNav('home')}><I.Arrow style={{ transform: 'rotate(180deg)' }} /> All stories</button>
        <div className="cr-article__head">
          <Badge tone={s.tone} dot={s.tone === 'breaking'}>{s.beat} \u00b7 {s.kicker}</Badge>
          <h1 className="cr-article__title">{s.title}</h1>
          <p className="cr-article__dek">{s.dek}</p>
          <div className="cr-article__byline">
            <MetaRow time={s.time} date={s.date} read={s.read} author={s.author} />
            <div className="cr-article__tools">
              <IconButton label="Save" variant="ghost"><I.Bookmark /></IconButton>
              <IconButton label="Share" variant="ghost"><I.Share /></IconButton>
              <Button variant="civic" size="sm" iconLeft={<I.Eye />}>Follow this story</Button>
            </div>
          </div>
        </div>

        <PhotoFrame photo={s.photo} ratio="21 / 9" label="PHOTO \u00b7 STAFF" className="cr-article__photo" />

        <div className="cr-article__layout">
          <div className="cr-article__body">
            {BODY.map((p, i) => <p key={i} className={i === 0 ? 'cr-article__lead' : ''}>{p}</p>)}
            <div className="cr-article__tags">
              {['Zoning','Appomattox River','Board of Supervisors','Route 10'].map((t) => <Tag key={t}>{t}</Tag>)}
            </div>
          </div>
          <aside className="cr-article__aside">
            <Card grad bracket className="cr-article__pull">
              <span className="cr-twrail__kicker">// The vote</span>
              <StatReadout label="Supervisors for" value="4" tone="lime" />
              <StatReadout label="Against" value="1" tone="magenta" />
              <div className="cr-article__pullnote">Roll call recorded 19:42, Jun 10.</div>
            </Card>
          </aside>
        </div>

        <SectionHead kicker="// Keep reading" title="More from the county" />
        <div className="cr-article__related">
          {related.map((r) => <StoryCard key={r.id} story={r} size="sm" onOpen={onOpen} />)}
        </div>
      </article>
    );
  }

  window.CRArticle = { Article };
})();
