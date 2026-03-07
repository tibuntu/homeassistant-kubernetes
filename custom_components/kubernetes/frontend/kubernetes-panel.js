/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
var _a;
const t$2 = globalThis, e$2 = t$2.ShadowRoot && (void 0 === t$2.ShadyCSS || t$2.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, s$2 = Symbol(), o$4 = /* @__PURE__ */ new WeakMap();
let n$3 = class n {
  constructor(t2, e2, o2) {
    if (this._$cssResult$ = true, o2 !== s$2) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t2, this.t = e2;
  }
  get styleSheet() {
    let t2 = this.o;
    const s2 = this.t;
    if (e$2 && void 0 === t2) {
      const e2 = void 0 !== s2 && 1 === s2.length;
      e2 && (t2 = o$4.get(s2)), void 0 === t2 && ((this.o = t2 = new CSSStyleSheet()).replaceSync(this.cssText), e2 && o$4.set(s2, t2));
    }
    return t2;
  }
  toString() {
    return this.cssText;
  }
};
const r$4 = (t2) => new n$3("string" == typeof t2 ? t2 : t2 + "", void 0, s$2), i$3 = (t2, ...e2) => {
  const o2 = 1 === t2.length ? t2[0] : e2.reduce((e3, s2, o3) => e3 + ((t3) => {
    if (true === t3._$cssResult$) return t3.cssText;
    if ("number" == typeof t3) return t3;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + t3 + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s2) + t2[o3 + 1], t2[0]);
  return new n$3(o2, t2, s$2);
}, S$1 = (s2, o2) => {
  if (e$2) s2.adoptedStyleSheets = o2.map((t2) => t2 instanceof CSSStyleSheet ? t2 : t2.styleSheet);
  else for (const e2 of o2) {
    const o3 = document.createElement("style"), n3 = t$2.litNonce;
    void 0 !== n3 && o3.setAttribute("nonce", n3), o3.textContent = e2.cssText, s2.appendChild(o3);
  }
}, c$2 = e$2 ? (t2) => t2 : (t2) => t2 instanceof CSSStyleSheet ? ((t3) => {
  let e2 = "";
  for (const s2 of t3.cssRules) e2 += s2.cssText;
  return r$4(e2);
})(t2) : t2;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: i$2, defineProperty: e$1, getOwnPropertyDescriptor: h$1, getOwnPropertyNames: r$3, getOwnPropertySymbols: o$3, getPrototypeOf: n$2 } = Object, a$1 = globalThis, c$1 = a$1.trustedTypes, l$1 = c$1 ? c$1.emptyScript : "", p$1 = a$1.reactiveElementPolyfillSupport, d$1 = (t2, s2) => t2, u$1 = { toAttribute(t2, s2) {
  switch (s2) {
    case Boolean:
      t2 = t2 ? l$1 : null;
      break;
    case Object:
    case Array:
      t2 = null == t2 ? t2 : JSON.stringify(t2);
  }
  return t2;
}, fromAttribute(t2, s2) {
  let i2 = t2;
  switch (s2) {
    case Boolean:
      i2 = null !== t2;
      break;
    case Number:
      i2 = null === t2 ? null : Number(t2);
      break;
    case Object:
    case Array:
      try {
        i2 = JSON.parse(t2);
      } catch (t3) {
        i2 = null;
      }
  }
  return i2;
} }, f$1 = (t2, s2) => !i$2(t2, s2), b$1 = { attribute: true, type: String, converter: u$1, reflect: false, useDefault: false, hasChanged: f$1 };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), a$1.litPropertyMetadata ?? (a$1.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let y$1 = class y extends HTMLElement {
  static addInitializer(t2) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t2);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t2, s2 = b$1) {
    if (s2.state && (s2.attribute = false), this._$Ei(), this.prototype.hasOwnProperty(t2) && ((s2 = Object.create(s2)).wrapped = true), this.elementProperties.set(t2, s2), !s2.noAccessor) {
      const i2 = Symbol(), h2 = this.getPropertyDescriptor(t2, i2, s2);
      void 0 !== h2 && e$1(this.prototype, t2, h2);
    }
  }
  static getPropertyDescriptor(t2, s2, i2) {
    const { get: e2, set: r2 } = h$1(this.prototype, t2) ?? { get() {
      return this[s2];
    }, set(t3) {
      this[s2] = t3;
    } };
    return { get: e2, set(s3) {
      const h2 = e2 == null ? void 0 : e2.call(this);
      r2 == null ? void 0 : r2.call(this, s3), this.requestUpdate(t2, h2, i2);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t2) {
    return this.elementProperties.get(t2) ?? b$1;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d$1("elementProperties"))) return;
    const t2 = n$2(this);
    t2.finalize(), void 0 !== t2.l && (this.l = [...t2.l]), this.elementProperties = new Map(t2.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(d$1("finalized"))) return;
    if (this.finalized = true, this._$Ei(), this.hasOwnProperty(d$1("properties"))) {
      const t3 = this.properties, s2 = [...r$3(t3), ...o$3(t3)];
      for (const i2 of s2) this.createProperty(i2, t3[i2]);
    }
    const t2 = this[Symbol.metadata];
    if (null !== t2) {
      const s2 = litPropertyMetadata.get(t2);
      if (void 0 !== s2) for (const [t3, i2] of s2) this.elementProperties.set(t3, i2);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t3, s2] of this.elementProperties) {
      const i2 = this._$Eu(t3, s2);
      void 0 !== i2 && this._$Eh.set(i2, t3);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s2) {
    const i2 = [];
    if (Array.isArray(s2)) {
      const e2 = new Set(s2.flat(1 / 0).reverse());
      for (const s3 of e2) i2.unshift(c$2(s3));
    } else void 0 !== s2 && i2.push(c$2(s2));
    return i2;
  }
  static _$Eu(t2, s2) {
    const i2 = s2.attribute;
    return false === i2 ? void 0 : "string" == typeof i2 ? i2 : "string" == typeof t2 ? t2.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = false, this.hasUpdated = false, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    var _a2;
    this._$ES = new Promise((t2) => this.enableUpdating = t2), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), (_a2 = this.constructor.l) == null ? void 0 : _a2.forEach((t2) => t2(this));
  }
  addController(t2) {
    var _a2;
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(t2), void 0 !== this.renderRoot && this.isConnected && ((_a2 = t2.hostConnected) == null ? void 0 : _a2.call(t2));
  }
  removeController(t2) {
    var _a2;
    (_a2 = this._$EO) == null ? void 0 : _a2.delete(t2);
  }
  _$E_() {
    const t2 = /* @__PURE__ */ new Map(), s2 = this.constructor.elementProperties;
    for (const i2 of s2.keys()) this.hasOwnProperty(i2) && (t2.set(i2, this[i2]), delete this[i2]);
    t2.size > 0 && (this._$Ep = t2);
  }
  createRenderRoot() {
    const t2 = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return S$1(t2, this.constructor.elementStyles), t2;
  }
  connectedCallback() {
    var _a2;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(true), (_a2 = this._$EO) == null ? void 0 : _a2.forEach((t2) => {
      var _a3;
      return (_a3 = t2.hostConnected) == null ? void 0 : _a3.call(t2);
    });
  }
  enableUpdating(t2) {
  }
  disconnectedCallback() {
    var _a2;
    (_a2 = this._$EO) == null ? void 0 : _a2.forEach((t2) => {
      var _a3;
      return (_a3 = t2.hostDisconnected) == null ? void 0 : _a3.call(t2);
    });
  }
  attributeChangedCallback(t2, s2, i2) {
    this._$AK(t2, i2);
  }
  _$ET(t2, s2) {
    var _a2;
    const i2 = this.constructor.elementProperties.get(t2), e2 = this.constructor._$Eu(t2, i2);
    if (void 0 !== e2 && true === i2.reflect) {
      const h2 = (void 0 !== ((_a2 = i2.converter) == null ? void 0 : _a2.toAttribute) ? i2.converter : u$1).toAttribute(s2, i2.type);
      this._$Em = t2, null == h2 ? this.removeAttribute(e2) : this.setAttribute(e2, h2), this._$Em = null;
    }
  }
  _$AK(t2, s2) {
    var _a2, _b;
    const i2 = this.constructor, e2 = i2._$Eh.get(t2);
    if (void 0 !== e2 && this._$Em !== e2) {
      const t3 = i2.getPropertyOptions(e2), h2 = "function" == typeof t3.converter ? { fromAttribute: t3.converter } : void 0 !== ((_a2 = t3.converter) == null ? void 0 : _a2.fromAttribute) ? t3.converter : u$1;
      this._$Em = e2;
      const r2 = h2.fromAttribute(s2, t3.type);
      this[e2] = r2 ?? ((_b = this._$Ej) == null ? void 0 : _b.get(e2)) ?? r2, this._$Em = null;
    }
  }
  requestUpdate(t2, s2, i2, e2 = false, h2) {
    var _a2;
    if (void 0 !== t2) {
      const r2 = this.constructor;
      if (false === e2 && (h2 = this[t2]), i2 ?? (i2 = r2.getPropertyOptions(t2)), !((i2.hasChanged ?? f$1)(h2, s2) || i2.useDefault && i2.reflect && h2 === ((_a2 = this._$Ej) == null ? void 0 : _a2.get(t2)) && !this.hasAttribute(r2._$Eu(t2, i2)))) return;
      this.C(t2, s2, i2);
    }
    false === this.isUpdatePending && (this._$ES = this._$EP());
  }
  C(t2, s2, { useDefault: i2, reflect: e2, wrapped: h2 }, r2) {
    i2 && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t2) && (this._$Ej.set(t2, r2 ?? s2 ?? this[t2]), true !== h2 || void 0 !== r2) || (this._$AL.has(t2) || (this.hasUpdated || i2 || (s2 = void 0), this._$AL.set(t2, s2)), true === e2 && this._$Em !== t2 && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t2));
  }
  async _$EP() {
    this.isUpdatePending = true;
    try {
      await this._$ES;
    } catch (t3) {
      Promise.reject(t3);
    }
    const t2 = this.scheduleUpdate();
    return null != t2 && await t2, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    var _a2;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [t4, s3] of this._$Ep) this[t4] = s3;
        this._$Ep = void 0;
      }
      const t3 = this.constructor.elementProperties;
      if (t3.size > 0) for (const [s3, i2] of t3) {
        const { wrapped: t4 } = i2, e2 = this[s3];
        true !== t4 || this._$AL.has(s3) || void 0 === e2 || this.C(s3, void 0, i2, e2);
      }
    }
    let t2 = false;
    const s2 = this._$AL;
    try {
      t2 = this.shouldUpdate(s2), t2 ? (this.willUpdate(s2), (_a2 = this._$EO) == null ? void 0 : _a2.forEach((t3) => {
        var _a3;
        return (_a3 = t3.hostUpdate) == null ? void 0 : _a3.call(t3);
      }), this.update(s2)) : this._$EM();
    } catch (s3) {
      throw t2 = false, this._$EM(), s3;
    }
    t2 && this._$AE(s2);
  }
  willUpdate(t2) {
  }
  _$AE(t2) {
    var _a2;
    (_a2 = this._$EO) == null ? void 0 : _a2.forEach((t3) => {
      var _a3;
      return (_a3 = t3.hostUpdated) == null ? void 0 : _a3.call(t3);
    }), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t2)), this.updated(t2);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = false;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t2) {
    return true;
  }
  update(t2) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t3) => this._$ET(t3, this[t3]))), this._$EM();
  }
  updated(t2) {
  }
  firstUpdated(t2) {
  }
};
y$1.elementStyles = [], y$1.shadowRootOptions = { mode: "open" }, y$1[d$1("elementProperties")] = /* @__PURE__ */ new Map(), y$1[d$1("finalized")] = /* @__PURE__ */ new Map(), p$1 == null ? void 0 : p$1({ ReactiveElement: y$1 }), (a$1.reactiveElementVersions ?? (a$1.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$1 = globalThis, i$1 = (t2) => t2, s$1 = t$1.trustedTypes, e = s$1 ? s$1.createPolicy("lit-html", { createHTML: (t2) => t2 }) : void 0, h = "$lit$", o$2 = `lit$${Math.random().toFixed(9).slice(2)}$`, n$1 = "?" + o$2, r$2 = `<${n$1}>`, l = document, c = () => l.createComment(""), a = (t2) => null === t2 || "object" != typeof t2 && "function" != typeof t2, u = Array.isArray, d = (t2) => u(t2) || "function" == typeof (t2 == null ? void 0 : t2[Symbol.iterator]), f = "[ 	\n\f\r]", v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, _ = /-->/g, m = />/g, p = RegExp(`>|${f}(?:([^\\s"'>=/]+)(${f}*=${f}*(?:[^
\f\r"'\`<>=]|("|')|))|$)`, "g"), g = /'/g, $ = /"/g, y2 = /^(?:script|style|textarea|title)$/i, x = (t2) => (i2, ...s2) => ({ _$litType$: t2, strings: i2, values: s2 }), b = x(1), E = Symbol.for("lit-noChange"), A = Symbol.for("lit-nothing"), C = /* @__PURE__ */ new WeakMap(), P = l.createTreeWalker(l, 129);
function V(t2, i2) {
  if (!u(t2) || !t2.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return void 0 !== e ? e.createHTML(i2) : i2;
}
const N = (t2, i2) => {
  const s2 = t2.length - 1, e2 = [];
  let n3, l2 = 2 === i2 ? "<svg>" : 3 === i2 ? "<math>" : "", c2 = v;
  for (let i3 = 0; i3 < s2; i3++) {
    const s3 = t2[i3];
    let a2, u2, d2 = -1, f2 = 0;
    for (; f2 < s3.length && (c2.lastIndex = f2, u2 = c2.exec(s3), null !== u2); ) f2 = c2.lastIndex, c2 === v ? "!--" === u2[1] ? c2 = _ : void 0 !== u2[1] ? c2 = m : void 0 !== u2[2] ? (y2.test(u2[2]) && (n3 = RegExp("</" + u2[2], "g")), c2 = p) : void 0 !== u2[3] && (c2 = p) : c2 === p ? ">" === u2[0] ? (c2 = n3 ?? v, d2 = -1) : void 0 === u2[1] ? d2 = -2 : (d2 = c2.lastIndex - u2[2].length, a2 = u2[1], c2 = void 0 === u2[3] ? p : '"' === u2[3] ? $ : g) : c2 === $ || c2 === g ? c2 = p : c2 === _ || c2 === m ? c2 = v : (c2 = p, n3 = void 0);
    const x2 = c2 === p && t2[i3 + 1].startsWith("/>") ? " " : "";
    l2 += c2 === v ? s3 + r$2 : d2 >= 0 ? (e2.push(a2), s3.slice(0, d2) + h + s3.slice(d2) + o$2 + x2) : s3 + o$2 + (-2 === d2 ? i3 : x2);
  }
  return [V(t2, l2 + (t2[s2] || "<?>") + (2 === i2 ? "</svg>" : 3 === i2 ? "</math>" : "")), e2];
};
class S {
  constructor({ strings: t2, _$litType$: i2 }, e2) {
    let r2;
    this.parts = [];
    let l2 = 0, a2 = 0;
    const u2 = t2.length - 1, d2 = this.parts, [f2, v2] = N(t2, i2);
    if (this.el = S.createElement(f2, e2), P.currentNode = this.el.content, 2 === i2 || 3 === i2) {
      const t3 = this.el.content.firstChild;
      t3.replaceWith(...t3.childNodes);
    }
    for (; null !== (r2 = P.nextNode()) && d2.length < u2; ) {
      if (1 === r2.nodeType) {
        if (r2.hasAttributes()) for (const t3 of r2.getAttributeNames()) if (t3.endsWith(h)) {
          const i3 = v2[a2++], s2 = r2.getAttribute(t3).split(o$2), e3 = /([.?@])?(.*)/.exec(i3);
          d2.push({ type: 1, index: l2, name: e3[2], strings: s2, ctor: "." === e3[1] ? I : "?" === e3[1] ? L : "@" === e3[1] ? z : H }), r2.removeAttribute(t3);
        } else t3.startsWith(o$2) && (d2.push({ type: 6, index: l2 }), r2.removeAttribute(t3));
        if (y2.test(r2.tagName)) {
          const t3 = r2.textContent.split(o$2), i3 = t3.length - 1;
          if (i3 > 0) {
            r2.textContent = s$1 ? s$1.emptyScript : "";
            for (let s2 = 0; s2 < i3; s2++) r2.append(t3[s2], c()), P.nextNode(), d2.push({ type: 2, index: ++l2 });
            r2.append(t3[i3], c());
          }
        }
      } else if (8 === r2.nodeType) if (r2.data === n$1) d2.push({ type: 2, index: l2 });
      else {
        let t3 = -1;
        for (; -1 !== (t3 = r2.data.indexOf(o$2, t3 + 1)); ) d2.push({ type: 7, index: l2 }), t3 += o$2.length - 1;
      }
      l2++;
    }
  }
  static createElement(t2, i2) {
    const s2 = l.createElement("template");
    return s2.innerHTML = t2, s2;
  }
}
function M(t2, i2, s2 = t2, e2) {
  var _a2, _b;
  if (i2 === E) return i2;
  let h2 = void 0 !== e2 ? (_a2 = s2._$Co) == null ? void 0 : _a2[e2] : s2._$Cl;
  const o2 = a(i2) ? void 0 : i2._$litDirective$;
  return (h2 == null ? void 0 : h2.constructor) !== o2 && ((_b = h2 == null ? void 0 : h2._$AO) == null ? void 0 : _b.call(h2, false), void 0 === o2 ? h2 = void 0 : (h2 = new o2(t2), h2._$AT(t2, s2, e2)), void 0 !== e2 ? (s2._$Co ?? (s2._$Co = []))[e2] = h2 : s2._$Cl = h2), void 0 !== h2 && (i2 = M(t2, h2._$AS(t2, i2.values), h2, e2)), i2;
}
class R {
  constructor(t2, i2) {
    this._$AV = [], this._$AN = void 0, this._$AD = t2, this._$AM = i2;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t2) {
    const { el: { content: i2 }, parts: s2 } = this._$AD, e2 = ((t2 == null ? void 0 : t2.creationScope) ?? l).importNode(i2, true);
    P.currentNode = e2;
    let h2 = P.nextNode(), o2 = 0, n3 = 0, r2 = s2[0];
    for (; void 0 !== r2; ) {
      if (o2 === r2.index) {
        let i3;
        2 === r2.type ? i3 = new k(h2, h2.nextSibling, this, t2) : 1 === r2.type ? i3 = new r2.ctor(h2, r2.name, r2.strings, this, t2) : 6 === r2.type && (i3 = new Z(h2, this, t2)), this._$AV.push(i3), r2 = s2[++n3];
      }
      o2 !== (r2 == null ? void 0 : r2.index) && (h2 = P.nextNode(), o2++);
    }
    return P.currentNode = l, e2;
  }
  p(t2) {
    let i2 = 0;
    for (const s2 of this._$AV) void 0 !== s2 && (void 0 !== s2.strings ? (s2._$AI(t2, s2, i2), i2 += s2.strings.length - 2) : s2._$AI(t2[i2])), i2++;
  }
}
class k {
  get _$AU() {
    var _a2;
    return ((_a2 = this._$AM) == null ? void 0 : _a2._$AU) ?? this._$Cv;
  }
  constructor(t2, i2, s2, e2) {
    this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = t2, this._$AB = i2, this._$AM = s2, this.options = e2, this._$Cv = (e2 == null ? void 0 : e2.isConnected) ?? true;
  }
  get parentNode() {
    let t2 = this._$AA.parentNode;
    const i2 = this._$AM;
    return void 0 !== i2 && 11 === (t2 == null ? void 0 : t2.nodeType) && (t2 = i2.parentNode), t2;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t2, i2 = this) {
    t2 = M(this, t2, i2), a(t2) ? t2 === A || null == t2 || "" === t2 ? (this._$AH !== A && this._$AR(), this._$AH = A) : t2 !== this._$AH && t2 !== E && this._(t2) : void 0 !== t2._$litType$ ? this.$(t2) : void 0 !== t2.nodeType ? this.T(t2) : d(t2) ? this.k(t2) : this._(t2);
  }
  O(t2) {
    return this._$AA.parentNode.insertBefore(t2, this._$AB);
  }
  T(t2) {
    this._$AH !== t2 && (this._$AR(), this._$AH = this.O(t2));
  }
  _(t2) {
    this._$AH !== A && a(this._$AH) ? this._$AA.nextSibling.data = t2 : this.T(l.createTextNode(t2)), this._$AH = t2;
  }
  $(t2) {
    var _a2;
    const { values: i2, _$litType$: s2 } = t2, e2 = "number" == typeof s2 ? this._$AC(t2) : (void 0 === s2.el && (s2.el = S.createElement(V(s2.h, s2.h[0]), this.options)), s2);
    if (((_a2 = this._$AH) == null ? void 0 : _a2._$AD) === e2) this._$AH.p(i2);
    else {
      const t3 = new R(e2, this), s3 = t3.u(this.options);
      t3.p(i2), this.T(s3), this._$AH = t3;
    }
  }
  _$AC(t2) {
    let i2 = C.get(t2.strings);
    return void 0 === i2 && C.set(t2.strings, i2 = new S(t2)), i2;
  }
  k(t2) {
    u(this._$AH) || (this._$AH = [], this._$AR());
    const i2 = this._$AH;
    let s2, e2 = 0;
    for (const h2 of t2) e2 === i2.length ? i2.push(s2 = new k(this.O(c()), this.O(c()), this, this.options)) : s2 = i2[e2], s2._$AI(h2), e2++;
    e2 < i2.length && (this._$AR(s2 && s2._$AB.nextSibling, e2), i2.length = e2);
  }
  _$AR(t2 = this._$AA.nextSibling, s2) {
    var _a2;
    for ((_a2 = this._$AP) == null ? void 0 : _a2.call(this, false, true, s2); t2 !== this._$AB; ) {
      const s3 = i$1(t2).nextSibling;
      i$1(t2).remove(), t2 = s3;
    }
  }
  setConnected(t2) {
    var _a2;
    void 0 === this._$AM && (this._$Cv = t2, (_a2 = this._$AP) == null ? void 0 : _a2.call(this, t2));
  }
}
class H {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t2, i2, s2, e2, h2) {
    this.type = 1, this._$AH = A, this._$AN = void 0, this.element = t2, this.name = i2, this._$AM = e2, this.options = h2, s2.length > 2 || "" !== s2[0] || "" !== s2[1] ? (this._$AH = Array(s2.length - 1).fill(new String()), this.strings = s2) : this._$AH = A;
  }
  _$AI(t2, i2 = this, s2, e2) {
    const h2 = this.strings;
    let o2 = false;
    if (void 0 === h2) t2 = M(this, t2, i2, 0), o2 = !a(t2) || t2 !== this._$AH && t2 !== E, o2 && (this._$AH = t2);
    else {
      const e3 = t2;
      let n3, r2;
      for (t2 = h2[0], n3 = 0; n3 < h2.length - 1; n3++) r2 = M(this, e3[s2 + n3], i2, n3), r2 === E && (r2 = this._$AH[n3]), o2 || (o2 = !a(r2) || r2 !== this._$AH[n3]), r2 === A ? t2 = A : t2 !== A && (t2 += (r2 ?? "") + h2[n3 + 1]), this._$AH[n3] = r2;
    }
    o2 && !e2 && this.j(t2);
  }
  j(t2) {
    t2 === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t2 ?? "");
  }
}
class I extends H {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t2) {
    this.element[this.name] = t2 === A ? void 0 : t2;
  }
}
class L extends H {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t2) {
    this.element.toggleAttribute(this.name, !!t2 && t2 !== A);
  }
}
class z extends H {
  constructor(t2, i2, s2, e2, h2) {
    super(t2, i2, s2, e2, h2), this.type = 5;
  }
  _$AI(t2, i2 = this) {
    if ((t2 = M(this, t2, i2, 0) ?? A) === E) return;
    const s2 = this._$AH, e2 = t2 === A && s2 !== A || t2.capture !== s2.capture || t2.once !== s2.once || t2.passive !== s2.passive, h2 = t2 !== A && (s2 === A || e2);
    e2 && this.element.removeEventListener(this.name, this, s2), h2 && this.element.addEventListener(this.name, this, t2), this._$AH = t2;
  }
  handleEvent(t2) {
    var _a2;
    "function" == typeof this._$AH ? this._$AH.call(((_a2 = this.options) == null ? void 0 : _a2.host) ?? this.element, t2) : this._$AH.handleEvent(t2);
  }
}
class Z {
  constructor(t2, i2, s2) {
    this.element = t2, this.type = 6, this._$AN = void 0, this._$AM = i2, this.options = s2;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t2) {
    M(this, t2);
  }
}
const B = t$1.litHtmlPolyfillSupport;
B == null ? void 0 : B(S, k), (t$1.litHtmlVersions ?? (t$1.litHtmlVersions = [])).push("3.3.2");
const D = (t2, i2, s2) => {
  const e2 = (s2 == null ? void 0 : s2.renderBefore) ?? i2;
  let h2 = e2._$litPart$;
  if (void 0 === h2) {
    const t3 = (s2 == null ? void 0 : s2.renderBefore) ?? null;
    e2._$litPart$ = h2 = new k(i2.insertBefore(c(), t3), t3, void 0, s2 ?? {});
  }
  return h2._$AI(t2), h2;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const s = globalThis;
class i extends y$1 {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var _a2;
    const t2 = super.createRenderRoot();
    return (_a2 = this.renderOptions).renderBefore ?? (_a2.renderBefore = t2.firstChild), t2;
  }
  update(t2) {
    const r2 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t2), this._$Do = D(r2, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    var _a2;
    super.connectedCallback(), (_a2 = this._$Do) == null ? void 0 : _a2.setConnected(true);
  }
  disconnectedCallback() {
    var _a2;
    super.disconnectedCallback(), (_a2 = this._$Do) == null ? void 0 : _a2.setConnected(false);
  }
  render() {
    return E;
  }
}
i._$litElement$ = true, i["finalized"] = true, (_a = s.litElementHydrateSupport) == null ? void 0 : _a.call(s, { LitElement: i });
const o$1 = s.litElementPolyfillSupport;
o$1 == null ? void 0 : o$1({ LitElement: i });
(s.litElementVersions ?? (s.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t = (t2) => (e2, o2) => {
  void 0 !== o2 ? o2.addInitializer(() => {
    customElements.define(t2, e2);
  }) : customElements.define(t2, e2);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const o = { attribute: true, type: String, converter: u$1, reflect: false, hasChanged: f$1 }, r$1 = (t2 = o, e2, r2) => {
  const { kind: n3, metadata: i2 } = r2;
  let s2 = globalThis.litPropertyMetadata.get(i2);
  if (void 0 === s2 && globalThis.litPropertyMetadata.set(i2, s2 = /* @__PURE__ */ new Map()), "setter" === n3 && ((t2 = Object.create(t2)).wrapped = true), s2.set(r2.name, t2), "accessor" === n3) {
    const { name: o2 } = r2;
    return { set(r3) {
      const n4 = e2.get.call(this);
      e2.set.call(this, r3), this.requestUpdate(o2, n4, t2, true, r3);
    }, init(e3) {
      return void 0 !== e3 && this.C(o2, void 0, t2, e3), e3;
    } };
  }
  if ("setter" === n3) {
    const { name: o2 } = r2;
    return function(r3) {
      const n4 = this[o2];
      e2.call(this, r3), this.requestUpdate(o2, n4, t2, true, r3);
    };
  }
  throw Error("Unsupported decorator location: " + n3);
};
function n2(t2) {
  return (e2, o2) => "object" == typeof o2 ? r$1(t2, e2, o2) : ((t3, e3, o3) => {
    const r2 = e3.hasOwnProperty(o3);
    return e3.constructor.createProperty(o3, t3), r2 ? Object.getOwnPropertyDescriptor(e3, o3) : void 0;
  })(t2, e2, o2);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function r(r2) {
  return n2({ ...r2, state: true, attribute: false });
}
const LOAD_TIMEOUT_MS = 1e4;
function withTimeout(promise, ms, label) {
  return Promise.race([
    promise,
    new Promise(
      (_2, reject) => setTimeout(() => reject(new Error(`Timeout waiting for ${label} (${ms}ms)`)), ms)
    )
  ]);
}
const loadHaElements = async () => {
  if (customElements.get("ha-card")) return;
  try {
    await withTimeout(
      customElements.whenDefined("partial-panel-resolver"),
      LOAD_TIMEOUT_MS,
      "partial-panel-resolver"
    );
    const ppr = document.createElement("partial-panel-resolver");
    ppr.hass = {
      panels: [
        {
          url_path: "tmp",
          component_name: "config"
        }
      ]
    };
    ppr._updateRoutes();
    await ppr.routerOptions.routes.tmp.load();
    if (!customElements.get("ha-card")) {
      await withTimeout(
        customElements.whenDefined("ha-card"),
        LOAD_TIMEOUT_MS,
        "ha-card"
      );
    }
  } catch (err) {
    console.warn("[kubernetes-panel] Failed to load HA elements:", err);
  }
};
var __defProp$5 = Object.defineProperty;
var __getOwnPropDesc$5 = Object.getOwnPropertyDescriptor;
var __decorateClass$5 = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc$5(target, key) : target;
  for (var i2 = decorators.length - 1, decorator; i2 >= 0; i2--)
    if (decorator = decorators[i2])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result) __defProp$5(target, key, result);
  return result;
};
const RESOURCE_ICONS = {
  pods: "mdi:cube-outline",
  nodes: "mdi:server",
  deployments: "mdi:rocket-launch",
  statefulsets: "mdi:database",
  daemonsets: "mdi:lan",
  cronjobs: "mdi:clock-outline",
  jobs: "mdi:briefcase-check"
};
const RESOURCE_LABELS = {
  pods: "Pods",
  nodes: "Nodes",
  deployments: "Deployments",
  statefulsets: "StatefulSets",
  daemonsets: "DaemonSets",
  cronjobs: "CronJobs",
  jobs: "Jobs"
};
const CONDITION_LABELS$1 = {
  memory_pressure: "Memory Pressure",
  disk_pressure: "Disk Pressure",
  pid_pressure: "PID Pressure",
  network_unavailable: "Network Unavailable"
};
let K8sOverview = class extends i {
  constructor() {
    super(...arguments);
    this._data = null;
    this._loading = true;
    this._error = null;
    this._expandedNamespaces = /* @__PURE__ */ new Set();
    this._loadingInFlight = false;
    this._boundVisibilityHandler = this._handleVisibilityChange.bind(this);
  }
  firstUpdated(_changedProps) {
    this._loadData();
    this._startPolling();
    document.addEventListener("visibilitychange", this._boundVisibilityHandler);
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this._stopPolling();
    document.removeEventListener("visibilitychange", this._boundVisibilityHandler);
  }
  _handleVisibilityChange() {
    if (document.hidden) {
      this._stopPolling();
    } else {
      this._loadData();
      this._startPolling();
    }
  }
  _startPolling() {
    if (!this._refreshInterval) {
      this._refreshInterval = setInterval(() => this._loadData(), 3e4);
    }
  }
  _stopPolling() {
    if (this._refreshInterval) {
      clearInterval(this._refreshInterval);
      this._refreshInterval = void 0;
    }
  }
  async _loadData() {
    if (this._loadingInFlight) return;
    this._loadingInFlight = true;
    if (!this._data) {
      this._loading = true;
    }
    this._error = null;
    try {
      const result = await this.hass.callWS({
        type: "kubernetes/cluster/overview"
      });
      this._data = result;
    } catch (err) {
      this._error = err.message || "Failed to load cluster data";
    } finally {
      this._loading = false;
      this._loadingInFlight = false;
    }
  }
  _toggleNamespaces(clusterId) {
    const updated = new Set(this._expandedNamespaces);
    if (updated.has(clusterId)) {
      updated.delete(clusterId);
    } else {
      updated.add(clusterId);
    }
    this._expandedNamespaces = updated;
  }
  _formatRelativeTime(timestamp) {
    if (!timestamp) return "Never";
    const now = Date.now() / 1e3;
    const diff = Math.max(0, Math.floor(now - timestamp));
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  }
  render() {
    var _a2;
    if (this._loading) {
      return b`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
    }
    if (this._error) {
      return b`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
    }
    if (!((_a2 = this._data) == null ? void 0 : _a2.clusters.length)) {
      return b` <div class="empty">No Kubernetes clusters configured.</div> `;
    }
    return b` ${this._data.clusters.map((c2) => this._renderCluster(c2))} `;
  }
  _renderCluster(cluster) {
    const totalAlerts = cluster.alerts.nodes_with_pressure.length + cluster.alerts.degraded_workloads.length + cluster.alerts.failed_pods.length;
    return b`
      <div class="cluster-section">
        <div class="cluster-header">
          <span class="cluster-name">${cluster.cluster_name}</span>
          ${this._renderHealthBadge(cluster.healthy)}
          ${this._renderWatchBadge(cluster.watch_enabled)}
        </div>

        <div class="meta-row">
          <div class="meta-item">
            <ha-icon icon="mdi:update"></ha-icon>
            <span>Updated ${this._formatRelativeTime(cluster.last_update)}</span>
          </div>
          <button class="refresh-btn" @click=${this._loadData} title="Refresh data">
            <ha-icon icon="mdi:refresh"></ha-icon>
          </button>
        </div>

        <div class="counts-grid">
          ${Object.entries(cluster.counts).map(
      ([key, count]) => b`
              <ha-card class="count-card">
                <ha-icon icon=${RESOURCE_ICONS[key] || "mdi:help"}></ha-icon>
                <div class="count-value">${count}</div>
                <div class="count-label">${RESOURCE_LABELS[key] || key}</div>
              </ha-card>
            `
    )}
        </div>

        <div class="alerts-section">
          <div class="alerts-header">
            <ha-icon icon="mdi:bell-outline"></ha-icon>
            <span>Alerts${totalAlerts > 0 ? ` (${totalAlerts})` : ""}</span>
            <span class="alerts-info-icon">
              <ha-icon icon="mdi:information-outline"></ha-icon>
              <div class="alerts-tooltip">
                Alerts monitor your cluster for issues that may need attention: nodes
                experiencing memory, disk, or PID pressure; workloads with fewer ready
                replicas than desired; and pods in a failed state.
              </div>
            </span>
          </div>
          ${totalAlerts > 0 ? this._renderAlerts(cluster.alerts) : b`
                <div class="no-alerts">
                  <ha-icon icon="mdi:check-circle"></ha-icon>
                  <div class="no-alerts-text">
                    <div class="no-alerts-title">No active alerts</div>
                    <div class="no-alerts-detail">
                      All nodes, workloads, and pods are operating normally.
                    </div>
                  </div>
                </div>
              `}
        </div>

        ${this._renderNamespaceSection(cluster)}
      </div>
    `;
  }
  _renderHealthBadge(healthy) {
    if (healthy === true) {
      return b`<span class="badge badge-healthy">Healthy</span>`;
    }
    if (healthy === false) {
      return b`<span class="badge badge-unhealthy">Unhealthy</span>`;
    }
    return b`<span class="badge badge-unknown">Unknown</span>`;
  }
  _renderWatchBadge(enabled) {
    if (enabled) {
      return b`
        <span class="badge badge-watch">
          <ha-icon icon="mdi:eye"></ha-icon> Watch Active
        </span>
      `;
    }
    return b`
      <span class="badge badge-watch-off">
        <ha-icon icon="mdi:eye-off"></ha-icon> Polling
      </span>
    `;
  }
  _renderNamespaceSection(cluster) {
    const nsEntries = Object.entries(cluster.namespaces);
    if (nsEntries.length === 0) return A;
    const expanded = this._expandedNamespaces.has(cluster.entry_id);
    return b`
      <div
        class="section-header"
        @click=${() => this._toggleNamespaces(cluster.entry_id)}
      >
        <ha-icon icon=${expanded ? "mdi:chevron-down" : "mdi:chevron-right"}></ha-icon>
        <span>Namespaces (${nsEntries.length})</span>
      </div>
      ${expanded ? this._renderNamespaceTable(nsEntries) : A}
    `;
  }
  _renderNamespaceTable(nsEntries) {
    const columns = [
      "pods",
      "deployments",
      "statefulsets",
      "daemonsets",
      "cronjobs",
      "jobs"
    ];
    return b`
      <table class="ns-table">
        <thead>
          <tr>
            <th>Namespace</th>
            ${columns.map((col) => b`<th>${RESOURCE_LABELS[col] || col}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${nsEntries.sort(([a2], [b2]) => a2.localeCompare(b2)).map(
      ([ns, counts]) => b`
                <tr>
                  <td>${ns}</td>
                  ${columns.map((col) => b`<td>${counts[col] || 0}</td>`)}
                </tr>
              `
    )}
        </tbody>
      </table>
    `;
  }
  _renderAlerts(alerts) {
    return b`
      ${alerts.nodes_with_pressure.map(
      (node) => b`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:server-network-off"></ha-icon>
            <div>
              <div class="alert-title">Node: ${node.name}</div>
              <div class="alert-detail">
                ${node.conditions.map((c2) => CONDITION_LABELS$1[c2] || c2).join(", ")}
              </div>
            </div>
          </div>
        `
    )}
      ${alerts.degraded_workloads.map(
      (wl) => b`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:alert"></ha-icon>
            <div>
              <div class="alert-title">${wl.type}: ${wl.namespace}/${wl.name}</div>
              <div class="alert-detail">${wl.ready}/${wl.desired} replicas ready</div>
            </div>
          </div>
        `
    )}
      ${alerts.failed_pods.map(
      (pod) => b`
          <div class="alert-card alert-error">
            <ha-icon icon="mdi:alert-octagon"></ha-icon>
            <div>
              <div class="alert-title">Pod: ${pod.namespace}/${pod.name}</div>
              <div class="alert-detail">Phase: ${pod.phase}</div>
            </div>
          </div>
        `
    )}
    `;
  }
};
K8sOverview.styles = i$3`
    :host {
      display: block;
    }

    .loading {
      display: flex;
      justify-content: center;
      padding: 64px 0;
    }

    .error-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px;
      text-align: center;
      color: var(--error-color, #db4437);
      --mdc-icon-size: 48px;
    }

    .error-card p {
      margin: 16px 0;
    }

    .retry-btn {
      cursor: pointer;
      padding: 8px 24px;
      border: 1px solid var(--primary-color);
      border-radius: 4px;
      background: transparent;
      color: var(--primary-color);
      font-size: 14px;
    }

    .retry-btn:hover {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }

    .empty {
      text-align: center;
      padding: 64px 16px;
      color: var(--secondary-text-color);
      font-size: 16px;
    }

    .cluster-section {
      margin-bottom: 24px;
    }

    .cluster-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }

    .cluster-name {
      font-size: 24px;
      font-weight: 500;
      color: var(--primary-text-color);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }

    .badge-healthy {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-unhealthy {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
      color: var(--error-color, #f44336);
    }

    .badge-unknown {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
      color: var(--disabled-color, #9e9e9e);
    }

    .badge-watch {
      background: rgba(var(--rgb-info-color, 33, 150, 243), 0.15);
      color: var(--info-color, #2196f3);
    }

    .badge-watch-off {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.1);
      color: var(--secondary-text-color);
    }

    .meta-row {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 16px;
      font-size: 13px;
      color: var(--secondary-text-color);
      flex-wrap: wrap;
    }

    .meta-item {
      display: flex;
      align-items: center;
      gap: 4px;
      --mdc-icon-size: 16px;
    }

    .refresh-btn {
      cursor: pointer;
      background: none;
      border: none;
      color: var(--primary-color);
      padding: 4px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      --mdc-icon-size: 18px;
    }

    .refresh-btn:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
    }

    .counts-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }

    .count-card {
      padding: 16px;
      border-radius: 12px;
      text-align: center;
      --mdc-icon-size: 28px;
    }

    .count-card ha-icon {
      color: var(--primary-color);
      margin-bottom: 8px;
    }

    .count-value {
      font-size: 28px;
      font-weight: 500;
      color: var(--primary-text-color);
    }

    .count-label {
      font-size: 13px;
      color: var(--secondary-text-color);
      margin-top: 4px;
    }

    .section-header {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      user-select: none;
      padding: 8px 0;
      font-size: 16px;
      font-weight: 500;
      color: var(--primary-text-color);
      --mdc-icon-size: 20px;
    }

    .section-header:hover {
      color: var(--primary-color);
    }

    .ns-table {
      width: 100%;
      border-collapse: collapse;
      margin: 8px 0 16px;
      font-size: 13px;
    }

    .ns-table th {
      text-align: left;
      padding: 8px 12px;
      color: var(--secondary-text-color);
      font-weight: 500;
      border-bottom: 1px solid var(--divider-color);
    }

    .ns-table td {
      padding: 6px 12px;
      border-bottom: 1px solid var(--divider-color);
    }

    .ns-table tr:last-child td {
      border-bottom: none;
    }

    .alerts-section {
      margin-top: 16px;
    }

    .alert-card {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px 16px;
      margin-bottom: 8px;
      border-radius: 8px;
      font-size: 14px;
      --mdc-icon-size: 20px;
    }

    .alert-warning {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.1);
      color: var(--primary-text-color);
    }

    .alert-warning ha-icon {
      color: var(--warning-color, #ff9800);
    }

    .alert-error {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
      color: var(--primary-text-color);
    }

    .alert-error ha-icon {
      color: var(--error-color, #f44336);
    }

    .alert-title {
      font-weight: 500;
    }

    .alert-detail {
      font-size: 13px;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }

    .no-alerts {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      border-radius: 8px;
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.08);
      font-size: 14px;
      --mdc-icon-size: 24px;
    }

    .no-alerts ha-icon {
      color: var(--success-color, #4caf50);
      flex-shrink: 0;
    }

    .no-alerts-text {
      flex: 1;
    }

    .no-alerts-title {
      font-weight: 500;
      color: var(--primary-text-color);
    }

    .no-alerts-detail {
      font-size: 12px;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }

    .alerts-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      font-size: 16px;
      font-weight: 500;
      color: var(--primary-text-color);
      --mdc-icon-size: 20px;
    }

    .alerts-info-icon {
      color: var(--secondary-text-color);
      cursor: help;
      --mdc-icon-size: 18px;
      position: relative;
    }

    .alerts-info-icon:hover {
      color: var(--primary-color);
    }

    .alerts-tooltip {
      display: none;
      position: absolute;
      bottom: calc(100% + 8px);
      left: 0;
      background: var(--card-background-color, #fff);
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      padding: 12px 16px;
      font-size: 12px;
      font-weight: 400;
      color: var(--secondary-text-color);
      width: 280px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      z-index: 10;
      line-height: 1.5;
    }

    .alerts-info-icon:hover .alerts-tooltip {
      display: block;
    }
  `;
__decorateClass$5([
  n2({ attribute: false })
], K8sOverview.prototype, "hass", 2);
__decorateClass$5([
  r()
], K8sOverview.prototype, "_data", 2);
__decorateClass$5([
  r()
], K8sOverview.prototype, "_loading", 2);
__decorateClass$5([
  r()
], K8sOverview.prototype, "_error", 2);
__decorateClass$5([
  r()
], K8sOverview.prototype, "_expandedNamespaces", 2);
K8sOverview = __decorateClass$5([
  t("k8s-overview")
], K8sOverview);
var __defProp$4 = Object.defineProperty;
var __getOwnPropDesc$4 = Object.getOwnPropertyDescriptor;
var __decorateClass$4 = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc$4(target, key) : target;
  for (var i2 = decorators.length - 1, decorator; i2 >= 0; i2--)
    if (decorator = decorators[i2])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result) __defProp$4(target, key, result);
  return result;
};
const CONDITION_LABELS = {
  memory_pressure: "Memory Pressure",
  disk_pressure: "Disk Pressure",
  pid_pressure: "PID Pressure",
  network_unavailable: "Network Unavailable"
};
let K8sNodesTable = class extends i {
  constructor() {
    super(...arguments);
    this._data = null;
    this._loading = true;
    this._error = null;
    this._expandedNodes = /* @__PURE__ */ new Set();
    this._statusFilter = "all";
    this._searchQuery = "";
    this._loadingInFlight = false;
    this._boundVisibilityHandler = this._handleVisibilityChange.bind(this);
  }
  firstUpdated(_changedProps) {
    this._loadData();
    this._startPolling();
    document.addEventListener("visibilitychange", this._boundVisibilityHandler);
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this._stopPolling();
    document.removeEventListener("visibilitychange", this._boundVisibilityHandler);
  }
  _handleVisibilityChange() {
    if (document.hidden) {
      this._stopPolling();
    } else {
      this._loadData();
      this._startPolling();
    }
  }
  _startPolling() {
    if (!this._refreshInterval) {
      this._refreshInterval = setInterval(() => this._loadData(), 3e4);
    }
  }
  _stopPolling() {
    if (this._refreshInterval) {
      clearInterval(this._refreshInterval);
      this._refreshInterval = void 0;
    }
  }
  async _loadData() {
    if (this._loadingInFlight) return;
    this._loadingInFlight = true;
    if (!this._data) {
      this._loading = true;
    }
    this._error = null;
    try {
      const result = await this.hass.callWS({
        type: "kubernetes/nodes/list"
      });
      this._data = result;
    } catch (err) {
      this._error = err.message || "Failed to load nodes data";
    } finally {
      this._loading = false;
      this._loadingInFlight = false;
    }
  }
  _toggleNode(nodeKey) {
    const updated = new Set(this._expandedNodes);
    if (updated.has(nodeKey)) {
      updated.delete(nodeKey);
    } else {
      updated.add(nodeKey);
    }
    this._expandedNodes = updated;
  }
  _getConditions(node) {
    const conditions = [];
    if (node.memory_pressure) conditions.push("memory_pressure");
    if (node.disk_pressure) conditions.push("disk_pressure");
    if (node.pid_pressure) conditions.push("pid_pressure");
    if (node.network_unavailable) conditions.push("network_unavailable");
    return conditions;
  }
  _formatAge(timestamp) {
    if (!timestamp || timestamp === "N/A") return "N/A";
    const created = new Date(timestamp).getTime();
    const now = Date.now();
    const diff = Math.max(0, Math.floor((now - created) / 1e3));
    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
    return `${Math.floor(diff / 86400)}d`;
  }
  _getFilteredNodes(nodes) {
    let filtered = nodes;
    if (this._statusFilter !== "all") {
      filtered = filtered.filter(
        (n3) => this._statusFilter === "ready" ? n3.status === "Ready" : n3.status !== "Ready"
      );
    }
    if (this._searchQuery) {
      const q = this._searchQuery.toLowerCase();
      filtered = filtered.filter(
        (n3) => n3.name.toLowerCase().includes(q) || n3.internal_ip.toLowerCase().includes(q) || n3.kubelet_version.toLowerCase().includes(q)
      );
    }
    return filtered;
  }
  render() {
    var _a2;
    if (this._loading) {
      return b`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
    }
    if (this._error) {
      return b`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
    }
    if (!((_a2 = this._data) == null ? void 0 : _a2.clusters.length)) {
      return b`<div class="empty">No Kubernetes clusters configured.</div>`;
    }
    return b`${this._data.clusters.map((c2) => this._renderCluster(c2))}`;
  }
  _renderCluster(cluster) {
    const filtered = this._getFilteredNodes(cluster.nodes);
    const readyCount = cluster.nodes.filter((n3) => n3.status === "Ready").length;
    return b`
      <div class="cluster-section">
        ${this._data.clusters.length > 1 ? b`<div class="cluster-name">${cluster.cluster_name}</div>` : A}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search nodes..."
            .value=${this._searchQuery}
            @input=${(e2) => {
      this._searchQuery = e2.target.value;
    }}
          />
          ${["all", "ready", "not-ready"].map(
      (f2) => b`
              <button
                class="filter-chip"
                ?active=${this._statusFilter === f2}
                @click=${() => {
        this._statusFilter = f2;
      }}
              >
                ${f2 === "all" ? "All" : f2 === "ready" ? "Ready" : "Not Ready"}
              </button>
            `
    )}
        </div>

        <div class="node-count">
          ${readyCount}/${cluster.nodes.length} nodes ready
          ${filtered.length !== cluster.nodes.length ? b` &middot; showing ${filtered.length}` : A}
        </div>

        ${filtered.length === 0 ? b`<div class="empty">No nodes match your filters.</div>` : filtered.map((node) => this._renderNode(cluster.entry_id, node))}
      </div>
    `;
  }
  _renderNode(entryId, node) {
    const nodeKey = `${entryId}_${node.name}`;
    const expanded = this._expandedNodes.has(nodeKey);
    const conditions = this._getConditions(node);
    const memPercent = node.memory_capacity_gib > 0 ? Math.round(node.memory_allocatable_gib / node.memory_capacity_gib * 100) : 0;
    return b`
      <ha-card class="node-card">
        <div class="node-row" @click=${() => this._toggleNode(nodeKey)}>
          <div class="node-name">
            <ha-icon
              icon=${expanded ? "mdi:chevron-down" : "mdi:chevron-right"}
            ></ha-icon>
            ${node.name}
            ${!node.schedulable ? b`<span class="badge badge-unschedulable">Unschedulable</span>` : A}
            ${conditions.length > 0 ? b`<span class="badge badge-condition"
                  >${conditions.length}
                  condition${conditions.length > 1 ? "s" : ""}</span
                >` : A}
          </div>
          <span
            class="badge ${node.status === "Ready" ? "badge-ready" : "badge-not-ready"}"
          >
            ${node.status}
          </span>
          <span class="node-ip">${node.internal_ip}</span>
          <div class="node-resources">
            <span>${node.cpu_cores} CPU</span>
            <div class="resource-bar-container">
              <div class="resource-bar">
                <div class="resource-bar-fill" style="width: ${memPercent}%"></div>
              </div>
              <span
                >${node.memory_allocatable_gib}/${node.memory_capacity_gib} GiB</span
              >
            </div>
          </div>
          <span class="node-age">${this._formatAge(node.creation_timestamp)}</span>
        </div>
        ${expanded ? this._renderNodeDetails(node, conditions) : A}
      </ha-card>
    `;
  }
  _renderNodeDetails(node, conditions) {
    return b`
      <div class="node-details">
        <div class="details-grid">
          <div class="detail-item">
            <span class="detail-label">Internal IP</span>
            <span class="detail-value mono">${node.internal_ip}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">External IP</span>
            <span class="detail-value mono">${node.external_ip}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">CPU Cores</span>
            <span class="detail-value">${node.cpu_cores}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Memory Capacity</span>
            <span class="detail-value">${node.memory_capacity_gib} GiB</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Memory Allocatable</span>
            <span class="detail-value">${node.memory_allocatable_gib} GiB</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">OS Image</span>
            <span class="detail-value">${node.os_image}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Kernel</span>
            <span class="detail-value mono">${node.kernel_version}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Container Runtime</span>
            <span class="detail-value">${node.container_runtime}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Kubelet Version</span>
            <span class="detail-value mono">${node.kubelet_version}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Schedulable</span>
            <span class="detail-value">${node.schedulable ? "Yes" : "No"}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Created</span>
            <span class="detail-value">${node.creation_timestamp}</span>
          </div>
        </div>
        ${conditions.length > 0 ? b`
              <div class="conditions-row">
                ${conditions.map(
      (c2) => b`
                    <span class="badge badge-condition">
                      ${CONDITION_LABELS[c2] || c2}
                    </span>
                  `
    )}
              </div>
            ` : A}
      </div>
    `;
  }
};
K8sNodesTable.styles = i$3`
    :host {
      display: block;
    }

    .loading {
      display: flex;
      justify-content: center;
      padding: 64px 0;
    }

    .error-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px;
      text-align: center;
      color: var(--error-color, #db4437);
      --mdc-icon-size: 48px;
    }

    .error-card p {
      margin: 16px 0;
    }

    .retry-btn {
      cursor: pointer;
      padding: 8px 24px;
      border: 1px solid var(--primary-color);
      border-radius: 4px;
      background: transparent;
      color: var(--primary-color);
      font-size: 14px;
    }

    .retry-btn:hover {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }

    .empty {
      text-align: center;
      padding: 64px 16px;
      color: var(--secondary-text-color);
      font-size: 16px;
    }

    .cluster-section {
      margin-bottom: 24px;
    }

    .cluster-name {
      font-size: 20px;
      font-weight: 500;
      color: var(--primary-text-color);
      margin-bottom: 12px;
    }

    .filters {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
      align-items: center;
    }

    .search-input {
      padding: 8px 12px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      font-size: 14px;
      min-width: 200px;
    }

    .search-input:focus {
      outline: none;
      border-color: var(--primary-color);
    }

    .filter-chip {
      display: inline-flex;
      align-items: center;
      padding: 6px 14px;
      border-radius: 16px;
      font-size: 13px;
      cursor: pointer;
      border: 1px solid var(--divider-color);
      background: transparent;
      color: var(--primary-text-color);
      user-select: none;
      transition:
        background 0.2s,
        border-color 0.2s;
    }

    .filter-chip:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08);
    }

    .filter-chip[active] {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
      border-color: var(--primary-color);
      color: var(--primary-color);
    }

    .node-card {
      margin-bottom: 8px;
      border-radius: 12px;
      overflow: hidden;
    }

    .node-row {
      display: grid;
      grid-template-columns: 1fr auto auto auto auto auto;
      align-items: center;
      gap: 16px;
      padding: 12px 16px;
      cursor: pointer;
      font-size: 14px;
      transition: background 0.15s;
    }

    .node-row:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.04);
    }

    .node-name {
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 8px;
      --mdc-icon-size: 18px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
    }

    .badge-ready {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-not-ready {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
      color: var(--error-color, #f44336);
    }

    .badge-unschedulable {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
      color: var(--warning-color, #ff9800);
    }

    .badge-condition {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
      color: var(--warning-color, #ff9800);
    }

    .node-ip {
      color: var(--secondary-text-color);
      font-size: 13px;
      font-family: monospace;
    }

    .node-resources {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 13px;
      color: var(--secondary-text-color);
      --mdc-icon-size: 16px;
    }

    .node-age {
      font-size: 13px;
      color: var(--secondary-text-color);
    }

    .node-details {
      padding: 0 16px 16px;
    }

    .details-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 12px;
    }

    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .detail-label {
      font-size: 12px;
      color: var(--secondary-text-color);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .detail-value {
      font-size: 14px;
      color: var(--primary-text-color);
    }

    .detail-value.mono {
      font-family: monospace;
    }

    .conditions-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 8px;
    }

    .resource-bar-container {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .resource-bar {
      width: 60px;
      height: 6px;
      background: var(--divider-color);
      border-radius: 3px;
      overflow: hidden;
    }

    .resource-bar-fill {
      height: 100%;
      border-radius: 3px;
      background: var(--primary-color);
    }

    .node-count {
      font-size: 13px;
      color: var(--secondary-text-color);
      margin-bottom: 8px;
    }

    @media (max-width: 768px) {
      .node-row {
        grid-template-columns: 1fr auto;
        gap: 8px;
      }

      .node-ip,
      .node-resources,
      .node-age {
        display: none;
      }
    }
  `;
__decorateClass$4([
  n2({ attribute: false })
], K8sNodesTable.prototype, "hass", 2);
__decorateClass$4([
  r()
], K8sNodesTable.prototype, "_data", 2);
__decorateClass$4([
  r()
], K8sNodesTable.prototype, "_loading", 2);
__decorateClass$4([
  r()
], K8sNodesTable.prototype, "_error", 2);
__decorateClass$4([
  r()
], K8sNodesTable.prototype, "_expandedNodes", 2);
__decorateClass$4([
  r()
], K8sNodesTable.prototype, "_statusFilter", 2);
__decorateClass$4([
  r()
], K8sNodesTable.prototype, "_searchQuery", 2);
K8sNodesTable = __decorateClass$4([
  t("k8s-nodes-table")
], K8sNodesTable);
var __defProp$3 = Object.defineProperty;
var __getOwnPropDesc$3 = Object.getOwnPropertyDescriptor;
var __decorateClass$3 = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc$3(target, key) : target;
  for (var i2 = decorators.length - 1, decorator; i2 >= 0; i2--)
    if (decorator = decorators[i2])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result) __defProp$3(target, key, result);
  return result;
};
const PHASE_CLASSES = {
  Running: "badge-running",
  Succeeded: "badge-succeeded",
  Pending: "badge-pending",
  Failed: "badge-failed",
  Unknown: "badge-unknown"
};
let K8sPodsTable = class extends i {
  constructor() {
    super(...arguments);
    this._data = null;
    this._loading = true;
    this._error = null;
    this._searchQuery = "";
    this._phaseFilter = "all";
    this._namespaceFilter = "all";
    this._sortField = "name";
    this._sortAsc = true;
    this._loadingInFlight = false;
    this._boundVisibilityHandler = this._handleVisibilityChange.bind(this);
  }
  firstUpdated(_changedProps) {
    this._loadData();
    this._startPolling();
    document.addEventListener("visibilitychange", this._boundVisibilityHandler);
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this._stopPolling();
    document.removeEventListener("visibilitychange", this._boundVisibilityHandler);
  }
  _handleVisibilityChange() {
    if (document.hidden) {
      this._stopPolling();
    } else {
      this._loadData();
      this._startPolling();
    }
  }
  _startPolling() {
    if (!this._refreshInterval) {
      this._refreshInterval = setInterval(() => this._loadData(), 3e4);
    }
  }
  _stopPolling() {
    if (this._refreshInterval) {
      clearInterval(this._refreshInterval);
      this._refreshInterval = void 0;
    }
  }
  async _loadData() {
    if (this._loadingInFlight) return;
    this._loadingInFlight = true;
    if (!this._data) {
      this._loading = true;
    }
    this._error = null;
    try {
      const result = await this.hass.callWS({
        type: "kubernetes/pods/list"
      });
      this._data = result;
    } catch (err) {
      this._error = err.message || "Failed to load pods data";
    } finally {
      this._loading = false;
      this._loadingInFlight = false;
    }
  }
  _formatAge(timestamp) {
    if (!timestamp || timestamp === "N/A") return "N/A";
    const created = new Date(timestamp).getTime();
    const now = Date.now();
    const diff = Math.max(0, Math.floor((now - created) / 1e3));
    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
    return `${Math.floor(diff / 86400)}d`;
  }
  _getNamespaces(pods) {
    return [...new Set(pods.map((p2) => p2.namespace))].sort();
  }
  _getFilteredPods(pods) {
    let filtered = pods;
    if (this._phaseFilter !== "all") {
      filtered = filtered.filter((p2) => p2.phase === this._phaseFilter);
    }
    if (this._namespaceFilter !== "all") {
      filtered = filtered.filter((p2) => p2.namespace === this._namespaceFilter);
    }
    if (this._searchQuery) {
      const q = this._searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p2) => p2.name.toLowerCase().includes(q) || p2.namespace.toLowerCase().includes(q) || p2.node_name.toLowerCase().includes(q) || p2.owner_name.toLowerCase().includes(q)
      );
    }
    filtered.sort((a2, b2) => {
      let valA;
      let valB;
      const field = this._sortField;
      if (field === "restarts") {
        valA = a2.restart_count;
        valB = b2.restart_count;
      } else if (field === "age") {
        valA = a2.creation_timestamp || "";
        valB = b2.creation_timestamp || "";
      } else {
        valA = a2[field] || "";
        valB = b2[field] || "";
      }
      const cmp = valA < valB ? -1 : valA > valB ? 1 : 0;
      return this._sortAsc ? cmp : -cmp;
    });
    return filtered;
  }
  _handleSort(field) {
    if (this._sortField === field) {
      this._sortAsc = !this._sortAsc;
    } else {
      this._sortField = field;
      this._sortAsc = true;
    }
  }
  _sortIcon(field) {
    if (this._sortField !== field) return "";
    return this._sortAsc ? "mdi:arrow-up" : "mdi:arrow-down";
  }
  render() {
    var _a2;
    if (this._loading) {
      return b`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
    }
    if (this._error) {
      return b`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
    }
    if (!((_a2 = this._data) == null ? void 0 : _a2.clusters.length)) {
      return b`<div class="empty">No Kubernetes clusters configured.</div>`;
    }
    return b`${this._data.clusters.map((c2) => this._renderCluster(c2))}`;
  }
  _renderCluster(cluster) {
    const filtered = this._getFilteredPods(cluster.pods);
    const namespaces = this._getNamespaces(cluster.pods);
    const phases = [...new Set(cluster.pods.map((p2) => p2.phase))].sort();
    return b`
      <div class="cluster-section">
        ${this._data.clusters.length > 1 ? b`<div class="cluster-name">${cluster.cluster_name}</div>` : A}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search pods..."
            .value=${this._searchQuery}
            @input=${(e2) => {
      this._searchQuery = e2.target.value;
    }}
          />

          <select
            class="ns-select"
            .value=${this._namespaceFilter}
            @change=${(e2) => {
      this._namespaceFilter = e2.target.value;
    }}
          >
            <option value="all">All namespaces</option>
            ${namespaces.map((ns) => b`<option value=${ns}>${ns}</option>`)}
          </select>

          <button
            class="filter-chip"
            ?active=${this._phaseFilter === "all"}
            @click=${() => {
      this._phaseFilter = "all";
    }}
          >
            All
          </button>
          ${phases.map(
      (phase) => b`
              <button
                class="filter-chip"
                ?active=${this._phaseFilter === phase}
                @click=${() => {
        this._phaseFilter = phase;
      }}
              >
                ${phase}
              </button>
            `
    )}
        </div>

        <div class="pod-count">${filtered.length}/${cluster.pods.length} pods</div>

        ${filtered.length === 0 ? b`<div class="empty">No pods match your filters.</div>` : b`
              <ha-card>
                <div class="table-wrapper">
                  <table class="pods-table">
                    <thead>
                      <tr>
                        <th @click=${() => this._handleSort("namespace")}>
                          Namespace
                          ${this._sortIcon("namespace") ? b`<ha-icon
                                icon=${this._sortIcon("namespace")}
                              ></ha-icon>` : A}
                        </th>
                        <th @click=${() => this._handleSort("name")}>
                          Name
                          ${this._sortIcon("name") ? b`<ha-icon icon=${this._sortIcon("name")}></ha-icon>` : A}
                        </th>
                        <th @click=${() => this._handleSort("phase")}>
                          Phase
                          ${this._sortIcon("phase") ? b`<ha-icon icon=${this._sortIcon("phase")}></ha-icon>` : A}
                        </th>
                        <th>Ready</th>
                        <th @click=${() => this._handleSort("restarts")}>
                          Restarts
                          ${this._sortIcon("restarts") ? b`<ha-icon
                                icon=${this._sortIcon("restarts")}
                              ></ha-icon>` : A}
                        </th>
                        <th
                          class="col-node"
                          @click=${() => this._handleSort("node_name")}
                        >
                          Node
                          ${this._sortIcon("node_name") ? b`<ha-icon
                                icon=${this._sortIcon("node_name")}
                              ></ha-icon>` : A}
                        </th>
                        <th class="col-ip">IP</th>
                        <th class="col-owner">Owner</th>
                        <th @click=${() => this._handleSort("age")}>
                          Age
                          ${this._sortIcon("age") ? b`<ha-icon icon=${this._sortIcon("age")}></ha-icon>` : A}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      ${filtered.map((pod) => this._renderPodRow(pod))}
                    </tbody>
                  </table>
                </div>
              </ha-card>
            `}
      </div>
    `;
  }
  _renderPodRow(pod) {
    const phaseClass = PHASE_CLASSES[pod.phase] || "badge-unknown";
    return b`
      <tr>
        <td>${pod.namespace}</td>
        <td class="pod-name">${pod.name}</td>
        <td><span class="badge ${phaseClass}">${pod.phase}</span></td>
        <td>${pod.ready_containers}/${pod.total_containers}</td>
        <td class=${pod.restart_count > 5 ? "restart-warn" : ""}>
          ${pod.restart_count}
        </td>
        <td class="col-node">${pod.node_name}</td>
        <td class="col-ip mono">${pod.pod_ip}</td>
        <td class="col-owner">
          ${pod.owner_kind !== "N/A" ? b`<span class="owner-info">${pod.owner_kind}/${pod.owner_name}</span>` : b`<span class="owner-info">-</span>`}
        </td>
        <td>${this._formatAge(pod.creation_timestamp)}</td>
      </tr>
    `;
  }
};
K8sPodsTable.styles = i$3`
    :host {
      display: block;
    }

    .loading {
      display: flex;
      justify-content: center;
      padding: 64px 0;
    }

    .error-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px;
      text-align: center;
      color: var(--error-color, #db4437);
      --mdc-icon-size: 48px;
    }

    .error-card p {
      margin: 16px 0;
    }

    .retry-btn {
      cursor: pointer;
      padding: 8px 24px;
      border: 1px solid var(--primary-color);
      border-radius: 4px;
      background: transparent;
      color: var(--primary-color);
      font-size: 14px;
    }

    .retry-btn:hover {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }

    .empty {
      text-align: center;
      padding: 64px 16px;
      color: var(--secondary-text-color);
      font-size: 16px;
    }

    .cluster-section {
      margin-bottom: 24px;
    }

    .cluster-name {
      font-size: 20px;
      font-weight: 500;
      color: var(--primary-text-color);
      margin-bottom: 12px;
    }

    .filters {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
      align-items: center;
    }

    .search-input {
      padding: 8px 12px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      font-size: 14px;
      min-width: 200px;
    }

    .search-input:focus {
      outline: none;
      border-color: var(--primary-color);
    }

    .filter-chip {
      display: inline-flex;
      align-items: center;
      padding: 6px 14px;
      border-radius: 16px;
      font-size: 13px;
      cursor: pointer;
      border: 1px solid var(--divider-color);
      background: transparent;
      color: var(--primary-text-color);
      user-select: none;
      transition:
        background 0.2s,
        border-color 0.2s;
    }

    .filter-chip:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08);
    }

    .filter-chip[active] {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
      border-color: var(--primary-color);
      color: var(--primary-color);
    }

    select.ns-select {
      padding: 6px 12px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      font-size: 13px;
    }

    .pod-count {
      font-size: 13px;
      color: var(--secondary-text-color);
      margin-bottom: 8px;
    }

    .pods-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    .pods-table th {
      text-align: left;
      padding: 10px 12px;
      color: var(--secondary-text-color);
      font-weight: 500;
      border-bottom: 2px solid var(--divider-color);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
      --mdc-icon-size: 14px;
    }

    .pods-table th:hover {
      color: var(--primary-color);
    }

    .pods-table th ha-icon {
      vertical-align: middle;
      margin-left: 2px;
    }

    .pods-table td {
      padding: 8px 12px;
      border-bottom: 1px solid var(--divider-color);
      vertical-align: middle;
    }

    .pods-table tr:last-child td {
      border-bottom: none;
    }

    .pods-table tr:hover td {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.04);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
    }

    .badge-running {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-succeeded {
      background: rgba(var(--rgb-info-color, 33, 150, 243), 0.15);
      color: var(--info-color, #2196f3);
    }

    .badge-pending {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
      color: var(--warning-color, #ff9800);
    }

    .badge-failed {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
      color: var(--error-color, #f44336);
    }

    .badge-unknown {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
      color: var(--disabled-color, #9e9e9e);
    }

    .mono {
      font-family: monospace;
    }

    .pod-name {
      font-weight: 500;
      word-break: break-all;
    }

    .owner-info {
      font-size: 12px;
      color: var(--secondary-text-color);
    }

    .restart-warn {
      color: var(--warning-color, #ff9800);
      font-weight: 500;
    }

    .table-wrapper {
      overflow-x: auto;
    }

    @media (max-width: 768px) {
      .col-node,
      .col-ip,
      .col-owner {
        display: none;
      }
    }
  `;
__decorateClass$3([
  n2({ attribute: false })
], K8sPodsTable.prototype, "hass", 2);
__decorateClass$3([
  r()
], K8sPodsTable.prototype, "_data", 2);
__decorateClass$3([
  r()
], K8sPodsTable.prototype, "_loading", 2);
__decorateClass$3([
  r()
], K8sPodsTable.prototype, "_error", 2);
__decorateClass$3([
  r()
], K8sPodsTable.prototype, "_searchQuery", 2);
__decorateClass$3([
  r()
], K8sPodsTable.prototype, "_phaseFilter", 2);
__decorateClass$3([
  r()
], K8sPodsTable.prototype, "_namespaceFilter", 2);
__decorateClass$3([
  r()
], K8sPodsTable.prototype, "_sortField", 2);
__decorateClass$3([
  r()
], K8sPodsTable.prototype, "_sortAsc", 2);
K8sPodsTable = __decorateClass$3([
  t("k8s-pods-table")
], K8sPodsTable);
var __defProp$2 = Object.defineProperty;
var __getOwnPropDesc$2 = Object.getOwnPropertyDescriptor;
var __decorateClass$2 = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc$2(target, key) : target;
  for (var i2 = decorators.length - 1, decorator; i2 >= 0; i2--)
    if (decorator = decorators[i2])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result) __defProp$2(target, key, result);
  return result;
};
let K8sWorkloads = class extends i {
  constructor() {
    super(...arguments);
    this._data = null;
    this._loading = true;
    this._error = null;
    this._namespaceFilter = "all";
    this._categoryFilter = "all";
    this._statusFilter = "all";
    this._searchQuery = "";
    this._actionInProgress = /* @__PURE__ */ new Set();
    this._actionError = null;
    this._loadingInFlight = false;
    this._boundVisibilityHandler = this._handleVisibilityChange.bind(this);
  }
  firstUpdated(_changedProps) {
    this._loadData();
    this._startPolling();
    document.addEventListener("visibilitychange", this._boundVisibilityHandler);
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this._stopPolling();
    document.removeEventListener("visibilitychange", this._boundVisibilityHandler);
  }
  _handleVisibilityChange() {
    if (document.hidden) {
      this._stopPolling();
    } else {
      this._loadData();
      this._startPolling();
    }
  }
  _startPolling() {
    if (!this._refreshInterval) {
      this._refreshInterval = setInterval(() => this._loadData(), 3e4);
    }
  }
  _stopPolling() {
    if (this._refreshInterval) {
      clearInterval(this._refreshInterval);
      this._refreshInterval = void 0;
    }
  }
  async _loadData() {
    if (this._loadingInFlight) return;
    this._loadingInFlight = true;
    if (!this._data) {
      this._loading = true;
    }
    this._error = null;
    try {
      const result = await this.hass.callWS({
        type: "kubernetes/workloads/list"
      });
      this._data = result;
    } catch (err) {
      this._error = err.message || "Failed to load workloads data";
    } finally {
      this._loading = false;
      this._loadingInFlight = false;
    }
  }
  _getNamespaces(cluster) {
    const namespaces = /* @__PURE__ */ new Set();
    for (const d2 of cluster.deployments) namespaces.add(d2.namespace);
    for (const s2 of cluster.statefulsets) namespaces.add(s2.namespace);
    for (const ds of cluster.daemonsets) namespaces.add(ds.namespace);
    for (const cj of cluster.cronjobs) namespaces.add(cj.namespace);
    for (const j of cluster.jobs) namespaces.add(j.namespace);
    return [...namespaces].sort();
  }
  _matchesNamespace(namespace) {
    return this._namespaceFilter === "all" || namespace === this._namespaceFilter;
  }
  _matchesSearch(name) {
    if (!this._searchQuery) return true;
    return name.toLowerCase().includes(this._searchQuery.toLowerCase());
  }
  _formatAge(timestamp) {
    if (!timestamp) return "N/A";
    const created = new Date(timestamp).getTime();
    const now = Date.now();
    const diff = Math.max(0, Math.floor((now - created) / 1e3));
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  }
  async _callService(service, data, actionKey) {
    const updated = new Set(this._actionInProgress);
    updated.add(actionKey);
    this._actionInProgress = updated;
    try {
      await this.hass.callService("kubernetes", service, data);
      setTimeout(() => this._loadData(), 2e3);
    } catch (err) {
      const message = (err == null ? void 0 : err.message) || "Service call failed";
      this._actionError = `Action failed: ${message}`;
      console.error("[k8s-workloads] Service call failed:", err);
    } finally {
      const done = new Set(this._actionInProgress);
      done.delete(actionKey);
      this._actionInProgress = done;
    }
  }
  render() {
    var _a2;
    if (this._loading) {
      return b`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
    }
    if (this._error) {
      return b`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
    }
    if (!((_a2 = this._data) == null ? void 0 : _a2.clusters.length)) {
      return b`<div class="empty">No Kubernetes clusters configured.</div>`;
    }
    return b`
      ${this._actionError ? b`
            <div class="action-error">
              <span>${this._actionError}</span>
              <button
                class="dismiss-btn"
                @click=${() => {
      this._actionError = null;
    }}
                title="Dismiss"
              >
                <ha-icon icon="mdi:close"></ha-icon>
              </button>
            </div>
          ` : A}
      ${this._data.clusters.map((c2) => this._renderCluster(c2))}
    `;
  }
  _renderCluster(cluster) {
    const namespaces = this._getNamespaces(cluster);
    return b`
      <div class="cluster-section">
        ${this._data.clusters.length > 1 ? b`<div class="cluster-name">${cluster.cluster_name}</div>` : A}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search workloads..."
            .value=${this._searchQuery}
            @input=${(e2) => {
      this._searchQuery = e2.target.value;
    }}
          />

          <select
            class="filter-select"
            .value=${this._namespaceFilter}
            @change=${(e2) => {
      this._namespaceFilter = e2.target.value;
    }}
          >
            <option value="all">All namespaces</option>
            ${namespaces.map((ns) => b`<option value=${ns}>${ns}</option>`)}
          </select>

          <select
            class="filter-select"
            .value=${this._categoryFilter}
            @change=${(e2) => {
      this._categoryFilter = e2.target.value;
    }}
          >
            <option value="all">All types</option>
            <option value="deployments">Deployments</option>
            <option value="statefulsets">StatefulSets</option>
            <option value="daemonsets">DaemonSets</option>
            <option value="cronjobs">CronJobs</option>
            <option value="jobs">Jobs</option>
          </select>

          ${["all", "healthy", "degraded", "stopped"].map(
      (f2) => b`
              <button
                class="filter-chip"
                ?active=${this._statusFilter === f2}
                @click=${() => {
        this._statusFilter = f2;
      }}
              >
                ${f2.charAt(0).toUpperCase() + f2.slice(1)}
              </button>
            `
    )}
        </div>

        ${this._shouldShowCategory("deployments") ? this._renderDeployments(cluster.deployments, cluster.entry_id) : A}
        ${this._shouldShowCategory("statefulsets") ? this._renderStatefulSets(cluster.statefulsets, cluster.entry_id) : A}
        ${this._shouldShowCategory("daemonsets") ? this._renderDaemonSets(cluster.daemonsets) : A}
        ${this._shouldShowCategory("cronjobs") ? this._renderCronJobs(cluster.cronjobs, cluster.entry_id) : A}
        ${this._shouldShowCategory("jobs") ? this._renderJobs(cluster.jobs) : A}
      </div>
    `;
  }
  _shouldShowCategory(category) {
    return this._categoryFilter === "all" || this._categoryFilter === category;
  }
  _getDeploymentStatus(d2) {
    if (d2.replicas === 0) return "stopped";
    if ((d2.available_replicas || 0) < d2.replicas) return "degraded";
    return "healthy";
  }
  _getStatefulSetStatus(s2) {
    if (s2.replicas === 0) return "stopped";
    if ((s2.ready_replicas || 0) < s2.replicas) return "degraded";
    return "healthy";
  }
  _getDaemonSetStatus(ds) {
    if (ds.desired_number_scheduled === 0) return "stopped";
    if ((ds.number_available || 0) < ds.desired_number_scheduled) return "degraded";
    return "healthy";
  }
  _matchesStatusFilter(status) {
    return this._statusFilter === "all" || this._statusFilter === status;
  }
  _statusBadgeClass(status) {
    const map = {
      all: "",
      healthy: "badge-healthy",
      degraded: "badge-degraded",
      stopped: "badge-stopped"
    };
    return map[status] || "";
  }
  _statusLabel(status) {
    const map = {
      all: "",
      healthy: "Healthy",
      degraded: "Degraded",
      stopped: "Stopped"
    };
    return map[status] || "";
  }
  _renderDeployments(deployments, entryId) {
    const filtered = deployments.filter(
      (d2) => this._matchesNamespace(d2.namespace) && this._matchesSearch(d2.name) && this._matchesStatusFilter(this._getDeploymentStatus(d2))
    );
    if (filtered.length === 0 && this._categoryFilter !== "all") {
      return b`<div class="empty">No deployments match your filters.</div>`;
    }
    if (filtered.length === 0) return A;
    return b`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:rocket-launch"></ha-icon>
          Deployments
          <span class="category-count">(${filtered.length})</span>
        </div>
        ${filtered.map((d2) => this._renderDeploymentCard(d2, entryId))}
      </div>
    `;
  }
  _renderDeploymentCard(d2, entryId) {
    const status = this._getDeploymentStatus(d2);
    const actionKey = `deploy_${d2.namespace}_${d2.name}`;
    const busy = this._actionInProgress.has(actionKey);
    return b`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${d2.name}</div>
            <div class="workload-namespace">${d2.namespace}</div>
          </div>
          <span class="replica-info">
            ${d2.available_replicas ?? 0}/${d2.replicas} ready
          </span>
          <span class="badge ${this._statusBadgeClass(status)}">
            ${this._statusLabel(status)}
          </span>
          <div class="workload-actions">
            ${d2.replicas === 0 ? b`
                  <button
                    class="action-btn start"
                    title="Start (scale to 1)"
                    ?disabled=${busy}
                    @click=${() => this._callService(
      "start_workload",
      {
        workload_name: d2.name,
        namespace: d2.namespace,
        entry_id: entryId
      },
      actionKey
    )}
                  >
                    <ha-icon icon="mdi:play"></ha-icon>
                  </button>
                ` : b`
                  <button
                    class="action-btn stop"
                    title="Stop (scale to 0)"
                    ?disabled=${busy}
                    @click=${() => this._callService(
      "stop_workload",
      {
        workload_name: d2.name,
        namespace: d2.namespace,
        entry_id: entryId
      },
      actionKey
    )}
                  >
                    <ha-icon icon="mdi:stop"></ha-icon>
                  </button>
                `}
          </div>
        </div>
      </ha-card>
    `;
  }
  _renderStatefulSets(statefulsets, entryId) {
    const filtered = statefulsets.filter(
      (s2) => this._matchesNamespace(s2.namespace) && this._matchesSearch(s2.name) && this._matchesStatusFilter(this._getStatefulSetStatus(s2))
    );
    if (filtered.length === 0 && this._categoryFilter !== "all") {
      return b`<div class="empty">No statefulsets match your filters.</div>`;
    }
    if (filtered.length === 0) return A;
    return b`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:database"></ha-icon>
          StatefulSets
          <span class="category-count">(${filtered.length})</span>
        </div>
        ${filtered.map((s2) => this._renderStatefulSetCard(s2, entryId))}
      </div>
    `;
  }
  _renderStatefulSetCard(s2, entryId) {
    const status = this._getStatefulSetStatus(s2);
    const actionKey = `sts_${s2.namespace}_${s2.name}`;
    const busy = this._actionInProgress.has(actionKey);
    return b`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${s2.name}</div>
            <div class="workload-namespace">${s2.namespace}</div>
          </div>
          <span class="replica-info">
            ${s2.ready_replicas ?? 0}/${s2.replicas} ready
          </span>
          <span class="badge ${this._statusBadgeClass(status)}">
            ${this._statusLabel(status)}
          </span>
          <div class="workload-actions">
            ${s2.replicas === 0 ? b`
                  <button
                    class="action-btn start"
                    title="Start (scale to 1)"
                    ?disabled=${busy}
                    @click=${() => this._callService(
      "start_workload",
      {
        workload_name: s2.name,
        namespace: s2.namespace,
        entry_id: entryId
      },
      actionKey
    )}
                  >
                    <ha-icon icon="mdi:play"></ha-icon>
                  </button>
                ` : b`
                  <button
                    class="action-btn stop"
                    title="Stop (scale to 0)"
                    ?disabled=${busy}
                    @click=${() => this._callService(
      "stop_workload",
      {
        workload_name: s2.name,
        namespace: s2.namespace,
        entry_id: entryId
      },
      actionKey
    )}
                  >
                    <ha-icon icon="mdi:stop"></ha-icon>
                  </button>
                `}
          </div>
        </div>
      </ha-card>
    `;
  }
  _renderDaemonSets(daemonsets) {
    const filtered = daemonsets.filter(
      (ds) => this._matchesNamespace(ds.namespace) && this._matchesSearch(ds.name) && this._matchesStatusFilter(this._getDaemonSetStatus(ds))
    );
    if (filtered.length === 0 && this._categoryFilter !== "all") {
      return b`<div class="empty">No daemonsets match your filters.</div>`;
    }
    if (filtered.length === 0) return A;
    return b`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:lan"></ha-icon>
          DaemonSets
          <span class="category-count">(${filtered.length})</span>
        </div>
        ${filtered.map((ds) => this._renderDaemonSetCard(ds))}
      </div>
    `;
  }
  _renderDaemonSetCard(ds) {
    const status = this._getDaemonSetStatus(ds);
    return b`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${ds.name}</div>
            <div class="workload-namespace">${ds.namespace}</div>
          </div>
          <span class="replica-info">
            ${ds.number_available ?? 0}/${ds.desired_number_scheduled} available
          </span>
          <span class="badge ${this._statusBadgeClass(status)}">
            ${this._statusLabel(status)}
          </span>
        </div>
      </ha-card>
    `;
  }
  _renderCronJobs(cronjobs, entryId) {
    const filtered = cronjobs.filter(
      (cj) => this._matchesNamespace(cj.namespace) && this._matchesSearch(cj.name)
    );
    const statusFiltered = this._statusFilter === "all" ? filtered : filtered.filter((cj) => {
      if (this._statusFilter === "stopped") return cj.suspend;
      if (this._statusFilter === "healthy") return !cj.suspend;
      return true;
    });
    if (statusFiltered.length === 0 && this._categoryFilter !== "all") {
      return b`<div class="empty">No cronjobs match your filters.</div>`;
    }
    if (statusFiltered.length === 0) return A;
    return b`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:clock-outline"></ha-icon>
          CronJobs
          <span class="category-count">(${statusFiltered.length})</span>
        </div>
        ${statusFiltered.map((cj) => this._renderCronJobCard(cj, entryId))}
      </div>
    `;
  }
  _renderCronJobCard(cj, entryId) {
    const actionKey = `cj_${cj.namespace}_${cj.name}`;
    const busy = this._actionInProgress.has(actionKey);
    return b`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${cj.name}</div>
            <div class="workload-namespace">${cj.namespace}</div>
          </div>
          <span class="schedule-info">${cj.schedule}</span>
          ${cj.active_jobs_count > 0 ? b`<span class="badge badge-active"
                >${cj.active_jobs_count} active</span
              >` : A}
          ${cj.suspend ? b`<span class="badge badge-suspended">Suspended</span>` : b`<span class="badge badge-healthy">Active</span>`}
          ${cj.last_schedule_time ? b`<span class="last-schedule"
                >Last: ${this._formatAge(cj.last_schedule_time)}</span
              >` : A}
          <div class="workload-actions">
            <button
              class="action-btn start"
              title="Trigger now"
              ?disabled=${busy}
              @click=${() => this._callService(
      "start_workload",
      {
        workload_name: cj.name,
        namespace: cj.namespace,
        entry_id: entryId
      },
      actionKey
    )}
            >
              <ha-icon icon="mdi:play"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `;
  }
  _renderJobs(jobs) {
    const filtered = jobs.filter(
      (j) => this._matchesNamespace(j.namespace) && this._matchesSearch(j.name)
    );
    const statusFiltered = this._statusFilter === "all" ? filtered : filtered.filter((j) => {
      if (this._statusFilter === "healthy") return j.succeeded >= j.completions;
      if (this._statusFilter === "degraded")
        return j.failed > 0 && j.succeeded < j.completions;
      if (this._statusFilter === "stopped") return j.active === 0;
      return true;
    });
    if (statusFiltered.length === 0 && this._categoryFilter !== "all") {
      return b`<div class="empty">No jobs match your filters.</div>`;
    }
    if (statusFiltered.length === 0) return A;
    return b`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:briefcase-check"></ha-icon>
          Jobs
          <span class="category-count">(${statusFiltered.length})</span>
        </div>
        ${statusFiltered.map((j) => this._renderJobCard(j))}
      </div>
    `;
  }
  _renderJobCard(j) {
    const isComplete = j.succeeded >= j.completions;
    const hasFailed = j.failed > 0;
    return b`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${j.name}</div>
            <div class="workload-namespace">${j.namespace}</div>
          </div>
          <span class="replica-info"> ${j.succeeded}/${j.completions} completed </span>
          ${j.active > 0 ? b`<span class="badge badge-active">${j.active} active</span>` : A}
          ${hasFailed ? b`<span class="badge badge-failed">${j.failed} failed</span>` : A}
          ${isComplete ? b`<span class="badge badge-complete">Complete</span>` : A}
          ${j.start_time ? b`<span class="last-schedule"
                >Started: ${this._formatAge(j.start_time)}</span
              >` : A}
        </div>
      </ha-card>
    `;
  }
};
K8sWorkloads.styles = i$3`
    :host {
      display: block;
    }

    .loading {
      display: flex;
      justify-content: center;
      padding: 64px 0;
    }

    .error-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px;
      text-align: center;
      color: var(--error-color, #db4437);
      --mdc-icon-size: 48px;
    }

    .error-card p {
      margin: 16px 0;
    }

    .retry-btn {
      cursor: pointer;
      padding: 8px 24px;
      border: 1px solid var(--primary-color);
      border-radius: 4px;
      background: transparent;
      color: var(--primary-color);
      font-size: 14px;
    }

    .retry-btn:hover {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }

    .empty {
      text-align: center;
      padding: 64px 16px;
      color: var(--secondary-text-color);
      font-size: 16px;
    }

    .cluster-section {
      margin-bottom: 24px;
    }

    .cluster-name {
      font-size: 20px;
      font-weight: 500;
      color: var(--primary-text-color);
      margin-bottom: 12px;
    }

    .filters {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
      align-items: center;
    }

    .search-input {
      padding: 8px 12px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      font-size: 14px;
      min-width: 200px;
    }

    .search-input:focus {
      outline: none;
      border-color: var(--primary-color);
    }

    select.filter-select {
      padding: 6px 12px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      font-size: 13px;
    }

    .filter-chip {
      display: inline-flex;
      align-items: center;
      padding: 6px 14px;
      border-radius: 16px;
      font-size: 13px;
      cursor: pointer;
      border: 1px solid var(--divider-color);
      background: transparent;
      color: var(--primary-text-color);
      user-select: none;
      transition:
        background 0.2s,
        border-color 0.2s;
    }

    .filter-chip:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08);
    }

    .filter-chip[active] {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
      border-color: var(--primary-color);
      color: var(--primary-color);
    }

    .category-section {
      margin-bottom: 20px;
    }

    .category-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 0;
      font-size: 16px;
      font-weight: 500;
      color: var(--primary-text-color);
      --mdc-icon-size: 20px;
    }

    .category-count {
      font-size: 13px;
      color: var(--secondary-text-color);
      font-weight: 400;
    }

    .workload-card {
      margin-bottom: 8px;
      border-radius: 12px;
      overflow: hidden;
    }

    .workload-row {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 12px 16px;
      font-size: 14px;
    }

    .workload-info {
      flex: 1;
      min-width: 0;
    }

    .workload-name {
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .workload-namespace {
      font-size: 12px;
      color: var(--secondary-text-color);
    }

    .workload-status {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
    }

    .badge-healthy {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-degraded {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
      color: var(--warning-color, #ff9800);
    }

    .badge-stopped {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
      color: var(--disabled-color, #9e9e9e);
    }

    .badge-failed {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
      color: var(--error-color, #f44336);
    }

    .badge-active {
      background: rgba(var(--rgb-info-color, 33, 150, 243), 0.15);
      color: var(--info-color, #2196f3);
    }

    .badge-suspended {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
      color: var(--disabled-color, #9e9e9e);
    }

    .badge-complete {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .replica-info {
      font-size: 13px;
      color: var(--secondary-text-color);
      white-space: nowrap;
    }

    .schedule-info {
      font-size: 13px;
      color: var(--secondary-text-color);
      font-family: monospace;
    }

    .workload-actions {
      display: flex;
      gap: 4px;
      flex-shrink: 0;
    }

    .action-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border: none;
      border-radius: 50%;
      background: transparent;
      cursor: pointer;
      color: var(--secondary-text-color);
      --mdc-icon-size: 18px;
      transition:
        background 0.15s,
        color 0.15s;
    }

    .action-btn:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
      color: var(--primary-color);
    }

    .action-btn[disabled] {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .action-btn.stop:hover {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
      color: var(--error-color, #f44336);
    }

    .action-btn.start:hover {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.1);
      color: var(--success-color, #4caf50);
    }

    .last-schedule {
      font-size: 12px;
      color: var(--secondary-text-color);
    }

    .action-error {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 16px;
      margin-bottom: 16px;
      border-radius: 8px;
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
      color: var(--error-color, #f44336);
      font-size: 14px;
    }

    .action-error .dismiss-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border: none;
      border-radius: 50%;
      background: transparent;
      cursor: pointer;
      color: var(--error-color, #f44336);
      --mdc-icon-size: 16px;
      flex-shrink: 0;
    }

    .action-error .dismiss-btn:hover {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
    }

    @media (max-width: 768px) {
      .workload-row {
        flex-wrap: wrap;
        gap: 8px;
      }

      .replica-info,
      .schedule-info {
        display: none;
      }
    }
  `;
__decorateClass$2([
  n2({ attribute: false })
], K8sWorkloads.prototype, "hass", 2);
__decorateClass$2([
  r()
], K8sWorkloads.prototype, "_data", 2);
__decorateClass$2([
  r()
], K8sWorkloads.prototype, "_loading", 2);
__decorateClass$2([
  r()
], K8sWorkloads.prototype, "_error", 2);
__decorateClass$2([
  r()
], K8sWorkloads.prototype, "_namespaceFilter", 2);
__decorateClass$2([
  r()
], K8sWorkloads.prototype, "_categoryFilter", 2);
__decorateClass$2([
  r()
], K8sWorkloads.prototype, "_statusFilter", 2);
__decorateClass$2([
  r()
], K8sWorkloads.prototype, "_searchQuery", 2);
__decorateClass$2([
  r()
], K8sWorkloads.prototype, "_actionInProgress", 2);
__decorateClass$2([
  r()
], K8sWorkloads.prototype, "_actionError", 2);
K8sWorkloads = __decorateClass$2([
  t("k8s-workloads")
], K8sWorkloads);
var __defProp$1 = Object.defineProperty;
var __getOwnPropDesc$1 = Object.getOwnPropertyDescriptor;
var __decorateClass$1 = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc$1(target, key) : target;
  for (var i2 = decorators.length - 1, decorator; i2 >= 0; i2--)
    if (decorator = decorators[i2])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result) __defProp$1(target, key, result);
  return result;
};
let K8sSettings = class extends i {
  constructor() {
    super(...arguments);
    this._data = null;
    this._loading = true;
    this._error = null;
  }
  firstUpdated(_changedProps) {
    this._loadData();
  }
  async _loadData() {
    this._loading = true;
    this._error = null;
    try {
      const result = await this.hass.callWS({
        type: "kubernetes/config/list"
      });
      this._data = result;
    } catch (err) {
      this._error = err.message || "Failed to load configuration";
    } finally {
      this._loading = false;
    }
  }
  _navigateToIntegration() {
    window.open("/config/integrations/integration/kubernetes", "_blank");
  }
  render() {
    var _a2;
    if (this._loading) {
      return b`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
    }
    if (this._error) {
      return b`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
    }
    if (!((_a2 = this._data) == null ? void 0 : _a2.entries.length)) {
      return b`<div class="empty">No Kubernetes entries configured.</div>`;
    }
    return b`${this._data.entries.map((e2) => this._renderEntry(e2))}`;
  }
  _renderEntry(entry) {
    return b`
      <div class="entry-section">
        <div class="entry-header">
          <span class="entry-name">${entry.cluster_name}</span>
          ${this._renderHealthBadge(entry.healthy)}
        </div>

        <div class="cards-grid">
          ${this._renderConnectionCard(entry)} ${this._renderNamespaceCard(entry)}
          ${this._renderTimingCard(entry)} ${this._renderFeaturesCard(entry)}
        </div>

        <div class="actions-bar">
          <button class="action-btn" @click=${this._navigateToIntegration}>
            <ha-icon icon="mdi:cog"></ha-icon>
            Configure Integration
          </button>
        </div>
      </div>
    `;
  }
  _renderHealthBadge(healthy) {
    if (healthy === true) {
      return b`<span class="badge badge-healthy">Connected</span>`;
    }
    if (healthy === false) {
      return b`<span class="badge badge-unhealthy">Disconnected</span>`;
    }
    return b`<span class="badge badge-unknown">Unknown</span>`;
  }
  _renderConnectionCard(entry) {
    return b`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:connection"></ha-icon>
          Connection
        </div>
        <div class="setting-row">
          <span class="setting-label">Host</span>
          <span class="setting-value">${entry.host}</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Port</span>
          <span class="setting-value">${entry.port}</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Verify SSL</span>
          <span class="setting-value">${this._renderBool(entry.verify_ssl)}</span>
        </div>
      </ha-card>
    `;
  }
  _renderNamespaceCard(entry) {
    return b`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:folder-multiple"></ha-icon>
          Namespaces
        </div>
        <div class="setting-row">
          <span class="setting-label">Monitor All</span>
          <span class="setting-value"
            >${this._renderBool(entry.monitor_all_namespaces)}</span
          >
        </div>
        ${!entry.monitor_all_namespaces && entry.namespaces.length > 0 ? b`
              <div class="setting-row">
                <span class="setting-label">Selected</span>
                <span class="setting-value">
                  <div class="namespace-tags">
                    ${entry.namespaces.map(
      (ns) => b`<span class="ns-tag">${ns}</span>`
    )}
                  </div>
                </span>
              </div>
            ` : A}
        <div class="setting-row">
          <span class="setting-label">Device Grouping</span>
          <span class="setting-value"
            >${entry.device_grouping_mode === "namespace" ? "By Namespace" : "By Cluster"}</span
          >
        </div>
      </ha-card>
    `;
  }
  _renderTimingCard(entry) {
    return b`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:timer-cog"></ha-icon>
          Timing
        </div>
        <div class="setting-row">
          <span class="setting-label">Poll Interval</span>
          <span class="setting-value">${entry.switch_update_interval}s</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Scale Timeout</span>
          <span class="setting-value">${entry.scale_verification_timeout}s</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Scale Cooldown</span>
          <span class="setting-value">${entry.scale_cooldown}s</span>
        </div>
      </ha-card>
    `;
  }
  _renderFeaturesCard(entry) {
    return b`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:flask"></ha-icon>
          Features
        </div>
        <div class="setting-row">
          <span class="setting-label">Sidebar Panel</span>
          <span class="setting-value">${this._renderBool(entry.panel_enabled)}</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Watch API</span>
          <span class="setting-value">${this._renderBool(entry.watch_enabled)}</span>
        </div>
      </ha-card>
    `;
  }
  _renderBool(value) {
    if (value) {
      return b`
        <span class="setting-value-bool bool-true">
          <ha-icon icon="mdi:check-circle"></ha-icon> Enabled
        </span>
      `;
    }
    return b`
      <span class="setting-value-bool bool-false">
        <ha-icon icon="mdi:close-circle-outline"></ha-icon> Disabled
      </span>
    `;
  }
};
K8sSettings.styles = i$3`
    :host {
      display: block;
    }

    .loading {
      display: flex;
      justify-content: center;
      padding: 64px 0;
    }

    .error-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px;
      text-align: center;
      color: var(--error-color, #db4437);
      --mdc-icon-size: 48px;
    }

    .error-card p {
      margin: 16px 0;
    }

    .retry-btn {
      cursor: pointer;
      padding: 8px 24px;
      border: 1px solid var(--primary-color);
      border-radius: 4px;
      background: transparent;
      color: var(--primary-color);
      font-size: 14px;
    }

    .retry-btn:hover {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }

    .empty {
      text-align: center;
      padding: 64px 16px;
      color: var(--secondary-text-color);
      font-size: 16px;
    }

    .entry-section {
      margin-bottom: 24px;
    }

    .entry-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }

    .entry-name {
      font-size: 24px;
      font-weight: 500;
      color: var(--primary-text-color);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }

    .badge-healthy {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-unhealthy {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
      color: var(--error-color, #f44336);
    }

    .badge-unknown {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
      color: var(--disabled-color, #9e9e9e);
    }

    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }

    .settings-card {
      padding: 20px;
      border-radius: 12px;
    }

    .card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 500;
      color: var(--primary-text-color);
      margin-bottom: 16px;
      --mdc-icon-size: 20px;
    }

    .card-title ha-icon {
      color: var(--primary-color);
    }

    .setting-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--divider-color);
      font-size: 14px;
    }

    .setting-row:last-child {
      border-bottom: none;
    }

    .setting-label {
      color: var(--secondary-text-color);
    }

    .setting-value {
      color: var(--primary-text-color);
      font-weight: 500;
      text-align: right;
      max-width: 60%;
      word-break: break-all;
    }

    .setting-value-bool {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      --mdc-icon-size: 16px;
    }

    .bool-true {
      color: var(--success-color, #4caf50);
    }

    .bool-false {
      color: var(--secondary-text-color);
    }

    .namespace-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      justify-content: flex-end;
    }

    .ns-tag {
      padding: 2px 8px;
      border-radius: 4px;
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
      color: var(--primary-color);
      font-size: 12px;
    }

    .actions-bar {
      display: flex;
      gap: 12px;
      margin-top: 16px;
      flex-wrap: wrap;
    }

    .action-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      padding: 8px 20px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: transparent;
      color: var(--primary-text-color);
      font-size: 14px;
      transition:
        background 0.2s,
        border-color 0.2s;
      --mdc-icon-size: 18px;
    }

    .action-btn:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08);
      border-color: var(--primary-color);
      color: var(--primary-color);
    }
  `;
__decorateClass$1([
  n2({ attribute: false })
], K8sSettings.prototype, "hass", 2);
__decorateClass$1([
  r()
], K8sSettings.prototype, "_data", 2);
__decorateClass$1([
  r()
], K8sSettings.prototype, "_loading", 2);
__decorateClass$1([
  r()
], K8sSettings.prototype, "_error", 2);
K8sSettings = __decorateClass$1([
  t("k8s-settings")
], K8sSettings);
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __decorateClass = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc(target, key) : target;
  for (var i2 = decorators.length - 1, decorator; i2 >= 0; i2--)
    if (decorator = decorators[i2])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result) __defProp(target, key, result);
  return result;
};
let KubernetesPanel = class extends i {
  constructor() {
    super(...arguments);
    this.narrow = false;
    this._activeTab = "overview";
    this._tabs = [
      { id: "overview", label: "Overview", icon: "mdi:view-dashboard" },
      { id: "nodes", label: "Nodes", icon: "mdi:server" },
      { id: "workloads", label: "Workloads", icon: "mdi:application-cog" },
      { id: "pods", label: "Pods", icon: "mdi:cube-outline" },
      { id: "settings", label: "Settings", icon: "mdi:cog" }
    ];
  }
  firstUpdated(_changedProps) {
    loadHaElements();
  }
  _handleTabChange(tab) {
    this._activeTab = tab;
  }
  _toggleSidebar() {
    this.dispatchEvent(
      new Event("hass-toggle-menu", { bubbles: true, composed: true })
    );
  }
  render() {
    return b`
      <div class="toolbar">
        <div class="menu-btn" @click=${this._toggleSidebar}>
          <ha-icon icon="mdi:menu"></ha-icon>
        </div>
        <h1>Kubernetes</h1>
      </div>
      <div class="tab-bar">
        ${this._tabs.map(
      (tab) => b`
            <div
              class="tab"
              ?active=${this._activeTab === tab.id}
              @click=${() => this._handleTabChange(tab.id)}
            >
              <ha-icon icon=${tab.icon}></ha-icon>
              <span>${tab.label}</span>
            </div>
          `
    )}
      </div>
      <div class="content">${this._renderActiveTab()}</div>
    `;
  }
  _renderActiveTab() {
    switch (this._activeTab) {
      case "overview":
        return b`<k8s-overview .hass=${this.hass}></k8s-overview>`;
      case "nodes":
        return b`<k8s-nodes-table .hass=${this.hass}></k8s-nodes-table>`;
      case "pods":
        return b`<k8s-pods-table .hass=${this.hass}></k8s-pods-table>`;
      case "workloads":
        return b`<k8s-workloads .hass=${this.hass}></k8s-workloads>`;
      case "settings":
        return b`<k8s-settings .hass=${this.hass}></k8s-settings>`;
      default:
        return b`
          <div class="coming-soon">
            <ha-icon icon="mdi:hammer-wrench"></ha-icon>
            <p>This tab is coming in a future release.</p>
          </div>
        `;
    }
  }
};
KubernetesPanel.styles = i$3`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
    }

    .toolbar {
      display: flex;
      align-items: center;
      height: 56px;
      padding: 0 16px;
      background: var(--app-header-background-color, var(--primary-color));
      color: var(--app-header-text-color, var(--text-primary-color, #fff));
      font-size: 20px;
      box-sizing: border-box;
    }

    .toolbar h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 400;
      flex: 1;
    }

    .menu-btn {
      display: none;
      cursor: pointer;
      margin-right: 8px;
      --mdc-icon-size: 24px;
    }

    :host([narrow]) .menu-btn {
      display: block;
    }

    .tab-bar {
      display: flex;
      background: var(--primary-background-color);
      border-bottom: 1px solid var(--divider-color);
      overflow-x: auto;
      scrollbar-width: none;
    }

    .tab-bar::-webkit-scrollbar {
      display: none;
    }

    .tab {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 12px 20px;
      cursor: pointer;
      font-size: 14px;
      color: var(--secondary-text-color);
      border-bottom: 2px solid transparent;
      white-space: nowrap;
      transition:
        color 0.2s,
        border-color 0.2s;
      user-select: none;
      --mdc-icon-size: 20px;
    }

    .tab:hover {
      color: var(--primary-text-color);
    }

    .tab[active] {
      color: var(--primary-color);
      border-bottom-color: var(--primary-color);
    }

    .content {
      padding: 16px;
      overflow-y: auto;
      flex: 1;
      box-sizing: border-box;
    }

    .coming-soon {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 64px 16px;
      color: var(--secondary-text-color);
      text-align: center;
      --mdc-icon-size: 48px;
    }

    .coming-soon p {
      margin-top: 16px;
      font-size: 16px;
    }
  `;
__decorateClass([
  n2({ attribute: false })
], KubernetesPanel.prototype, "hass", 2);
__decorateClass([
  n2({ type: Boolean, reflect: true })
], KubernetesPanel.prototype, "narrow", 2);
__decorateClass([
  n2({ attribute: false })
], KubernetesPanel.prototype, "route", 2);
__decorateClass([
  n2({ attribute: false })
], KubernetesPanel.prototype, "panel", 2);
__decorateClass([
  r()
], KubernetesPanel.prototype, "_activeTab", 2);
KubernetesPanel = __decorateClass([
  t("kubernetes-panel")
], KubernetesPanel);
export {
  KubernetesPanel
};
