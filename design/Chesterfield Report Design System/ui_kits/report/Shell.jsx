// Shell: header, breaking ticker, footer. -> window.CRShell
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const { Button, IconButton, Tabs, Badge } = DS;
  const I = window.CRIcons;
  const { beats } = window.CR_DATA;

  function Wordmark({ onClick }) {
    return (
      <button className="cr-wm" onClick={onClick} aria-label="The Chesterfield Report home">
        <img src="../../assets/logo-mark.svg" alt="" className="cr-wm__mark" />
        <span className="cr-wm__text">
          <span className="cr-wm__top">The</span>
          <span className="cr-wm__main">Chesterfield Report</span>
        </span>
      </button>
    );
  }

  function Ticker() {
    const items = [
      'ROUTE 10 reopens after tanker crash \u2014 no injuries',
      'BOARD votes 4\u20131 to approve riverfront rezoning',
      'SWIFT CREEK reservoir at five-year low \u2014 voluntary water cuts',
      'COSBY HIGH breaks ground on STEM wing',
    ];
    const stream = items.concat(items);
    return (
      <div className="cr-ticker" role="marquee" aria-label="Breaking headlines">
        <span className="cr-ticker__tag"><span className="cr-ticker__dot"></span>LIVE</span>
        <div className="cr-ticker__viewport">
          <div className="cr-ticker__track">
            {stream.map((t, i) => (
              <span className="cr-ticker__item" key={i}><span className="cr-ticker__sep">//</span>{t}</span>
            ))}
          </div>
        </div>
      </div>
    );
  }

  function Header({ view, beat, onBeat, onNav, onSearch }) {
    return (
      <header className="cr-header">
        <div className="cr-header__bar">
          <Wordmark onClick={() => onNav('home')} />
          <div className="cr-header__search">
            <I.Search className="cr-header__search-icon" />
            <input placeholder="Search Chesterfield \u2014 zoning, schools, police\u2026"
              onFocus={onSearch} readOnly />
            <kbd>/</kbd>
          </div>
          <div className="cr-header__actions">
            <IconButton label="Map" variant="ghost" onClick={() => onNav('map')}><I.MapPin /></IconButton>
            <IconButton label="Alerts" variant="ghost"><I.Bell /></IconButton>
            <Button variant="primary" size="sm" onClick={() => onNav('tip')}>Subscribe</Button>
          </div>
        </div>
        <nav className="cr-header__nav">
          <Tabs value={beat} onChange={onBeat} items={beats.map((b) => ({ value: b, label: b }))} />
        </nav>
      </header>
    );
  }

  function Footer({ onNav }) {
    return (
      <footer className="cr-footer">
        <div className="cr-footer__top">
          <div className="cr-footer__brand">
            <img src="../../assets/logo-mark.svg" alt="" />
            <div>
              <div className="cr-footer__name">The Chesterfield Report</div>
              <div className="cr-footer__tag">Hyperlocal news \u2014 Chesterfield County, Virginia</div>
            </div>
          </div>
          <div className="cr-footer__cols">
            <div><h5>Beats</h5><a>Growth</a><a>Schools</a><a>Police</a><a>Government</a></div>
            <div><h5>The Report</h5><a>This Week</a><a>About</a><a>Tip line</a><a>Corrections</a></div>
            <div><h5>Follow</h5><a onClick={() => onNav('tip')}>Newsletter</a><a>RSS</a><a>Mastodon</a></div>
          </div>
        </div>
        <div className="cr-footer__legal">
          <span>\u00a9 2026 The Chesterfield Report \u00b7 Independent &amp; reader-funded</span>
          <span className="cr-footer__mono">build 26.06.10 \u00b7 all systems nominal</span>
        </div>
      </footer>
    );
  }

  window.CRShell = { Header, Footer, Ticker, Wordmark };
})();
