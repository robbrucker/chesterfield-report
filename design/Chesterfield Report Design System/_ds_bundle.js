/* @ds-bundle: {"format":3,"namespace":"ChesterfieldReportDesignSystem_ad430c","components":[{"name":"Button","sourcePath":"components/buttons/Button.jsx"},{"name":"IconButton","sourcePath":"components/buttons/IconButton.jsx"},{"name":"StatReadout","sourcePath":"components/data/StatReadout.jsx"},{"name":"Toast","sourcePath":"components/feedback/Toast.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"Input","sourcePath":"components/forms/Input.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Switch","sourcePath":"components/forms/Switch.jsx"},{"name":"Badge","sourcePath":"components/labels/Badge.jsx"},{"name":"Tag","sourcePath":"components/labels/Tag.jsx"},{"name":"Tabs","sourcePath":"components/navigation/Tabs.jsx"},{"name":"Card","sourcePath":"components/surface/Card.jsx"}],"sourceHashes":{"components/buttons/Button.jsx":"6ad1eabd4a49","components/buttons/IconButton.jsx":"afb5a6baf8c0","components/data/StatReadout.jsx":"3317369a4546","components/feedback/Toast.jsx":"691b1e106fa0","components/forms/Checkbox.jsx":"55339b40dba6","components/forms/Input.jsx":"03f89122a745","components/forms/Select.jsx":"7dcc95e49ae9","components/forms/Switch.jsx":"2469b2dbd61d","components/labels/Badge.jsx":"98cf04d1cbbf","components/labels/Tag.jsx":"dee0024ec09d","components/navigation/Tabs.jsx":"16e43461b814","components/surface/Card.jsx":"89fe139f8888","ui_kits/report/Article.jsx":"2bd98e41c476","ui_kits/report/HomeFeed.jsx":"9198b04b9c6c","ui_kits/report/MapView.jsx":"2c4426ac682a","ui_kits/report/Shell.jsx":"0a64ca5b9f9d","ui_kits/report/ThisWeek.jsx":"6cc401b27328","ui_kits/report/TipSubmit.jsx":"1f53966ad372","ui_kits/report/TopicFilter.jsx":"80831e0b9e26","ui_kits/report/app.jsx":"20bde97d3dcb","ui_kits/report/data.js":"95863f8d31dd","ui_kits/report/icons.js":"a82c95ace1eb","ui_kits/report/parts.jsx":"44f030e1ddc5"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.ChesterfieldReportDesignSystem_ad430c = window.ChesterfieldReportDesignSystem_ad430c || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/buttons/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-button-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-btn {
    --_fg: var(--text-on-neon);
    display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2);
    font-family: var(--font-display); font-weight: var(--fw-semibold);
    letter-spacing: var(--ls-wide); line-height: 1; white-space: nowrap;
    border: var(--bw-1) solid transparent; border-radius: var(--radius-sm);
    cursor: pointer; text-decoration: none; position: relative;
    transition: var(--transition-base);
    -webkit-tap-highlight-color: transparent; user-select: none;
  }
  .cr-btn:focus-visible { outline: none; box-shadow: var(--ring); }
  .cr-btn:active { transform: translateY(1px); }
  .cr-btn[disabled], .cr-btn[aria-disabled="true"] {
    opacity: 0.4; cursor: not-allowed; pointer-events: none;
  }
  /* sizes */
  .cr-btn--sm { font-size: var(--fs-2xs); padding: 7px 12px; }
  .cr-btn--md { font-size: var(--fs-xs); padding: 10px 18px; }
  .cr-btn--lg { font-size: var(--fs-sm); padding: 14px 26px; }
  /* primary — neon teal fill */
  .cr-btn--primary { background: var(--neon-teal); color: var(--text-on-neon); border-color: var(--neon-teal); box-shadow: 0 0 0 1px rgba(34,245,212,.0), 0 0 18px rgba(34,245,212,.0); }
  .cr-btn--primary:hover { box-shadow: var(--glow-md-teal); }
  .cr-btn--primary:active { background: var(--neon-teal-dim); }
  /* secondary — ghost with neon edge */
  .cr-btn--secondary { background: transparent; color: var(--neon-teal); border-color: var(--ink-300); }
  .cr-btn--secondary:hover { border-color: var(--neon-teal); color: var(--text-strong); box-shadow: var(--glow-sm-teal); }
  /* ghost — bare */
  .cr-btn--ghost { background: transparent; color: var(--text-default); border-color: transparent; }
  .cr-btn--ghost:hover { background: var(--surface-well); color: var(--text-strong); }
  /* danger / breaking — magenta */
  .cr-btn--danger { background: transparent; color: var(--neon-magenta); border-color: var(--neon-magenta-dim); }
  .cr-btn--danger:hover { color: var(--text-strong); box-shadow: var(--glow-md-magenta); border-color: var(--neon-magenta); }
  /* civic — amber */
  .cr-btn--civic { background: transparent; color: var(--neon-amber); border-color: var(--neon-amber-dim); }
  .cr-btn--civic:hover { color: var(--text-strong); box-shadow: var(--glow-md-amber); border-color: var(--neon-amber); }
  .cr-btn--block { display: flex; width: 100%; }
  `;
  document.head.appendChild(el);
}

/**
 * Button — primary action control for The Chesterfield Report.
 */
function Button({
  children,
  variant = 'primary',
  size = 'md',
  block = false,
  iconLeft = null,
  iconRight = null,
  as = 'button',
  className = '',
  ...rest
}) {
  const Tag = as;
  const cls = ['cr-btn', `cr-btn--${variant}`, `cr-btn--${size}`, block ? 'cr-btn--block' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement(Tag, _extends({
    className: cls
  }, rest), iconLeft ? /*#__PURE__*/React.createElement("span", {
    className: "cr-btn__icon",
    "aria-hidden": "true"
  }, iconLeft) : null, /*#__PURE__*/React.createElement("span", null, children), iconRight ? /*#__PURE__*/React.createElement("span", {
    className: "cr-btn__icon",
    "aria-hidden": "true"
  }, iconRight) : null);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/buttons/Button.jsx", error: String((e && e.message) || e) }); }

// components/buttons/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-iconbutton-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-iconbtn {
    display: inline-flex; align-items: center; justify-content: center;
    border: var(--bw-1) solid var(--ink-400); background: var(--surface-raised);
    color: var(--text-default); border-radius: var(--radius-sm); cursor: pointer;
    transition: var(--transition-base); padding: 0;
  }
  .cr-iconbtn svg { width: 1.15em; height: 1.15em; }
  .cr-iconbtn:hover { color: var(--neon-teal); border-color: var(--neon-teal); box-shadow: var(--glow-sm-teal); }
  .cr-iconbtn:active { transform: translateY(1px); }
  .cr-iconbtn:focus-visible { outline: none; box-shadow: var(--ring); }
  .cr-iconbtn[disabled] { opacity: .4; cursor: not-allowed; }
  .cr-iconbtn--sm { width: 30px; height: 30px; font-size: 14px; }
  .cr-iconbtn--md { width: 38px; height: 38px; font-size: 16px; }
  .cr-iconbtn--lg { width: 46px; height: 46px; font-size: 19px; }
  .cr-iconbtn--ghost { background: transparent; border-color: transparent; }
  .cr-iconbtn--ghost:hover { background: var(--surface-well); }
  `;
  document.head.appendChild(el);
}

/**
 * IconButton — square icon-only control (toolbar, card actions, nav).
 */
