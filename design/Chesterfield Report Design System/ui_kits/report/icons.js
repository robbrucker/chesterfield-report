// Inline stroke icons (Lucide-style, 2px round) for the UI kit. -> window.CRIcons
(function () {
  const React = window.React;
  const s = (paths, extra) => (props) => React.createElement('svg', Object.assign({
    viewBox:'0 0 24 24', fill:'none', stroke:'currentColor', strokeWidth:2,
    strokeLinecap:'round', strokeLinejoin:'round', width:'1em', height:'1em'
  }, extra, props), paths.map((d,i)=>React.createElement('path',{key:i,d})));
  const c = (cx,cy,r)=>({__c:[cx,cy,r]});
  const make = (children, extra) => (props) => React.createElement('svg', Object.assign({
    viewBox:'0 0 24 24', fill:'none', stroke:'currentColor', strokeWidth:2,
    strokeLinecap:'round', strokeLinejoin:'round', width:'1em', height:'1em'
  }, extra, props), children.map((ch,i)=> ch.__c
    ? React.createElement('circle',{key:i,cx:ch.__c[0],cy:ch.__c[1],r:ch.__c[2]})
    : React.createElement('path',{key:i,d:ch})));

  window.CRIcons = {
    Search: make([c(11,11,7),'m21 21-4.3-4.3']),
    Bell: make(['M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9','M10.3 21a1.94 1.94 0 0 0 3.4 0']),
    Menu: make(['M3 6h18','M3 12h18','M3 18h18']),
    Clock: make([c(12,12,9),'M12 7v5l3 2']),
    MapPin: make(['M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0',c(12,10,3)]),
    Arrow: make(['M5 12h14','m13 6 6 6-6 6']),
    ArrowUpRight: make(['M7 17 17 7','M7 7h10v10']),
    Share: make([c(18,5,3),c(6,12,3),c(18,19,3),'m8.6 13.5 6.8 4','m15.4 6.5-6.8 4']),
    Bookmark: make(['M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z']),
    Mail: make(['M3 5h18v14H3z','m3 7 9 6 9-6']),
    Send: make(['M22 2 11 13','M22 2 15 22l-4-9-9-4 20-7z']),
    Filter: make(['M22 3H2l8 9.5V19l4 2v-8.5z']),
    X: make(['M18 6 6 18','M6 6l12 12']),
    ChevronRight: make(['m9 6 6 6-6 6']),
    Sun: make([c(12,12,4),'M12 2v2','M12 20v2','m4.9 4.9 1.4 1.4','m17.7 17.7 1.4 1.4','M2 12h2','M20 12h2','m6.3 17.7-1.4 1.4','m19.1 4.9-1.4 1.4']),
    Eye: make(['M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z',c(12,12,3)]),
    Flame: make(['M12 2c1 4 4 5 4 9a4 4 0 0 1-8 0c0-1 .5-2 1-2.5C9 11 12 9 12 6c2 1 3 3 3 5']),
    Grid: make(['M3 3h7v7H3z','M14 3h7v7h-7z','M14 14h7v7h-7z','M3 14h7v7H3z']),
  };
})();
