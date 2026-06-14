// Map / radar view. -> window.CRMap
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const { Card, Badge, StatReadout } = DS;
  const { SectionHead } = window.CRParts;
  const I = window.CRIcons;
  const { mapPins } = window.CR_DATA;

  const TONE_VAR = { breaking: 'var(--neon-magenta)', civic: 'var(--neon-amber)', teal: 'var(--neon-teal)', eco: 'var(--neon-lime)' };

  function Map({ onOpen }) {
    const [sel, setSel] = React.useState(null);
    return (
      <div className="cr-map">
        <SectionHead kicker="// Live county map" title="What's happening, where"
          action={<Badge tone="teal" live>Realtime</Badge>} />
        <div className="cr-map__grid">
          <div className="cr-mapcanvas cr-scanlines">
            <div className="cr-mapcanvas__county">
              <div className="cr-mapcanvas__sweep"></div>
              {mapPins.map((p, i) => (
                <button key={i} className={'cr-pin' + (sel === i ? ' cr-pin--active' : '')}
                  style={{ left: p.x + '%', top: p.y + '%', '--pin': TONE_VAR[p.tone] }}
                  onClick={() => setSel(i)} aria-label={p.label}>
                  <span className="cr-pin__dot"></span>
                  <span className="cr-pin__ring"></span>
                  <span className="cr-pin__label">{p.label}</span>
                </button>
              ))}
            </div>
            <div className="cr-mapcanvas__readout">
              <span>CHESTERFIELD CO. \u00b7 VA</span>
              <span>37.3771\u00b0 N \u00b7 77.5089\u00b0 W</span>
              <span>{mapPins.length} ACTIVE PINGS</span>
            </div>
          </div>

          <aside className="cr-map__side">
            <div className="cr-map__stats">
              <StatReadout label="Active incidents" value="2" tone="magenta" />
              <StatReadout label="Civic events" value="3" tone="amber" />
            </div>
            <Card grad className="cr-map__legend" pad={false}>
              <div className="cr-map__legendhead">// Pings</div>
              <ul>
                {mapPins.map((p, i) => (
                  <li key={i} className={sel === i ? 'is-sel' : ''} onClick={() => setSel(i)}>
                    <span className="cr-map__swatch" style={{ background: TONE_VAR[p.tone] }}></span>
                    <span className="cr-map__legendlabel">{p.label}</span>
                    <I.ChevronRight />
                  </li>
                ))}
              </ul>
            </Card>
          </aside>
        </div>
      </div>
    );
  }

  window.CRMap = { Map };
})();