function IconButton({
  children,
  label,
  size = 'md',
  variant = 'solid',
  className = '',
  ...rest
}) {
  const cls = ['cr-iconbtn', `cr-iconbtn--${size}`, variant === 'ghost' ? 'cr-iconbtn--ghost' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    className: cls,
    "aria-label": label,
    title: label
  }, rest), children);
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/buttons/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/data/StatReadout.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-statreadout-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-stat {
    display: flex; flex-direction: column; gap: 4px; padding: 14px 16px;
    background: var(--surface-card); border: var(--bw-1) solid var(--ink-400);
    border-radius: var(--radius-sm); position: relative; overflow: hidden; min-width: 120px;
  }
  .cr-stat::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 2px; background: var(--stat-accent, var(--neon-teal)); box-shadow: 0 0 10px var(--stat-accent, var(--neon-teal)); }
  .cr-stat__label { font: var(--fw-bold) var(--fs-3xs)/1 var(--font-mono); letter-spacing: var(--ls-wider); text-transform: uppercase; color: var(--text-muted); }
  .cr-stat__value { font: var(--fw-bold) var(--fs-2xl)/1 var(--font-mono); color: var(--stat-accent, var(--neon-teal)); font-variant-numeric: tabular-nums; text-shadow: 0 0 14px var(--stat-glow, var(--glow-teal)); }
  .cr-stat__delta { font-family: var(--font-mono); font-size: var(--fs-3xs); color: var(--text-faint); display: flex; align-items: center; gap: 4px; }
  .cr-stat__delta--up { color: var(--neon-lime); }
  .cr-stat__delta--down { color: var(--neon-magenta); }
  `;
  document.head.appendChild(el);
}
const STAT = {
  teal: ['var(--neon-teal)', 'var(--glow-teal)'],
  magenta: ['var(--neon-magenta)', 'var(--glow-magenta)'],
  amber: ['var(--neon-amber)', 'var(--glow-amber)'],
  lime: ['var(--neon-lime)', 'rgba(141,255,94,.4)']
};

/**
 * StatReadout — mono HUD data block (label, big value, optional delta).
 */
function StatReadout({
  label,
  value,
  delta,
  trend,
  tone = 'teal',
  className = '',
  ...rest
}) {
  const [c, g] = STAT[tone] || STAT.teal;
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ['cr-stat', className].filter(Boolean).join(' '),
    style: {
      '--stat-accent': c,
      '--stat-glow': g
    }
  }, rest), /*#__PURE__*/React.createElement("span", {
    className: "cr-stat__label"
  }, label), /*#__PURE__*/React.createElement("span", {
    className: "cr-stat__value"
  }, value), delta != null ? /*#__PURE__*/React.createElement("span", {
    className: ['cr-stat__delta', trend === 'up' ? 'cr-stat__delta--up' : trend === 'down' ? 'cr-stat__delta--down' : ''].filter(Boolean).join(' ')
  }, trend === 'up' ? '▲' : trend === 'down' ? '▼' : '·', " ", delta) : null);
}
Object.assign(__ds_scope, { StatReadout });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/StatReadout.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Toast.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-toast-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-toast {
    display: flex; align-items: flex-start; gap: 12px; max-width: 380px;
    background: var(--surface-raised); border: var(--bw-1) solid var(--ink-300);
    border-left: var(--bw-3) solid var(--toast-accent, var(--neon-teal));
    border-radius: var(--radius-sm); padding: 13px 14px; box-shadow: var(--shadow-lg);
    position: relative; overflow: hidden;
  }
  .cr-toast::before { content: ""; position: absolute; inset: 0; background: var(--tex-scanlines); opacity: .25; pointer-events: none; }
  .cr-toast__icon { color: var(--toast-accent, var(--neon-teal)); flex: none; display: flex; margin-top: 1px; }
  .cr-toast__icon svg { width: 18px; height: 18px; }
  .cr-toast__body { flex: 1; min-width: 0; }
  .cr-toast__title { font: var(--fw-semibold) var(--fs-sm)/1.3 var(--font-display); color: var(--text-strong); letter-spacing: var(--ls-wide); }
  .cr-toast__msg { font-size: var(--fs-2xs); color: var(--text-muted); margin-top: 3px; }
  .cr-toast__close { appearance: none; background: none; border: none; color: var(--text-faint); cursor: pointer; padding: 2px; display: flex; transition: color var(--dur-fast); }
  .cr-toast__close:hover { color: var(--neon-magenta); }
  .cr-toast__close svg { width: 14px; height: 14px; }
  `;
  document.head.appendChild(el);
}
const TOAST_ACCENT = {
  info: 'var(--neon-teal)',
  success: 'var(--neon-lime)',
  breaking: 'var(--neon-magenta)',
  civic: 'var(--neon-amber)'
};
const ICONS = {
  info: /*#__PURE__*/React.createElement("path", {
    d: "M12 16v-5M12 8h.01M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z"
  }),
  success: /*#__PURE__*/React.createElement("path", {
    d: "M22 11.1V12a10 10 0 1 1-5.9-9.1M22 4 12 14.01l-3-3"
  }),
  breaking: /*#__PURE__*/React.createElement("path", {
    d: "M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"
  }),
  civic: /*#__PURE__*/React.createElement("path", {
    d: "M3 21h18M5 21V8l7-5 7 5v13M9 21v-6h6v6"
  })
};

/**
 * Toast — transient notification. Pulls accent + icon from tone.
 */
function Toast({
  title,
  children,
  tone = 'info',
  onClose,
  className = '',
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ['cr-toast', className].filter(Boolean).join(' '),
    style: {
      '--toast-accent': TOAST_ACCENT[tone] || TOAST_ACCENT.info
    },
    role: "status"
  }, rest), /*#__PURE__*/React.createElement("span", {
    className: "cr-toast__icon",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, ICONS[tone] || ICONS.info)), /*#__PURE__*/React.createElement("div", {
    className: "cr-toast__body"
  }, title ? /*#__PURE__*/React.createElement("div", {
    className: "cr-toast__title"
  }, title) : null, children ? /*#__PURE__*/React.createElement("div", {
    className: "cr-toast__msg"
  }, children) : null), onClose ? /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "cr-toast__close",
    "aria-label": "Dismiss",
    onClick: onClose
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2.5",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M18 6 6 18M6 6l12 12"
  }))) : null);
}
Object.assign(__ds_scope, { Toast });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Toast.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-checkbox-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-check { display: inline-flex; align-items: center; gap: 10px; cursor: pointer; user-select: none; font-size: var(--fs-sm); color: var(--text-default); }
  .cr-check input { position: absolute; opacity: 0; width: 0; height: 0; }
  .cr-check__box {
    width: 18px; height: 18px; flex: none; border: var(--bw-1) solid var(--ink-300);
    border-radius: var(--radius-xs); background: var(--surface-raised);
    display: grid; place-items: center; transition: var(--transition-base);
  }
  .cr-check__box svg { width: 12px; height: 12px; opacity: 0; transform: scale(.5); transition: var(--transition-base); color: var(--text-on-neon); }
  .cr-check:hover .cr-check__box { border-color: var(--neon-teal); }
  .cr-check input:checked + .cr-check__box { background: var(--neon-teal); border-color: var(--neon-teal); box-shadow: var(--glow-sm-teal); }
  .cr-check input:checked + .cr-check__box svg { opacity: 1; transform: scale(1); }
  .cr-check input:focus-visible + .cr-check__box { box-shadow: var(--ring); }
  .cr-check input:disabled ~ * { opacity: .45; }
  `;
  document.head.appendChild(el);
}

/**
 * Checkbox — boolean toggle with label.
 */
function Checkbox({
  label,
  id,
  className = '',
  ...rest
}) {
  const fieldId = id || (label ? 'cr-cb-' + String(label).toLowerCase().replace(/\s+/g, '-') : undefined);
  return /*#__PURE__*/React.createElement("label", {
    className: ['cr-check', className].filter(Boolean).join(' '),
    htmlFor: fieldId
  }, /*#__PURE__*/React.createElement("input", _extends({
    type: "checkbox",
    id: fieldId
  }, rest)), /*#__PURE__*/React.createElement("span", {
    className: "cr-check__box",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "3.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M20 6 9 17l-5-5"
  }))), label ? /*#__PURE__*/React.createElement("span", null, label) : null);
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/Input.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-input-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-field { display: flex; flex-direction: column; gap: 6px; }
  .cr-field__label { font: var(--fw-bold) var(--fs-3xs)/1 var(--font-mono); letter-spacing: var(--ls-wider); text-transform: uppercase; color: var(--text-muted); }
  .cr-input-wrap { position: relative; display: flex; align-items: center; }
  .cr-input-wrap__icon { position: absolute; left: 12px; color: var(--text-muted); display: flex; pointer-events: none; }
  .cr-input-wrap__icon svg { width: 16px; height: 16px; }
  .cr-input {
    width: 100%; font: var(--text-body-r); font-size: var(--fs-sm); color: var(--text-strong);
    background: var(--surface-raised); border: var(--bw-1) solid var(--ink-400);
    border-radius: var(--radius-sm); padding: 11px 13px; transition: var(--transition-base);
  }
  .cr-input--has-icon { padding-left: 36px; }
  .cr-input::placeholder { color: var(--text-faint); }
  .cr-input:hover { border-color: var(--ink-300); }
  .cr-input:focus { outline: none; border-color: var(--neon-teal); box-shadow: var(--glow-sm-teal); background: var(--ink-700); }
  .cr-input[aria-invalid="true"] { border-color: var(--neon-magenta); }
  .cr-input[aria-invalid="true"]:focus { box-shadow: var(--glow-md-magenta); }
  .cr-input:disabled { opacity: .5; cursor: not-allowed; }
  .cr-field__hint { font-size: var(--fs-2xs); color: var(--text-faint); }
  .cr-field__hint--error { color: var(--neon-magenta); }
  `;
  document.head.appendChild(el);
}

/**
 * Input — single-line text field with optional label, leading icon and hint.
 */
