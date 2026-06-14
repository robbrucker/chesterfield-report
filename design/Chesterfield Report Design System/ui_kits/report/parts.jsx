// Shared presentational parts. -> window.CRParts
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const { Card, Badge } = DS;
  const I = window.CRIcons;

  // Image stand-in: duotone gradient + grid + corner brackets + caption.
  function PhotoFrame({ photo, label, ratio = '16 / 9', children, className = '' }) {
    return (
      <div className={'cr-photo ' + className} style={{ background: photo, aspectRatio: ratio }}>
        <div className="cr-photo__grid"></div>
        <div className="cr-photo__scan"></div>
        <span className="cr-photo__b cr-photo__b--tl"></span>
        <span className="cr-photo__b cr-photo__b--br"></span>
        {children}
        {label ? <span className="cr-photo__cap">{label}</span> : null}
      </div>
    );
  }

  function MetaRow({ time, date, read, author }) {
    return (
      <div className="cr-meta">
        {time ? <span className="cr-meta__t"><I.Clock /> {time}</span> : null}
        {date ? <span>{date}</span> : null}
        {read ? <span>{read}</span> : null}
        {author ? <span className="cr-meta__by">by {author}</span> : null}
      </div>
    );
  }

  function StoryCard({ story, onOpen, size = 'md' }) {
    return (
      <Card interactive accent tone={story.tone} bracket pad={false}
        className={'cr-story cr-story--' + size} onClick={() => onOpen && onOpen(story)}>
        <PhotoFrame photo={story.photo} label={'PHOTO \u00b7 ' + story.beat.toUpperCase()} />
        <div className="cr-story__body">
          <Badge tone={story.tone} dot={story.tone === 'breaking'}>{story.kicker}</Badge>
          <h3 className="cr-story__title">{story.title}</h3>
          {size !== 'sm' ? <p className="cr-story__dek">{story.dek}</p> : null}
          <MetaRow time={story.time} date={story.date} read={story.read}
            author={size === 'lg' ? story.author : null} />
        </div>
      </Card>
    );
  }

  function ListRow({ story, onOpen }) {
    return (
      <button className="cr-listrow" onClick={() => onOpen && onOpen(story)}>
        <span className={'cr-listrow__rail cr-listrow__rail--' + story.tone}></span>
        <div className="cr-listrow__body">
          <div className="cr-listrow__top">
            <Badge tone={story.tone}>{story.beat}</Badge>
            <span className="cr-listrow__time">{story.time}</span>
          </div>
          <h4 className="cr-listrow__title">{story.title}</h4>
          <p className="cr-listrow__dek">{story.dek}</p>
        </div>
        <span className="cr-listrow__go"><I.ChevronRight /></span>
      </button>
    );
  }

  function SectionHead({ kicker, title, action }) {
    return (
      <div className="cr-sechead">
        <div>
          <div className="cr-sechead__kicker">{kicker}</div>
          <h2 className="cr-sechead__title">{title}</h2>
        </div>
        {action || null}
      </div>
    );
  }

  window.CRParts = { PhotoFrame, MetaRow, StoryCard, ListRow, SectionHead };
})();
