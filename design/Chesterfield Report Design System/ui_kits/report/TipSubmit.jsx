// Newsletter + tip submission view. -> window.CRTip
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const { Card, Button, Input, Select, Checkbox, Switch, Toast, Badge } = DS;
  const I = window.CRIcons;
  const { beats } = window.CR_DATA;

  function Tip() {
    const [sent, setSent] = React.useState(null); // 'tip' | 'sub'
    return (
      <div className="cr-tip">
        <div className="cr-tip__grid">
          {/* Tip line */}
          <Card bracket className="cr-tip__card cr-scanlines">
            <span className="cr-twrail__kicker">// Secure tip line</span>
            <h2 className="cr-tip__title">Saw something the county didn't announce?</h2>
            <p className="cr-tip__dek">Drop a tip. We read everything. Share contact details only if you want a reply \u2014 anonymous is fine.</p>
            <div className="cr-tip__form">
              <Input label="What's going on?" placeholder="A short headline for your tip" />
              <Select label="Which beat?" options={beats.filter((b) => b !== 'This Week')} />
              <Input label="Details" placeholder="Dates, places, names, documents\u2026" />
              <div className="cr-tip__row">
                <Input label="Email (optional)" type="email" placeholder="you@\u2026" icon={<I.Mail />} />
                <Checkbox label="Keep me anonymous" defaultChecked />
              </div>
              <Button variant="primary" iconRight={<I.Send />} onClick={() => setSent('tip')}>Send to the newsroom</Button>
            </div>
          </Card>

          {/* Newsletter */}
          <div className="cr-tip__col">
            <Card grad bracket className="cr-tip__nl">
              <Badge tone="teal" dot>Free \u00b7 Sundays 7am</Badge>
              <h2 className="cr-tip__title">This Week, in your inbox.</h2>
              <p className="cr-tip__dek">Every county decision from the past seven days, decoded in a five-minute read.</p>
              <div className="cr-tip__form">
                <Input label="Email" type="email" placeholder="you@chesterfield.com" icon={<I.Mail />} />
                <div className="cr-tip__prefs">
                  <Switch label="Breaking alerts (rare, real)" defaultChecked />
                  <Switch label="Weekend long reads" />
                </div>
                <Button variant="primary" block iconRight={<I.Arrow />} onClick={() => setSent('sub')}>Subscribe</Button>
                <div className="cr-tip__fine">No spam. Unsubscribe in one click. Reader-funded, ad-light.</div>
              </div>
            </Card>
          </div>
        </div>

        {sent ? (
          <div className="cr-tip__toast">
            <Toast tone={sent === 'tip' ? 'civic' : 'success'}
              title={sent === 'tip' ? 'Tip received \u2014 thank you' : 'You\u2019re on the list'}
              onClose={() => setSent(null)}>
              {sent === 'tip' ? 'A reporter will review it within 24 hours.' : 'Your first This Week digest lands Sunday at 7am.'}
            </Toast>
          </div>
        ) : null}
      </div>
    );
  }

  window.CRTip = { Tip };
})();
