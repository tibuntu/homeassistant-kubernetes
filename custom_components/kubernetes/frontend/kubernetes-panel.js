//#region node_modules/@lit/reactive-element/css-tag.js
/**
* @license
* Copyright 2019 Google LLC
* SPDX-License-Identifier: BSD-3-Clause
*/
var t$2 = globalThis, e$2 = t$2.ShadowRoot && (void 0 === t$2.ShadyCSS || t$2.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, s$2 = Symbol(), o$4 = /* @__PURE__ */ new WeakMap();
var n$3 = class {
	constructor(t, e, o) {
		if (this._$cssResult$ = !0, o !== s$2) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
		this.cssText = t, this.t = e;
	}
	get styleSheet() {
		let t = this.o;
		const s = this.t;
		if (e$2 && void 0 === t) {
			const e = void 0 !== s && 1 === s.length;
			e && (t = o$4.get(s)), void 0 === t && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), e && o$4.set(s, t));
		}
		return t;
	}
	toString() {
		return this.cssText;
	}
};
var r$4 = (t) => new n$3("string" == typeof t ? t : t + "", void 0, s$2), i$3 = (t, ...e) => {
	return new n$3(1 === t.length ? t[0] : e.reduce((e, s, o) => e + ((t) => {
		if (!0 === t._$cssResult$) return t.cssText;
		if ("number" == typeof t) return t;
		throw Error("Value passed to 'css' function must be a 'css' function result: " + t + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
	})(s) + t[o + 1], t[0]), t, s$2);
}, S$1 = (s, o) => {
	if (e$2) s.adoptedStyleSheets = o.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
	else for (const e of o) {
		const o = document.createElement("style"), n = t$2.litNonce;
		void 0 !== n && o.setAttribute("nonce", n), o.textContent = e.cssText, s.appendChild(o);
	}
}, c$2 = e$2 ? (t) => t : (t) => t instanceof CSSStyleSheet ? ((t) => {
	let e = "";
	for (const s of t.cssRules) e += s.cssText;
	return r$4(e);
})(t) : t;
//#endregion
//#region node_modules/@lit/reactive-element/reactive-element.js
/**
* @license
* Copyright 2017 Google LLC
* SPDX-License-Identifier: BSD-3-Clause
*/ var { is: i$2, defineProperty: e$1, getOwnPropertyDescriptor: h$1, getOwnPropertyNames: r$3, getOwnPropertySymbols: o$3, getPrototypeOf: n$2 } = Object, a$1 = globalThis, c$1 = a$1.trustedTypes, l$1 = c$1 ? c$1.emptyScript : "", p$1 = a$1.reactiveElementPolyfillSupport, d$1 = (t, s) => t, u$1 = {
	toAttribute(t, s) {
		switch (s) {
			case Boolean:
				t = t ? l$1 : null;
				break;
			case Object:
			case Array: t = null == t ? t : JSON.stringify(t);
		}
		return t;
	},
	fromAttribute(t, s) {
		let i = t;
		switch (s) {
			case Boolean:
				i = null !== t;
				break;
			case Number:
				i = null === t ? null : Number(t);
				break;
			case Object:
			case Array: try {
				i = JSON.parse(t);
			} catch (t) {
				i = null;
			}
		}
		return i;
	}
}, f$1 = (t, s) => !i$2(t, s), b$1 = {
	attribute: !0,
	type: String,
	converter: u$1,
	reflect: !1,
	useDefault: !1,
	hasChanged: f$1
};
Symbol.metadata ??= Symbol("metadata"), a$1.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var y$1 = class extends HTMLElement {
	static addInitializer(t) {
		this._$Ei(), (this.l ??= []).push(t);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(t, s = b$1) {
		if (s.state && (s.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((s = Object.create(s)).wrapped = !0), this.elementProperties.set(t, s), !s.noAccessor) {
			const i = Symbol(), h = this.getPropertyDescriptor(t, i, s);
			void 0 !== h && e$1(this.prototype, t, h);
		}
	}
	static getPropertyDescriptor(t, s, i) {
		const { get: e, set: r } = h$1(this.prototype, t) ?? {
			get() {
				return this[s];
			},
			set(t) {
				this[s] = t;
			}
		};
		return {
			get: e,
			set(s) {
				const h = e?.call(this);
				r?.call(this, s), this.requestUpdate(t, h, i);
			},
			configurable: !0,
			enumerable: !0
		};
	}
	static getPropertyOptions(t) {
		return this.elementProperties.get(t) ?? b$1;
	}
	static _$Ei() {
		if (this.hasOwnProperty(d$1("elementProperties"))) return;
		const t = n$2(this);
		t.finalize(), void 0 !== t.l && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(d$1("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(d$1("properties"))) {
			const t = this.properties, s = [...r$3(t), ...o$3(t)];
			for (const i of s) this.createProperty(i, t[i]);
		}
		const t = this[Symbol.metadata];
		if (null !== t) {
			const s = litPropertyMetadata.get(t);
			if (void 0 !== s) for (const [t, i] of s) this.elementProperties.set(t, i);
		}
		this._$Eh = /* @__PURE__ */ new Map();
		for (const [t, s] of this.elementProperties) {
			const i = this._$Eu(t, s);
			void 0 !== i && this._$Eh.set(i, t);
		}
		this.elementStyles = this.finalizeStyles(this.styles);
	}
	static finalizeStyles(s) {
		const i = [];
		if (Array.isArray(s)) {
			const e = new Set(s.flat(Infinity).reverse());
			for (const s of e) i.unshift(c$2(s));
		} else void 0 !== s && i.push(c$2(s));
		return i;
	}
	static _$Eu(t, s) {
		const i = s.attribute;
		return !1 === i ? void 0 : "string" == typeof i ? i : "string" == typeof t ? t.toLowerCase() : void 0;
	}
	constructor() {
		super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
	}
	_$Ev() {
		this._$ES = new Promise((t) => this.enableUpdating = t), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t) => t(this));
	}
	addController(t) {
		(this._$EO ??= /* @__PURE__ */ new Set()).add(t), void 0 !== this.renderRoot && this.isConnected && t.hostConnected?.();
	}
	removeController(t) {
		this._$EO?.delete(t);
	}
	_$E_() {
		const t = /* @__PURE__ */ new Map(), s = this.constructor.elementProperties;
		for (const i of s.keys()) this.hasOwnProperty(i) && (t.set(i, this[i]), delete this[i]);
		t.size > 0 && (this._$Ep = t);
	}
	createRenderRoot() {
		const t = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
		return S$1(t, this.constructor.elementStyles), t;
	}
	connectedCallback() {
		this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((t) => t.hostConnected?.());
	}
	enableUpdating(t) {}
	disconnectedCallback() {
		this._$EO?.forEach((t) => t.hostDisconnected?.());
	}
	attributeChangedCallback(t, s, i) {
		this._$AK(t, i);
	}
	_$ET(t, s) {
		const i = this.constructor.elementProperties.get(t), e = this.constructor._$Eu(t, i);
		if (void 0 !== e && !0 === i.reflect) {
			const h = (void 0 !== i.converter?.toAttribute ? i.converter : u$1).toAttribute(s, i.type);
			this._$Em = t, null == h ? this.removeAttribute(e) : this.setAttribute(e, h), this._$Em = null;
		}
	}
	_$AK(t, s) {
		const i = this.constructor, e = i._$Eh.get(t);
		if (void 0 !== e && this._$Em !== e) {
			const t = i.getPropertyOptions(e), h = "function" == typeof t.converter ? { fromAttribute: t.converter } : void 0 !== t.converter?.fromAttribute ? t.converter : u$1;
			this._$Em = e;
			const r = h.fromAttribute(s, t.type);
			this[e] = r ?? this._$Ej?.get(e) ?? r, this._$Em = null;
		}
	}
	requestUpdate(t, s, i, e = !1, h) {
		if (void 0 !== t) {
			const r = this.constructor;
			if (!1 === e && (h = this[t]), i ??= r.getPropertyOptions(t), !((i.hasChanged ?? f$1)(h, s) || i.useDefault && i.reflect && h === this._$Ej?.get(t) && !this.hasAttribute(r._$Eu(t, i)))) return;
			this.C(t, s, i);
		}
		!1 === this.isUpdatePending && (this._$ES = this._$EP());
	}
	C(t, s, { useDefault: i, reflect: e, wrapped: h }, r) {
		i && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t) && (this._$Ej.set(t, r ?? s ?? this[t]), !0 !== h || void 0 !== r) || (this._$AL.has(t) || (this.hasUpdated || i || (s = void 0), this._$AL.set(t, s)), !0 === e && this._$Em !== t && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t));
	}
	async _$EP() {
		this.isUpdatePending = !0;
		try {
			await this._$ES;
		} catch (t) {
			Promise.reject(t);
		}
		const t = this.scheduleUpdate();
		return null != t && await t, !this.isUpdatePending;
	}
	scheduleUpdate() {
		return this.performUpdate();
	}
	performUpdate() {
		if (!this.isUpdatePending) return;
		if (!this.hasUpdated) {
			if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
				for (const [t, s] of this._$Ep) this[t] = s;
				this._$Ep = void 0;
			}
			const t = this.constructor.elementProperties;
			if (t.size > 0) for (const [s, i] of t) {
				const { wrapped: t } = i, e = this[s];
				!0 !== t || this._$AL.has(s) || void 0 === e || this.C(s, void 0, i, e);
			}
		}
		let t = !1;
		const s = this._$AL;
		try {
			t = this.shouldUpdate(s), t ? (this.willUpdate(s), this._$EO?.forEach((t) => t.hostUpdate?.()), this.update(s)) : this._$EM();
		} catch (s) {
			throw t = !1, this._$EM(), s;
		}
		t && this._$AE(s);
	}
	willUpdate(t) {}
	_$AE(t) {
		this._$EO?.forEach((t) => t.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(t)), this.updated(t);
	}
	_$EM() {
		this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
	}
	get updateComplete() {
		return this.getUpdateComplete();
	}
	getUpdateComplete() {
		return this._$ES;
	}
	shouldUpdate(t) {
		return !0;
	}
	update(t) {
		this._$Eq &&= this._$Eq.forEach((t) => this._$ET(t, this[t])), this._$EM();
	}
	updated(t) {}
	firstUpdated(t) {}
};
y$1.elementStyles = [], y$1.shadowRootOptions = { mode: "open" }, y$1[d$1("elementProperties")] = /* @__PURE__ */ new Map(), y$1[d$1("finalized")] = /* @__PURE__ */ new Map(), p$1?.({ ReactiveElement: y$1 }), (a$1.reactiveElementVersions ??= []).push("2.1.2");
//#endregion
//#region node_modules/lit-html/lit-html.js
/**
* @license
* Copyright 2017 Google LLC
* SPDX-License-Identifier: BSD-3-Clause
*/
var t$1 = globalThis, i$1 = (t) => t, s$1 = t$1.trustedTypes, e = s$1 ? s$1.createPolicy("lit-html", { createHTML: (t) => t }) : void 0, h = "$lit$", o$2 = `lit$${Math.random().toFixed(9).slice(2)}$`, n$1 = "?" + o$2, r$2 = `<${n$1}>`, l = document, c = () => l.createComment(""), a = (t) => null === t || "object" != typeof t && "function" != typeof t, u = Array.isArray, d = (t) => u(t) || "function" == typeof t?.[Symbol.iterator], f = "[ 	\n\f\r]", v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, _ = /-->/g, m = />/g, p = RegExp(`>|${f}(?:([^\\s"'>=/]+)(${f}*=${f}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), g = /'/g, $ = /"/g, y = /^(?:script|style|textarea|title)$/i, x = (t) => (i, ...s) => ({
	_$litType$: t,
	strings: i,
	values: s
}), b = x(1);
x(2);
x(3);
var E = Symbol.for("lit-noChange"), A = Symbol.for("lit-nothing"), C = /* @__PURE__ */ new WeakMap(), P = l.createTreeWalker(l, 129);
function V(t, i) {
	if (!u(t) || !t.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return void 0 !== e ? e.createHTML(i) : i;
}
var N = (t, i) => {
	const s = t.length - 1, e = [];
	let n, l = 2 === i ? "<svg>" : 3 === i ? "<math>" : "", c = v;
	for (let i = 0; i < s; i++) {
		const s = t[i];
		let a, u, d = -1, f = 0;
		for (; f < s.length && (c.lastIndex = f, u = c.exec(s), null !== u);) f = c.lastIndex, c === v ? "!--" === u[1] ? c = _ : void 0 !== u[1] ? c = m : void 0 !== u[2] ? (y.test(u[2]) && (n = RegExp("</" + u[2], "g")), c = p) : void 0 !== u[3] && (c = p) : c === p ? ">" === u[0] ? (c = n ?? v, d = -1) : void 0 === u[1] ? d = -2 : (d = c.lastIndex - u[2].length, a = u[1], c = void 0 === u[3] ? p : "\"" === u[3] ? $ : g) : c === $ || c === g ? c = p : c === _ || c === m ? c = v : (c = p, n = void 0);
		const x = c === p && t[i + 1].startsWith("/>") ? " " : "";
		l += c === v ? s + r$2 : d >= 0 ? (e.push(a), s.slice(0, d) + h + s.slice(d) + o$2 + x) : s + o$2 + (-2 === d ? i : x);
	}
	return [V(t, l + (t[s] || "<?>") + (2 === i ? "</svg>" : 3 === i ? "</math>" : "")), e];
};
var S = class S {
	constructor({ strings: t, _$litType$: i }, e) {
		let r;
		this.parts = [];
		let l = 0, a = 0;
		const u = t.length - 1, d = this.parts, [f, v] = N(t, i);
		if (this.el = S.createElement(f, e), P.currentNode = this.el.content, 2 === i || 3 === i) {
			const t = this.el.content.firstChild;
			t.replaceWith(...t.childNodes);
		}
		for (; null !== (r = P.nextNode()) && d.length < u;) {
			if (1 === r.nodeType) {
				if (r.hasAttributes()) for (const t of r.getAttributeNames()) if (t.endsWith(h)) {
					const i = v[a++], s = r.getAttribute(t).split(o$2), e = /([.?@])?(.*)/.exec(i);
					d.push({
						type: 1,
						index: l,
						name: e[2],
						strings: s,
						ctor: "." === e[1] ? I : "?" === e[1] ? L : "@" === e[1] ? z : H
					}), r.removeAttribute(t);
				} else t.startsWith(o$2) && (d.push({
					type: 6,
					index: l
				}), r.removeAttribute(t));
				if (y.test(r.tagName)) {
					const t = r.textContent.split(o$2), i = t.length - 1;
					if (i > 0) {
						r.textContent = s$1 ? s$1.emptyScript : "";
						for (let s = 0; s < i; s++) r.append(t[s], c()), P.nextNode(), d.push({
							type: 2,
							index: ++l
						});
						r.append(t[i], c());
					}
				}
			} else if (8 === r.nodeType) if (r.data === n$1) d.push({
				type: 2,
				index: l
			});
			else {
				let t = -1;
				for (; -1 !== (t = r.data.indexOf(o$2, t + 1));) d.push({
					type: 7,
					index: l
				}), t += o$2.length - 1;
			}
			l++;
		}
	}
	static createElement(t, i) {
		const s = l.createElement("template");
		return s.innerHTML = t, s;
	}
};
function M(t, i, s = t, e) {
	if (i === E) return i;
	let h = void 0 !== e ? s._$Co?.[e] : s._$Cl;
	const o = a(i) ? void 0 : i._$litDirective$;
	return h?.constructor !== o && (h?._$AO?.(!1), void 0 === o ? h = void 0 : (h = new o(t), h._$AT(t, s, e)), void 0 !== e ? (s._$Co ??= [])[e] = h : s._$Cl = h), void 0 !== h && (i = M(t, h._$AS(t, i.values), h, e)), i;
}
var R = class {
	constructor(t, i) {
		this._$AV = [], this._$AN = void 0, this._$AD = t, this._$AM = i;
	}
	get parentNode() {
		return this._$AM.parentNode;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	u(t) {
		const { el: { content: i }, parts: s } = this._$AD, e = (t?.creationScope ?? l).importNode(i, !0);
		P.currentNode = e;
		let h = P.nextNode(), o = 0, n = 0, r = s[0];
		for (; void 0 !== r;) {
			if (o === r.index) {
				let i;
				2 === r.type ? i = new k(h, h.nextSibling, this, t) : 1 === r.type ? i = new r.ctor(h, r.name, r.strings, this, t) : 6 === r.type && (i = new Z(h, this, t)), this._$AV.push(i), r = s[++n];
			}
			o !== r?.index && (h = P.nextNode(), o++);
		}
		return P.currentNode = l, e;
	}
	p(t) {
		let i = 0;
		for (const s of this._$AV) void 0 !== s && (void 0 !== s.strings ? (s._$AI(t, s, i), i += s.strings.length - 2) : s._$AI(t[i])), i++;
	}
};
var k = class k {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(t, i, s, e) {
		this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = t, this._$AB = i, this._$AM = s, this.options = e, this._$Cv = e?.isConnected ?? !0;
	}
	get parentNode() {
		let t = this._$AA.parentNode;
		const i = this._$AM;
		return void 0 !== i && 11 === t?.nodeType && (t = i.parentNode), t;
	}
	get startNode() {
		return this._$AA;
	}
	get endNode() {
		return this._$AB;
	}
	_$AI(t, i = this) {
		t = M(this, t, i), a(t) ? t === A || null == t || "" === t ? (this._$AH !== A && this._$AR(), this._$AH = A) : t !== this._$AH && t !== E && this._(t) : void 0 !== t._$litType$ ? this.$(t) : void 0 !== t.nodeType ? this.T(t) : d(t) ? this.k(t) : this._(t);
	}
	O(t) {
		return this._$AA.parentNode.insertBefore(t, this._$AB);
	}
	T(t) {
		this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
	}
	_(t) {
		this._$AH !== A && a(this._$AH) ? this._$AA.nextSibling.data = t : this.T(l.createTextNode(t)), this._$AH = t;
	}
	$(t) {
		const { values: i, _$litType$: s } = t, e = "number" == typeof s ? this._$AC(t) : (void 0 === s.el && (s.el = S.createElement(V(s.h, s.h[0]), this.options)), s);
		if (this._$AH?._$AD === e) this._$AH.p(i);
		else {
			const t = new R(e, this), s = t.u(this.options);
			t.p(i), this.T(s), this._$AH = t;
		}
	}
	_$AC(t) {
		let i = C.get(t.strings);
		return void 0 === i && C.set(t.strings, i = new S(t)), i;
	}
	k(t) {
		u(this._$AH) || (this._$AH = [], this._$AR());
		const i = this._$AH;
		let s, e = 0;
		for (const h of t) e === i.length ? i.push(s = new k(this.O(c()), this.O(c()), this, this.options)) : s = i[e], s._$AI(h), e++;
		e < i.length && (this._$AR(s && s._$AB.nextSibling, e), i.length = e);
	}
	_$AR(t = this._$AA.nextSibling, s) {
		for (this._$AP?.(!1, !0, s); t !== this._$AB;) {
			const s = i$1(t).nextSibling;
			i$1(t).remove(), t = s;
		}
	}
	setConnected(t) {
		void 0 === this._$AM && (this._$Cv = t, this._$AP?.(t));
	}
};
var H = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(t, i, s, e, h) {
		this.type = 1, this._$AH = A, this._$AN = void 0, this.element = t, this.name = i, this._$AM = e, this.options = h, s.length > 2 || "" !== s[0] || "" !== s[1] ? (this._$AH = Array(s.length - 1).fill(/* @__PURE__ */ new String()), this.strings = s) : this._$AH = A;
	}
	_$AI(t, i = this, s, e) {
		const h = this.strings;
		let o = !1;
		if (void 0 === h) t = M(this, t, i, 0), o = !a(t) || t !== this._$AH && t !== E, o && (this._$AH = t);
		else {
			const e = t;
			let n, r;
			for (t = h[0], n = 0; n < h.length - 1; n++) r = M(this, e[s + n], i, n), r === E && (r = this._$AH[n]), o ||= !a(r) || r !== this._$AH[n], r === A ? t = A : t !== A && (t += (r ?? "") + h[n + 1]), this._$AH[n] = r;
		}
		o && !e && this.j(t);
	}
	j(t) {
		t === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
	}
};
var I = class extends H {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(t) {
		this.element[this.name] = t === A ? void 0 : t;
	}
};
var L = class extends H {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(t) {
		this.element.toggleAttribute(this.name, !!t && t !== A);
	}
};
var z = class extends H {
	constructor(t, i, s, e, h) {
		super(t, i, s, e, h), this.type = 5;
	}
	_$AI(t, i = this) {
		if ((t = M(this, t, i, 0) ?? A) === E) return;
		const s = this._$AH, e = t === A && s !== A || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, h = t !== A && (s === A || e);
		e && this.element.removeEventListener(this.name, this, s), h && this.element.addEventListener(this.name, this, t), this._$AH = t;
	}
	handleEvent(t) {
		"function" == typeof this._$AH ? this._$AH.call(this.options?.host ?? this.element, t) : this._$AH.handleEvent(t);
	}
};
var Z = class {
	constructor(t, i, s) {
		this.element = t, this.type = 6, this._$AN = void 0, this._$AM = i, this.options = s;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(t) {
		M(this, t);
	}
}, B = t$1.litHtmlPolyfillSupport;
B?.(S, k), (t$1.litHtmlVersions ??= []).push("3.3.2");
var D = (t, i, s) => {
	const e = s?.renderBefore ?? i;
	let h = e._$litPart$;
	if (void 0 === h) {
		const t = s?.renderBefore ?? null;
		e._$litPart$ = h = new k(i.insertBefore(c(), t), t, void 0, s ?? {});
	}
	return h._$AI(t), h;
};
//#endregion
//#region node_modules/lit-element/lit-element.js
/**
* @license
* Copyright 2017 Google LLC
* SPDX-License-Identifier: BSD-3-Clause
*/ var s = globalThis;
var i = class extends y$1 {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		const t = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= t.firstChild, t;
	}
	update(t) {
		const r = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = D(r, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return E;
	}
};
i._$litElement$ = !0, i["finalized"] = !0, s.litElementHydrateSupport?.({ LitElement: i });
var o$1 = s.litElementPolyfillSupport;
o$1?.({ LitElement: i });
(s.litElementVersions ??= []).push("4.2.2");
//#endregion
//#region node_modules/@lit/reactive-element/decorators/custom-element.js
/**
* @license
* Copyright 2017 Google LLC
* SPDX-License-Identifier: BSD-3-Clause
*/
var t = (t) => (e, o) => {
	void 0 !== o ? o.addInitializer(() => {
		customElements.define(t, e);
	}) : customElements.define(t, e);
};
//#endregion
//#region node_modules/@lit/reactive-element/decorators/property.js
/**
* @license
* Copyright 2017 Google LLC
* SPDX-License-Identifier: BSD-3-Clause
*/ var o = {
	attribute: !0,
	type: String,
	converter: u$1,
	reflect: !1,
	hasChanged: f$1
}, r$1 = (t = o, e, r) => {
	const { kind: n, metadata: i } = r;
	let s = globalThis.litPropertyMetadata.get(i);
	if (void 0 === s && globalThis.litPropertyMetadata.set(i, s = /* @__PURE__ */ new Map()), "setter" === n && ((t = Object.create(t)).wrapped = !0), s.set(r.name, t), "accessor" === n) {
		const { name: o } = r;
		return {
			set(r) {
				const n = e.get.call(this);
				e.set.call(this, r), this.requestUpdate(o, n, t, !0, r);
			},
			init(e) {
				return void 0 !== e && this.C(o, void 0, t, e), e;
			}
		};
	}
	if ("setter" === n) {
		const { name: o } = r;
		return function(r) {
			const n = this[o];
			e.call(this, r), this.requestUpdate(o, n, t, !0, r);
		};
	}
	throw Error("Unsupported decorator location: " + n);
};
function n(t) {
	return (e, o) => "object" == typeof o ? r$1(t, e, o) : ((t, e, o) => {
		const r = e.hasOwnProperty(o);
		return e.constructor.createProperty(o, t), r ? Object.getOwnPropertyDescriptor(e, o) : void 0;
	})(t, e, o);
}
//#endregion
//#region node_modules/@lit/reactive-element/decorators/state.js
/**
* @license
* Copyright 2017 Google LLC
* SPDX-License-Identifier: BSD-3-Clause
*/ function r(r) {
	return n({
		...r,
		state: !0,
		attribute: !1
	});
}
//#endregion
//#region src/utils/load-ha-elements.ts
/**
* Load Home Assistant built-in elements (ha-card, ha-icon, etc.) so they can
* be used inside our custom panel.
*
* This uses the well-known community technique of loading HA's own panel
* resolver to trigger element registration.
*/
var LOAD_TIMEOUT_MS = 1e4;
function withTimeout(promise, ms, label) {
	return Promise.race([promise, new Promise((_, reject) => setTimeout(() => reject(/* @__PURE__ */ new Error(`Timeout waiting for ${label} (${ms}ms)`)), ms))]);
}
var loadHaElements = async () => {
	if (customElements.get("ha-card")) return;
	try {
		await withTimeout(customElements.whenDefined("partial-panel-resolver"), LOAD_TIMEOUT_MS, "partial-panel-resolver");
		const ppr = document.createElement("partial-panel-resolver");
		ppr.hass = { panels: [{
			url_path: "tmp",
			component_name: "config"
		}] };
		ppr._updateRoutes();
		await ppr.routerOptions.routes.tmp.load();
		if (!customElements.get("ha-card")) await withTimeout(customElements.whenDefined("ha-card"), LOAD_TIMEOUT_MS, "ha-card");
	} catch (err) {
		console.warn("[kubernetes-panel] Failed to load HA elements:", err);
	}
};
//#endregion
//#region \0@oxc-project+runtime@0.123.0/helpers/decorate.js
function __decorate(decorators, target, key, desc) {
	var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
	if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
	else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
	return c > 3 && r && Object.defineProperty(target, key, r), r;
}
//#endregion
//#region src/views/k8s-overview.ts
var RESOURCE_ICONS = {
	pods: "mdi:cube-outline",
	nodes: "mdi:server",
	deployments: "mdi:rocket-launch",
	statefulsets: "mdi:database",
	daemonsets: "mdi:lan",
	cronjobs: "mdi:clock-outline",
	jobs: "mdi:briefcase-check"
};
var RESOURCE_LABELS = {
	pods: "Pods",
	nodes: "Nodes",
	deployments: "Deployments",
	statefulsets: "StatefulSets",
	daemonsets: "DaemonSets",
	cronjobs: "CronJobs",
	jobs: "Jobs"
};
var CONDITION_LABELS$1 = {
	memory_pressure: "Memory Pressure",
	disk_pressure: "Disk Pressure",
	pid_pressure: "PID Pressure",
	network_unavailable: "Network Unavailable"
};
var K8sOverview = class K8sOverview extends i {
	constructor(..._args) {
		super(..._args);
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
		if (document.hidden) this._stopPolling();
		else {
			this._loadData();
			this._startPolling();
		}
	}
	_startPolling() {
		if (!this._refreshInterval) this._refreshInterval = setInterval(() => this._loadData(), 3e4);
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
		if (!this._data) this._loading = true;
		this._error = null;
		try {
			this._data = await this.hass.callWS({ type: "kubernetes/cluster/overview" });
		} catch (err) {
			this._error = err.message || "Failed to load cluster data";
		} finally {
			this._loading = false;
			this._loadingInFlight = false;
		}
	}
	_toggleNamespaces(clusterId) {
		const updated = new Set(this._expandedNamespaces);
		if (updated.has(clusterId)) updated.delete(clusterId);
		else updated.add(clusterId);
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
	static {
		this.styles = i$3`
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
	}
	render() {
		if (this._loading) return b`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
		if (this._error) return b`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
		if (!this._data?.clusters.length) return b` <div class="empty">No Kubernetes clusters configured.</div> `;
		return b` ${this._data.clusters.map((c) => this._renderCluster(c))} `;
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
          ${Object.entries(cluster.counts).map(([key, count]) => b`
              <ha-card class="count-card">
                <ha-icon icon=${RESOURCE_ICONS[key] || "mdi:help"}></ha-icon>
                <div class="count-value">${count}</div>
                <div class="count-label">${RESOURCE_LABELS[key] || key}</div>
              </ha-card>
            `)}
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
		if (healthy === true) return b`<span class="badge badge-healthy">Healthy</span>`;
		if (healthy === false) return b`<span class="badge badge-unhealthy">Unhealthy</span>`;
		return b`<span class="badge badge-unknown">Unknown</span>`;
	}
	_renderWatchBadge(enabled) {
		if (enabled) return b`
        <span class="badge badge-watch">
          <ha-icon icon="mdi:eye"></ha-icon> Watch Active
        </span>
      `;
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
          ${nsEntries.sort(([a], [b]) => a.localeCompare(b)).map(([ns, counts]) => b`
                <tr>
                  <td>${ns}</td>
                  ${columns.map((col) => b`<td>${counts[col] || 0}</td>`)}
                </tr>
              `)}
        </tbody>
      </table>
    `;
	}
	_renderAlerts(alerts) {
		return b`
      ${alerts.nodes_with_pressure.map((node) => b`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:server-network-off"></ha-icon>
            <div>
              <div class="alert-title">Node: ${node.name}</div>
              <div class="alert-detail">
                ${node.conditions.map((c) => CONDITION_LABELS$1[c] || c).join(", ")}
              </div>
            </div>
          </div>
        `)}
      ${alerts.degraded_workloads.map((wl) => b`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:alert"></ha-icon>
            <div>
              <div class="alert-title">${wl.type}: ${wl.namespace}/${wl.name}</div>
              <div class="alert-detail">${wl.ready}/${wl.desired} replicas ready</div>
            </div>
          </div>
        `)}
      ${alerts.failed_pods.map((pod) => b`
          <div class="alert-card alert-error">
            <ha-icon icon="mdi:alert-octagon"></ha-icon>
            <div>
              <div class="alert-title">Pod: ${pod.namespace}/${pod.name}</div>
              <div class="alert-detail">Phase: ${pod.phase}</div>
            </div>
          </div>
        `)}
    `;
	}
};
__decorate([n({ attribute: false })], K8sOverview.prototype, "hass", void 0);
__decorate([r()], K8sOverview.prototype, "_data", void 0);
__decorate([r()], K8sOverview.prototype, "_loading", void 0);
__decorate([r()], K8sOverview.prototype, "_error", void 0);
__decorate([r()], K8sOverview.prototype, "_expandedNamespaces", void 0);
K8sOverview = __decorate([t("k8s-overview")], K8sOverview);
//#endregion
//#region src/views/k8s-nodes-table.ts
var CONDITION_LABELS = {
	memory_pressure: "Memory Pressure",
	disk_pressure: "Disk Pressure",
	pid_pressure: "PID Pressure",
	network_unavailable: "Network Unavailable"
};
var K8sNodesTable = class K8sNodesTable extends i {
	constructor(..._args) {
		super(..._args);
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
		if (document.hidden) this._stopPolling();
		else {
			this._loadData();
			this._startPolling();
		}
	}
	_startPolling() {
		if (!this._refreshInterval) this._refreshInterval = setInterval(() => this._loadData(), 3e4);
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
		if (!this._data) this._loading = true;
		this._error = null;
		try {
			this._data = await this.hass.callWS({ type: "kubernetes/nodes/list" });
		} catch (err) {
			this._error = err.message || "Failed to load nodes data";
		} finally {
			this._loading = false;
			this._loadingInFlight = false;
		}
	}
	_toggleNode(nodeKey) {
		const updated = new Set(this._expandedNodes);
		if (updated.has(nodeKey)) updated.delete(nodeKey);
		else updated.add(nodeKey);
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
		const diff = Math.max(0, Math.floor((Date.now() - created) / 1e3));
		if (diff < 60) return `${diff}s`;
		if (diff < 3600) return `${Math.floor(diff / 60)}m`;
		if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
		return `${Math.floor(diff / 86400)}d`;
	}
	_getFilteredNodes(nodes) {
		let filtered = nodes;
		if (this._statusFilter !== "all") filtered = filtered.filter((n) => this._statusFilter === "ready" ? n.status === "Ready" : n.status !== "Ready");
		if (this._searchQuery) {
			const q = this._searchQuery.toLowerCase();
			filtered = filtered.filter((n) => n.name.toLowerCase().includes(q) || n.internal_ip.toLowerCase().includes(q) || n.kubelet_version.toLowerCase().includes(q));
		}
		return filtered;
	}
	static {
		this.styles = i$3`
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
      gap: 6px;
    }

    .resource-label {
      font-size: 11px;
      font-weight: 500;
      color: var(--secondary-text-color);
      min-width: 28px;
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

    .resource-bar-fill.bar-warn {
      background: var(--warning-color, #ff9800);
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
	}
	render() {
		if (this._loading) return b`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
		if (this._error) return b`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
		if (!this._data?.clusters.length) return b`<div class="empty">No Kubernetes clusters configured.</div>`;
		return b`${this._data.clusters.map((c) => this._renderCluster(c))}`;
	}
	_renderCluster(cluster) {
		const filtered = this._getFilteredNodes(cluster.nodes);
		const readyCount = cluster.nodes.filter((n) => n.status === "Ready").length;
		return b`
      <div class="cluster-section">
        ${this._data.clusters.length > 1 ? b`<div class="cluster-name">${cluster.cluster_name}</div>` : A}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search nodes..."
            .value=${this._searchQuery}
            @input=${(e) => {
			this._searchQuery = e.target.value;
		}}
          />
          ${[
			"all",
			"ready",
			"not-ready"
		].map((f) => b`
              <button
                class="filter-chip"
                ?active=${this._statusFilter === f}
                @click=${() => {
			this._statusFilter = f;
		}}
              >
                ${f === "all" ? "All" : f === "ready" ? "Ready" : "Not Ready"}
              </button>
            `)}
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
		const hasMetrics = node.cpu_usage_millicores != null && node.memory_usage_mib != null;
		const cpuCapacityMillicores = node.cpu_cores * 1e3;
		const cpuPercent = hasMetrics ? Math.round(node.cpu_usage_millicores / cpuCapacityMillicores * 100) : 0;
		const memUsageGib = hasMetrics ? node.memory_usage_mib / 1024 : 0;
		const memPercent = hasMetrics ? Math.round(memUsageGib / node.memory_capacity_gib * 100) : 0;
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
            ${hasMetrics ? b`
                  <div class="resource-bar-container" title="CPU usage">
                    <span class="resource-label">CPU</span>
                    <div class="resource-bar">
                      <div
                        class="resource-bar-fill ${cpuPercent > 80 ? "bar-warn" : ""}"
                        style="width: ${Math.min(cpuPercent, 100)}%"
                      ></div>
                    </div>
                    <span>${cpuPercent}%</span>
                  </div>
                  <div class="resource-bar-container" title="Memory usage">
                    <span class="resource-label">MEM</span>
                    <div class="resource-bar">
                      <div
                        class="resource-bar-fill ${memPercent > 80 ? "bar-warn" : ""}"
                        style="width: ${Math.min(memPercent, 100)}%"
                      ></div>
                    </div>
                    <span>${memPercent}%</span>
                  </div>
                ` : b`<span
                  >${node.cpu_cores} CPU &middot; ${node.memory_capacity_gib} GiB</span
                >`}
          </div>
          <span class="node-age">${this._formatAge(node.creation_timestamp)}</span>
        </div>
        ${expanded ? this._renderNodeDetails(node, conditions) : A}
      </ha-card>
    `;
	}
	_renderNodeDetails(node, conditions) {
		const hasMetrics = node.cpu_usage_millicores != null && node.memory_usage_mib != null;
		const memUsageGib = hasMetrics ? Math.round(node.memory_usage_mib / 1024 * 100) / 100 : null;
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
          ${hasMetrics ? b`
                <div class="detail-item">
                  <span class="detail-label">CPU Usage</span>
                  <span class="detail-value"
                    >${node.cpu_usage_millicores}m / ${node.cpu_cores * 1e3}m</span
                  >
                </div>
              ` : A}
          <div class="detail-item">
            <span class="detail-label">Memory Capacity</span>
            <span class="detail-value">${node.memory_capacity_gib} GiB</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Memory Allocatable</span>
            <span class="detail-value">${node.memory_allocatable_gib} GiB</span>
          </div>
          ${hasMetrics ? b`
                <div class="detail-item">
                  <span class="detail-label">Memory Usage</span>
                  <span class="detail-value"
                    >${memUsageGib} / ${node.memory_capacity_gib} GiB</span
                  >
                </div>
              ` : A}
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
                ${conditions.map((c) => b`
                    <span class="badge badge-condition">
                      ${CONDITION_LABELS[c] || c}
                    </span>
                  `)}
              </div>
            ` : A}
      </div>
    `;
	}
};
__decorate([n({ attribute: false })], K8sNodesTable.prototype, "hass", void 0);
__decorate([r()], K8sNodesTable.prototype, "_data", void 0);
__decorate([r()], K8sNodesTable.prototype, "_loading", void 0);
__decorate([r()], K8sNodesTable.prototype, "_error", void 0);
__decorate([r()], K8sNodesTable.prototype, "_expandedNodes", void 0);
__decorate([r()], K8sNodesTable.prototype, "_statusFilter", void 0);
__decorate([r()], K8sNodesTable.prototype, "_searchQuery", void 0);
K8sNodesTable = __decorate([t("k8s-nodes-table")], K8sNodesTable);
//#endregion
//#region src/views/k8s-pods-table.ts
var PHASE_CLASSES = {
	Running: "badge-running",
	Succeeded: "badge-succeeded",
	Pending: "badge-pending",
	Failed: "badge-failed",
	Unknown: "badge-unknown"
};
var K8sPodsTable = class K8sPodsTable extends i {
	constructor(..._args) {
		super(..._args);
		this._data = null;
		this._loading = true;
		this._error = null;
		this._searchQuery = "";
		this._phaseFilter = "all";
		this._namespaceFilter = "all";
		this._sortField = "name";
		this._sortAsc = true;
		this._deleteConfirm = null;
		this._deleting = false;
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
		if (document.hidden) this._stopPolling();
		else {
			this._loadData();
			this._startPolling();
		}
	}
	_startPolling() {
		if (!this._refreshInterval) this._refreshInterval = setInterval(() => this._loadData(), 3e4);
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
		if (!this._data) this._loading = true;
		this._error = null;
		try {
			this._data = await this.hass.callWS({ type: "kubernetes/pods/list" });
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
		const diff = Math.max(0, Math.floor((Date.now() - created) / 1e3));
		if (diff < 60) return `${diff}s`;
		if (diff < 3600) return `${Math.floor(diff / 60)}m`;
		if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
		return `${Math.floor(diff / 86400)}d`;
	}
	_getNamespaces(pods) {
		return [...new Set(pods.map((p) => p.namespace))].sort();
	}
	_getFilteredPods(pods) {
		let filtered = pods;
		if (this._phaseFilter !== "all") filtered = filtered.filter((p) => p.phase === this._phaseFilter);
		if (this._namespaceFilter !== "all") filtered = filtered.filter((p) => p.namespace === this._namespaceFilter);
		if (this._searchQuery) {
			const q = this._searchQuery.toLowerCase();
			filtered = filtered.filter((p) => p.name.toLowerCase().includes(q) || p.namespace.toLowerCase().includes(q) || p.node_name.toLowerCase().includes(q) || p.owner_name.toLowerCase().includes(q));
		}
		filtered.sort((a, b) => {
			let valA;
			let valB;
			const field = this._sortField;
			if (field === "restarts") {
				valA = a.restart_count;
				valB = b.restart_count;
			} else if (field === "age") {
				valA = a.creation_timestamp || "";
				valB = b.creation_timestamp || "";
			} else {
				valA = a[field] || "";
				valB = b[field] || "";
			}
			const cmp = valA < valB ? -1 : valA > valB ? 1 : 0;
			return this._sortAsc ? cmp : -cmp;
		});
		return filtered;
	}
	_handleSort(field) {
		if (this._sortField === field) this._sortAsc = !this._sortAsc;
		else {
			this._sortField = field;
			this._sortAsc = true;
		}
	}
	_requestDelete(entryId, pod) {
		this._deleteConfirm = {
			entry_id: entryId,
			pod_name: pod.name,
			namespace: pod.namespace
		};
	}
	_cancelDelete() {
		this._deleteConfirm = null;
	}
	async _confirmDelete() {
		if (!this._deleteConfirm) return;
		this._deleting = true;
		try {
			await this.hass.callWS({
				type: "kubernetes/pods/delete",
				entry_id: this._deleteConfirm.entry_id,
				pod_name: this._deleteConfirm.pod_name,
				namespace: this._deleteConfirm.namespace
			});
			this._deleteConfirm = null;
			await this._loadData();
		} catch (err) {
			this._error = err.message || "Failed to delete pod";
			this._deleteConfirm = null;
		} finally {
			this._deleting = false;
		}
	}
	_sortIcon(field) {
		if (this._sortField !== field) return "";
		return this._sortAsc ? "mdi:arrow-up" : "mdi:arrow-down";
	}
	static {
		this.styles = i$3`
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

    .col-actions {
      width: 40px;
      min-width: 40px;
      cursor: default;
    }

    .delete-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
      cursor: pointer;
      padding: 4px;
      border-radius: 50%;
      color: var(--secondary-text-color);
      --mdc-icon-size: 18px;
      transition:
        color 0.2s,
        background 0.2s;
    }

    .delete-btn:hover {
      color: var(--error-color, #f44336);
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
    }

    .confirm-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999;
    }

    .confirm-dialog {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      padding: 24px;
      max-width: 400px;
      width: 90%;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
    }

    .confirm-dialog h3 {
      margin: 0 0 12px;
      font-size: 18px;
      color: var(--primary-text-color);
    }

    .confirm-dialog p {
      margin: 0 0 20px;
      color: var(--secondary-text-color);
      font-size: 14px;
    }

    .confirm-dialog .pod-ref {
      font-family: monospace;
      font-weight: 500;
      color: var(--primary-text-color);
    }

    .confirm-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }

    .confirm-actions button {
      padding: 8px 20px;
      border-radius: 4px;
      font-size: 14px;
      cursor: pointer;
      border: 1px solid var(--divider-color);
      background: transparent;
      color: var(--primary-text-color);
    }

    .confirm-actions button:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08);
    }

    .confirm-actions .delete-action {
      background: var(--error-color, #f44336);
      color: #fff;
      border-color: var(--error-color, #f44336);
    }

    .confirm-actions .delete-action:hover {
      opacity: 0.9;
      background: var(--error-color, #f44336);
    }

    .confirm-actions .delete-action:disabled {
      opacity: 0.6;
      cursor: not-allowed;
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
	}
	render() {
		if (this._loading) return b`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
		if (this._error) return b`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
		if (!this._data?.clusters.length) return b`<div class="empty">No Kubernetes clusters configured.</div>`;
		return b`
      ${this._data.clusters.map((c) => this._renderCluster(c))}
      ${this._deleteConfirm ? this._renderDeleteDialog() : A}
    `;
	}
	_renderCluster(cluster) {
		const filtered = this._getFilteredPods(cluster.pods);
		const namespaces = this._getNamespaces(cluster.pods);
		const phases = [...new Set(cluster.pods.map((p) => p.phase))].sort();
		return b`
      <div class="cluster-section">
        ${this._data.clusters.length > 1 ? b`<div class="cluster-name">${cluster.cluster_name}</div>` : A}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search pods..."
            .value=${this._searchQuery}
            @input=${(e) => {
			this._searchQuery = e.target.value;
		}}
          />

          <select
            class="ns-select"
            .value=${this._namespaceFilter}
            @change=${(e) => {
			this._namespaceFilter = e.target.value;
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
          ${phases.map((phase) => b`
              <button
                class="filter-chip"
                ?active=${this._phaseFilter === phase}
                @click=${() => {
			this._phaseFilter = phase;
		}}
              >
                ${phase}
              </button>
            `)}
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
                        <th class="col-actions"></th>
                      </tr>
                    </thead>
                    <tbody>
                      ${filtered.map((pod) => this._renderPodRow(cluster.entry_id, pod))}
                    </tbody>
                  </table>
                </div>
              </ha-card>
            `}
      </div>
    `;
	}
	_renderPodRow(entryId, pod) {
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
        <td>
          <button
            class="delete-btn"
            title="Delete pod"
            @click=${() => this._requestDelete(entryId, pod)}
          >
            <ha-icon icon="mdi:delete-outline"></ha-icon>
          </button>
        </td>
      </tr>
    `;
	}
	_renderDeleteDialog() {
		const confirm = this._deleteConfirm;
		return b`
      <div
        class="confirm-overlay"
        @click=${this._deleting ? A : this._cancelDelete}
      >
        <div class="confirm-dialog" @click=${(e) => e.stopPropagation()}>
          <h3>Delete Pod</h3>
          <p>
            Are you sure you want to delete
            <span class="pod-ref">${confirm.namespace}/${confirm.pod_name}</span>? This
            action cannot be undone.
          </p>
          <div class="confirm-actions">
            <button @click=${this._cancelDelete} ?disabled=${this._deleting}>
              Cancel
            </button>
            <button
              class="delete-action"
              @click=${this._confirmDelete}
              ?disabled=${this._deleting}
            >
              ${this._deleting ? "Deleting..." : "Delete"}
            </button>
          </div>
        </div>
      </div>
    `;
	}
};
__decorate([n({ attribute: false })], K8sPodsTable.prototype, "hass", void 0);
__decorate([r()], K8sPodsTable.prototype, "_data", void 0);
__decorate([r()], K8sPodsTable.prototype, "_loading", void 0);
__decorate([r()], K8sPodsTable.prototype, "_error", void 0);
__decorate([r()], K8sPodsTable.prototype, "_searchQuery", void 0);
__decorate([r()], K8sPodsTable.prototype, "_phaseFilter", void 0);
__decorate([r()], K8sPodsTable.prototype, "_namespaceFilter", void 0);
__decorate([r()], K8sPodsTable.prototype, "_sortField", void 0);
__decorate([r()], K8sPodsTable.prototype, "_sortAsc", void 0);
__decorate([r()], K8sPodsTable.prototype, "_deleteConfirm", void 0);
__decorate([r()], K8sPodsTable.prototype, "_deleting", void 0);
K8sPodsTable = __decorate([t("k8s-pods-table")], K8sPodsTable);
//#endregion
//#region src/views/k8s-workloads.ts
var K8sWorkloads = class K8sWorkloads extends i {
	constructor(..._args) {
		super(..._args);
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
		if (document.hidden) this._stopPolling();
		else {
			this._loadData();
			this._startPolling();
		}
	}
	_startPolling() {
		if (!this._refreshInterval) this._refreshInterval = setInterval(() => this._loadData(), 3e4);
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
		if (!this._data) this._loading = true;
		this._error = null;
		try {
			this._data = await this.hass.callWS({ type: "kubernetes/workloads/list" });
		} catch (err) {
			this._error = err.message || "Failed to load workloads data";
		} finally {
			this._loading = false;
			this._loadingInFlight = false;
		}
	}
	_getNamespaces(cluster) {
		const namespaces = /* @__PURE__ */ new Set();
		for (const d of cluster.deployments) namespaces.add(d.namespace);
		for (const s of cluster.statefulsets) namespaces.add(s.namespace);
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
		const diff = Math.max(0, Math.floor((Date.now() - created) / 1e3));
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
			this._actionError = `Action failed: ${err?.message || "Service call failed"}`;
			console.error("[k8s-workloads] Service call failed:", err);
		} finally {
			const done = new Set(this._actionInProgress);
			done.delete(actionKey);
			this._actionInProgress = done;
		}
	}
	static {
		this.styles = i$3`
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

    .action-btn.restart:hover {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.1);
      color: var(--warning-color, #ff9800);
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
	}
	render() {
		if (this._loading) return b`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
		if (this._error) return b`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
		if (!this._data?.clusters.length) return b`<div class="empty">No Kubernetes clusters configured.</div>`;
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
      ${this._data.clusters.map((c) => this._renderCluster(c))}
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
            @input=${(e) => {
			this._searchQuery = e.target.value;
		}}
          />

          <select
            class="filter-select"
            .value=${this._namespaceFilter}
            @change=${(e) => {
			this._namespaceFilter = e.target.value;
		}}
          >
            <option value="all">All namespaces</option>
            ${namespaces.map((ns) => b`<option value=${ns}>${ns}</option>`)}
          </select>

          <select
            class="filter-select"
            .value=${this._categoryFilter}
            @change=${(e) => {
			this._categoryFilter = e.target.value;
		}}
          >
            <option value="all">All types</option>
            <option value="deployments">Deployments</option>
            <option value="statefulsets">StatefulSets</option>
            <option value="daemonsets">DaemonSets</option>
            <option value="cronjobs">CronJobs</option>
            <option value="jobs">Jobs</option>
          </select>

          ${[
			"all",
			"healthy",
			"degraded",
			"stopped"
		].map((f) => b`
              <button
                class="filter-chip"
                ?active=${this._statusFilter === f}
                @click=${() => {
			this._statusFilter = f;
		}}
              >
                ${f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            `)}
        </div>

        ${this._shouldShowCategory("deployments") ? this._renderDeployments(cluster.deployments, cluster.entry_id) : A}
        ${this._shouldShowCategory("statefulsets") ? this._renderStatefulSets(cluster.statefulsets, cluster.entry_id) : A}
        ${this._shouldShowCategory("daemonsets") ? this._renderDaemonSets(cluster.daemonsets, cluster.entry_id) : A}
        ${this._shouldShowCategory("cronjobs") ? this._renderCronJobs(cluster.cronjobs, cluster.entry_id) : A}
        ${this._shouldShowCategory("jobs") ? this._renderJobs(cluster.jobs) : A}
      </div>
    `;
	}
	_shouldShowCategory(category) {
		return this._categoryFilter === "all" || this._categoryFilter === category;
	}
	_getDeploymentStatus(d) {
		if (d.replicas === 0) return "stopped";
		if ((d.available_replicas || 0) < d.replicas) return "degraded";
		return "healthy";
	}
	_getStatefulSetStatus(s) {
		if (s.replicas === 0) return "stopped";
		if ((s.ready_replicas || 0) < s.replicas) return "degraded";
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
		return {
			all: "",
			healthy: "badge-healthy",
			degraded: "badge-degraded",
			stopped: "badge-stopped"
		}[status] || "";
	}
	_statusLabel(status) {
		return {
			all: "",
			healthy: "Healthy",
			degraded: "Degraded",
			stopped: "Stopped"
		}[status] || "";
	}
	_renderDeployments(deployments, entryId) {
		const filtered = deployments.filter((d) => this._matchesNamespace(d.namespace) && this._matchesSearch(d.name) && this._matchesStatusFilter(this._getDeploymentStatus(d)));
		if (filtered.length === 0 && this._categoryFilter !== "all") return b`<div class="empty">No deployments match your filters.</div>`;
		if (filtered.length === 0) return A;
		return b`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:rocket-launch"></ha-icon>
          Deployments
          <span class="category-count">(${filtered.length})</span>
        </div>
        ${filtered.map((d) => this._renderDeploymentCard(d, entryId))}
      </div>
    `;
	}
	_renderDeploymentCard(d, entryId) {
		const status = this._getDeploymentStatus(d);
		const actionKey = `deploy_${d.namespace}_${d.name}`;
		const busy = this._actionInProgress.has(actionKey);
		return b`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${d.name}</div>
            <div class="workload-namespace">${d.namespace}</div>
          </div>
          <span class="replica-info">
            ${d.available_replicas ?? 0}/${d.replicas} ready
          </span>
          <span class="badge ${this._statusBadgeClass(status)}">
            ${this._statusLabel(status)}
          </span>
          <div class="workload-actions">
            ${d.replicas === 0 ? b`
                  <button
                    class="action-btn start"
                    title="Start (scale to 1)"
                    ?disabled=${busy}
                    @click=${() => this._callService("start_workload", {
			workload_name: d.name,
			namespace: d.namespace,
			entry_id: entryId
		}, actionKey)}
                  >
                    <ha-icon icon="mdi:play"></ha-icon>
                  </button>
                ` : b`
                  <button
                    class="action-btn stop"
                    title="Stop (scale to 0)"
                    ?disabled=${busy}
                    @click=${() => this._callService("stop_workload", {
			workload_name: d.name,
			namespace: d.namespace,
			entry_id: entryId
		}, actionKey)}
                  >
                    <ha-icon icon="mdi:stop"></ha-icon>
                  </button>
                `}
            <button
              class="action-btn restart"
              title="Rolling restart"
              ?disabled=${busy}
              @click=${() => this._callService("restart_workload", {
			workload_name: d.name,
			namespace: d.namespace,
			entry_id: entryId
		}, actionKey)}
            >
              <ha-icon icon="mdi:restart"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `;
	}
	_renderStatefulSets(statefulsets, entryId) {
		const filtered = statefulsets.filter((s) => this._matchesNamespace(s.namespace) && this._matchesSearch(s.name) && this._matchesStatusFilter(this._getStatefulSetStatus(s)));
		if (filtered.length === 0 && this._categoryFilter !== "all") return b`<div class="empty">No statefulsets match your filters.</div>`;
		if (filtered.length === 0) return A;
		return b`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:database"></ha-icon>
          StatefulSets
          <span class="category-count">(${filtered.length})</span>
        </div>
        ${filtered.map((s) => this._renderStatefulSetCard(s, entryId))}
      </div>
    `;
	}
	_renderStatefulSetCard(s, entryId) {
		const status = this._getStatefulSetStatus(s);
		const actionKey = `sts_${s.namespace}_${s.name}`;
		const busy = this._actionInProgress.has(actionKey);
		return b`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${s.name}</div>
            <div class="workload-namespace">${s.namespace}</div>
          </div>
          <span class="replica-info">
            ${s.ready_replicas ?? 0}/${s.replicas} ready
          </span>
          <span class="badge ${this._statusBadgeClass(status)}">
            ${this._statusLabel(status)}
          </span>
          <div class="workload-actions">
            ${s.replicas === 0 ? b`
                  <button
                    class="action-btn start"
                    title="Start (scale to 1)"
                    ?disabled=${busy}
                    @click=${() => this._callService("start_workload", {
			workload_name: s.name,
			namespace: s.namespace,
			entry_id: entryId
		}, actionKey)}
                  >
                    <ha-icon icon="mdi:play"></ha-icon>
                  </button>
                ` : b`
                  <button
                    class="action-btn stop"
                    title="Stop (scale to 0)"
                    ?disabled=${busy}
                    @click=${() => this._callService("stop_workload", {
			workload_name: s.name,
			namespace: s.namespace,
			entry_id: entryId
		}, actionKey)}
                  >
                    <ha-icon icon="mdi:stop"></ha-icon>
                  </button>
                `}
            <button
              class="action-btn restart"
              title="Rolling restart"
              ?disabled=${busy}
              @click=${() => this._callService("restart_workload", {
			workload_name: s.name,
			namespace: s.namespace,
			entry_id: entryId
		}, actionKey)}
            >
              <ha-icon icon="mdi:restart"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `;
	}
	_renderDaemonSets(daemonsets, entryId) {
		const filtered = daemonsets.filter((ds) => this._matchesNamespace(ds.namespace) && this._matchesSearch(ds.name) && this._matchesStatusFilter(this._getDaemonSetStatus(ds)));
		if (filtered.length === 0 && this._categoryFilter !== "all") return b`<div class="empty">No daemonsets match your filters.</div>`;
		if (filtered.length === 0) return A;
		return b`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:lan"></ha-icon>
          DaemonSets
          <span class="category-count">(${filtered.length})</span>
        </div>
        ${filtered.map((ds) => this._renderDaemonSetCard(ds, entryId))}
      </div>
    `;
	}
	_renderDaemonSetCard(ds, entryId) {
		const status = this._getDaemonSetStatus(ds);
		const actionKey = `ds_${ds.namespace}_${ds.name}`;
		const busy = this._actionInProgress.has(actionKey);
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
          <div class="workload-actions">
            <button
              class="action-btn restart"
              title="Rolling restart"
              ?disabled=${busy}
              @click=${() => this._callService("restart_workload", {
			workload_name: ds.name,
			namespace: ds.namespace,
			entry_id: entryId
		}, actionKey)}
            >
              <ha-icon icon="mdi:restart"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `;
	}
	_renderCronJobs(cronjobs, entryId) {
		const filtered = cronjobs.filter((cj) => this._matchesNamespace(cj.namespace) && this._matchesSearch(cj.name));
		const statusFiltered = this._statusFilter === "all" ? filtered : filtered.filter((cj) => {
			if (this._statusFilter === "stopped") return cj.suspend;
			if (this._statusFilter === "healthy") return !cj.suspend;
			return false;
		});
		if (statusFiltered.length === 0 && this._categoryFilter !== "all") return b`<div class="empty">No cronjobs match your filters.</div>`;
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
              @click=${() => this._callService("start_workload", {
			workload_name: cj.name,
			namespace: cj.namespace,
			entry_id: entryId
		}, actionKey)}
            >
              <ha-icon icon="mdi:play"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `;
	}
	_renderJobs(jobs) {
		const filtered = jobs.filter((j) => this._matchesNamespace(j.namespace) && this._matchesSearch(j.name));
		const statusFiltered = this._statusFilter === "all" ? filtered : filtered.filter((j) => {
			if (this._statusFilter === "healthy") return j.succeeded >= j.completions;
			if (this._statusFilter === "degraded") return j.failed > 0 && j.succeeded < j.completions;
			if (this._statusFilter === "stopped") return j.active === 0;
			return true;
		});
		if (statusFiltered.length === 0 && this._categoryFilter !== "all") return b`<div class="empty">No jobs match your filters.</div>`;
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
__decorate([n({ attribute: false })], K8sWorkloads.prototype, "hass", void 0);
__decorate([r()], K8sWorkloads.prototype, "_data", void 0);
__decorate([r()], K8sWorkloads.prototype, "_loading", void 0);
__decorate([r()], K8sWorkloads.prototype, "_error", void 0);
__decorate([r()], K8sWorkloads.prototype, "_namespaceFilter", void 0);
__decorate([r()], K8sWorkloads.prototype, "_categoryFilter", void 0);
__decorate([r()], K8sWorkloads.prototype, "_statusFilter", void 0);
__decorate([r()], K8sWorkloads.prototype, "_searchQuery", void 0);
__decorate([r()], K8sWorkloads.prototype, "_actionInProgress", void 0);
__decorate([r()], K8sWorkloads.prototype, "_actionError", void 0);
K8sWorkloads = __decorate([t("k8s-workloads")], K8sWorkloads);
//#endregion
//#region src/views/k8s-settings.ts
var K8sSettings = class K8sSettings extends i {
	constructor(..._args) {
		super(..._args);
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
			this._data = await this.hass.callWS({ type: "kubernetes/config/list" });
		} catch (err) {
			this._error = err.message || "Failed to load configuration";
		} finally {
			this._loading = false;
		}
	}
	_navigateToIntegration() {
		window.open("/config/integrations/integration/kubernetes", "_blank");
	}
	static {
		this.styles = i$3`
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
	}
	render() {
		if (this._loading) return b`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
		if (this._error) return b`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
		if (!this._data?.entries.length) return b`<div class="empty">No Kubernetes entries configured.</div>`;
		return b`${this._data.entries.map((e) => this._renderEntry(e))}`;
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
		if (healthy === true) return b`<span class="badge badge-healthy">Connected</span>`;
		if (healthy === false) return b`<span class="badge badge-unhealthy">Disconnected</span>`;
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
                    ${entry.namespaces.map((ns) => b`<span class="ns-tag">${ns}</span>`)}
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
		if (value) return b`
        <span class="setting-value-bool bool-true">
          <ha-icon icon="mdi:check-circle"></ha-icon> Enabled
        </span>
      `;
		return b`
      <span class="setting-value-bool bool-false">
        <ha-icon icon="mdi:close-circle-outline"></ha-icon> Disabled
      </span>
    `;
	}
};
__decorate([n({ attribute: false })], K8sSettings.prototype, "hass", void 0);
__decorate([r()], K8sSettings.prototype, "_data", void 0);
__decorate([r()], K8sSettings.prototype, "_loading", void 0);
__decorate([r()], K8sSettings.prototype, "_error", void 0);
K8sSettings = __decorate([t("k8s-settings")], K8sSettings);
//#endregion
//#region src/kubernetes-panel.ts
var KubernetesPanel = class KubernetesPanel extends i {
	constructor(..._args) {
		super(..._args);
		this.narrow = false;
		this._activeTab = "overview";
		this._tabs = [
			{
				id: "overview",
				label: "Overview",
				icon: "mdi:view-dashboard"
			},
			{
				id: "nodes",
				label: "Nodes",
				icon: "mdi:server"
			},
			{
				id: "workloads",
				label: "Workloads",
				icon: "mdi:application-cog"
			},
			{
				id: "pods",
				label: "Pods",
				icon: "mdi:cube-outline"
			},
			{
				id: "settings",
				label: "Settings",
				icon: "mdi:cog"
			}
		];
	}
	firstUpdated(_changedProps) {
		loadHaElements();
	}
	_handleTabChange(tab) {
		this._activeTab = tab;
	}
	_toggleSidebar() {
		this.dispatchEvent(new Event("hass-toggle-menu", {
			bubbles: true,
			composed: true
		}));
	}
	static {
		this.styles = i$3`
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
        ${this._tabs.map((tab) => b`
            <div
              class="tab"
              ?active=${this._activeTab === tab.id}
              @click=${() => this._handleTabChange(tab.id)}
            >
              <ha-icon icon=${tab.icon}></ha-icon>
              <span>${tab.label}</span>
            </div>
          `)}
      </div>
      <div class="content">${this._renderActiveTab()}</div>
    `;
	}
	_renderActiveTab() {
		switch (this._activeTab) {
			case "overview": return b`<k8s-overview .hass=${this.hass}></k8s-overview>`;
			case "nodes": return b`<k8s-nodes-table .hass=${this.hass}></k8s-nodes-table>`;
			case "pods": return b`<k8s-pods-table .hass=${this.hass}></k8s-pods-table>`;
			case "workloads": return b`<k8s-workloads .hass=${this.hass}></k8s-workloads>`;
			case "settings": return b`<k8s-settings .hass=${this.hass}></k8s-settings>`;
			default: return b`
          <div class="coming-soon">
            <ha-icon icon="mdi:hammer-wrench"></ha-icon>
            <p>This tab is coming in a future release.</p>
          </div>
        `;
		}
	}
};
__decorate([n({ attribute: false })], KubernetesPanel.prototype, "hass", void 0);
__decorate([n({
	type: Boolean,
	reflect: true
})], KubernetesPanel.prototype, "narrow", void 0);
__decorate([n({ attribute: false })], KubernetesPanel.prototype, "route", void 0);
__decorate([n({ attribute: false })], KubernetesPanel.prototype, "panel", void 0);
__decorate([r()], KubernetesPanel.prototype, "_activeTab", void 0);
KubernetesPanel = __decorate([t("kubernetes-panel")], KubernetesPanel);
//#endregion
export { KubernetesPanel };