function Input({
  label,
  hint,
  error,
  icon = null,
  id,
  className = '',
  ...rest
}) {
  const fieldId = id || (label ? 'cr-' + label.toLowerCase().replace(/\s+/g, '-') : undefined);
  return /*#__PURE__*/React.createElement("div", {
    className: "cr-field"
  }, label ? /*#__PURE__*/React.createElement("label", {
    className: "cr-field__label",
    htmlFor: fieldId
  }, label) : null, /*#__PURE__*/React.createElement("div", {
    className: "cr-input-wrap"
  }, icon ? /*#__PURE__*/React.createElement("span", {
    className: "cr-input-wrap__icon"
  }, icon) : null, /*#__PURE__*/React.createElement("input", _extends({
    id: fieldId,
    className: ['cr-input', icon ? 'cr-input--has-icon' : '', className].filter(Boolean).join(' '),
    "aria-invalid": error ? 'true' : undefined
  }, rest))), error ? /*#__PURE__*/React.createElement("span", {
    className: "cr-field__hint cr-field__hint--error"
  }, error) : hint ? /*#__PURE__*/React.createElement("span", {
    className: "cr-field__hint"
  }, hint) : null);
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Input.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-select-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-select-wrap { position: relative; display: flex; flex-direction: column; gap: 6px; }
  .cr-select-wrap__inner { position: relative; display: flex; align-items: center; }
  .cr-select {
    appearance: none; width: 100%; font: var(--text-body-r); font-size: var(--fs-sm);
    color: var(--text-strong); background: var(--surface-raised);
    border: var(--bw-1) solid var(--ink-400); border-radius: var(--radius-sm);
    padding: 11px 36px 11px 13px; cursor: pointer; transition: var(--transition-base);
  }
  .cr-select:hover { border-color: var(--ink-300); }
  .cr-select:focus { outline: none; border-color: var(--neon-teal); box-shadow: var(--glow-sm-teal); }
  .cr-select:disabled { opacity: .5; cursor: not-allowed; }
  .cr-select-wrap__chevron { position: absolute; right: 12px; pointer-events: none; color: var(--neon-teal); display: flex; }
  .cr-select-wrap__chevron svg { width: 14px; height: 14px; }
  .cr-select option { background: var(--ink-700); color: var(--text-strong); }
  `;
  document.head.appendChild(el);
}

/**
 * Select — native dropdown styled for the dark HUD surface.
 */
function Select({
  label,
  options = [],
  id,
  className = '',
  children,
  ...rest
}) {
  const fieldId = id || (label ? 'cr-sel-' + label.toLowerCase().replace(/\s+/g, '-') : undefined);
  return /*#__PURE__*/React.createElement("div", {
    className: "cr-select-wrap"
  }, label ? /*#__PURE__*/React.createElement("label", {
    className: "cr-field__label",
    htmlFor: fieldId
  }, label) : null, /*#__PURE__*/React.createElement("div", {
    className: "cr-select-wrap__inner"
  }, /*#__PURE__*/React.createElement("select", _extends({
    id: fieldId,
    className: ['cr-select', className].filter(Boolean).join(' ')
  }, rest), children || options.map(o => {
    const val = typeof o === 'string' ? o : o.value;
    const lbl = typeof o === 'string' ? o : o.label;
    return /*#__PURE__*/React.createElement("option", {
      key: val,
      value: val
    }, lbl);
  })), /*#__PURE__*/React.createElement("span", {
    className: "cr-select-wrap__chevron",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "m6 9 6 6 6-6"
  })))));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Switch.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-switch-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-switch { display: inline-flex; align-items: center; gap: 10px; cursor: pointer; user-select: none; font-size: var(--fs-sm); color: var(--text-default); }
  .cr-switch input { position: absolute; opacity: 0; width: 0; height: 0; }
  .cr-switch__track {
    width: 40px; height: 22px; flex: none; border-radius: var(--radius-pill);
    background: var(--ink-500); border: var(--bw-1) solid var(--ink-300);
    position: relative; transition: var(--transition-base);
  }
  .cr-switch__thumb {
    position: absolute; top: 2px; left: 2px; width: 16px; height: 16px;
    border-radius: 50%; background: var(--fog); transition: var(--transition-base);
  }
  .cr-switch:hover .cr-switch__track { border-color: var(--neon-teal); }
  .cr-switch input:checked + .cr-switch__track { background: var(--neon-teal); border-color: var(--neon-teal); box-shadow: var(--glow-sm-teal); }
  .cr-switch input:checked + .cr-switch__track .cr-switch__thumb { transform: translateX(18px); background: var(--text-on-neon); }
  .cr-switch input:focus-visible + .cr-switch__track { box-shadow: var(--ring); }
  .cr-switch input:disabled ~ * { opacity: .45; }
  `;
  document.head.appendChild(el);
}

/**
 * Switch — on/off toggle for settings and live filters.
 */
function Switch({
  label,
  id,
  className = '',
  ...rest
}) {
  const fieldId = id || (label ? 'cr-sw-' + String(label).toLowerCase().replace(/\s+/g, '-') : undefined);
  return /*#__PURE__*/React.createElement("label", {
    className: ['cr-switch', className].filter(Boolean).join(' '),
    htmlFor: fieldId
  }, /*#__PURE__*/React.createElement("input", _extends({
    type: "checkbox",
    role: "switch",
    id: fieldId
  }, rest)), /*#__PURE__*/React.createElement("span", {
    className: "cr-switch__track",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("span", {
    className: "cr-switch__thumb"
  })), label ? /*#__PURE__*/React.createElement("span", null, label) : null);
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Switch.jsx", error: String((e && e.message) || e) }); }

// components/labels/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-badge-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-badge {
    display: inline-flex; align-items: center; gap: 6px;
    font: var(--fw-bold) var(--fs-3xs)/1 var(--font-mono); letter-spacing: var(--ls-wider);
    text-transform: uppercase; padding: 5px 9px; border-radius: var(--radius-xs);
    border: var(--bw-1) solid transparent; white-space: nowrap;
  }
  .cr-badge--solid { background: var(--neon-teal); color: var(--text-on-neon); }
  .cr-badge--teal   { color: var(--neon-teal);   border-color: rgba(34,245,212,.4);  background: var(--teal-wash); }
  .cr-badge--breaking { color: var(--neon-magenta); border-color: rgba(255,46,136,.5); background: var(--magenta-wash); }
  .cr-badge--civic  { color: var(--neon-amber);  border-color: rgba(255,210,63,.45); background: var(--amber-wash); }
  .cr-badge--eco    { color: var(--neon-lime);   border-color: rgba(141,255,94,.4);  background: rgba(141,255,94,.08); }
  .cr-badge--neutral{ color: var(--text-muted);  border-color: var(--ink-400);       background: var(--surface-raised); }
  .cr-badge__dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
  .cr-badge--live .cr-badge__dot { animation: cr-pulse 1.4s var(--ease-in-out) infinite; }
  @keyframes cr-pulse { 0%,100% { opacity: 1; } 50% { opacity: .25; } }
  `;
  document.head.appendChild(el);
}

/**
 * Badge — compact status / category label (breaking, live, civic, beat tag).
 */
function Badge({
  children,
  tone = 'teal',
  dot = false,
  live = false,
  className = '',
  ...rest
}) {
  const cls = ['cr-badge', `cr-badge--${tone}`, live ? 'cr-badge--live' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("span", _extends({
    className: cls
  }, rest), dot || live ? /*#__PURE__*/React.createElement("span", {
    className: "cr-badge__dot",
    "aria-hidden": "true"
  }) : null, children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/labels/Badge.jsx", error: String((e && e.message) || e) }); }

// components/labels/Tag.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-tag-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-tag {
    display: inline-flex; align-items: center; gap: 7px; cursor: pointer;
    font-family: var(--font-mono); font-size: var(--fs-2xs); letter-spacing: var(--ls-wide);
    color: var(--text-default); background: var(--surface-raised);
    border: var(--bw-1) solid var(--ink-400); border-radius: var(--radius-pill);
    padding: 6px 13px; transition: var(--transition-base); user-select: none;
  }
  .cr-tag:hover { border-color: var(--neon-teal); color: var(--text-strong); }
  .cr-tag--active { background: var(--teal-wash); border-color: var(--neon-teal); color: var(--neon-teal); box-shadow: var(--glow-sm-teal); }
  .cr-tag__hash { color: var(--neon-teal); opacity: .8; }
  .cr-tag__x { display: inline-flex; opacity: .6; }
  .cr-tag__x:hover { opacity: 1; color: var(--neon-magenta); }
  .cr-tag__x svg { width: 12px; height: 12px; }
  .cr-tag:focus-visible { outline: none; box-shadow: var(--ring); }
  `;
  document.head.appendChild(el);
}

/**
 * Tag — topic / filter chip. Use for selectable beats and removable filters.
 */
