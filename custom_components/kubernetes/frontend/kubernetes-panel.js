var KubernetesPanel=(function(m){"use strict";/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */var ve;const j=globalThis,W=j.ShadowRoot&&(j.ShadyCSS===void 0||j.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,q=Symbol(),X=new WeakMap;let Y=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==q)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(W&&e===void 0){const r=t!==void 0&&t.length===1;r&&(e=X.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),r&&X.set(t,e))}return e}toString(){return this.cssText}};const _e=i=>new Y(typeof i=="string"?i:i+"",void 0,q),ee=(i,...e)=>{const t=i.length===1?i[0]:e.reduce((r,s,n)=>r+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+i[n+1],i[0]);return new Y(t,i,q)},$e=(i,e)=>{if(W)i.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const t of e){const r=document.createElement("style"),s=j.litNonce;s!==void 0&&r.setAttribute("nonce",s),r.textContent=t.cssText,i.appendChild(r)}},te=W?i=>i:i=>i instanceof CSSStyleSheet?(e=>{let t="";for(const r of e.cssRules)t+=r.cssText;return _e(t)})(i):i;/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const{is:be,defineProperty:ye,getOwnPropertyDescriptor:xe,getOwnPropertyNames:Ae,getOwnPropertySymbols:we,getPrototypeOf:Ee}=Object,g=globalThis,re=g.trustedTypes,Se=re?re.emptyScript:"",V=g.reactiveElementPolyfillSupport,N=(i,e)=>i,I={toAttribute(i,e){switch(e){case Boolean:i=i?Se:null;break;case Object:case Array:i=i==null?i:JSON.stringify(i)}return i},fromAttribute(i,e){let t=i;switch(e){case Boolean:t=i!==null;break;case Number:t=i===null?null:Number(i);break;case Object:case Array:try{t=JSON.parse(i)}catch{t=null}}return t}},J=(i,e)=>!be(i,e),se={attribute:!0,type:String,converter:I,reflect:!1,useDefault:!1,hasChanged:J};Symbol.metadata??(Symbol.metadata=Symbol("metadata")),g.litPropertyMetadata??(g.litPropertyMetadata=new WeakMap);let w=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??(this.l=[])).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=se){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const r=Symbol(),s=this.getPropertyDescriptor(e,r,t);s!==void 0&&ye(this.prototype,e,s)}}static getPropertyDescriptor(e,t,r){const{get:s,set:n}=xe(this.prototype,e)??{get(){return this[t]},set(o){this[t]=o}};return{get:s,set(o){const l=s==null?void 0:s.call(this);n==null||n.call(this,o),this.requestUpdate(e,l,r)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??se}static _$Ei(){if(this.hasOwnProperty(N("elementProperties")))return;const e=Ee(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(N("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(N("properties"))){const t=this.properties,r=[...Ae(t),...we(t)];for(const s of r)this.createProperty(s,t[s])}const e=this[Symbol.metadata];if(e!==null){const t=litPropertyMetadata.get(e);if(t!==void 0)for(const[r,s]of t)this.elementProperties.set(r,s)}this._$Eh=new Map;for(const[t,r]of this.elementProperties){const s=this._$Eu(t,r);s!==void 0&&this._$Eh.set(s,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const r=new Set(e.flat(1/0).reverse());for(const s of r)t.unshift(te(s))}else e!==void 0&&t.push(te(e));return t}static _$Eu(e,t){const r=t.attribute;return r===!1?void 0:typeof r=="string"?r:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){var e;this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),(e=this.constructor.l)==null||e.forEach(t=>t(this))}addController(e){var t;(this._$EO??(this._$EO=new Set)).add(e),this.renderRoot!==void 0&&this.isConnected&&((t=e.hostConnected)==null||t.call(e))}removeController(e){var t;(t=this._$EO)==null||t.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const r of t.keys())this.hasOwnProperty(r)&&(e.set(r,this[r]),delete this[r]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return $e(e,this.constructor.elementStyles),e}connectedCallback(){var e;this.renderRoot??(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),(e=this._$EO)==null||e.forEach(t=>{var r;return(r=t.hostConnected)==null?void 0:r.call(t)})}enableUpdating(e){}disconnectedCallback(){var e;(e=this._$EO)==null||e.forEach(t=>{var r;return(r=t.hostDisconnected)==null?void 0:r.call(t)})}attributeChangedCallback(e,t,r){this._$AK(e,r)}_$ET(e,t){var n;const r=this.constructor.elementProperties.get(e),s=this.constructor._$Eu(e,r);if(s!==void 0&&r.reflect===!0){const o=(((n=r.converter)==null?void 0:n.toAttribute)!==void 0?r.converter:I).toAttribute(t,r.type);this._$Em=e,o==null?this.removeAttribute(s):this.setAttribute(s,o),this._$Em=null}}_$AK(e,t){var n,o;const r=this.constructor,s=r._$Eh.get(e);if(s!==void 0&&this._$Em!==s){const l=r.getPropertyOptions(s),a=typeof l.converter=="function"?{fromAttribute:l.converter}:((n=l.converter)==null?void 0:n.fromAttribute)!==void 0?l.converter:I;this._$Em=s;const h=a.fromAttribute(t,l.type);this[s]=h??((o=this._$Ej)==null?void 0:o.get(s))??h,this._$Em=null}}requestUpdate(e,t,r,s=!1,n){var o;if(e!==void 0){const l=this.constructor;if(s===!1&&(n=this[e]),r??(r=l.getPropertyOptions(e)),!((r.hasChanged??J)(n,t)||r.useDefault&&r.reflect&&n===((o=this._$Ej)==null?void 0:o.get(e))&&!this.hasAttribute(l._$Eu(e,r))))return;this.C(e,t,r)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:r,reflect:s,wrapped:n},o){r&&!(this._$Ej??(this._$Ej=new Map)).has(e)&&(this._$Ej.set(e,o??t??this[e]),n!==!0||o!==void 0)||(this._$AL.has(e)||(this.hasUpdated||r||(t=void 0),this._$AL.set(e,t)),s===!0&&this._$Em!==e&&(this._$Eq??(this._$Eq=new Set)).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){var r;if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??(this.renderRoot=this.createRenderRoot()),this._$Ep){for(const[n,o]of this._$Ep)this[n]=o;this._$Ep=void 0}const s=this.constructor.elementProperties;if(s.size>0)for(const[n,o]of s){const{wrapped:l}=o,a=this[n];l!==!0||this._$AL.has(n)||a===void 0||this.C(n,void 0,o,a)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),(r=this._$EO)==null||r.forEach(s=>{var n;return(n=s.hostUpdate)==null?void 0:n.call(s)}),this.update(t)):this._$EM()}catch(s){throw e=!1,this._$EM(),s}e&&this._$AE(t)}willUpdate(e){}_$AE(e){var t;(t=this._$EO)==null||t.forEach(r=>{var s;return(s=r.hostUpdated)==null?void 0:s.call(r)}),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&(this._$Eq=this._$Eq.forEach(t=>this._$ET(t,this[t]))),this._$EM()}updated(e){}firstUpdated(e){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[N("elementProperties")]=new Map,w[N("finalized")]=new Map,V==null||V({ReactiveElement:w}),(g.reactiveElementVersions??(g.reactiveElementVersions=[])).push("2.1.2");/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const U=globalThis,ie=i=>i,L=U.trustedTypes,oe=L?L.createPolicy("lit-html",{createHTML:i=>i}):void 0,ne="$lit$",v=`lit$${Math.random().toFixed(9).slice(2)}$`,ae="?"+v,Pe=`<${ae}>`,b=document,T=()=>b.createComment(""),z=i=>i===null||typeof i!="object"&&typeof i!="function",Z=Array.isArray,Ce=i=>Z(i)||typeof(i==null?void 0:i[Symbol.iterator])=="function",F=`[
\f\r]`,M=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,le=/-->/g,ce=/>/g,y=RegExp(`>|${F}(?:([^\\s"'>=/]+)(${F}*=${F}*(?:[^
\f\r"'\`<>=]|("|')|))|$)`,"g"),de=/'/g,he=/"/g,pe=/^(?:script|style|textarea|title)$/i,Oe=i=>(e,...t)=>({_$litType$:i,strings:e,values:t}),c=Oe(1),E=Symbol.for("lit-noChange"),p=Symbol.for("lit-nothing"),ue=new WeakMap,x=b.createTreeWalker(b,129);function me(i,e){if(!Z(i)||!i.hasOwnProperty("raw"))throw Error("invalid template strings array");return oe!==void 0?oe.createHTML(e):e}const ke=(i,e)=>{const t=i.length-1,r=[];let s,n=e===2?"<svg>":e===3?"<math>":"",o=M;for(let l=0;l<t;l++){const a=i[l];let h,u,d=-1,f=0;for(;f<a.length&&(o.lastIndex=f,u=o.exec(a),u!==null);)f=o.lastIndex,o===M?u[1]==="!--"?o=le:u[1]!==void 0?o=ce:u[2]!==void 0?(pe.test(u[2])&&(s=RegExp("</"+u[2],"g")),o=y):u[3]!==void 0&&(o=y):o===y?u[0]===">"?(o=s??M,d=-1):u[1]===void 0?d=-2:(d=o.lastIndex-u[2].length,h=u[1],o=u[3]===void 0?y:u[3]==='"'?he:de):o===he||o===de?o=y:o===le||o===ce?o=M:(o=y,s=void 0);const $=o===y&&i[l+1].startsWith("/>")?" ":"";n+=o===M?a+Pe:d>=0?(r.push(h),a.slice(0,d)+ne+a.slice(d)+v+$):a+v+(d===-2?l:$)}return[me(i,n+(i[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),r]};class H{constructor({strings:e,_$litType$:t},r){let s;this.parts=[];let n=0,o=0;const l=e.length-1,a=this.parts,[h,u]=ke(e,t);if(this.el=H.createElement(h,r),x.currentNode=this.el.content,t===2||t===3){const d=this.el.content.firstChild;d.replaceWith(...d.childNodes)}for(;(s=x.nextNode())!==null&&a.length<l;){if(s.nodeType===1){if(s.hasAttributes())for(const d of s.getAttributeNames())if(d.endsWith(ne)){const f=u[o++],$=s.getAttribute(d).split(v),K=/([.?@])?(.*)/.exec(f);a.push({type:1,index:n,name:K[2],strings:$,ctor:K[1]==="."?Ue:K[1]==="?"?Te:K[1]==="@"?ze:B}),s.removeAttribute(d)}else d.startsWith(v)&&(a.push({type:6,index:n}),s.removeAttribute(d));if(pe.test(s.tagName)){const d=s.textContent.split(v),f=d.length-1;if(f>0){s.textContent=L?L.emptyScript:"";for(let $=0;$<f;$++)s.append(d[$],T()),x.nextNode(),a.push({type:2,index:++n});s.append(d[f],T())}}}else if(s.nodeType===8)if(s.data===ae)a.push({type:2,index:n});else{let d=-1;for(;(d=s.data.indexOf(v,d+1))!==-1;)a.push({type:7,index:n}),d+=v.length-1}n++}}static createElement(e,t){const r=b.createElement("template");return r.innerHTML=e,r}}function S(i,e,t=i,r){var o,l;if(e===E)return e;let s=r!==void 0?(o=t._$Co)==null?void 0:o[r]:t._$Cl;const n=z(e)?void 0:e._$litDirective$;return(s==null?void 0:s.constructor)!==n&&((l=s==null?void 0:s._$AO)==null||l.call(s,!1),n===void 0?s=void 0:(s=new n(i),s._$AT(i,t,r)),r!==void 0?(t._$Co??(t._$Co=[]))[r]=s:t._$Cl=s),s!==void 0&&(e=S(i,s._$AS(i,e.values),s,r)),e}class Ne{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:r}=this._$AD,s=((e==null?void 0:e.creationScope)??b).importNode(t,!0);x.currentNode=s;let n=x.nextNode(),o=0,l=0,a=r[0];for(;a!==void 0;){if(o===a.index){let h;a.type===2?h=new R(n,n.nextSibling,this,e):a.type===1?h=new a.ctor(n,a.name,a.strings,this,e):a.type===6&&(h=new Me(n,this,e)),this._$AV.push(h),a=r[++l]}o!==(a==null?void 0:a.index)&&(n=x.nextNode(),o++)}return x.currentNode=b,s}p(e){let t=0;for(const r of this._$AV)r!==void 0&&(r.strings!==void 0?(r._$AI(e,r,t),t+=r.strings.length-2):r._$AI(e[t])),t++}}class R{get _$AU(){var e;return((e=this._$AM)==null?void 0:e._$AU)??this._$Cv}constructor(e,t,r,s){this.type=2,this._$AH=p,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=r,this.options=s,this._$Cv=(s==null?void 0:s.isConnected)??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return t!==void 0&&(e==null?void 0:e.nodeType)===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=S(this,e,t),z(e)?e===p||e==null||e===""?(this._$AH!==p&&this._$AR(),this._$AH=p):e!==this._$AH&&e!==E&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):Ce(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==p&&z(this._$AH)?this._$AA.nextSibling.data=e:this.T(b.createTextNode(e)),this._$AH=e}$(e){var n;const{values:t,_$litType$:r}=e,s=typeof r=="number"?this._$AC(e):(r.el===void 0&&(r.el=H.createElement(me(r.h,r.h[0]),this.options)),r);if(((n=this._$AH)==null?void 0:n._$AD)===s)this._$AH.p(t);else{const o=new Ne(s,this),l=o.u(this.options);o.p(t),this.T(l),this._$AH=o}}_$AC(e){let t=ue.get(e.strings);return t===void 0&&ue.set(e.strings,t=new H(e)),t}k(e){Z(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let r,s=0;for(const n of e)s===t.length?t.push(r=new R(this.O(T()),this.O(T()),this,this.options)):r=t[s],r._$AI(n),s++;s<t.length&&(this._$AR(r&&r._$AB.nextSibling,s),t.length=s)}_$AR(e=this._$AA.nextSibling,t){var r;for((r=this._$AP)==null?void 0:r.call(this,!1,!0,t);e!==this._$AB;){const s=ie(e).nextSibling;ie(e).remove(),e=s}}setConnected(e){var t;this._$AM===void 0&&(this._$Cv=e,(t=this._$AP)==null||t.call(this,e))}}class B{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,r,s,n){this.type=1,this._$AH=p,this._$AN=void 0,this.element=e,this.name=t,this._$AM=s,this.options=n,r.length>2||r[0]!==""||r[1]!==""?(this._$AH=Array(r.length-1).fill(new String),this.strings=r):this._$AH=p}_$AI(e,t=this,r,s){const n=this.strings;let o=!1;if(n===void 0)e=S(this,e,t,0),o=!z(e)||e!==this._$AH&&e!==E,o&&(this._$AH=e);else{const l=e;let a,h;for(e=n[0],a=0;a<n.length-1;a++)h=S(this,l[r+a],t,a),h===E&&(h=this._$AH[a]),o||(o=!z(h)||h!==this._$AH[a]),h===p?e=p:e!==p&&(e+=(h??"")+n[a+1]),this._$AH[a]=h}o&&!s&&this.j(e)}j(e){e===p?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class Ue extends B{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===p?void 0:e}}class Te extends B{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==p)}}class ze extends B{constructor(e,t,r,s,n){super(e,t,r,s,n),this.type=5}_$AI(e,t=this){if((e=S(this,e,t,0)??p)===E)return;const r=this._$AH,s=e===p&&r!==p||e.capture!==r.capture||e.once!==r.once||e.passive!==r.passive,n=e!==p&&(r===p||s);s&&this.element.removeEventListener(this.name,this,r),n&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){var t;typeof this._$AH=="function"?this._$AH.call(((t=this.options)==null?void 0:t.host)??this.element,e):this._$AH.handleEvent(e)}}class Me{constructor(e,t,r){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=r}get _$AU(){return this._$AM._$AU}_$AI(e){S(this,e)}}const G=U.litHtmlPolyfillSupport;G==null||G(H,R),(U.litHtmlVersions??(U.litHtmlVersions=[])).push("3.3.2");const He=(i,e,t)=>{const r=(t==null?void 0:t.renderBefore)??e;let s=r._$litPart$;if(s===void 0){const n=(t==null?void 0:t.renderBefore)??null;r._$litPart$=s=new R(e.insertBefore(T(),n),n,void 0,t??{})}return s._$AI(i),s};/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const A=globalThis;class P extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){var t;const e=super.createRenderRoot();return(t=this.renderOptions).renderBefore??(t.renderBefore=e.firstChild),e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=He(t,this.renderRoot,this.renderOptions)}connectedCallback(){var e;super.connectedCallback(),(e=this._$Do)==null||e.setConnected(!0)}disconnectedCallback(){var e;super.disconnectedCallback(),(e=this._$Do)==null||e.setConnected(!1)}render(){return E}}P._$litElement$=!0,P.finalized=!0,(ve=A.litElementHydrateSupport)==null||ve.call(A,{LitElement:P});const Q=A.litElementPolyfillSupport;Q==null||Q({LitElement:P}),(A.litElementVersions??(A.litElementVersions=[])).push("4.2.2");/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const fe=i=>(e,t)=>{t!==void 0?t.addInitializer(()=>{customElements.define(i,e)}):customElements.define(i,e)};/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const Re={attribute:!0,type:String,converter:I,reflect:!1,hasChanged:J},De=(i=Re,e,t)=>{const{kind:r,metadata:s}=t;let n=globalThis.litPropertyMetadata.get(s);if(n===void 0&&globalThis.litPropertyMetadata.set(s,n=new Map),r==="setter"&&((i=Object.create(i)).wrapped=!0),n.set(t.name,i),r==="accessor"){const{name:o}=t;return{set(l){const a=e.get.call(this);e.set.call(this,l),this.requestUpdate(o,a,i,!0,l)},init(l){return l!==void 0&&this.C(o,void 0,i,l),l}}}if(r==="setter"){const{name:o}=t;return function(l){const a=this[o];e.call(this,l),this.requestUpdate(o,a,i,!0,l)}}throw Error("Unsupported decorator location: "+r)};function C(i){return(e,t)=>typeof t=="object"?De(i,e,t):((r,s,n)=>{const o=s.hasOwnProperty(n);return s.constructor.createProperty(n,r),o?Object.getOwnPropertyDescriptor(s,n):void 0})(i,e,t)}/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function D(i){return C({...i,state:!0,attribute:!1})}const je=async()=>{if(customElements.get("ha-card"))return;await customElements.whenDefined("partial-panel-resolver");const i=document.createElement("partial-panel-resolver");i.hass={panels:[{url_path:"tmp",component_name:"config"}]},i._updateRoutes(),await i.routerOptions.routes.tmp.load(),customElements.get("ha-card")||await customElements.whenDefined("ha-card")};var Ie=Object.defineProperty,Le=Object.getOwnPropertyDescriptor,O=(i,e,t,r)=>{for(var s=r>1?void 0:r?Le(e,t):e,n=i.length-1,o;n>=0;n--)(o=i[n])&&(s=(r?o(e,t,s):o(s))||s);return r&&s&&Ie(e,t,s),s};const Be={pods:"mdi:cube-outline",nodes:"mdi:server",deployments:"mdi:rocket-launch",statefulsets:"mdi:database",daemonsets:"mdi:lan",cronjobs:"mdi:clock-outline",jobs:"mdi:briefcase-check"},ge={pods:"Pods",nodes:"Nodes",deployments:"Deployments",statefulsets:"StatefulSets",daemonsets:"DaemonSets",cronjobs:"CronJobs",jobs:"Jobs"},Ke={memory_pressure:"Memory Pressure",disk_pressure:"Disk Pressure",pid_pressure:"PID Pressure",network_unavailable:"Network Unavailable"};let _=class extends P{constructor(){super(...arguments),this._data=null,this._loading=!0,this._error=null,this._expandedNamespaces=new Set}firstUpdated(i){this._loadData(),this._refreshInterval=setInterval(()=>this._loadData(),3e4)}disconnectedCallback(){super.disconnectedCallback(),this._refreshInterval&&(clearInterval(this._refreshInterval),this._refreshInterval=void 0)}async _loadData(){this._data||(this._loading=!0),this._error=null;try{const i=await this.hass.callWS({type:"kubernetes/cluster/overview"});this._data=i}catch(i){this._error=i.message||"Failed to load cluster data"}finally{this._loading=!1}}_toggleNamespaces(i){const e=new Set(this._expandedNamespaces);e.has(i)?e.delete(i):e.add(i),this._expandedNamespaces=e}_formatRelativeTime(i){if(!i)return"Never";const e=Date.now()/1e3,t=Math.max(0,Math.floor(e-i));return t<60?`${t}s ago`:t<3600?`${Math.floor(t/60)}m ago`:t<86400?`${Math.floor(t/3600)}h ago`:`${Math.floor(t/86400)}d ago`}render(){var i;return this._loading?c`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `:this._error?c`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `:(i=this._data)!=null&&i.clusters.length?c` ${this._data.clusters.map(e=>this._renderCluster(e))} `:c` <div class="empty">No Kubernetes clusters configured.</div> `}_renderCluster(i){const e=i.alerts.nodes_with_pressure.length+i.alerts.degraded_workloads.length+i.alerts.failed_pods.length;return c`
      <div class="cluster-section">
        <div class="cluster-header">
          <span class="cluster-name">${i.cluster_name}</span>
          ${this._renderHealthBadge(i.healthy)}
          ${this._renderWatchBadge(i.watch_enabled)}
        </div>

        <div class="meta-row">
          <div class="meta-item">
            <ha-icon icon="mdi:update"></ha-icon>
            <span>Updated ${this._formatRelativeTime(i.last_update)}</span>
          </div>
          <button class="refresh-btn" @click=${this._loadData} title="Refresh data">
            <ha-icon icon="mdi:refresh"></ha-icon>
          </button>
        </div>

        <div class="counts-grid">
          ${Object.entries(i.counts).map(([t,r])=>c`
              <ha-card class="count-card">
                <ha-icon icon=${Be[t]||"mdi:help"}></ha-icon>
                <div class="count-value">${r}</div>
                <div class="count-label">${ge[t]||t}</div>
              </ha-card>
            `)}
        </div>

        ${this._renderNamespaceSection(i)}

        <div class="alerts-section">
          ${e>0?this._renderAlerts(i.alerts):c`
                <div class="no-alerts">
                  <ha-icon icon="mdi:check-circle"></ha-icon>
                  <span>No active alerts</span>
                </div>
              `}
        </div>
      </div>
    `}_renderHealthBadge(i){return i===!0?c`<span class="badge badge-healthy">Healthy</span>`:i===!1?c`<span class="badge badge-unhealthy">Unhealthy</span>`:c`<span class="badge badge-unknown">Unknown</span>`}_renderWatchBadge(i){return i?c`
        <span class="badge badge-watch">
          <ha-icon icon="mdi:eye"></ha-icon> Watch Active
        </span>
      `:c`
      <span class="badge badge-watch-off">
        <ha-icon icon="mdi:eye-off"></ha-icon> Polling
      </span>
    `}_renderNamespaceSection(i){const e=Object.entries(i.namespaces);if(e.length===0)return p;const t=this._expandedNamespaces.has(i.entry_id);return c`
      <div
        class="section-header"
        @click=${()=>this._toggleNamespaces(i.entry_id)}
      >
        <ha-icon icon=${t?"mdi:chevron-down":"mdi:chevron-right"}></ha-icon>
        <span>Namespaces (${e.length})</span>
      </div>
      ${t?this._renderNamespaceTable(e):p}
    `}_renderNamespaceTable(i){const e=["pods","deployments","statefulsets","daemonsets","cronjobs","jobs"];return c`
      <table class="ns-table">
        <thead>
          <tr>
            <th>Namespace</th>
            ${e.map(t=>c`<th>${ge[t]||t}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${i.sort(([t],[r])=>t.localeCompare(r)).map(([t,r])=>c`
                <tr>
                  <td>${t}</td>
                  ${e.map(s=>c`<td>${r[s]||0}</td>`)}
                </tr>
              `)}
        </tbody>
      </table>
    `}_renderAlerts(i){return c`
      ${i.nodes_with_pressure.map(e=>c`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:server-network-off"></ha-icon>
            <div>
              <div class="alert-title">Node: ${e.name}</div>
              <div class="alert-detail">
                ${e.conditions.map(t=>Ke[t]||t).join(", ")}
              </div>
            </div>
          </div>
        `)}
      ${i.degraded_workloads.map(e=>c`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:alert"></ha-icon>
            <div>
              <div class="alert-title">${e.type}: ${e.namespace}/${e.name}</div>
              <div class="alert-detail">${e.ready}/${e.desired} replicas ready</div>
            </div>
          </div>
        `)}
      ${i.failed_pods.map(e=>c`
          <div class="alert-card alert-error">
            <ha-icon icon="mdi:alert-octagon"></ha-icon>
            <div>
              <div class="alert-title">Pod: ${e.namespace}/${e.name}</div>
              <div class="alert-detail">Phase: ${e.phase}</div>
            </div>
          </div>
        `)}
    `}};_.styles=ee`
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
  `,O([C({attribute:!1})],_.prototype,"hass",2),O([D()],_.prototype,"_data",2),O([D()],_.prototype,"_loading",2),O([D()],_.prototype,"_error",2),O([D()],_.prototype,"_expandedNamespaces",2),_=O([fe("k8s-overview")],_);var We=Object.defineProperty,qe=Object.getOwnPropertyDescriptor,k=(i,e,t,r)=>{for(var s=r>1?void 0:r?qe(e,t):e,n=i.length-1,o;n>=0;n--)(o=i[n])&&(s=(r?o(e,t,s):o(s))||s);return r&&s&&We(e,t,s),s};return m.KubernetesPanel=class extends P{constructor(){super(...arguments),this.narrow=!1,this._activeTab="overview",this._tabs=[{id:"overview",label:"Overview",icon:"mdi:view-dashboard"},{id:"nodes",label:"Nodes",icon:"mdi:server"},{id:"workloads",label:"Workloads",icon:"mdi:application-cog"},{id:"pods",label:"Pods",icon:"mdi:cube-outline"},{id:"settings",label:"Settings",icon:"mdi:cog"}]}firstUpdated(e){je()}_handleTabChange(e){this._activeTab=e}_toggleSidebar(){this.dispatchEvent(new Event("hass-toggle-menu",{bubbles:!0,composed:!0}))}render(){return c`
      <div class="toolbar">
        <div class="menu-btn" @click=${this._toggleSidebar}>
          <ha-icon icon="mdi:menu"></ha-icon>
        </div>
        <h1>Kubernetes</h1>
      </div>
      <div class="tab-bar">
        ${this._tabs.map(e=>c`
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
    `}_renderActiveTab(){return this._activeTab==="overview"?c`<k8s-overview .hass=${this.hass}></k8s-overview>`:c`
      <div class="coming-soon">
        <ha-icon icon="mdi:hammer-wrench"></ha-icon>
        <p>This tab is coming in a future release.</p>
      </div>
    `}},m.KubernetesPanel.styles=ee`
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
  `,k([C({attribute:!1})],m.KubernetesPanel.prototype,"hass",2),k([C({type:Boolean,reflect:!0})],m.KubernetesPanel.prototype,"narrow",2),k([C({attribute:!1})],m.KubernetesPanel.prototype,"route",2),k([C({attribute:!1})],m.KubernetesPanel.prototype,"panel",2),k([D()],m.KubernetesPanel.prototype,"_activeTab",2),m.KubernetesPanel=k([fe("kubernetes-panel")],m.KubernetesPanel),Object.defineProperty(m,Symbol.toStringTag,{value:"Module"}),m})({});
