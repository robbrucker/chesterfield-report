// Mock content for The Chesterfield Report UI kit. Assigned to window.CR_DATA.
(function () {
  const PHOTO = {
    river: 'linear-gradient(160deg,#0a2f33 0%,#0e3b3a 35%,#15243b 100%)',
    civic: 'linear-gradient(160deg,#10222b 0%,#1a2f24 60%,#06141a 100%)',
    night: 'linear-gradient(160deg,#0c1430 0%,#1a1030 55%,#06141a 100%)',
    school:'linear-gradient(160deg,#0a2f33 0%,#102a1c 60%,#06141a 100%)',
    road:  'linear-gradient(160deg,#1a1224 0%,#2a1430 50%,#06141a 100%)',
    park:  'linear-gradient(160deg,#0a2a22 0%,#13351f 60%,#06141a 100%)',
  };

  const lead = {
    id: 'rezoning',
    beat: 'Government',
    tone: 'breaking',
    kicker: 'Board of Supervisors',
    title: 'Supervisors clear 220-acre riverfront rezoning on a 4\u20131 vote',
    dek: 'After three hours of public comment, the board approved mixed-use development along the Appomattox with a 40-foot floodplain setback. Opponents pledged a referendum.',
    time: '19:42',
    date: 'Jun 10, 2026',
    read: '6 min',
    photo: PHOTO.river,
    author: 'M. Okafor',
  };

  const stories = [
    { id:'stem', beat:'Schools', tone:'teal', kicker:'Cosby High', title:'New STEM wing breaks ground for fall 2027', dek:'A 40,000 sq ft lab block adds robotics, biotech and a fabrication shop.', time:'17:10', date:'Jun 10', read:'4 min', photo:PHOTO.school, author:'D. Reyes' },
    { id:'route10', beat:'Police', tone:'breaking', kicker:'Traffic', title:'Route 10 reopens after tanker crash near Chester', dek:'No injuries reported; VDOT cleared the spill by 8pm after a six-hour closure.', time:'20:05', date:'Jun 10', read:'2 min', photo:PHOTO.road, author:'Newsroom' },
    { id:'budget', beat:'Government', tone:'civic', kicker:'Explainer', title:'Where the county\u2019s $1.9B budget actually goes', dek:'Schools take 48 cents of every dollar. We break down the rest, line by line.', time:'08:00', date:'Jun 10', read:'9 min', photo:PHOTO.civic, author:'M. Okafor' },
    { id:'reservoir', beat:'Environment', tone:'eco', kicker:'Swift Creek', title:'Reservoir levels hit a five-year low after dry spring', dek:'Utilities ask residents to voluntarily cut outdoor watering through July.', time:'13:30', date:'Jun 9', read:'3 min', photo:PHOTO.park, author:'L. Tran' },
    { id:'market', beat:'Community', tone:'teal', kicker:'Midlothian', title:'Saturday market returns to the village with 60 vendors', dek:'Local growers, makers and three new food trucks line Coalfield Road.', time:'09:15', date:'Jun 9', read:'2 min', photo:PHOTO.civic, author:'A. Bell' },
    { id:'transit', beat:'Growth & Development', tone:'teal', kicker:'Hull Street', title:'Bus rapid transit study eyes the Hull Street corridor', dek:'Planners float dedicated lanes from the courthouse to the city line.', time:'11:45', date:'Jun 9', read:'5 min', photo:PHOTO.night, author:'D. Reyes' },
  ];

  const thisWeek = [
    { day:'MON', label:'Planning Commission', title:'Moseley mixed-use hearing', tone:'civic' },
    { day:'TUE', label:'Schools', title:'Calendar vote: later start times', tone:'teal' },
    { day:'WED', label:'Community', title:'Pocahontas Park night hike', tone:'eco' },
    { day:'THU', label:'Government', title:'Budget work session (final)', tone:'civic' },
    { day:'FRI', label:'Police', title:'Citizen academy graduation', tone:'breaking' },
  ];

  const beats = ['This Week','Growth & Development','Schools','Police','Government','Community','Opinion'];

  const mapPins = [
    { x:32, y:38, tone:'breaking', label:'Route 10 crash' },
    { x:54, y:30, tone:'civic',    label:'County complex' },
    { x:44, y:58, tone:'teal',     label:'Cosby High' },
    { x:24, y:64, tone:'eco',      label:'Swift Creek' },
    { x:66, y:48, tone:'teal',     label:'Midlothian market' },
    { x:60, y:70, tone:'eco',      label:'Pocahontas Park' },
  ];

  window.CR_DATA = { PHOTO, lead, stories, thisWeek, beats, mapPins };
})();