function Tag({
  children,
  active = false,
  hash = true,
  onRemove,
  className = '',
  ...rest
}) {
  const cls = ['cr-tag', active ? 'cr-tag--active' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    className: cls,
    "aria-pressed": active
  }, rest), hash ? /*#__PURE__*/React.createElement("span", {
    className: "cr-tag__hash",
    "aria-hidden": "true"
  }, "#") : null, children, onRemove ? /*#__PURE__*/React.createElement("span", {
    className: "cr-tag__x",
    role: "button",
    "aria-label": "Remove",
    onClick: e => {
      e.stopPropagation();
      onRemove(e);
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2.5",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M18 6 6 18M6 6l12 12"
  }))) : null);
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/labels/Tag.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Tabs.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-tabs-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-tabs { display: flex; gap: 2px; border-bottom: var(--bw-1) solid var(--ink-400); }
  .cr-tab {
    appearance: none; background: none; border: none; cursor: pointer;
    font-family: var(--font-display); font-weight: var(--fw-semibold); font-size: var(--fs-sm);
    letter-spacing: var(--ls-wide); color: var(--text-muted); padding: 12px 16px;
    position: relative; transition: var(--transition-base); white-space: nowrap;
  }
  .cr-tab::after {
    content: ""; position: absolute; left: 12px; right: 12px; bottom: -1px; height: 2px;
    background: var(--neon-teal); transform: scaleX(0); transform-origin: left;
    transition: transform var(--dur-base) var(--ease-out); box-shadow: 0 0 10px var(--glow-teal);
  }
  .cr-tab:hover { color: var(--text-strong); }
  .cr-tab[aria-selected="true"] { color: var(--neon-teal); }
  .cr-tab[aria-selected="true"]::after { transform: scaleX(1); }
  .cr-tab:focus-visible { outline: none; box-shadow: var(--ring); border-radius: var(--radius-xs); }
  .cr-tab__count { font-family: var(--font-mono); font-size: var(--fs-3xs); margin-left: 6px; opacity: .7; }
  `;
  document.head.appendChild(el);
}

/**
 * Tabs — section navigation with an animated neon underline.
 */
function Tabs({
  items = [],
  value,
  onChange,
  className = '',
  ...rest
}) {
  const active = value != null ? value : items[0] && (items[0].value ?? items[0]);
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ['cr-tabs', className].filter(Boolean).join(' '),
    role: "tablist"
  }, rest), items.map(it => {
    const val = typeof it === 'string' ? it : it.value;
    const lbl = typeof it === 'string' ? it : it.label;
    const count = typeof it === 'object' ? it.count : undefined;
    return /*#__PURE__*/React.createElement("button", {
      key: val,
      role: "tab",
      type: "button",
      "aria-selected": val === active,
      className: "cr-tab",
      onClick: () => onChange && onChange(val)
    }, lbl, count != null ? /*#__PURE__*/React.createElement("span", {
      className: "cr-tab__count"
    }, count) : null);
  }));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Tabs.jsx", error: String((e && e.message) || e) }); }

// components/surface/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const STYLE_ID = 'cr-card-styles';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const el = document.createElement('style');
  el.id = STYLE_ID;
  el.textContent = `
  .cr-card {
    position: relative; background: var(--surface-card);
    border: var(--bw-1) solid var(--ink-400); border-radius: var(--radius-card);
    transition: var(--transition-base); overflow: hidden;
  }
  .cr-card--pad { padding: var(--space-5); }
  .cr-card--grad::before {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background: var(--grad-panel); opacity: .8;
  }
  /* top accent bar */
  .cr-card--accent { border-top: var(--bw-3) solid var(--accent-color, var(--neon-teal)); }
  .cr-card--interactive { cursor: pointer; }
  .cr-card--interactive:hover {
    border-color: var(--accent-color, var(--neon-teal));
    box-shadow: var(--shadow-lg), 0 0 22px rgba(34,245,212,.12);
    transform: translateY(-2px);
  }
  .cr-card--interactive:active { transform: translateY(0); }
  .cr-card > * { position: relative; }
  /* corner bracket flourish */
  .cr-card--bracket::after {
    content: ""; position: absolute; top: 8px; right: 8px; width: 12px; height: 12px;
    border-top: 1px solid var(--neon-teal); border-right: 1px solid var(--neon-teal);
    opacity: .5; pointer-events: none;
  }
  `;
  document.head.appendChild(el);
}
const TONE_COLOR = {
  teal: 'var(--neon-teal)',
  breaking: 'var(--neon-magenta)',
  civic: 'var(--neon-amber)',
  eco: 'var(--river-green)'
};

/**
 * Card — base surface panel. Compose article cards, digests and HUD panels.
 */
function Card({
  children,
  pad = true,
  accent = false,
  tone = 'teal',
  interactive = false,
  grad = false,
  bracket = false,
  className = '',
  style = {},
  ...rest
}) {
  const cls = ['cr-card', pad ? 'cr-card--pad' : '', accent ? 'cr-card--accent' : '', interactive ? 'cr-card--interactive' : '', grad ? 'cr-card--grad' : '', bracket ? 'cr-card--bracket' : '', className].filter(Boolean).join(' ');
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls,
    style: {
      '--accent-color': TONE_COLOR[tone] || TONE_COLOR.teal,
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/surface/Card.jsx", error: String((e && e.message) || e) }); }

// ui_kits/report/Article.jsx
try { (() => {
// Single article view. -> window.CRArticle
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const {
    Card,
    Badge,
    Button,
    IconButton,
    Tag,
    StatReadout
  } = DS;
  const {
    PhotoFrame,
    MetaRow,
    StoryCard,
    SectionHead
  } = window.CRParts;
  const I = window.CRIcons;
  const {
    stories
  } = window.CR_DATA;
  const BODY = ['After three hours of public comment, the Chesterfield County Board of Supervisors voted 4\u20131 Wednesday night to approve a mixed-use rezoning of 220 acres along the Appomattox River, clearing the way for what developers call a \u201criverfront district\u201d of housing, retail and a public greenway.', 'The approval carries a 40-foot setback from the regulatory floodplain and requires the developer to fund a pedestrian bridge connecting the site to the existing trail network. Supervisor Lena Hargrove cast the lone dissenting vote, citing traffic on Route 10.', 'Opponents, organized as Keep the Appomattox Wild, pledged within minutes to gather signatures for a referendum. \u201cThis isn\u2019t over,\u201d said spokesperson Dale Whitford. \u201cThe county just traded a floodplain for a tax base.\u201d', 'County planners estimate the project will generate $3.2 million in annual tax revenue at build-out, projected for 2031. Construction on the first phase \u2014 320 townhomes \u2014 could begin as early as next spring.'];
  function Article({
    story,
    onOpen,
    onNav
  }) {
    const s = story || stories[0];
    const related = stories.filter(x => x.id !== s.id).slice(0, 3);
    return /*#__PURE__*/React.createElement("article", {
      className: "cr-article"
    }, /*#__PURE__*/React.createElement("button", {
      className: "cr-article__back",
      onClick: () => onNav('home')
    }, /*#__PURE__*/React.createElement(I.Arrow, {
      style: {
        transform: 'rotate(180deg)'
      }
    }), " All stories"), /*#__PURE__*/React.createElement("div", {
      className: "cr-article__head"
    }, /*#__PURE__*/React.createElement(Badge, {
      tone: s.tone,
      dot: s.tone === 'breaking'
    }, s.beat, " \\u00b7 ", s.kicker), /*#__PURE__*/React.createElement("h1", {
      className: "cr-article__title"
    }, s.title), /*#__PURE__*/React.createElement("p", {
      className: "cr-article__dek"
    }, s.dek), /*#__PURE__*/React.createElement("div", {
      className: "cr-article__byline"
    }, /*#__PURE__*/React.createElement(MetaRow, {
      time: s.time,
      date: s.date,
      read: s.read,
      author: s.author
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-article__tools"
    }, /*#__PURE__*/React.createElement(IconButton, {
      label: "Save",
      variant: "ghost"
    }, /*#__PURE__*/React.createElement(I.Bookmark, null)), /*#__PURE__*/React.createElement(IconButton, {
      label: "Share",
      variant: "ghost"
    }, /*#__PURE__*/React.createElement(I.Share, null)), /*#__PURE__*/React.createElement(Button, {
      variant: "civic",
      size: "sm",
      iconLeft: /*#__PURE__*/React.createElement(I.Eye, null)
    }, "Follow this story")))), /*#__PURE__*/React.createElement(PhotoFrame, {
      photo: s.photo,
      ratio: "21 / 9",
      label: "PHOTO \\u00b7 STAFF",
      className: "cr-article__photo"
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-article__layout"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-article__body"
    }, BODY.map((p, i) => /*#__PURE__*/React.createElement("p", {
      key: i,
      className: i === 0 ? 'cr-article__lead' : ''
    }, p)), /*#__PURE__*/React.createElement("div", {
      className: "cr-article__tags"
    }, ['Zoning', 'Appomattox River', 'Board of Supervisors', 'Route 10'].map(t => /*#__PURE__*/React.createElement(Tag, {
      key: t
    }, t)))), /*#__PURE__*/React.createElement("aside", {
      className: "cr-article__aside"
    }, /*#__PURE__*/React.createElement(Card, {
      grad: true,
      bracket: true,
      className: "cr-article__pull"
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-twrail__kicker"
    }, "// The vote"), /*#__PURE__*/React.createElement(StatReadout, {
      label: "Supervisors for",
      value: "4",
      tone: "lime"
    }), /*#__PURE__*/React.createElement(StatReadout, {
      label: "Against",
      value: "1",
      tone: "magenta"
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-article__pullnote"
    }, "Roll call recorded 19:42, Jun 10.")))), /*#__PURE__*/React.createElement(SectionHead, {
      kicker: "// Keep reading",
      title: "More from the county"
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-article__related"
    }, related.map(r => /*#__PURE__*/React.createElement(StoryCard, {
      key: r.id,
      story: r,
      size: "sm",
      onOpen: onOpen
    }))));
  }
  window.CRArticle = {
    Article
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/Article.jsx", error: String((e && e.message) || e) }); }

// ui_kits/report/HomeFeed.jsx
try { (() => {
// Home feed view. -> window.CRHome
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const {
    Card,
    Badge,
    Button,
    StatReadout,
    Tag
  } = DS;
  const {
    StoryCard,
    ListRow,
    SectionHead,
    MetaRow,
    PhotoFrame
  } = window.CRParts;
  const I = window.CRIcons;
  const {
    lead,
    stories,
    thisWeek
  } = window.CR_DATA;
  function HeroLead({
    onOpen
  }) {
    return /*#__PURE__*/React.createElement(Card, {
      interactive: true,
      accent: true,
      tone: "breaking",
      bracket: true,
      pad: false,
      className: "cr-hero",
      onClick: () => onOpen(lead)
    }, /*#__PURE__*/React.createElement(PhotoFrame, {
      photo: lead.photo,
      ratio: "21 / 9",
      label: "PHOTO \\u00b7 APPOMATTOX RIVERFRONT"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-hero__overlay"
    }, /*#__PURE__*/React.createElement(Badge, {
      tone: "breaking",
      dot: true
    }, "Breaking \\u00b7 ", lead.kicker), /*#__PURE__*/React.createElement("h1", {
      className: "cr-hero__title"
    }, lead.title), /*#__PURE__*/React.createElement("p", {
      className: "cr-hero__dek"
    }, lead.dek), /*#__PURE__*/React.createElement(MetaRow, {
      time: lead.time,
      date: lead.date,
      read: lead.read,
      author: lead.author
    }))));
  }
  function ThisWeekRail({
    onNav
  }) {
    return /*#__PURE__*/React.createElement(Card, {
      grad: true,
      className: "cr-twrail",
      pad: false
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-twrail__head"
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-twrail__kicker"
    }, "// This Week in Chesterfield"), /*#__PURE__*/React.createElement("button", {
      className: "cr-twrail__all",
      onClick: () => onNav('thisweek')
    }, "Full digest ", /*#__PURE__*/React.createElement(I.ArrowUpRight, null))), /*#__PURE__*/React.createElement("ul", {
      className: "cr-twrail__list"
    }, thisWeek.map((d, i) => /*#__PURE__*/React.createElement("li", {
      key: i,
      className: "cr-twrail__item"
    }, /*#__PURE__*/React.createElement("span", {
      className: 'cr-twrail__day cr-twrail__day--' + d.tone
    }, d.day), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      className: "cr-twrail__label"
    }, d.label), /*#__PURE__*/React.createElement("div", {
      className: "cr-twrail__title"
    }, d.title))))));
  }
  function Newsletter({
    onNav
  }) {
    return /*#__PURE__*/React.createElement(Card, {
      grad: true,
      bracket: true,
      className: "cr-nl"
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-nl__kicker"
    }, "// Sunday 7am"), /*#__PURE__*/React.createElement("h3", {
      className: "cr-nl__title"
    }, "The week, decoded."), /*#__PURE__*/React.createElement("p", {
      className: "cr-nl__dek"
    }, "One email. Every decision the county made, in plain language."), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      size: "sm",
      block: true,
      iconRight: /*#__PURE__*/React.createElement(I.Send, null),
      onClick: () => onNav('tip')
    }, "Get This Week"));
  }
  function Home({
    onOpen,
    onNav
  }) {
    const grid = stories.slice(0, 4);
    const list = stories.slice(2);
    return /*#__PURE__*/React.createElement("div", {
      className: "cr-home"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-home__main"
    }, /*#__PURE__*/React.createElement(HeroLead, {
      onOpen: onOpen
    }), /*#__PURE__*/React.createElement(SectionHead, {
      kicker: "// The feed",
      title: "Across the county",
      action: /*#__PURE__*/React.createElement(Button, {
        variant: "secondary",
        size: "sm",
        iconRight: /*#__PURE__*/React.createElement(I.Arrow, null),
        onClick: () => onNav('topics')
      }, "Filter beats")
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-home__grid"
    }, grid.map(s => /*#__PURE__*/React.createElement(StoryCard, {
      key: s.id,
      story: s,
      onOpen: onOpen
    }))), /*#__PURE__*/React.createElement(SectionHead, {
      kicker: "// Latest",
      title: "As it files in"
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-home__list"
    }, list.map(s => /*#__PURE__*/React.createElement(ListRow, {
      key: s.id,
      story: s,
      onOpen: onOpen
    })))), /*#__PURE__*/React.createElement("aside", {
      className: "cr-home__side"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-home__stats"
    }, /*#__PURE__*/React.createElement(StatReadout, {
      label: "Stories this week",
      value: "47",
      delta: "+12",
      trend: "up"
    }), /*#__PURE__*/React.createElement(StatReadout, {
      label: "Board votes tracked",
      value: "216",
      tone: "amber",
      delta: "3 pending",
      trend: "flat"
    })), /*#__PURE__*/React.createElement(ThisWeekRail, {
      onNav: onNav
    }), /*#__PURE__*/React.createElement(Newsletter, {
      onNav: onNav
    }), /*#__PURE__*/React.createElement(Card, {
      className: "cr-trend",
      grad: true
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-twrail__kicker"
    }, "// Trending tags"), /*#__PURE__*/React.createElement("div", {
      className: "cr-trend__tags"
    }, ['Zoning', 'Route 10', 'School calendar', 'Swift Creek', 'Budget', 'Midlothian'].map(t => /*#__PURE__*/React.createElement(Tag, {
      key: t,
      onClick: () => onNav('topics')
    }, t))))));
  }
  window.CRHome = {
    Home
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/HomeFeed.jsx", error: String((e && e.message) || e) }); }

// ui_kits/report/MapView.jsx
try { (() => {
// Map / radar view. -> window.CRMap
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const {
    Card,
    Badge,
    StatReadout
  } = DS;
  const {
    SectionHead
  } = window.CRParts;
  const I = window.CRIcons;
  const {
    mapPins
  } = window.CR_DATA;
  const TONE_VAR = {
    breaking: 'var(--neon-magenta)',
    civic: 'var(--neon-amber)',
    teal: 'var(--neon-teal)',
    eco: 'var(--neon-lime)'
  };
  function Map({
    onOpen
  }) {
    const [sel, setSel] = React.useState(null);
    return /*#__PURE__*/React.createElement("div", {
      className: "cr-map"
    }, /*#__PURE__*/React.createElement(SectionHead, {
      kicker: "// Live county map",
      title: "What's happening, where",
      action: /*#__PURE__*/React.createElement(Badge, {
        tone: "teal",
        live: true
      }, "Realtime")
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-map__grid"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-mapcanvas cr-scanlines"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-mapcanvas__county"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-mapcanvas__sweep"
    }), mapPins.map((p, i) => /*#__PURE__*/React.createElement("button", {
      key: i,
      className: 'cr-pin' + (sel === i ? ' cr-pin--active' : ''),
      style: {
        left: p.x + '%',
        top: p.y + '%',
        '--pin': TONE_VAR[p.tone]
      },
      onClick: () => setSel(i),
      "aria-label": p.label
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-pin__dot"
    }), /*#__PURE__*/React.createElement("span", {
      className: "cr-pin__ring"
    }), /*#__PURE__*/React.createElement("span", {
      className: "cr-pin__label"
    }, p.label)))), /*#__PURE__*/React.createElement("div", {
      className: "cr-mapcanvas__readout"
    }, /*#__PURE__*/React.createElement("span", null, "CHESTERFIELD CO. \\u00b7 VA"), /*#__PURE__*/React.createElement("span", null, "37.3771\\u00b0 N \\u00b7 77.5089\\u00b0 W"), /*#__PURE__*/React.createElement("span", null, mapPins.length, " ACTIVE PINGS"))), /*#__PURE__*/React.createElement("aside", {
      className: "cr-map__side"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-map__stats"
    }, /*#__PURE__*/React.createElement(StatReadout, {
      label: "Active incidents",
      value: "2",
      tone: "magenta"
    }), /*#__PURE__*/React.createElement(StatReadout, {
      label: "Civic events",
      value: "3",
      tone: "amber"
    })), /*#__PURE__*/React.createElement(Card, {
      grad: true,
      className: "cr-map__legend",
      pad: false
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-map__legendhead"
    }, "// Pings"), /*#__PURE__*/React.createElement("ul", null, mapPins.map((p, i) => /*#__PURE__*/React.createElement("li", {
      key: i,
      className: sel === i ? 'is-sel' : '',
      onClick: () => setSel(i)
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-map__swatch",
      style: {
        background: TONE_VAR[p.tone]
      }
    }), /*#__PURE__*/React.createElement("span", {
      className: "cr-map__legendlabel"
    }, p.label), /*#__PURE__*/React.createElement(I.ChevronRight, null))))))));
  }
  window.CRMap = {
    Map
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/MapView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/report/Shell.jsx
try { (() => {
// Shell: header, breaking ticker, footer. -> window.CRShell
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const {
    Button,
    IconButton,
    Tabs,
    Badge
  } = DS;
  const I = window.CRIcons;
  const {
    beats
  } = window.CR_DATA;
  function Wordmark({
    onClick
  }) {
    return /*#__PURE__*/React.createElement("button", {
      className: "cr-wm",
      onClick: onClick,
      "aria-label": "The Chesterfield Report home"
    }, /*#__PURE__*/React.createElement("img", {
      src: "../../assets/logo-mark.svg",
      alt: "",
      className: "cr-wm__mark"
    }), /*#__PURE__*/React.createElement("span", {
      className: "cr-wm__text"
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-wm__top"
    }, "The"), /*#__PURE__*/React.createElement("span", {
      className: "cr-wm__main"
    }, "Chesterfield Report")));
  }
  function Ticker() {
    const items = ['ROUTE 10 reopens after tanker crash \u2014 no injuries', 'BOARD votes 4\u20131 to approve riverfront rezoning', 'SWIFT CREEK reservoir at five-year low \u2014 voluntary water cuts', 'COSBY HIGH breaks ground on STEM wing'];
    const stream = items.concat(items);
    return /*#__PURE__*/React.createElement("div", {
      className: "cr-ticker",
      role: "marquee",
      "aria-label": "Breaking headlines"
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-ticker__tag"
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-ticker__dot"
    }), "LIVE"), /*#__PURE__*/React.createElement("div", {
      className: "cr-ticker__viewport"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-ticker__track"
    }, stream.map((t, i) => /*#__PURE__*/React.createElement("span", {
      className: "cr-ticker__item",
      key: i
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-ticker__sep"
    }, "//"), t)))));
  }
  function Header({
    view,
    beat,
    onBeat,
    onNav,
    onSearch
  }) {
    return /*#__PURE__*/React.createElement("header", {
      className: "cr-header"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-header__bar"
    }, /*#__PURE__*/React.createElement(Wordmark, {
      onClick: () => onNav('home')
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-header__search"
    }, /*#__PURE__*/React.createElement(I.Search, {
      className: "cr-header__search-icon"
    }), /*#__PURE__*/React.createElement("input", {
      placeholder: "Search Chesterfield \\u2014 zoning, schools, police\\u2026",
      onFocus: onSearch,
      readOnly: true
    }), /*#__PURE__*/React.createElement("kbd", null, "/")), /*#__PURE__*/React.createElement("div", {
      className: "cr-header__actions"
    }, /*#__PURE__*/React.createElement(IconButton, {
      label: "Map",
      variant: "ghost",
      onClick: () => onNav('map')
    }, /*#__PURE__*/React.createElement(I.MapPin, null)), /*#__PURE__*/React.createElement(IconButton, {
      label: "Alerts",
      variant: "ghost"
    }, /*#__PURE__*/React.createElement(I.Bell, null)), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      size: "sm",
      onClick: () => onNav('tip')
    }, "Subscribe"))), /*#__PURE__*/React.createElement("nav", {
      className: "cr-header__nav"
    }, /*#__PURE__*/React.createElement(Tabs, {
      value: beat,
      onChange: onBeat,
      items: beats.map(b => ({
        value: b,
        label: b
      }))
    })));
  }
  function Footer({
    onNav
  }) {
    return /*#__PURE__*/React.createElement("footer", {
      className: "cr-footer"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-footer__top"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-footer__brand"
    }, /*#__PURE__*/React.createElement("img", {
      src: "../../assets/logo-mark.svg",
      alt: ""
    }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      className: "cr-footer__name"
    }, "The Chesterfield Report"), /*#__PURE__*/React.createElement("div", {
      className: "cr-footer__tag"
    }, "Hyperlocal news \\u2014 Chesterfield County, Virginia"))), /*#__PURE__*/React.createElement("div", {
      className: "cr-footer__cols"
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h5", null, "Beats"), /*#__PURE__*/React.createElement("a", null, "Growth"), /*#__PURE__*/React.createElement("a", null, "Schools"), /*#__PURE__*/React.createElement("a", null, "Police"), /*#__PURE__*/React.createElement("a", null, "Government")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h5", null, "The Report"), /*#__PURE__*/React.createElement("a", null, "This Week"), /*#__PURE__*/React.createElement("a", null, "About"), /*#__PURE__*/React.createElement("a", null, "Tip line"), /*#__PURE__*/React.createElement("a", null, "Corrections")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h5", null, "Follow"), /*#__PURE__*/React.createElement("a", {
      onClick: () => onNav('tip')
    }, "Newsletter"), /*#__PURE__*/React.createElement("a", null, "RSS"), /*#__PURE__*/React.createElement("a", null, "Mastodon")))), /*#__PURE__*/React.createElement("div", {
      className: "cr-footer__legal"
    }, /*#__PURE__*/React.createElement("span", null, "\\u00a9 2026 The Chesterfield Report \\u00b7 Independent & reader-funded"), /*#__PURE__*/React.createElement("span", {
      className: "cr-footer__mono"
    }, "build 26.06.10 \\u00b7 all systems nominal")));
  }
  window.CRShell = {
    Header,
    Footer,
    Ticker,
    Wordmark
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/Shell.jsx", error: String((e && e.message) || e) }); }

// ui_kits/report/ThisWeek.jsx
try { (() => {
// This Week digest view. -> window.CRWeek
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const {
    Card,
    Badge,
    Button,
    StatReadout
  } = DS;
  const {
    SectionHead,
    ListRow
  } = window.CRParts;
  const I = window.CRIcons;
  const {
    thisWeek,
    stories
  } = window.CR_DATA;
  function Week({
    onOpen,
    onNav
  }) {
    return /*#__PURE__*/React.createElement("div", {
      className: "cr-week"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-week__hero cr-scanlines"
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-week__kicker"
    }, "// Digest \\u00b7 Week of June 8\\u201314, 2026"), /*#__PURE__*/React.createElement("h1", {
      className: "cr-week__title"
    }, "This Week in Chesterfield"), /*#__PURE__*/React.createElement("p", {
      className: "cr-week__dek"
    }, "Everything the county decided, scheduled, or set in motion \\u2014 one scan."), /*#__PURE__*/React.createElement("div", {
      className: "cr-week__stats"
    }, /*#__PURE__*/React.createElement(StatReadout, {
      label: "Public meetings",
      value: "5"
    }), /*#__PURE__*/React.createElement(StatReadout, {
      label: "Decisions logged",
      value: "11",
      tone: "amber",
      delta: "+4",
      trend: "up"
    }), /*#__PURE__*/React.createElement(StatReadout, {
      label: "Days to budget vote",
      value: "04",
      tone: "magenta"
    }))), /*#__PURE__*/React.createElement(SectionHead, {
      kicker: "// The schedule",
      title: "On the county calendar"
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-week__rail"
    }, thisWeek.map((d, i) => /*#__PURE__*/React.createElement(Card, {
      key: i,
      accent: true,
      tone: d.tone,
      bracket: true,
      className: "cr-week__day"
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-week__dayname"
    }, d.day), /*#__PURE__*/React.createElement(Badge, {
      tone: d.tone
    }, d.label), /*#__PURE__*/React.createElement("div", {
      className: "cr-week__daytitle"
    }, d.title)))), /*#__PURE__*/React.createElement(SectionHead, {
      kicker: "// In case you missed it",
      title: "The week's biggest files",
      action: /*#__PURE__*/React.createElement(Button, {
        variant: "secondary",
        size: "sm",
        iconRight: /*#__PURE__*/React.createElement(I.Arrow, null),
        onClick: () => onNav('home')
      }, "Back to feed")
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-week__list"
    }, stories.slice(0, 4).map(s => /*#__PURE__*/React.createElement(ListRow, {
      key: s.id,
      story: s,
      onOpen: onOpen
    }))));
  }
  window.CRWeek = {
    Week
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/ThisWeek.jsx", error: String((e && e.message) || e) }); }

// ui_kits/report/TipSubmit.jsx
try { (() => {
// Newsletter + tip submission view. -> window.CRTip
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const {
    Card,
    Button,
    Input,
    Select,
    Checkbox,
    Switch,
    Toast,
    Badge
  } = DS;
  const I = window.CRIcons;
  const {
    beats
  } = window.CR_DATA;
  function Tip() {
    const [sent, setSent] = React.useState(null); // 'tip' | 'sub'
    return /*#__PURE__*/React.createElement("div", {
      className: "cr-tip"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-tip__grid"
    }, /*#__PURE__*/React.createElement(Card, {
      bracket: true,
      className: "cr-tip__card cr-scanlines"
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-twrail__kicker"
    }, "// Secure tip line"), /*#__PURE__*/React.createElement("h2", {
      className: "cr-tip__title"
    }, "Saw something the county didn't announce?"), /*#__PURE__*/React.createElement("p", {
      className: "cr-tip__dek"
    }, "Drop a tip. We read everything. Share contact details only if you want a reply \\u2014 anonymous is fine."), /*#__PURE__*/React.createElement("div", {
      className: "cr-tip__form"
    }, /*#__PURE__*/React.createElement(Input, {
      label: "What's going on?",
      placeholder: "A short headline for your tip"
    }), /*#__PURE__*/React.createElement(Select, {
      label: "Which beat?",
      options: beats.filter(b => b !== 'This Week')
    }), /*#__PURE__*/React.createElement(Input, {
      label: "Details",
      placeholder: "Dates, places, names, documents\\u2026"
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-tip__row"
    }, /*#__PURE__*/React.createElement(Input, {
      label: "Email (optional)",
      type: "email",
      placeholder: "you@\\u2026",
      icon: /*#__PURE__*/React.createElement(I.Mail, null)
    }), /*#__PURE__*/React.createElement(Checkbox, {
      label: "Keep me anonymous",
      defaultChecked: true
    })), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      iconRight: /*#__PURE__*/React.createElement(I.Send, null),
      onClick: () => setSent('tip')
    }, "Send to the newsroom"))), /*#__PURE__*/React.createElement("div", {
      className: "cr-tip__col"
    }, /*#__PURE__*/React.createElement(Card, {
      grad: true,
      bracket: true,
      className: "cr-tip__nl"
    }, /*#__PURE__*/React.createElement(Badge, {
      tone: "teal",
      dot: true
    }, "Free \\u00b7 Sundays 7am"), /*#__PURE__*/React.createElement("h2", {
      className: "cr-tip__title"
    }, "This Week, in your inbox."), /*#__PURE__*/React.createElement("p", {
      className: "cr-tip__dek"
    }, "Every county decision from the past seven days, decoded in a five-minute read."), /*#__PURE__*/React.createElement("div", {
      className: "cr-tip__form"
    }, /*#__PURE__*/React.createElement(Input, {
      label: "Email",
      type: "email",
      placeholder: "you@chesterfield.com",
      icon: /*#__PURE__*/React.createElement(I.Mail, null)
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-tip__prefs"
    }, /*#__PURE__*/React.createElement(Switch, {
      label: "Breaking alerts (rare, real)",
      defaultChecked: true
    }), /*#__PURE__*/React.createElement(Switch, {
      label: "Weekend long reads"
    })), /*#__PURE__*/React.createElement(Button, {
      variant: "primary",
      block: true,
      iconRight: /*#__PURE__*/React.createElement(I.Arrow, null),
      onClick: () => setSent('sub')
    }, "Subscribe"), /*#__PURE__*/React.createElement("div", {
      className: "cr-tip__fine"
    }, "No spam. Unsubscribe in one click. Reader-funded, ad-light."))))), sent ? /*#__PURE__*/React.createElement("div", {
      className: "cr-tip__toast"
    }, /*#__PURE__*/React.createElement(Toast, {
      tone: sent === 'tip' ? 'civic' : 'success',
      title: sent === 'tip' ? 'Tip received \u2014 thank you' : 'You\u2019re on the list',
      onClose: () => setSent(null)
    }, sent === 'tip' ? 'A reporter will review it within 24 hours.' : 'Your first This Week digest lands Sunday at 7am.')) : null);
  }
  window.CRTip = {
    Tip
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/TipSubmit.jsx", error: String((e && e.message) || e) }); }

// ui_kits/report/TopicFilter.jsx
try { (() => {
// Topic filter view. -> window.CRTopics
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const {
    Card,
    Tag,
    Select,
    StatReadout,
    Switch
  } = DS;
  const {
    ListRow,
    SectionHead
  } = window.CRParts;
  const {
    stories,
    beats
  } = window.CR_DATA;
  function Topics({
    onOpen
  }) {
    const allBeats = beats.filter(b => b !== 'This Week');
    const [active, setActive] = React.useState({});
    const [live, setLive] = React.useState(true);
    const sel = Object.keys(active).filter(k => active[k]);
    const toggle = b => setActive(s => ({
      ...s,
      [b]: !s[b]
    }));
    const filtered = stories.filter(s => {
      if (sel.length === 0) return true;
      return sel.some(b => s.beat === b || b.startsWith(s.beat) || s.beat.startsWith(b));
    });
    return /*#__PURE__*/React.createElement("div", {
      className: "cr-topics"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-topics__hero cr-grid-bg"
    }, /*#__PURE__*/React.createElement("span", {
      className: "cr-week__kicker"
    }, "// Filter the county"), /*#__PURE__*/React.createElement("h1", {
      className: "cr-week__title"
    }, "Follow the beats that matter to you"), /*#__PURE__*/React.createElement("div", {
      className: "cr-topics__tags"
    }, allBeats.map(b => /*#__PURE__*/React.createElement(Tag, {
      key: b,
      active: !!active[b],
      hash: true,
      onClick: () => toggle(b)
    }, b)))), /*#__PURE__*/React.createElement("div", {
      className: "cr-topics__bar"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-topics__count"
    }, /*#__PURE__*/React.createElement(StatReadout, {
      label: sel.length ? 'Matching ' + sel.length + ' beat' + (sel.length > 1 ? 's' : '') : 'All stories',
      value: String(filtered.length).padStart(2, '0')
    })), /*#__PURE__*/React.createElement("div", {
      className: "cr-topics__controls"
    }, /*#__PURE__*/React.createElement(Switch, {
      label: "Live updates",
      checked: live,
      onChange: e => setLive(e.target.checked)
    }), /*#__PURE__*/React.createElement(Select, {
      "aria-label": "Sort",
      options: ['Newest first', 'Most read', 'Oldest first']
    }))), /*#__PURE__*/React.createElement("div", {
      className: "cr-topics__list"
    }, filtered.map(s => /*#__PURE__*/React.createElement(ListRow, {
      key: s.id,
      story: s,
      onOpen: onOpen
    })), filtered.length === 0 ? /*#__PURE__*/React.createElement(Card, {
      className: "cr-topics__empty"
    }, "No stories match those beats yet. Try fewer filters.") : null));
  }
  window.CRTopics = {
    Topics
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/TopicFilter.jsx", error: String((e && e.message) || e) }); }

// ui_kits/report/app.jsx
try { (() => {
// App router. -> window.CRApp
(function () {
  const React = window.React;
  const {
    Header,
    Footer,
    Ticker
  } = window.CRShell;
  const {
    Home
  } = window.CRHome;
  const {
    Week
  } = window.CRWeek;
  const {
    Article
  } = window.CRArticle;
  const {
    Topics
  } = window.CRTopics;
  const {
    Map
  } = window.CRMap;
  const {
    Tip
  } = window.CRTip;
  function App() {
    const [view, setView] = React.useState('home');
    const [beat, setBeat] = React.useState('This Week');
    const [story, setStory] = React.useState(null);
    const main = React.useRef(null);
    const go = v => {
      setView(v);
      if (main.current) main.current.scrollTop = 0;
    };
    const open = s => {
      setStory(s);
      go('article');
    };
    const onBeat = b => {
      setBeat(b);
      go(b === 'This Week' ? 'thisweek' : 'topics');
    };
    let body;
    if (view === 'home') body = /*#__PURE__*/React.createElement(Home, {
      onOpen: open,
      onNav: go
    });else if (view === 'thisweek') body = /*#__PURE__*/React.createElement(Week, {
      onOpen: open,
      onNav: go
    });else if (view === 'article') body = /*#__PURE__*/React.createElement(Article, {
      story: story,
      onOpen: open,
      onNav: go
    });else if (view === 'topics') body = /*#__PURE__*/React.createElement(Topics, {
      onOpen: open
    });else if (view === 'map') body = /*#__PURE__*/React.createElement(Map, {
      onOpen: open
    });else if (view === 'tip') body = /*#__PURE__*/React.createElement(Tip, null);
    return /*#__PURE__*/React.createElement("div", {
      className: "cr-app"
    }, /*#__PURE__*/React.createElement(Header, {
      view: view,
      beat: beat,
      onBeat: onBeat,
      onNav: go,
      onSearch: () => go('topics')
    }), /*#__PURE__*/React.createElement(Ticker, null), /*#__PURE__*/React.createElement("main", {
      className: "cr-main",
      ref: main
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-main__inner"
    }, body), /*#__PURE__*/React.createElement(Footer, {
      onNav: go
    })));
  }
  window.CRApp = {
    App
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/app.jsx", error: String((e && e.message) || e) }); }

// ui_kits/report/data.js
try { (() => {
// Mock content for The Chesterfield Report UI kit. Assigned to window.CR_DATA.
(function () {
  const PHOTO = {
    river: 'linear-gradient(160deg,#0a2f33 0%,#0e3b3a 35%,#15243b 100%)',
    civic: 'linear-gradient(160deg,#10222b 0%,#1a2f24 60%,#06141a 100%)',
    night: 'linear-gradient(160deg,#0c1430 0%,#1a1030 55%,#06141a 100%)',
    school: 'linear-gradient(160deg,#0a2f33 0%,#102a1c 60%,#06141a 100%)',
    road: 'linear-gradient(160deg,#1a1224 0%,#2a1430 50%,#06141a 100%)',
    park: 'linear-gradient(160deg,#0a2a22 0%,#13351f 60%,#06141a 100%)'
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
    author: 'M. Okafor'
  };
  const stories = [{
    id: 'stem',
    beat: 'Schools',
    tone: 'teal',
    kicker: 'Cosby High',
    title: 'New STEM wing breaks ground for fall 2027',
    dek: 'A 40,000 sq ft lab block adds robotics, biotech and a fabrication shop.',
    time: '17:10',
    date: 'Jun 10',
    read: '4 min',
    photo: PHOTO.school,
    author: 'D. Reyes'
  }, {
    id: 'route10',
    beat: 'Police',
    tone: 'breaking',
    kicker: 'Traffic',
    title: 'Route 10 reopens after tanker crash near Chester',
    dek: 'No injuries reported; VDOT cleared the spill by 8pm after a six-hour closure.',
    time: '20:05',
    date: 'Jun 10',
    read: '2 min',
    photo: PHOTO.road,
    author: 'Newsroom'
  }, {
    id: 'budget',
    beat: 'Government',
    tone: 'civic',
    kicker: 'Explainer',
    title: 'Where the county\u2019s $1.9B budget actually goes',
    dek: 'Schools take 48 cents of every dollar. We break down the rest, line by line.',
    time: '08:00',
    date: 'Jun 10',
    read: '9 min',
    photo: PHOTO.civic,
    author: 'M. Okafor'
  }, {
    id: 'reservoir',
    beat: 'Environment',
    tone: 'eco',
    kicker: 'Swift Creek',
    title: 'Reservoir levels hit a five-year low after dry spring',
    dek: 'Utilities ask residents to voluntarily cut outdoor watering through July.',
    time: '13:30',
    date: 'Jun 9',
    read: '3 min',
    photo: PHOTO.park,
    author: 'L. Tran'
  }, {
    id: 'market',
    beat: 'Community',
    tone: 'teal',
    kicker: 'Midlothian',
    title: 'Saturday market returns to the village with 60 vendors',
    dek: 'Local growers, makers and three new food trucks line Coalfield Road.',
    time: '09:15',
    date: 'Jun 9',
    read: '2 min',
    photo: PHOTO.civic,
    author: 'A. Bell'
  }, {
    id: 'transit',
    beat: 'Growth & Development',
    tone: 'teal',
    kicker: 'Hull Street',
    title: 'Bus rapid transit study eyes the Hull Street corridor',
    dek: 'Planners float dedicated lanes from the courthouse to the city line.',
    time: '11:45',
    date: 'Jun 9',
    read: '5 min',
    photo: PHOTO.night,
    author: 'D. Reyes'
  }];
  const thisWeek = [{
    day: 'MON',
    label: 'Planning Commission',
    title: 'Moseley mixed-use hearing',
    tone: 'civic'
  }, {
    day: 'TUE',
    label: 'Schools',
    title: 'Calendar vote: later start times',
    tone: 'teal'
  }, {
    day: 'WED',
    label: 'Community',
    title: 'Pocahontas Park night hike',
    tone: 'eco'
  }, {
    day: 'THU',
    label: 'Government',
    title: 'Budget work session (final)',
    tone: 'civic'
  }, {
    day: 'FRI',
    label: 'Police',
    title: 'Citizen academy graduation',
    tone: 'breaking'
  }];
  const beats = ['This Week', 'Growth & Development', 'Schools', 'Police', 'Government', 'Community', 'Opinion'];
  const mapPins = [{
    x: 32,
    y: 38,
    tone: 'breaking',
    label: 'Route 10 crash'
  }, {
    x: 54,
    y: 30,
    tone: 'civic',
    label: 'County complex'
  }, {
    x: 44,
    y: 58,
    tone: 'teal',
    label: 'Cosby High'
  }, {
    x: 24,
    y: 64,
    tone: 'eco',
    label: 'Swift Creek'
  }, {
    x: 66,
    y: 48,
    tone: 'teal',
    label: 'Midlothian market'
  }, {
    x: 60,
    y: 70,
    tone: 'eco',
    label: 'Pocahontas Park'
  }];
  window.CR_DATA = {
    PHOTO,
    lead,
    stories,
    thisWeek,
    beats,
    mapPins
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/data.js", error: String((e && e.message) || e) }); }

// ui_kits/report/icons.js
try { (() => {
// Inline stroke icons (Lucide-style, 2px round) for the UI kit. -> window.CRIcons
(function () {
  const React = window.React;
  const s = (paths, extra) => props => React.createElement('svg', Object.assign({
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 2,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    width: '1em',
    height: '1em'
  }, extra, props), paths.map((d, i) => React.createElement('path', {
    key: i,
    d
  })));
  const c = (cx, cy, r) => ({
    __c: [cx, cy, r]
  });
  const make = (children, extra) => props => React.createElement('svg', Object.assign({
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 2,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    width: '1em',
    height: '1em'
  }, extra, props), children.map((ch, i) => ch.__c ? React.createElement('circle', {
    key: i,
    cx: ch.__c[0],
    cy: ch.__c[1],
    r: ch.__c[2]
  }) : React.createElement('path', {
    key: i,
    d: ch
  })));
  window.CRIcons = {
    Search: make([c(11, 11, 7), 'm21 21-4.3-4.3']),
    Bell: make(['M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9', 'M10.3 21a1.94 1.94 0 0 0 3.4 0']),
    Menu: make(['M3 6h18', 'M3 12h18', 'M3 18h18']),
    Clock: make([c(12, 12, 9), 'M12 7v5l3 2']),
    MapPin: make(['M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0', c(12, 10, 3)]),
    Arrow: make(['M5 12h14', 'm13 6 6 6-6 6']),
    ArrowUpRight: make(['M7 17 17 7', 'M7 7h10v10']),
    Share: make([c(18, 5, 3), c(6, 12, 3), c(18, 19, 3), 'm8.6 13.5 6.8 4', 'm15.4 6.5-6.8 4']),
    Bookmark: make(['M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z']),
    Mail: make(['M3 5h18v14H3z', 'm3 7 9 6 9-6']),
    Send: make(['M22 2 11 13', 'M22 2 15 22l-4-9-9-4 20-7z']),
    Filter: make(['M22 3H2l8 9.5V19l4 2v-8.5z']),
    X: make(['M18 6 6 18', 'M6 6l12 12']),
    ChevronRight: make(['m9 6 6 6-6 6']),
    Sun: make([c(12, 12, 4), 'M12 2v2', 'M12 20v2', 'm4.9 4.9 1.4 1.4', 'm17.7 17.7 1.4 1.4', 'M2 12h2', 'M20 12h2', 'm6.3 17.7-1.4 1.4', 'm19.1 4.9-1.4 1.4']),
    Eye: make(['M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z', c(12, 12, 3)]),
    Flame: make(['M12 2c1 4 4 5 4 9a4 4 0 0 1-8 0c0-1 .5-2 1-2.5C9 11 12 9 12 6c2 1 3 3 3 5']),
    Grid: make(['M3 3h7v7H3z', 'M14 3h7v7h-7z', 'M14 14h7v7h-7z', 'M3 14h7v7H3z'])
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/icons.js", error: String((e && e.message) || e) }); }

// ui_kits/report/parts.jsx
try { (() => {
// Shared presentational parts. -> window.CRParts
(function () {
  const React = window.React;
  const DS = window.ChesterfieldReportDesignSystem_ad430c;
  const {
    Card,
    Badge
  } = DS;
  const I = window.CRIcons;

  // Image stand-in: duotone gradient + grid + corner brackets + caption.
  function PhotoFrame({
    photo,
    label,
    ratio = '16 / 9',
    children,
    className = ''
  }) {
    return /*#__PURE__*/React.createElement("div", {
      className: 'cr-photo ' + className,
      style: {
        background: photo,
        aspectRatio: ratio
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-photo__grid"
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-photo__scan"
    }), /*#__PURE__*/React.createElement("span", {
      className: "cr-photo__b cr-photo__b--tl"
    }), /*#__PURE__*/React.createElement("span", {
      className: "cr-photo__b cr-photo__b--br"
    }), children, label ? /*#__PURE__*/React.createElement("span", {
      className: "cr-photo__cap"
    }, label) : null);
  }
  function MetaRow({
    time,
    date,
    read,
    author
  }) {
    return /*#__PURE__*/React.createElement("div", {
      className: "cr-meta"
    }, time ? /*#__PURE__*/React.createElement("span", {
      className: "cr-meta__t"
    }, /*#__PURE__*/React.createElement(I.Clock, null), " ", time) : null, date ? /*#__PURE__*/React.createElement("span", null, date) : null, read ? /*#__PURE__*/React.createElement("span", null, read) : null, author ? /*#__PURE__*/React.createElement("span", {
      className: "cr-meta__by"
    }, "by ", author) : null);
  }
  function StoryCard({
    story,
    onOpen,
    size = 'md'
  }) {
    return /*#__PURE__*/React.createElement(Card, {
      interactive: true,
      accent: true,
      tone: story.tone,
      bracket: true,
      pad: false,
      className: 'cr-story cr-story--' + size,
      onClick: () => onOpen && onOpen(story)
    }, /*#__PURE__*/React.createElement(PhotoFrame, {
      photo: story.photo,
      label: 'PHOTO \u00b7 ' + story.beat.toUpperCase()
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-story__body"
    }, /*#__PURE__*/React.createElement(Badge, {
      tone: story.tone,
      dot: story.tone === 'breaking'
    }, story.kicker), /*#__PURE__*/React.createElement("h3", {
      className: "cr-story__title"
    }, story.title), size !== 'sm' ? /*#__PURE__*/React.createElement("p", {
      className: "cr-story__dek"
    }, story.dek) : null, /*#__PURE__*/React.createElement(MetaRow, {
      time: story.time,
      date: story.date,
      read: story.read,
      author: size === 'lg' ? story.author : null
    })));
  }
  function ListRow({
    story,
    onOpen
  }) {
    return /*#__PURE__*/React.createElement("button", {
      className: "cr-listrow",
      onClick: () => onOpen && onOpen(story)
    }, /*#__PURE__*/React.createElement("span", {
      className: 'cr-listrow__rail cr-listrow__rail--' + story.tone
    }), /*#__PURE__*/React.createElement("div", {
      className: "cr-listrow__body"
    }, /*#__PURE__*/React.createElement("div", {
      className: "cr-listrow__top"
    }, /*#__PURE__*/React.createElement(Badge, {
      tone: story.tone
    }, story.beat), /*#__PURE__*/React.createElement("span", {
      className: "cr-listrow__time"
    }, story.time)), /*#__PURE__*/React.createElement("h4", {
      className: "cr-listrow__title"
    }, story.title), /*#__PURE__*/React.createElement("p", {
      className: "cr-listrow__dek"
    }, story.dek)), /*#__PURE__*/React.createElement("span", {
      className: "cr-listrow__go"
    }, /*#__PURE__*/React.createElement(I.ChevronRight, null)));
  }
  function SectionHead({
    kicker,
    title,
    action
  }) {
    return /*#__PURE__*/React.createElement("div", {
      className: "cr-sechead"
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      className: "cr-sechead__kicker"
    }, kicker), /*#__PURE__*/React.createElement("h2", {
      className: "cr-sechead__title"
    }, title)), action || null);
  }
  window.CRParts = {
    PhotoFrame,
    MetaRow,
    StoryCard,
    ListRow,
    SectionHead
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/report/parts.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Button = __ds_scope.Button;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.StatReadout = __ds_scope.StatReadout;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.Tabs = __ds_scope.Tabs;

__ds_ns.Card = __ds_scope.Card;

})();
