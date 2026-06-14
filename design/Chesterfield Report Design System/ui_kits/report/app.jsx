// App router. -> window.CRApp
(function () {
  const React = window.React;
  const { Header, Footer, Ticker } = window.CRShell;
  const { Home } = window.CRHome;
  const { Week } = window.CRWeek;
  const { Article } = window.CRArticle;
  const { Topics } = window.CRTopics;
  const { Map } = window.CRMap;
  const { Tip } = window.CRTip;

  function App() {
    const [view, setView] = React.useState('home');
    const [beat, setBeat] = React.useState('This Week');
    const [story, setStory] = React.useState(null);
    const main = React.useRef(null);

    const go = (v) => {
      setView(v);
      if (main.current) main.current.scrollTop = 0;
    };
    const open = (s) => { setStory(s); go('article'); };
    const onBeat = (b) => {
      setBeat(b);
      go(b === 'This Week' ? 'thisweek' : 'topics');
    };

    let body;
    if (view === 'home') body = <Home onOpen={open} onNav={go} />;
    else if (view === 'thisweek') body = <Week onOpen={open} onNav={go} />;
    else if (view === 'article') body = <Article story={story} onOpen={open} onNav={go} />;
    else if (view === 'topics') body = <Topics onOpen={open} />;
    else if (view === 'map') body = <Map onOpen={open} />;
    else if (view === 'tip') body = <Tip />;

    return (
      <div className="cr-app">
        <Header view={view} beat={beat} onBeat={onBeat} onNav={go} onSearch={() => go('topics')} />
        <Ticker />
        <main className="cr-main" ref={main}>
          <div className="cr-main__inner">{body}</div>
          <Footer onNav={go} />
        </main>
      </div>
    );
  }

  window.CRApp = { App };
})();
