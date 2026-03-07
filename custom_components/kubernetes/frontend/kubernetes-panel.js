var KubernetesPanel=(function(f){"use strict";/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */var ye;const B=globalThis,G=B.ShadowRoot&&(B.ShadyCSS===void 0||B.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,Z=Symbol(),ae=new WeakMap;let ie=class{constructor(e,t,s){if(this._$cssResult$=!0,s!==Z)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(G&&e===void 0){const s=t!==void 0&&t.length===1;s&&(e=ae.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),s&&ae.set(t,e))}return e}toString(){return this.cssText}};const xe=r=>new ie(typeof r=="string"?r:r+"",void 0,Z),K=(r,...e)=>{const t=r.length===1?r[0]:e.reduce((s,a,i)=>s+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(a)+r[i+1],r[0]);return new ie(t,r,Z)},we=(r,e)=>{if(G)r.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const t of e){const s=document.createElement("style"),a=B.litNonce;a!==void 0&&s.setAttribute("nonce",a),s.textContent=t.cssText,r.appendChild(s)}},oe=G?r=>r:r=>r instanceof CSSStyleSheet?(e=>{let t="";for(const s of e.cssRules)t+=s.cssText;return xe(t)})(r):r;/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const{is:Ae,defineProperty:ke,getOwnPropertyDescriptor:Se,getOwnPropertyNames:Pe,getOwnPropertySymbols:Ee,getPrototypeOf:Ce}=Object,$=globalThis,ne=$.trustedTypes,Ne=ne?ne.emptyScript:"",Y=$.reactiveElementPolyfillSupport,T=(r,e)=>r,W={toAttribute(r,e){switch(e){case Boolean:r=r?Ne:null;break;case Object:case Array:r=r==null?r:JSON.stringify(r)}return r},fromAttribute(r,e){let t=r;switch(e){case Boolean:t=r!==null;break;case Number:t=r===null?null:Number(r);break;case Object:case Array:try{t=JSON.parse(r)}catch{t=null}}return t}},X=(r,e)=>!Ae(r,e),le={attribute:!0,type:String,converter:W,reflect:!1,useDefault:!1,hasChanged:X};Symbol.metadata??(Symbol.metadata=Symbol("metadata")),$.litPropertyMetadata??($.litPropertyMetadata=new WeakMap);let z=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??(this.l=[])).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=le){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const s=Symbol(),a=this.getPropertyDescriptor(e,s,t);a!==void 0&&ke(this.prototype,e,a)}}static getPropertyDescriptor(e,t,s){const{get:a,set:i}=Se(this.prototype,e)??{get(){return this[t]},set(o){this[t]=o}};return{get:a,set(o){const c=a==null?void 0:a.call(this);i==null||i.call(this,o),this.requestUpdate(e,c,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??le}static _$Ei(){if(this.hasOwnProperty(T("elementProperties")))return;const e=Ce(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(T("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(T("properties"))){const t=this.properties,s=[...Pe(t),...Ee(t)];for(const a of s)this.createProperty(a,t[a])}const e=this[Symbol.metadata];if(e!==null){const t=litPropertyMetadata.get(e);if(t!==void 0)for(const[s,a]of t)this.elementProperties.set(s,a)}this._$Eh=new Map;for(const[t,s]of this.elementProperties){const a=this._$Eu(t,s);a!==void 0&&this._$Eh.set(a,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const s=new Set(e.flat(1/0).reverse());for(const a of s)t.unshift(oe(a))}else e!==void 0&&t.push(oe(e));return t}static _$Eu(e,t){const s=t.attribute;return s===!1?void 0:typeof s=="string"?s:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){var e;this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),(e=this.constructor.l)==null||e.forEach(t=>t(this))}addController(e){var t;(this._$EO??(this._$EO=new Set)).add(e),this.renderRoot!==void 0&&this.isConnected&&((t=e.hostConnected)==null||t.call(e))}removeController(e){var t;(t=this._$EO)==null||t.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const s of t.keys())this.hasOwnProperty(s)&&(e.set(s,this[s]),delete this[s]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return we(e,this.constructor.elementStyles),e}connectedCallback(){var e;this.renderRoot??(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),(e=this._$EO)==null||e.forEach(t=>{var s;return(s=t.hostConnected)==null?void 0:s.call(t)})}enableUpdating(e){}disconnectedCallback(){var e;(e=this._$EO)==null||e.forEach(t=>{var s;return(s=t.hostDisconnected)==null?void 0:s.call(t)})}attributeChangedCallback(e,t,s){this._$AK(e,s)}_$ET(e,t){var i;const s=this.constructor.elementProperties.get(e),a=this.constructor._$Eu(e,s);if(a!==void 0&&s.reflect===!0){const o=(((i=s.converter)==null?void 0:i.toAttribute)!==void 0?s.converter:W).toAttribute(t,s.type);this._$Em=e,o==null?this.removeAttribute(a):this.setAttribute(a,o),this._$Em=null}}_$AK(e,t){var i,o;const s=this.constructor,a=s._$Eh.get(e);if(a!==void 0&&this._$Em!==a){const c=s.getPropertyOptions(a),l=typeof c.converter=="function"?{fromAttribute:c.converter}:((i=c.converter)==null?void 0:i.fromAttribute)!==void 0?c.converter:W;this._$Em=a;const h=l.fromAttribute(t,c.type);this[a]=h??((o=this._$Ej)==null?void 0:o.get(a))??h,this._$Em=null}}requestUpdate(e,t,s,a=!1,i){var o;if(e!==void 0){const c=this.constructor;if(a===!1&&(i=this[e]),s??(s=c.getPropertyOptions(e)),!((s.hasChanged??X)(i,t)||s.useDefault&&s.reflect&&i===((o=this._$Ej)==null?void 0:o.get(e))&&!this.hasAttribute(c._$Eu(e,s))))return;this.C(e,t,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:s,reflect:a,wrapped:i},o){s&&!(this._$Ej??(this._$Ej=new Map)).has(e)&&(this._$Ej.set(e,o??t??this[e]),i!==!0||o!==void 0)||(this._$AL.has(e)||(this.hasUpdated||s||(t=void 0),this._$AL.set(e,t)),a===!0&&this._$Em!==e&&(this._$Eq??(this._$Eq=new Set)).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){var s;if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??(this.renderRoot=this.createRenderRoot()),this._$Ep){for(const[i,o]of this._$Ep)this[i]=o;this._$Ep=void 0}const a=this.constructor.elementProperties;if(a.size>0)for(const[i,o]of a){const{wrapped:c}=o,l=this[i];c!==!0||this._$AL.has(i)||l===void 0||this.C(i,void 0,o,l)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),(s=this._$EO)==null||s.forEach(a=>{var i;return(i=a.hostUpdate)==null?void 0:i.call(a)}),this.update(t)):this._$EM()}catch(a){throw e=!1,this._$EM(),a}e&&this._$AE(t)}willUpdate(e){}_$AE(e){var t;(t=this._$EO)==null||t.forEach(s=>{var a;return(a=s.hostUpdated)==null?void 0:a.call(s)}),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&(this._$Eq=this._$Eq.forEach(t=>this._$ET(t,this[t]))),this._$EM()}updated(e){}firstUpdated(e){}};z.elementStyles=[],z.shadowRootOptions={mode:"open"},z[T("elementProperties")]=new Map,z[T("finalized")]=new Map,Y==null||Y({ReactiveElement:z}),($.reactiveElementVersions??($.reactiveElementVersions=[])).push("2.1.2");/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const I=globalThis,ce=r=>r,Q=I.trustedTypes,de=Q?Q.createPolicy("lit-html",{createHTML:r=>r}):void 0,pe="$lit$",y=`lit$${Math.random().toFixed(9).slice(2)}$`,he="?"+y,ze=`<${he}>`,P=document,R=()=>P.createComment(""),H=r=>r===null||typeof r!="object"&&typeof r!="function",ee=Array.isArray,Oe=r=>ee(r)||typeof(r==null?void 0:r[Symbol.iterator])=="function",te=`[
\f\r]`,j=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,ue=/-->/g,me=/>/g,E=RegExp(`>|${te}(?:([^\\s"'>=/]+)(${te}*=${te}*(?:[^
\f\r"'\`<>=]|("|')|))|$)`,"g"),ge=/'/g,fe=/"/g,_e=/^(?:script|style|textarea|title)$/i,Ue=r=>(e,...t)=>({_$litType$:r,strings:e,values:t}),n=Ue(1),O=Symbol.for("lit-noChange"),d=Symbol.for("lit-nothing"),ve=new WeakMap,C=P.createTreeWalker(P,129);function be(r,e){if(!ee(r)||!r.hasOwnProperty("raw"))throw Error("invalid template strings array");return de!==void 0?de.createHTML(e):e}const Me=(r,e)=>{const t=r.length-1,s=[];let a,i=e===2?"<svg>":e===3?"<math>":"",o=j;for(let c=0;c<t;c++){const l=r[c];let h,m,p=-1,b=0;for(;b<l.length&&(o.lastIndex=b,m=o.exec(l),m!==null);)b=o.lastIndex,o===j?m[1]==="!--"?o=ue:m[1]!==void 0?o=me:m[2]!==void 0?(_e.test(m[2])&&(a=RegExp("</"+m[2],"g")),o=E):m[3]!==void 0&&(o=E):o===E?m[0]===">"?(o=a??j,p=-1):m[1]===void 0?p=-2:(p=o.lastIndex-m[2].length,h=m[1],o=m[3]===void 0?E:m[3]==='"'?fe:ge):o===fe||o===ge?o=E:o===ue||o===me?o=j:(o=E,a=void 0);const S=o===E&&r[c+1].startsWith("/>")?" ":"";i+=o===j?l+ze:p>=0?(s.push(h),l.slice(0,p)+pe+l.slice(p)+y+S):l+y+(p===-2?c:S)}return[be(r,i+(r[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),s]};class F{constructor({strings:e,_$litType$:t},s){let a;this.parts=[];let i=0,o=0;const c=e.length-1,l=this.parts,[h,m]=Me(e,t);if(this.el=F.createElement(h,s),C.currentNode=this.el.content,t===2||t===3){const p=this.el.content.firstChild;p.replaceWith(...p.childNodes)}for(;(a=C.nextNode())!==null&&l.length<c;){if(a.nodeType===1){if(a.hasAttributes())for(const p of a.getAttributeNames())if(p.endsWith(pe)){const b=m[o++],S=a.getAttribute(p).split(y),J=/([.?@])?(.*)/.exec(b);l.push({type:1,index:i,name:J[2],strings:S,ctor:J[1]==="."?Te:J[1]==="?"?Ie:J[1]==="@"?Re:q}),a.removeAttribute(p)}else p.startsWith(y)&&(l.push({type:6,index:i}),a.removeAttribute(p));if(_e.test(a.tagName)){const p=a.textContent.split(y),b=p.length-1;if(b>0){a.textContent=Q?Q.emptyScript:"";for(let S=0;S<b;S++)a.append(p[S],R()),C.nextNode(),l.push({type:2,index:++i});a.append(p[b],R())}}}else if(a.nodeType===8)if(a.data===he)l.push({type:2,index:i});else{let p=-1;for(;(p=a.data.indexOf(y,p+1))!==-1;)l.push({type:7,index:i}),p+=y.length-1}i++}}static createElement(e,t){const s=P.createElement("template");return s.innerHTML=e,s}}function U(r,e,t=r,s){var o,c;if(e===O)return e;let a=s!==void 0?(o=t._$Co)==null?void 0:o[s]:t._$Cl;const i=H(e)?void 0:e._$litDirective$;return(a==null?void 0:a.constructor)!==i&&((c=a==null?void 0:a._$AO)==null||c.call(a,!1),i===void 0?a=void 0:(a=new i(r),a._$AT(r,t,s)),s!==void 0?(t._$Co??(t._$Co=[]))[s]=a:t._$Cl=a),a!==void 0&&(e=U(r,a._$AS(r,e.values),a,s)),e}class De{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:s}=this._$AD,a=((e==null?void 0:e.creationScope)??P).importNode(t,!0);C.currentNode=a;let i=C.nextNode(),o=0,c=0,l=s[0];for(;l!==void 0;){if(o===l.index){let h;l.type===2?h=new L(i,i.nextSibling,this,e):l.type===1?h=new l.ctor(i,l.name,l.strings,this,e):l.type===6&&(h=new He(i,this,e)),this._$AV.push(h),l=s[++c]}o!==(l==null?void 0:l.index)&&(i=C.nextNode(),o++)}return C.currentNode=P,a}p(e){let t=0;for(const s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(e,s,t),t+=s.strings.length-2):s._$AI(e[t])),t++}}class L{get _$AU(){var e;return((e=this._$AM)==null?void 0:e._$AU)??this._$Cv}constructor(e,t,s,a){this.type=2,this._$AH=d,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=s,this.options=a,this._$Cv=(a==null?void 0:a.isConnected)??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return t!==void 0&&(e==null?void 0:e.nodeType)===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=U(this,e,t),H(e)?e===d||e==null||e===""?(this._$AH!==d&&this._$AR(),this._$AH=d):e!==this._$AH&&e!==O&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):Oe(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==d&&H(this._$AH)?this._$AA.nextSibling.data=e:this.T(P.createTextNode(e)),this._$AH=e}$(e){var i;const{values:t,_$litType$:s}=e,a=typeof s=="number"?this._$AC(e):(s.el===void 0&&(s.el=F.createElement(be(s.h,s.h[0]),this.options)),s);if(((i=this._$AH)==null?void 0:i._$AD)===a)this._$AH.p(t);else{const o=new De(a,this),c=o.u(this.options);o.p(t),this.T(c),this._$AH=o}}_$AC(e){let t=ve.get(e.strings);return t===void 0&&ve.set(e.strings,t=new F(e)),t}k(e){ee(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let s,a=0;for(const i of e)a===t.length?t.push(s=new L(this.O(R()),this.O(R()),this,this.options)):s=t[a],s._$AI(i),a++;a<t.length&&(this._$AR(s&&s._$AB.nextSibling,a),t.length=a)}_$AR(e=this._$AA.nextSibling,t){var s;for((s=this._$AP)==null?void 0:s.call(this,!1,!0,t);e!==this._$AB;){const a=ce(e).nextSibling;ce(e).remove(),e=a}}setConnected(e){var t;this._$AM===void 0&&(this._$Cv=e,(t=this._$AP)==null||t.call(this,e))}}class q{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,s,a,i){this.type=1,this._$AH=d,this._$AN=void 0,this.element=e,this.name=t,this._$AM=a,this.options=i,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=d}_$AI(e,t=this,s,a){const i=this.strings;let o=!1;if(i===void 0)e=U(this,e,t,0),o=!H(e)||e!==this._$AH&&e!==O,o&&(this._$AH=e);else{const c=e;let l,h;for(e=i[0],l=0;l<i.length-1;l++)h=U(this,c[s+l],t,l),h===O&&(h=this._$AH[l]),o||(o=!H(h)||h!==this._$AH[l]),h===d?e=d:e!==d&&(e+=(h??"")+i[l+1]),this._$AH[l]=h}o&&!a&&this.j(e)}j(e){e===d?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class Te extends q{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===d?void 0:e}}class Ie extends q{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==d)}}class Re extends q{constructor(e,t,s,a,i){super(e,t,s,a,i),this.type=5}_$AI(e,t=this){if((e=U(this,e,t,0)??d)===O)return;const s=this._$AH,a=e===d&&s!==d||e.capture!==s.capture||e.once!==s.once||e.passive!==s.passive,i=e!==d&&(s===d||a);a&&this.element.removeEventListener(this.name,this,s),i&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){var t;typeof this._$AH=="function"?this._$AH.call(((t=this.options)==null?void 0:t.host)??this.element,e):this._$AH.handleEvent(e)}}class He{constructor(e,t,s){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(e){U(this,e)}}const re=I.litHtmlPolyfillSupport;re==null||re(F,L),(I.litHtmlVersions??(I.litHtmlVersions=[])).push("3.3.2");const je=(r,e,t)=>{const s=(t==null?void 0:t.renderBefore)??e;let a=s._$litPart$;if(a===void 0){const i=(t==null?void 0:t.renderBefore)??null;s._$litPart$=a=new L(e.insertBefore(R(),i),i,void 0,t??{})}return a._$AI(r),a};/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const N=globalThis;class x extends z{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){var t;const e=super.createRenderRoot();return(t=this.renderOptions).renderBefore??(t.renderBefore=e.firstChild),e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=je(t,this.renderRoot,this.renderOptions)}connectedCallback(){var e;super.connectedCallback(),(e=this._$Do)==null||e.setConnected(!0)}disconnectedCallback(){var e;super.disconnectedCallback(),(e=this._$Do)==null||e.setConnected(!1)}render(){return O}}x._$litElement$=!0,x.finalized=!0,(ye=N.litElementHydrateSupport)==null||ye.call(N,{LitElement:x});const se=N.litElementPolyfillSupport;se==null||se({LitElement:x}),(N.litElementVersions??(N.litElementVersions=[])).push("4.2.2");/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const V=r=>(e,t)=>{t!==void 0?t.addInitializer(()=>{customElements.define(r,e)}):customElements.define(r,e)};/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const Fe={attribute:!0,type:String,converter:W,reflect:!1,hasChanged:X},Le=(r=Fe,e,t)=>{const{kind:s,metadata:a}=t;let i=globalThis.litPropertyMetadata.get(a);if(i===void 0&&globalThis.litPropertyMetadata.set(a,i=new Map),s==="setter"&&((r=Object.create(r)).wrapped=!0),i.set(t.name,r),s==="accessor"){const{name:o}=t;return{set(c){const l=e.get.call(this);e.set.call(this,c),this.requestUpdate(o,l,r,!0,c)},init(c){return c!==void 0&&this.C(o,void 0,r,c),c}}}if(s==="setter"){const{name:o}=t;return function(c){const l=this[o];e.call(this,c),this.requestUpdate(o,l,r,!0,c)}}throw Error("Unsupported decorator location: "+s)};function w(r){return(e,t)=>typeof t=="object"?Le(r,e,t):((s,a,i)=>{const o=a.hasOwnProperty(i);return a.constructor.createProperty(i,s),o?Object.getOwnPropertyDescriptor(a,i):void 0})(r,e,t)}/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function u(r){return w({...r,state:!0,attribute:!1})}const Be=async()=>{if(customElements.get("ha-card"))return;await customElements.whenDefined("partial-panel-resolver");const r=document.createElement("partial-panel-resolver");r.hass={panels:[{url_path:"tmp",component_name:"config"}]},r._updateRoutes(),await r.routerOptions.routes.tmp.load(),customElements.get("ha-card")||await customElements.whenDefined("ha-card")};var Ke=Object.defineProperty,We=Object.getOwnPropertyDescriptor,M=(r,e,t,s)=>{for(var a=s>1?void 0:s?We(e,t):e,i=r.length-1,o;i>=0;i--)(o=r[i])&&(a=(s?o(e,t,a):o(a))||a);return s&&a&&Ke(e,t,a),a};const Qe={pods:"mdi:cube-outline",nodes:"mdi:server",deployments:"mdi:rocket-launch",statefulsets:"mdi:database",daemonsets:"mdi:lan",cronjobs:"mdi:clock-outline",jobs:"mdi:briefcase-check"},$e={pods:"Pods",nodes:"Nodes",deployments:"Deployments",statefulsets:"StatefulSets",daemonsets:"DaemonSets",cronjobs:"CronJobs",jobs:"Jobs"},qe={memory_pressure:"Memory Pressure",disk_pressure:"Disk Pressure",pid_pressure:"PID Pressure",network_unavailable:"Network Unavailable"};let A=class extends x{constructor(){super(...arguments),this._data=null,this._loading=!0,this._error=null,this._expandedNamespaces=new Set}firstUpdated(r){this._loadData(),this._refreshInterval=setInterval(()=>this._loadData(),3e4)}disconnectedCallback(){super.disconnectedCallback(),this._refreshInterval&&(clearInterval(this._refreshInterval),this._refreshInterval=void 0)}async _loadData(){this._data||(this._loading=!0),this._error=null;try{const r=await this.hass.callWS({type:"kubernetes/cluster/overview"});this._data=r}catch(r){this._error=r.message||"Failed to load cluster data"}finally{this._loading=!1}}_toggleNamespaces(r){const e=new Set(this._expandedNamespaces);e.has(r)?e.delete(r):e.add(r),this._expandedNamespaces=e}_formatRelativeTime(r){if(!r)return"Never";const e=Date.now()/1e3,t=Math.max(0,Math.floor(e-r));return t<60?`${t}s ago`:t<3600?`${Math.floor(t/60)}m ago`:t<86400?`${Math.floor(t/3600)}h ago`:`${Math.floor(t/86400)}d ago`}render(){var r;return this._loading?n`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `:this._error?n`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `:(r=this._data)!=null&&r.clusters.length?n` ${this._data.clusters.map(e=>this._renderCluster(e))} `:n` <div class="empty">No Kubernetes clusters configured.</div> `}_renderCluster(r){const e=r.alerts.nodes_with_pressure.length+r.alerts.degraded_workloads.length+r.alerts.failed_pods.length;return n`
      <div class="cluster-section">
        <div class="cluster-header">
          <span class="cluster-name">${r.cluster_name}</span>
          ${this._renderHealthBadge(r.healthy)}
          ${this._renderWatchBadge(r.watch_enabled)}
        </div>

        <div class="meta-row">
          <div class="meta-item">
            <ha-icon icon="mdi:update"></ha-icon>
            <span>Updated ${this._formatRelativeTime(r.last_update)}</span>
          </div>
          <button class="refresh-btn" @click=${this._loadData} title="Refresh data">
            <ha-icon icon="mdi:refresh"></ha-icon>
          </button>
        </div>

        <div class="counts-grid">
          ${Object.entries(r.counts).map(([t,s])=>n`
              <ha-card class="count-card">
                <ha-icon icon=${Qe[t]||"mdi:help"}></ha-icon>
                <div class="count-value">${s}</div>
                <div class="count-label">${$e[t]||t}</div>
              </ha-card>
            `)}
        </div>

        ${this._renderNamespaceSection(r)}

        <div class="alerts-section">
          ${e>0?this._renderAlerts(r.alerts):n`
                <div class="no-alerts">
                  <ha-icon icon="mdi:check-circle"></ha-icon>
                  <span>No active alerts</span>
                </div>
              `}
        </div>
      </div>
    `}_renderHealthBadge(r){return r===!0?n`<span class="badge badge-healthy">Healthy</span>`:r===!1?n`<span class="badge badge-unhealthy">Unhealthy</span>`:n`<span class="badge badge-unknown">Unknown</span>`}_renderWatchBadge(r){return r?n`
        <span class="badge badge-watch">
          <ha-icon icon="mdi:eye"></ha-icon> Watch Active
        </span>
      `:n`
      <span class="badge badge-watch-off">
        <ha-icon icon="mdi:eye-off"></ha-icon> Polling
      </span>
    `}_renderNamespaceSection(r){const e=Object.entries(r.namespaces);if(e.length===0)return d;const t=this._expandedNamespaces.has(r.entry_id);return n`
      <div
        class="section-header"
        @click=${()=>this._toggleNamespaces(r.entry_id)}
      >
        <ha-icon icon=${t?"mdi:chevron-down":"mdi:chevron-right"}></ha-icon>
        <span>Namespaces (${e.length})</span>
      </div>
      ${t?this._renderNamespaceTable(e):d}
    `}_renderNamespaceTable(r){const e=["pods","deployments","statefulsets","daemonsets","cronjobs","jobs"];return n`
      <table class="ns-table">
        <thead>
          <tr>
            <th>Namespace</th>
            ${e.map(t=>n`<th>${$e[t]||t}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${r.sort(([t],[s])=>t.localeCompare(s)).map(([t,s])=>n`
                <tr>
                  <td>${t}</td>
                  ${e.map(a=>n`<td>${s[a]||0}</td>`)}
                </tr>
              `)}
        </tbody>
      </table>
    `}_renderAlerts(r){return n`
      ${r.nodes_with_pressure.map(e=>n`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:server-network-off"></ha-icon>
            <div>
              <div class="alert-title">Node: ${e.name}</div>
              <div class="alert-detail">
                ${e.conditions.map(t=>qe[t]||t).join(", ")}
              </div>
            </div>
          </div>
        `)}
      ${r.degraded_workloads.map(e=>n`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:alert"></ha-icon>
            <div>
              <div class="alert-title">${e.type}: ${e.namespace}/${e.name}</div>
              <div class="alert-detail">${e.ready}/${e.desired} replicas ready</div>
            </div>
          </div>
        `)}
      ${r.failed_pods.map(e=>n`
          <div class="alert-card alert-error">
            <ha-icon icon="mdi:alert-octagon"></ha-icon>
            <div>
              <div class="alert-title">Pod: ${e.namespace}/${e.name}</div>
              <div class="alert-detail">Phase: ${e.phase}</div>
            </div>
          </div>
        `)}
    `}};A.styles=K`
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
      background: rgba(76, 175, 80, 0.15);
      color: #4caf50;
    }

    .badge-unhealthy {
      background: rgba(244, 67, 54, 0.15);
      color: #f44336;
    }

    .badge-unknown {
      background: rgba(158, 158, 158, 0.15);
      color: #9e9e9e;
    }

    .badge-watch {
      background: rgba(33, 150, 243, 0.15);
      color: #2196f3;
    }

    .badge-watch-off {
      background: rgba(158, 158, 158, 0.1);
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
      background: rgba(255, 152, 0, 0.1);
      color: var(--primary-text-color);
    }

    .alert-warning ha-icon {
      color: #ff9800;
    }

    .alert-error {
      background: rgba(244, 67, 54, 0.1);
      color: var(--primary-text-color);
    }

    .alert-error ha-icon {
      color: #f44336;
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
      gap: 8px;
      padding: 12px 0;
      color: #4caf50;
      font-size: 14px;
      --mdc-icon-size: 20px;
    }
  `,M([w({attribute:!1})],A.prototype,"hass",2),M([u()],A.prototype,"_data",2),M([u()],A.prototype,"_loading",2),M([u()],A.prototype,"_error",2),M([u()],A.prototype,"_expandedNamespaces",2),A=M([V("k8s-overview")],A);var Ve=Object.defineProperty,Je=Object.getOwnPropertyDescriptor,k=(r,e,t,s)=>{for(var a=s>1?void 0:s?Je(e,t):e,i=r.length-1,o;i>=0;i--)(o=r[i])&&(a=(s?o(e,t,a):o(a))||a);return s&&a&&Ve(e,t,a),a};const Ge={memory_pressure:"Memory Pressure",disk_pressure:"Disk Pressure",pid_pressure:"PID Pressure",network_unavailable:"Network Unavailable"};let _=class extends x{constructor(){super(...arguments),this._data=null,this._loading=!0,this._error=null,this._expandedNodes=new Set,this._statusFilter="all",this._searchQuery=""}firstUpdated(r){this._loadData(),this._refreshInterval=setInterval(()=>this._loadData(),3e4)}disconnectedCallback(){super.disconnectedCallback(),this._refreshInterval&&(clearInterval(this._refreshInterval),this._refreshInterval=void 0)}async _loadData(){this._data||(this._loading=!0),this._error=null;try{const r=await this.hass.callWS({type:"kubernetes/nodes/list"});this._data=r}catch(r){this._error=r.message||"Failed to load nodes data"}finally{this._loading=!1}}_toggleNode(r){const e=new Set(this._expandedNodes);e.has(r)?e.delete(r):e.add(r),this._expandedNodes=e}_getConditions(r){const e=[];return r.memory_pressure&&e.push("memory_pressure"),r.disk_pressure&&e.push("disk_pressure"),r.pid_pressure&&e.push("pid_pressure"),r.network_unavailable&&e.push("network_unavailable"),e}_formatAge(r){if(!r||r==="N/A")return"N/A";const e=new Date(r).getTime(),t=Date.now(),s=Math.max(0,Math.floor((t-e)/1e3));return s<60?`${s}s`:s<3600?`${Math.floor(s/60)}m`:s<86400?`${Math.floor(s/3600)}h`:`${Math.floor(s/86400)}d`}_getFilteredNodes(r){let e=r;if(this._statusFilter!=="all"&&(e=e.filter(t=>this._statusFilter==="ready"?t.status==="Ready":t.status!=="Ready")),this._searchQuery){const t=this._searchQuery.toLowerCase();e=e.filter(s=>s.name.toLowerCase().includes(t)||s.internal_ip.toLowerCase().includes(t)||s.kubelet_version.toLowerCase().includes(t))}return e}render(){var r;return this._loading?n`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `:this._error?n`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `:(r=this._data)!=null&&r.clusters.length?n`${this._data.clusters.map(e=>this._renderCluster(e))}`:n`<div class="empty">No Kubernetes clusters configured.</div>`}_renderCluster(r){const e=this._getFilteredNodes(r.nodes),t=r.nodes.filter(s=>s.status==="Ready").length;return n`
      <div class="cluster-section">
        ${this._data.clusters.length>1?n`<div class="cluster-name">${r.cluster_name}</div>`:d}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search nodes..."
            .value=${this._searchQuery}
            @input=${s=>{this._searchQuery=s.target.value}}
          />
          ${["all","ready","not-ready"].map(s=>n`
              <button
                class="filter-chip"
                ?active=${this._statusFilter===s}
                @click=${()=>{this._statusFilter=s}}
              >
                ${s==="all"?"All":s==="ready"?"Ready":"Not Ready"}
              </button>
            `)}
        </div>

        <div class="node-count">
          ${t}/${r.nodes.length} nodes ready
          ${e.length!==r.nodes.length?n` &middot; showing ${e.length}`:d}
        </div>

        ${e.length===0?n`<div class="empty">No nodes match your filters.</div>`:e.map(s=>this._renderNode(r.entry_id,s))}
      </div>
    `}_renderNode(r,e){const t=`${r}_${e.name}`,s=this._expandedNodes.has(t),a=this._getConditions(e),i=e.memory_capacity_gib>0?Math.round(e.memory_allocatable_gib/e.memory_capacity_gib*100):0;return n`
      <ha-card class="node-card">
        <div class="node-row" @click=${()=>this._toggleNode(t)}>
          <div class="node-name">
            <ha-icon
              icon=${s?"mdi:chevron-down":"mdi:chevron-right"}
            ></ha-icon>
            ${e.name}
            ${e.schedulable?d:n`<span class="badge badge-unschedulable">Unschedulable</span>`}
            ${a.length>0?n`<span class="badge badge-condition"
                  >${a.length}
                  condition${a.length>1?"s":""}</span
                >`:d}
          </div>
          <span
            class="badge ${e.status==="Ready"?"badge-ready":"badge-not-ready"}"
          >
            ${e.status}
          </span>
          <span class="node-ip">${e.internal_ip}</span>
          <div class="node-resources">
            <span>${e.cpu_cores} CPU</span>
            <div class="resource-bar-container">
              <div class="resource-bar">
                <div class="resource-bar-fill" style="width: ${i}%"></div>
              </div>
              <span
                >${e.memory_allocatable_gib}/${e.memory_capacity_gib} GiB</span
              >
            </div>
          </div>
          <span class="node-age">${this._formatAge(e.creation_timestamp)}</span>
        </div>
        ${s?this._renderNodeDetails(e,a):d}
      </ha-card>
    `}_renderNodeDetails(r,e){return n`
      <div class="node-details">
        <div class="details-grid">
          <div class="detail-item">
            <span class="detail-label">Internal IP</span>
            <span class="detail-value mono">${r.internal_ip}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">External IP</span>
            <span class="detail-value mono">${r.external_ip}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">CPU Cores</span>
            <span class="detail-value">${r.cpu_cores}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Memory Capacity</span>
            <span class="detail-value">${r.memory_capacity_gib} GiB</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Memory Allocatable</span>
            <span class="detail-value">${r.memory_allocatable_gib} GiB</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">OS Image</span>
            <span class="detail-value">${r.os_image}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Kernel</span>
            <span class="detail-value mono">${r.kernel_version}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Container Runtime</span>
            <span class="detail-value">${r.container_runtime}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Kubelet Version</span>
            <span class="detail-value mono">${r.kubelet_version}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Schedulable</span>
            <span class="detail-value">${r.schedulable?"Yes":"No"}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Created</span>
            <span class="detail-value">${r.creation_timestamp}</span>
          </div>
        </div>
        ${e.length>0?n`
              <div class="conditions-row">
                ${e.map(t=>n`
                    <span class="badge badge-condition">
                      ${Ge[t]||t}
                    </span>
                  `)}
              </div>
            `:d}
      </div>
    `}};_.styles=K`
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
      background: rgba(76, 175, 80, 0.15);
      color: #4caf50;
    }

    .badge-not-ready {
      background: rgba(244, 67, 54, 0.15);
      color: #f44336;
    }

    .badge-unschedulable {
      background: rgba(255, 152, 0, 0.15);
      color: #ff9800;
    }

    .badge-condition {
      background: rgba(255, 152, 0, 0.15);
      color: #ff9800;
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
  `,k([w({attribute:!1})],_.prototype,"hass",2),k([u()],_.prototype,"_data",2),k([u()],_.prototype,"_loading",2),k([u()],_.prototype,"_error",2),k([u()],_.prototype,"_expandedNodes",2),k([u()],_.prototype,"_statusFilter",2),k([u()],_.prototype,"_searchQuery",2),_=k([V("k8s-nodes-table")],_);var Ze=Object.defineProperty,Ye=Object.getOwnPropertyDescriptor,v=(r,e,t,s)=>{for(var a=s>1?void 0:s?Ye(e,t):e,i=r.length-1,o;i>=0;i--)(o=r[i])&&(a=(s?o(e,t,a):o(a))||a);return s&&a&&Ze(e,t,a),a};const Xe={Running:"badge-running",Succeeded:"badge-succeeded",Pending:"badge-pending",Failed:"badge-failed",Unknown:"badge-unknown"};let g=class extends x{constructor(){super(...arguments),this._data=null,this._loading=!0,this._error=null,this._searchQuery="",this._phaseFilter="all",this._namespaceFilter="all",this._sortField="name",this._sortAsc=!0}firstUpdated(r){this._loadData(),this._refreshInterval=setInterval(()=>this._loadData(),3e4)}disconnectedCallback(){super.disconnectedCallback(),this._refreshInterval&&(clearInterval(this._refreshInterval),this._refreshInterval=void 0)}async _loadData(){this._data||(this._loading=!0),this._error=null;try{const r=await this.hass.callWS({type:"kubernetes/pods/list"});this._data=r}catch(r){this._error=r.message||"Failed to load pods data"}finally{this._loading=!1}}_formatAge(r){if(!r||r==="N/A")return"N/A";const e=new Date(r).getTime(),t=Date.now(),s=Math.max(0,Math.floor((t-e)/1e3));return s<60?`${s}s`:s<3600?`${Math.floor(s/60)}m`:s<86400?`${Math.floor(s/3600)}h`:`${Math.floor(s/86400)}d`}_getNamespaces(r){return[...new Set(r.map(e=>e.namespace))].sort()}_getFilteredPods(r){let e=r;if(this._phaseFilter!=="all"&&(e=e.filter(t=>t.phase===this._phaseFilter)),this._namespaceFilter!=="all"&&(e=e.filter(t=>t.namespace===this._namespaceFilter)),this._searchQuery){const t=this._searchQuery.toLowerCase();e=e.filter(s=>s.name.toLowerCase().includes(t)||s.namespace.toLowerCase().includes(t)||s.node_name.toLowerCase().includes(t)||s.owner_name.toLowerCase().includes(t))}return e.sort((t,s)=>{let a,i;const o=this._sortField;o==="restarts"?(a=t.restart_count,i=s.restart_count):o==="age"?(a=t.creation_timestamp||"",i=s.creation_timestamp||""):(a=t[o]||"",i=s[o]||"");const c=a<i?-1:a>i?1:0;return this._sortAsc?c:-c}),e}_handleSort(r){this._sortField===r?this._sortAsc=!this._sortAsc:(this._sortField=r,this._sortAsc=!0)}_sortIcon(r){return this._sortField!==r?"":this._sortAsc?"mdi:arrow-up":"mdi:arrow-down"}render(){var r;return this._loading?n`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `:this._error?n`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `:(r=this._data)!=null&&r.clusters.length?n`${this._data.clusters.map(e=>this._renderCluster(e))}`:n`<div class="empty">No Kubernetes clusters configured.</div>`}_renderCluster(r){const e=this._getFilteredPods(r.pods),t=this._getNamespaces(r.pods),s=[...new Set(r.pods.map(a=>a.phase))].sort();return n`
      <div class="cluster-section">
        ${this._data.clusters.length>1?n`<div class="cluster-name">${r.cluster_name}</div>`:d}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search pods..."
            .value=${this._searchQuery}
            @input=${a=>{this._searchQuery=a.target.value}}
          />

          <select
            class="ns-select"
            .value=${this._namespaceFilter}
            @change=${a=>{this._namespaceFilter=a.target.value}}
          >
            <option value="all">All namespaces</option>
            ${t.map(a=>n`<option value=${a}>${a}</option>`)}
          </select>

          <button
            class="filter-chip"
            ?active=${this._phaseFilter==="all"}
            @click=${()=>{this._phaseFilter="all"}}
          >
            All
          </button>
          ${s.map(a=>n`
              <button
                class="filter-chip"
                ?active=${this._phaseFilter===a}
                @click=${()=>{this._phaseFilter=a}}
              >
                ${a}
              </button>
            `)}
        </div>

        <div class="pod-count">${e.length}/${r.pods.length} pods</div>

        ${e.length===0?n`<div class="empty">No pods match your filters.</div>`:n`
              <ha-card>
                <div class="table-wrapper">
                  <table class="pods-table">
                    <thead>
                      <tr>
                        <th @click=${()=>this._handleSort("namespace")}>
                          Namespace
                          ${this._sortIcon("namespace")?n`<ha-icon
                                icon=${this._sortIcon("namespace")}
                              ></ha-icon>`:d}
                        </th>
                        <th @click=${()=>this._handleSort("name")}>
                          Name
                          ${this._sortIcon("name")?n`<ha-icon icon=${this._sortIcon("name")}></ha-icon>`:d}
                        </th>
                        <th @click=${()=>this._handleSort("phase")}>
                          Phase
                          ${this._sortIcon("phase")?n`<ha-icon icon=${this._sortIcon("phase")}></ha-icon>`:d}
                        </th>
                        <th>Ready</th>
                        <th @click=${()=>this._handleSort("restarts")}>
                          Restarts
                          ${this._sortIcon("restarts")?n`<ha-icon
                                icon=${this._sortIcon("restarts")}
                              ></ha-icon>`:d}
                        </th>
                        <th
                          class="col-node"
                          @click=${()=>this._handleSort("node_name")}
                        >
                          Node
                          ${this._sortIcon("node_name")?n`<ha-icon
                                icon=${this._sortIcon("node_name")}
                              ></ha-icon>`:d}
                        </th>
                        <th class="col-ip">IP</th>
                        <th class="col-owner">Owner</th>
                        <th @click=${()=>this._handleSort("age")}>
                          Age
                          ${this._sortIcon("age")?n`<ha-icon icon=${this._sortIcon("age")}></ha-icon>`:d}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      ${e.map(a=>this._renderPodRow(a))}
                    </tbody>
                  </table>
                </div>
              </ha-card>
            `}
      </div>
    `}_renderPodRow(r){const e=Xe[r.phase]||"badge-unknown";return n`
      <tr>
        <td>${r.namespace}</td>
        <td class="pod-name">${r.name}</td>
        <td><span class="badge ${e}">${r.phase}</span></td>
        <td>${r.ready_containers}/${r.total_containers}</td>
        <td class=${r.restart_count>5?"restart-warn":""}>
          ${r.restart_count}
        </td>
        <td class="col-node">${r.node_name}</td>
        <td class="col-ip mono">${r.pod_ip}</td>
        <td class="col-owner">
          ${r.owner_kind!=="N/A"?n`<span class="owner-info">${r.owner_kind}/${r.owner_name}</span>`:n`<span class="owner-info">-</span>`}
        </td>
        <td>${this._formatAge(r.creation_timestamp)}</td>
      </tr>
    `}};g.styles=K`
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
      background: rgba(76, 175, 80, 0.15);
      color: #4caf50;
    }

    .badge-succeeded {
      background: rgba(33, 150, 243, 0.15);
      color: #2196f3;
    }

    .badge-pending {
      background: rgba(255, 152, 0, 0.15);
      color: #ff9800;
    }

    .badge-failed {
      background: rgba(244, 67, 54, 0.15);
      color: #f44336;
    }

    .badge-unknown {
      background: rgba(158, 158, 158, 0.15);
      color: #9e9e9e;
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
      color: #ff9800;
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
  `,v([w({attribute:!1})],g.prototype,"hass",2),v([u()],g.prototype,"_data",2),v([u()],g.prototype,"_loading",2),v([u()],g.prototype,"_error",2),v([u()],g.prototype,"_searchQuery",2),v([u()],g.prototype,"_phaseFilter",2),v([u()],g.prototype,"_namespaceFilter",2),v([u()],g.prototype,"_sortField",2),v([u()],g.prototype,"_sortAsc",2),g=v([V("k8s-pods-table")],g);var et=Object.defineProperty,tt=Object.getOwnPropertyDescriptor,D=(r,e,t,s)=>{for(var a=s>1?void 0:s?tt(e,t):e,i=r.length-1,o;i>=0;i--)(o=r[i])&&(a=(s?o(e,t,a):o(a))||a);return s&&a&&et(e,t,a),a};return f.KubernetesPanel=class extends x{constructor(){super(...arguments),this.narrow=!1,this._activeTab="overview",this._tabs=[{id:"overview",label:"Overview",icon:"mdi:view-dashboard"},{id:"nodes",label:"Nodes",icon:"mdi:server"},{id:"workloads",label:"Workloads",icon:"mdi:application-cog"},{id:"pods",label:"Pods",icon:"mdi:cube-outline"},{id:"settings",label:"Settings",icon:"mdi:cog"}]}firstUpdated(e){Be()}_handleTabChange(e){this._activeTab=e}_toggleSidebar(){this.dispatchEvent(new Event("hass-toggle-menu",{bubbles:!0,composed:!0}))}render(){return n`
      <div class="toolbar">
        <div class="menu-btn" @click=${this._toggleSidebar}>
          <ha-icon icon="mdi:menu"></ha-icon>
        </div>
        <h1>Kubernetes</h1>
      </div>
      <div class="tab-bar">
        ${this._tabs.map(e=>n`
            <div
              class="tab"
              ?active=${this._activeTab===e.id}
              @click=${()=>this._handleTabChange(e.id)}
            >
              <ha-icon icon=${e.icon}></ha-icon>
              <span>${e.label}</span>
            </div>
          `)}
      </div>
      <div class="content">${this._renderActiveTab()}</div>
    `}_renderActiveTab(){switch(this._activeTab){case"overview":return n`<k8s-overview .hass=${this.hass}></k8s-overview>`;case"nodes":return n`<k8s-nodes-table .hass=${this.hass}></k8s-nodes-table>`;case"pods":return n`<k8s-pods-table .hass=${this.hass}></k8s-pods-table>`;default:return n`
          <div class="coming-soon">
            <ha-icon icon="mdi:hammer-wrench"></ha-icon>
            <p>This tab is coming in a future release.</p>
          </div>
        `}}},f.KubernetesPanel.styles=K`
    :host {
      display: block;
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
      height: calc(100% - 56px - 49px);
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
  `,D([w({attribute:!1})],f.KubernetesPanel.prototype,"hass",2),D([w({type:Boolean,reflect:!0})],f.KubernetesPanel.prototype,"narrow",2),D([w({attribute:!1})],f.KubernetesPanel.prototype,"route",2),D([w({attribute:!1})],f.KubernetesPanel.prototype,"panel",2),D([u()],f.KubernetesPanel.prototype,"_activeTab",2),f.KubernetesPanel=D([V("kubernetes-panel")],f.KubernetesPanel),Object.defineProperty(f,Symbol.toStringTag,{value:"Module"}),f})({});
