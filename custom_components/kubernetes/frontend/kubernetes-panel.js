var e=globalThis,t=e.ShadowRoot&&(e.ShadyCSS===void 0||e.ShadyCSS.nativeShadow)&&`adoptedStyleSheets`in Document.prototype&&`replace`in CSSStyleSheet.prototype,n=Symbol(),r=/* @__PURE__ */ new WeakMap,i=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==n)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,n=this.t;if(t&&e===void 0){let t=n!==void 0&&n.length===1;t&&(e=r.get(n)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),t&&r.set(n,e))}return e}toString(){return this.cssText}},a=e=>new i(typeof e==`string`?e:e+``,void 0,n),o=(e,...t)=>new i(e.length===1?e[0]:t.reduce((t,n,r)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if(typeof e==`number`)return e;throw Error(`Value passed to 'css' function must be a 'css' function result: `+e+`. Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.`)})(n)+e[r+1],e[0]),e,n),s=(n,r)=>{if(t)n.adoptedStyleSheets=r.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let t of r){let r=document.createElement(`style`),i=e.litNonce;i!==void 0&&r.setAttribute(`nonce`,i),r.textContent=t.cssText,n.appendChild(r)}},c=t?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t=``;for(let n of e.cssRules)t+=n.cssText;return a(t)})(e):e,{is:l,defineProperty:u,getOwnPropertyDescriptor:d,getOwnPropertyNames:ee,getOwnPropertySymbols:te,getPrototypeOf:ne}=Object,f=globalThis,re=f.trustedTypes,ie=re?re.emptyScript:``,ae=f.reactiveElementPolyfillSupport,p=(e,t)=>e,m={toAttribute(e,t){switch(t){case Boolean:e=e?ie:null;break;case Object:case Array:e=e==null?e:JSON.stringify(e)}return e},fromAttribute(e,t){let n=e;switch(t){case Boolean:n=e!==null;break;case Number:n=e===null?null:Number(e);break;case Object:case Array:try{n=JSON.parse(e)}catch{n=null}}return n}},oe=(e,t)=>!l(e,t),se={attribute:!0,type:String,converter:m,reflect:!1,useDefault:!1,hasChanged:oe};Symbol.metadata??=Symbol(`metadata`),f.litPropertyMetadata??=/* @__PURE__ */ new WeakMap;var h=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=se){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let n=Symbol(),r=this.getPropertyDescriptor(e,n,t);r!==void 0&&u(this.prototype,e,r)}}static getPropertyDescriptor(e,t,n){let{get:r,set:i}=d(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:r,set(t){let a=r?.call(this);i?.call(this,t),this.requestUpdate(e,a,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??se}static _$Ei(){if(this.hasOwnProperty(p(`elementProperties`)))return;let e=ne(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(p(`finalized`)))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(p(`properties`))){let e=this.properties,t=[...ee(e),...te(e)];for(let n of t)this.createProperty(n,e[n])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[e,n]of t)this.elementProperties.set(e,n)}this._$Eh=/* @__PURE__ */ new Map;for(let[e,t]of this.elementProperties){let n=this._$Eu(e,t);n!==void 0&&this._$Eh.set(n,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let n=new Set(e.flat(1/0).reverse());for(let e of n)t.unshift(c(e))}else e!==void 0&&t.push(c(e));return t}static _$Eu(e,t){let n=t.attribute;return!1===n?void 0:typeof n==`string`?n:typeof e==`string`?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=/* @__PURE__ */ new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=/* @__PURE__ */ new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=/* @__PURE__ */ new Map,t=this.constructor.elementProperties;for(let n of t.keys())this.hasOwnProperty(n)&&(e.set(n,this[n]),delete this[n]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return s(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,n){this._$AK(e,n)}_$ET(e,t){let n=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,n);if(r!==void 0&&!0===n.reflect){let i=(n.converter?.toAttribute===void 0?m:n.converter).toAttribute(t,n.type);this._$Em=e,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(e,t){let n=this.constructor,r=n._$Eh.get(e);if(r!==void 0&&this._$Em!==r){let e=n.getPropertyOptions(r),i=typeof e.converter==`function`?{fromAttribute:e.converter}:e.converter?.fromAttribute===void 0?m:e.converter;this._$Em=r;let a=i.fromAttribute(t,e.type);this[r]=a??this._$Ej?.get(r)??a,this._$Em=null}}requestUpdate(e,t,n,r=!1,i){if(e!==void 0){let a=this.constructor;if(!1===r&&(i=this[e]),n??=a.getPropertyOptions(e),!((n.hasChanged??oe)(i,t)||n.useDefault&&n.reflect&&i===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,n))))return;this.C(e,t,n)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:n,reflect:r,wrapped:i},a){n&&!(this._$Ej??=/* @__PURE__ */ new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),!0!==i||a!==void 0)||(this._$AL.has(e)||(this.hasUpdated||n||(t=void 0),this._$AL.set(e,t)),!0===r&&this._$Em!==e&&(this._$Eq??=/* @__PURE__ */ new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}let e=this.constructor.elementProperties;if(e.size>0)for(let[t,n]of e){let{wrapped:e}=n,r=this[t];!0!==e||this._$AL.has(t)||r===void 0||this.C(t,void 0,n,r)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=/* @__PURE__ */ new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};h.elementStyles=[],h.shadowRootOptions={mode:`open`},h[p(`elementProperties`)]=/* @__PURE__ */ new Map,h[p(`finalized`)]=/* @__PURE__ */ new Map,ae?.({ReactiveElement:h}),(f.reactiveElementVersions??=[]).push(`2.1.2`);var ce=globalThis,le=e=>e,g=ce.trustedTypes,ue=g?g.createPolicy(`lit-html`,{createHTML:e=>e}):void 0,de=`$lit$`,_=`lit$${Math.random().toFixed(9).slice(2)}$`,v=`?`+_,fe=`<${v}>`,y=document,b=()=>y.createComment(``),x=e=>e===null||typeof e!=`object`&&typeof e!=`function`,S=Array.isArray,pe=e=>S(e)||typeof e?.[Symbol.iterator]==`function`,C=`[ 	
\f\r]`,w=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,me=/-->/g,he=/>/g,T=RegExp(`>|${C}(?:([^\\s"'>=/]+)(${C}*=${C}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,`g`),ge=/'/g,_e=/"/g,ve=/^(?:script|style|textarea|title)$/i,E=(e=>(t,...n)=>({_$litType$:e,strings:t,values:n}))(1),D=Symbol.for(`lit-noChange`),O=Symbol.for(`lit-nothing`),ye=/* @__PURE__ */ new WeakMap,k=y.createTreeWalker(y,129);function be(e,t){if(!S(e)||!e.hasOwnProperty(`raw`))throw Error(`invalid template strings array`);return ue===void 0?t:ue.createHTML(t)}var xe=(e,t)=>{let n=e.length-1,r=[],i,a=t===2?`<svg>`:t===3?`<math>`:``,o=w;for(let t=0;t<n;t++){let n=e[t],s,c,l=-1,u=0;for(;u<n.length&&(o.lastIndex=u,c=o.exec(n),c!==null);)u=o.lastIndex,o===w?c[1]===`!--`?o=me:c[1]===void 0?c[2]===void 0?c[3]!==void 0&&(o=T):(ve.test(c[2])&&(i=RegExp(`</`+c[2],`g`)),o=T):o=he:o===T?c[0]===`>`?(o=i??w,l=-1):c[1]===void 0?l=-2:(l=o.lastIndex-c[2].length,s=c[1],o=c[3]===void 0?T:c[3]===`"`?_e:ge):o===_e||o===ge?o=T:o===me||o===he?o=w:(o=T,i=void 0);let d=o===T&&e[t+1].startsWith(`/>`)?` `:``;a+=o===w?n+fe:l>=0?(r.push(s),n.slice(0,l)+de+n.slice(l)+_+d):n+_+(l===-2?t:d)}return[be(e,a+(e[n]||`<?>`)+(t===2?`</svg>`:t===3?`</math>`:``)),r]},A=class e{constructor({strings:t,_$litType$:n},r){let i;this.parts=[];let a=0,o=0,s=t.length-1,c=this.parts,[l,u]=xe(t,n);if(this.el=e.createElement(l,r),k.currentNode=this.el.content,n===2||n===3){let e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;(i=k.nextNode())!==null&&c.length<s;){if(i.nodeType===1){if(i.hasAttributes())for(let e of i.getAttributeNames())if(e.endsWith(de)){let t=u[o++],n=i.getAttribute(e).split(_),r=/([.?@])?(.*)/.exec(t);c.push({type:1,index:a,name:r[2],strings:n,ctor:r[1]===`.`?Ce:r[1]===`?`?we:r[1]===`@`?Te:N}),i.removeAttribute(e)}else e.startsWith(_)&&(c.push({type:6,index:a}),i.removeAttribute(e));if(ve.test(i.tagName)){let e=i.textContent.split(_),t=e.length-1;if(t>0){i.textContent=g?g.emptyScript:``;for(let n=0;n<t;n++)i.append(e[n],b()),k.nextNode(),c.push({type:2,index:++a});i.append(e[t],b())}}}else if(i.nodeType===8){if(i.data===v)c.push({type:2,index:a});else{let e=-1;for(;(e=i.data.indexOf(_,e+1))!==-1;)c.push({type:7,index:a}),e+=_.length-1}}a++}}static createElement(e,t){let n=y.createElement(`template`);return n.innerHTML=e,n}};function j(e,t,n=e,r){if(t===D)return t;let i=r===void 0?n._$Cl:n._$Co?.[r],a=x(t)?void 0:t._$litDirective$;return i?.constructor!==a&&(i?._$AO?.(!1),a===void 0?i=void 0:(i=new a(e),i._$AT(e,n,r)),r===void 0?n._$Cl=i:(n._$Co??=[])[r]=i),i!==void 0&&(t=j(e,i._$AS(e,t.values),i,r)),t}var Se=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:n}=this._$AD,r=(e?.creationScope??y).importNode(t,!0);k.currentNode=r;let i=k.nextNode(),a=0,o=0,s=n[0];for(;s!==void 0;){if(a===s.index){let t;s.type===2?t=new M(i,i.nextSibling,this,e):s.type===1?t=new s.ctor(i,s.name,s.strings,this,e):s.type===6&&(t=new Ee(i,this,e)),this._$AV.push(t),s=n[++o]}a!==s?.index&&(i=k.nextNode(),a++)}return k.currentNode=y,r}p(e){let t=0;for(let n of this._$AV)n!==void 0&&(n.strings===void 0?n._$AI(e[t]):(n._$AI(e,n,t),t+=n.strings.length-2)),t++}},M=class e{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,n,r){this.type=2,this._$AH=O,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=n,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=j(this,e,t),x(e)?e===O||e==null||e===``?(this._$AH!==O&&this._$AR(),this._$AH=O):e!==this._$AH&&e!==D&&this._(e):e._$litType$===void 0?e.nodeType===void 0?pe(e)?this.k(e):this._(e):this.T(e):this.$(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==O&&x(this._$AH)?this._$AA.nextSibling.data=e:this.T(y.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:n}=e,r=typeof n==`number`?this._$AC(e):(n.el===void 0&&(n.el=A.createElement(be(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===r)this._$AH.p(t);else{let e=new Se(r,this),n=e.u(this.options);e.p(t),this.T(n),this._$AH=e}}_$AC(e){let t=ye.get(e.strings);return t===void 0&&ye.set(e.strings,t=new A(e)),t}k(t){S(this._$AH)||(this._$AH=[],this._$AR());let n=this._$AH,r,i=0;for(let a of t)i===n.length?n.push(r=new e(this.O(b()),this.O(b()),this,this.options)):r=n[i],r._$AI(a),i++;i<n.length&&(this._$AR(r&&r._$AB.nextSibling,i),n.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let t=le(e).nextSibling;le(e).remove(),e=t}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},N=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,n,r,i){this.type=1,this._$AH=O,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=i,n.length>2||n[0]!==``||n[1]!==``?(this._$AH=Array(n.length-1).fill(/* @__PURE__ */ new String),this.strings=n):this._$AH=O}_$AI(e,t=this,n,r){let i=this.strings,a=!1;if(i===void 0)e=j(this,e,t,0),a=!x(e)||e!==this._$AH&&e!==D,a&&(this._$AH=e);else{let r=e,o,s;for(e=i[0],o=0;o<i.length-1;o++)s=j(this,r[n+o],t,o),s===D&&(s=this._$AH[o]),a||=!x(s)||s!==this._$AH[o],s===O?e=O:e!==O&&(e+=(s??``)+i[o+1]),this._$AH[o]=s}a&&!r&&this.j(e)}j(e){e===O?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??``)}},Ce=class extends N{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===O?void 0:e}},we=class extends N{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==O)}},Te=class extends N{constructor(e,t,n,r,i){super(e,t,n,r,i),this.type=5}_$AI(e,t=this){if((e=j(this,e,t,0)??O)===D)return;let n=this._$AH,r=e===O&&n!==O||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,i=e!==O&&(n===O||r);r&&this.element.removeEventListener(this.name,this,n),i&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH==`function`?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},Ee=class{constructor(e,t,n){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(e){j(this,e)}},De={M:de,P:_,A:v,C:1,L:xe,R:Se,D:pe,V:j,I:M,H:N,N:we,U:Te,B:Ce,F:Ee},Oe=ce.litHtmlPolyfillSupport;Oe?.(A,M),(ce.litHtmlVersions??=[]).push(`3.3.3`);var ke=(e,t,n)=>{let r=n?.renderBefore??t,i=r._$litPart$;if(i===void 0){let e=n?.renderBefore??null;r._$litPart$=i=new M(t.insertBefore(b(),e),e,void 0,n??{})}return i._$AI(e),i},P=globalThis,F=class extends h{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=ke(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return D}};F._$litElement$=!0,F.finalized=!0,P.litElementHydrateSupport?.({LitElement:F});var Ae=P.litElementPolyfillSupport;Ae?.({LitElement:F}),(P.litElementVersions??=[]).push(`4.2.2`);var I=e=>(t,n)=>{n===void 0?customElements.define(e,t):n.addInitializer(()=>{customElements.define(e,t)})},je={attribute:!0,type:String,converter:m,reflect:!1,hasChanged:oe},Me=(e=je,t,n)=>{let{kind:r,metadata:i}=n,a=globalThis.litPropertyMetadata.get(i);if(a===void 0&&globalThis.litPropertyMetadata.set(i,a=/* @__PURE__ */ new Map),r===`setter`&&((e=Object.create(e)).wrapped=!0),a.set(n.name,e),r===`accessor`){let{name:r}=n;return{set(n){let i=t.get.call(this);t.set.call(this,n),this.requestUpdate(r,i,e,!0,n)},init(t){return t!==void 0&&this.C(r,void 0,e,t),t}}}if(r===`setter`){let{name:r}=n;return function(n){let i=this[r];t.call(this,n),this.requestUpdate(r,i,e,!0,n)}}throw Error(`Unsupported decorator location: `+r)};function L(e){return(t,n)=>typeof n==`object`?Me(e,t,n):((e,t,n)=>{let r=t.hasOwnProperty(n);return t.constructor.createProperty(n,e),r?Object.getOwnPropertyDescriptor(t,n):void 0})(e,t,n)}function R(e){return L({...e,state:!0,attribute:!1})}var Ne=1e4;async function Pe(){await customElements.whenDefined(`partial-panel-resolver`);let e=document.createElement(`partial-panel-resolver`);e.hass={panels:[{url_path:`tmp`,component_name:`config`}]},e._updateRoutes(),await e.routerOptions.routes.tmp.load(),customElements.get(`ha-card`)||await customElements.whenDefined(`ha-card`)}var Fe=async()=>{if(!customElements.get(`ha-card`))try{await Promise.race([Pe(),new Promise((e,t)=>setTimeout(()=>t(/* @__PURE__ */ Error(`Timeout waiting for HA elements (${Ne}ms)`)),Ne))])}catch(e){console.warn(`[kubernetes-panel] Failed to load HA elements:`,e)}},{I:Ie}=De,Le=e=>e.strings===void 0,Re={ATTRIBUTE:1,CHILD:2,PROPERTY:3,BOOLEAN_ATTRIBUTE:4,EVENT:5,ELEMENT:6},ze=e=>(...t)=>({_$litDirective$:e,values:t}),Be=class{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,n){this._$Ct=e,this._$AM=t,this._$Ci=n}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}},z=(e,t)=>{let n=e._$AN;if(n===void 0)return!1;for(let e of n)e._$AO?.(t,!1),z(e,t);return!0},B=e=>{let t,n;do{if((t=e._$AM)===void 0)break;n=t._$AN,n.delete(e),e=t}while(n?.size===0)},Ve=e=>{for(let t;t=e._$AM;e=t){let n=t._$AN;if(n===void 0)t._$AN=n=/* @__PURE__ */ new Set;else if(n.has(e))break;n.add(e),We(t)}};function He(e){this._$AN===void 0?this._$AM=e:(B(this),this._$AM=e,Ve(this))}function Ue(e,t=!1,n=0){let r=this._$AH,i=this._$AN;if(i!==void 0&&i.size!==0){if(t){if(Array.isArray(r))for(let e=n;e<r.length;e++)z(r[e],!1),B(r[e]);else r!=null&&(z(r,!1),B(r))}else z(this,e)}}var We=e=>{e.type==Re.CHILD&&(e._$AP??=Ue,e._$AQ??=He)},Ge=class extends Be{constructor(){super(...arguments),this._$AN=void 0}_$AT(e,t,n){super._$AT(e,t,n),Ve(this),this.isConnected=e._$AU}_$AO(e,t=!0){e!==this.isConnected&&(this.isConnected=e,e?this.reconnected?.():this.disconnected?.()),t&&(z(this,e),B(this))}setValue(e){if(Le(this._$Ct))this._$Ct._$AI(e,this);else{let t=[...this._$Ct._$AH];t[this._$Ci]=e,this._$Ct._$AI(t,this,0)}}disconnected(){}reconnected(){}},Ke=/* @__PURE__ */ new WeakMap,qe=ze(class extends Ge{render(e){return O}update(e,[t]){let n=t!==this.G;return n&&this.rt(void 0),(n||this.lt!==this.ct)&&(this.G=t,this.ht=e.options?.host,this.rt(this.ct=e.element)),O}rt(e){if(this.G!==void 0){if(this.isConnected||(e=void 0),typeof this.G==`function`){let t=this.ht??globalThis,n=Ke.get(t);n===void 0&&(n=/* @__PURE__ */ new WeakMap,Ke.set(t,n)),n.get(this.G)!==void 0&&this.G.call(this.ht,void 0),n.set(this.G,e),e!==void 0&&this.G.call(this.ht,e)}else this.G.value=e}}get lt(){return typeof this.G==`function`?Ke.get(this.ht??globalThis)?.get(this.G):this.G?.value}disconnected(){this.lt===this.ct&&this.rt(void 0)}reconnected(){this.rt(this.ct)}}),Je={memory_pressure:`Memory Pressure`,disk_pressure:`Disk Pressure`,pid_pressure:`PID Pressure`,network_unavailable:`Network Unavailable`};function V(e){if(!e||e===`N/A`)return`N/A`;let t=new Date(e).getTime(),n=Math.max(0,Math.floor((Date.now()-t)/1e3));return n<60?`${n}s`:n<3600?`${Math.floor(n/60)}m`:n<86400?`${Math.floor(n/3600)}h`:`${Math.floor(n/86400)}d`}function Ye(e){if(!e)return`Never`;let t=Date.now()/1e3,n=Math.max(0,Math.floor(t-e));return n<60?`${n}s ago`:n<3600?`${Math.floor(n/60)}m ago`:n<86400?`${Math.floor(n/3600)}h ago`:`${Math.floor(n/86400)}d ago`}function Xe(e,t){let n=new Set(e);return n.has(t)?n.delete(t):n.add(t),n}function H(e,t){return typeof e==`object`&&e&&`message`in e&&typeof e.message==`string`&&e.message?e.message:t}function U(e,t,n,r){var i=arguments.length,a=i<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,n):r,o;if(typeof Reflect==`object`&&typeof Reflect.decorate==`function`)a=Reflect.decorate(e,t,n,r);else for(var s=e.length-1;s>=0;s--)(o=e[s])&&(a=(i<3?o(a):i>3?o(t,n,a):o(t,n))||a);return i>3&&a&&Object.defineProperty(t,n,a),a}var W=class extends F{constructor(...e){super(...e),this._data=null,this._loading=!0,this._error=null,this.pollMs=6e4,this.subscribe=!0,this.loadErrorFallback=`Failed to load data`,this.emptyMessage=`No Kubernetes clusters configured.`,this._loadingInFlight=!1,this._boundVisibilityHandler=this._handleVisibilityChange.bind(this)}hasData(){return this._data!==null}firstUpdated(e){this._loadData(),this.pollMs>0&&(this._startPolling(),document.addEventListener(`visibilitychange`,this._boundVisibilityHandler)),this.subscribe&&this._subscribeUpdates()}disconnectedCallback(){super.disconnectedCallback(),this._stopPolling(),document.removeEventListener(`visibilitychange`,this._boundVisibilityHandler),this._unsubUpdates?.().catch(()=>{}),this._unsubUpdates=void 0,this._updateDebounce&&=(clearTimeout(this._updateDebounce),void 0),this._reloadTimer&&=(clearTimeout(this._reloadTimer),void 0)}_handleVisibilityChange(){document.hidden?this._stopPolling():(this._loadData(),this._startPolling())}_startPolling(){this._refreshInterval||=setInterval(()=>this._loadData(),this.pollMs)}_stopPolling(){this._refreshInterval&&=(clearInterval(this._refreshInterval),void 0)}async _subscribeUpdates(){try{let e=await this.hass.connection.subscribeMessage(()=>this._scheduleLoad(),{type:`kubernetes/subscribe_updates`});if(!this.isConnected){e().catch(()=>{});return}this._unsubUpdates=e}catch{}}_scheduleLoad(){document.hidden||(this._updateDebounce||=setTimeout(()=>{this._updateDebounce=void 0,this._loadData()},1e3))}_scheduleReload(e){this._reloadTimer&&clearTimeout(this._reloadTimer),this._reloadTimer=setTimeout(()=>{this._reloadTimer=void 0,this._loadData()},e)}async _loadData(){if(!this._loadingInFlight){this._loadingInFlight=!0,this.hasData()||(this._loading=!0),this._error=null;try{await this.fetchData()}catch(e){this._error=H(e,this.loadErrorFallback)}finally{this._loading=!1,this._loadingInFlight=!1}}}_onOverlayKeydown(e){return t=>{t.key===`Escape`&&e!==O&&e()}}_autofocusOverlay(){return qe(e=>{let t=e;t&&!t.matches(`:focus-within`)&&t.focus({preventScroll:!0})})}renderState(e){return this._loading?E`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `:this._error?E`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `:e?E`<div class="empty">${this.emptyMessage}</div>`:O}};U([L({attribute:!1})],W.prototype,`hass`,void 0),U([R()],W.prototype,`_data`,void 0),U([R()],W.prototype,`_loading`,void 0),U([R()],W.prototype,`_error`,void 0);var G=o`
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
`,K=o`
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
`,q=o`
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

  .badge-healthy,
  .badge-ready,
  .badge-running,
  .badge-complete,
  .badge-tls,
  .badge-type-loadbalancer {
    background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
    color: var(--success-color, #4caf50);
  }

  .badge-unhealthy,
  .badge-not-ready,
  .badge-failed {
    background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
    color: var(--error-color, #f44336);
  }

  .badge-unschedulable,
  .badge-condition,
  .badge-pending,
  .badge-degraded,
  .badge-plain,
  .badge-type-externalname {
    background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
    color: var(--warning-color, #ff9800);
  }

  .badge-unknown,
  .badge-stopped,
  .badge-suspended {
    background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
    color: var(--disabled-color, #9e9e9e);
  }

  .badge-succeeded,
  .badge-active {
    background: rgba(var(--rgb-info-color, 33, 150, 243), 0.15);
    color: var(--info-color, #2196f3);
  }
`,Ze=o`
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

  .confirm-dialog .confirm-ref {
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
`,Qe=o`
  .table-wrapper {
    overflow-x: auto;
  }
`,$e={pods:`mdi:cube-outline`,nodes:`mdi:server`,deployments:`mdi:rocket-launch`,statefulsets:`mdi:database`,daemonsets:`mdi:lan`,cronjobs:`mdi:clock-outline`,jobs:`mdi:briefcase-check`,ingresses:`mdi:earth`,services:`mdi:swap-horizontal`},et={pods:`Pods`,nodes:`Nodes`,deployments:`Deployments`,statefulsets:`StatefulSets`,daemonsets:`DaemonSets`,cronjobs:`CronJobs`,jobs:`Jobs`,ingresses:`Ingresses`,services:`Services`},tt=class extends W{constructor(...e){super(...e),this._expandedNamespaces=/* @__PURE__ */ new Set,this.loadErrorFallback=`Failed to load cluster data`}async fetchData(){let e=await this.hass.callWS({type:`kubernetes/cluster/overview`});this._data=e}_toggleNamespaces(e){this._expandedNamespaces=Xe(this._expandedNamespaces,e)}static{this.styles=[G,q,o`
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
    `]}render(){let e=this.renderState(!this._data?.clusters.length);return e===O?E` ${this._data.clusters.map(e=>this._renderCluster(e))} `:e}_renderCluster(e){let t=e.alerts.nodes_with_pressure.length+e.alerts.degraded_workloads.length+e.alerts.failed_pods.length;return E`
      <div class="cluster-section">
        <div class="cluster-header">
          <span class="cluster-name">${e.cluster_name}</span>
          ${this._renderHealthBadge(e.healthy)}
        </div>

        <div class="meta-row">
          <div class="meta-item">
            <ha-icon icon="mdi:update"></ha-icon>
            <span>Updated ${Ye(e.last_update)}</span>
          </div>
          <button class="refresh-btn" @click=${this._loadData} title="Refresh data">
            <ha-icon icon="mdi:refresh"></ha-icon>
          </button>
        </div>

        <div class="counts-grid">
          ${Object.entries(e.counts).map(([e,t])=>E`
              <ha-card class="count-card">
                <ha-icon icon=${$e[e]||`mdi:help`}></ha-icon>
                <div class="count-value">${t}</div>
                <div class="count-label">${et[e]||e}</div>
              </ha-card>
            `)}
        </div>

        <div class="alerts-section">
          <div class="alerts-header">
            <ha-icon icon="mdi:bell-outline"></ha-icon>
            <span>Alerts${t>0?` (${t})`:``}</span>
            <span class="alerts-info-icon">
              <ha-icon icon="mdi:information-outline"></ha-icon>
              <div class="alerts-tooltip">
                Alerts monitor your cluster for issues that may need attention: nodes
                experiencing memory, disk, or PID pressure; workloads with fewer ready
                replicas than desired; and pods in a failed state.
              </div>
            </span>
          </div>
          ${t>0?this._renderAlerts(e.alerts):E`
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

        ${this._renderNamespaceSection(e)}
      </div>
    `}_renderHealthBadge(e){return e===!0?E`<span class="badge badge-healthy">Healthy</span>`:e===!1?E`<span class="badge badge-unhealthy">Unhealthy</span>`:E`<span class="badge badge-unknown">Unknown</span>`}_renderNamespaceSection(e){let t=Object.entries(e.namespaces);if(t.length===0)return O;let n=this._expandedNamespaces.has(e.entry_id);return E`
      <div
        class="section-header"
        role="button"
        tabindex="0"
        @click=${()=>this._toggleNamespaces(e.entry_id)}
        @keydown=${t=>{(t.key===`Enter`||t.key===` `)&&(t.preventDefault(),this._toggleNamespaces(e.entry_id))}}
      >
        <ha-icon icon=${n?`mdi:chevron-down`:`mdi:chevron-right`}></ha-icon>
        <span>Namespaces (${t.length})</span>
      </div>
      ${n?this._renderNamespaceTable(t):O}
    `}_renderNamespaceTable(e){let t=[`pods`,`deployments`,`statefulsets`,`daemonsets`,`cronjobs`,`jobs`];return E`
      <table class="ns-table">
        <thead>
          <tr>
            <th>Namespace</th>
            ${t.map(e=>E`<th>${et[e]||e}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${e.sort(([e],[t])=>e.localeCompare(t)).map(([e,n])=>E`
                <tr>
                  <td>${e}</td>
                  ${t.map(e=>E`<td>${n[e]||0}</td>`)}
                </tr>
              `)}
        </tbody>
      </table>
    `}_renderAlerts(e){return E`
      ${e.nodes_with_pressure.map(e=>E`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:server-network-off"></ha-icon>
            <div>
              <div class="alert-title">Node: ${e.name}</div>
              <div class="alert-detail">
                ${e.conditions.map(e=>Je[e]||e).join(`, `)}
              </div>
            </div>
          </div>
        `)}
      ${e.degraded_workloads.map(e=>E`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:alert"></ha-icon>
            <div>
              <div class="alert-title">${e.type}: ${e.namespace}/${e.name}</div>
              <div class="alert-detail">${e.ready}/${e.desired} replicas ready</div>
            </div>
          </div>
        `)}
      ${e.failed_pods.map(e=>E`
          <div class="alert-card alert-error">
            <ha-icon icon="mdi:alert-octagon"></ha-icon>
            <div>
              <div class="alert-title">Pod: ${e.namespace}/${e.name}</div>
              <div class="alert-detail">Phase: ${e.phase}</div>
            </div>
          </div>
        `)}
    `}};U([R()],tt.prototype,`_expandedNamespaces`,void 0),tt=U([I(`k8s-overview`)],tt);var nt=o`
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

  .action-btn.stop:hover,
  .action-btn.delete:hover {
    background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
    color: var(--error-color, #f44336);
  }

  .action-btn.start:hover,
  .action-btn.uncordon:hover {
    background: rgba(var(--rgb-success-color, 76, 175, 80), 0.1);
    color: var(--success-color, #4caf50);
  }

  .action-btn.restart:hover,
  .action-btn.suspend:hover,
  .action-btn.cordon:hover {
    background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.1);
    color: var(--warning-color, #ff9800);
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
`,J=class extends W{constructor(...e){super(...e),this._expandedNodes=/* @__PURE__ */ new Set,this._statusFilter=`all`,this._searchQuery=``,this._actionInProgress=/* @__PURE__ */ new Set,this._actionError=null,this.loadErrorFallback=`Failed to load nodes data`}async fetchData(){let e=await this.hass.callWS({type:`kubernetes/nodes/list`});this._data=e}_toggleNode(e){this._expandedNodes=Xe(this._expandedNodes,e)}_getConditions(e){let t=[];return e.memory_pressure&&t.push(`memory_pressure`),e.disk_pressure&&t.push(`disk_pressure`),e.pid_pressure&&t.push(`pid_pressure`),e.network_unavailable&&t.push(`network_unavailable`),t}_getFilteredNodes(e){let t=e;if(this._statusFilter!==`all`&&(t=t.filter(e=>this._statusFilter===`ready`?e.status===`Ready`:e.status!==`Ready`)),this._searchQuery){let e=this._searchQuery.toLowerCase();t=t.filter(t=>t.name.toLowerCase().includes(e)||t.internal_ip.toLowerCase().includes(e)||t.kubelet_version.toLowerCase().includes(e))}return t}async _setSchedulable(e,t,n){let r=`${e}_${t.name}`,i=new Set(this._actionInProgress);i.add(r),this._actionInProgress=i;try{await this.hass.callService(`kubernetes`,n?`uncordon_node`:`cordon_node`,{node_name:t.name,entry_id:e}),await this._loadData()}catch(e){let t=H(e,`Action failed`);this._actionError=`Action failed: ${t}`,console.error(`[k8s-nodes-table] Action failed:`,e)}finally{let e=new Set(this._actionInProgress);e.delete(r),this._actionInProgress=e}}static{this.styles=[nt,G,K,q,o`
      .cluster-section {
        margin-bottom: 24px;
      }

      .cluster-name {
        font-size: 20px;
        font-weight: 500;
        color: var(--primary-text-color);
        margin-bottom: 12px;
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
          grid-template-columns: 1fr auto auto;
          gap: 8px;
        }

        .node-ip,
        .node-resources,
        .node-age {
          display: none;
        }
      }
    `]}render(){let e=this.renderState(!this._data?.clusters.length);return e===O?E`
      ${this._actionError?E`
              <div class="action-error">
                <span>${this._actionError}</span>
                <button
                  class="dismiss-btn"
                  @click=${()=>{this._actionError=null}}
                  title="Dismiss"
                >
                  <ha-icon icon="mdi:close"></ha-icon>
                </button>
              </div>
            `:O}
      ${this._data.clusters.map(e=>this._renderCluster(e))}
    `:e}_renderCluster(e){let t=this._getFilteredNodes(e.nodes),n=e.nodes.filter(e=>e.status===`Ready`).length;return E`
      <div class="cluster-section">
        ${this._data.clusters.length>1?E`<div class="cluster-name">${e.cluster_name}</div>`:O}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search nodes..."
            .value=${this._searchQuery}
            @input=${e=>{this._searchQuery=e.target.value}}
          />
          ${[`all`,`ready`,`not-ready`].map(e=>E`
              <button
                class="filter-chip"
                ?active=${this._statusFilter===e}
                @click=${()=>{this._statusFilter=e}}
              >
                ${e===`all`?`All`:e===`ready`?`Ready`:`Not Ready`}
              </button>
            `)}
        </div>

        <div class="node-count">
          ${n}/${e.nodes.length} nodes ready
          ${t.length===e.nodes.length?O:E` &middot; showing ${t.length}`}
        </div>

        ${t.length===0?E`<div class="empty">No nodes match your filters.</div>`:t.map(t=>this._renderNode(e.entry_id,t))}
      </div>
    `}_renderNode(e,t){let n=`${e}_${t.name}`,r=this._expandedNodes.has(n),i=this._getConditions(t),a=t.cpu_usage_millicores!=null&&t.memory_usage_mib!=null,o=t.cpu_cores*1e3,s=a?Math.round(t.cpu_usage_millicores/o*100):0,c=a?t.memory_usage_mib/1024:0,l=a?Math.round(c/t.memory_capacity_gib*100):0;return E`
      <ha-card class="node-card">
        <div
          class="node-row"
          role="button"
          tabindex="0"
          @click=${()=>this._toggleNode(n)}
          @keydown=${e=>{(e.key===`Enter`||e.key===` `)&&(e.preventDefault(),this._toggleNode(n))}}
        >
          <div class="node-name">
            <ha-icon
              icon=${r?`mdi:chevron-down`:`mdi:chevron-right`}
            ></ha-icon>
            ${t.name}
            ${t.schedulable?O:E`<span class="badge badge-unschedulable">Unschedulable</span>`}
            ${i.length>0?E`<span class="badge badge-condition"
                    >${i.length}
                    condition${i.length>1?`s`:``}</span
                  >`:O}
          </div>
          <span
            class="badge ${t.status===`Ready`?`badge-ready`:`badge-not-ready`}"
          >
            ${t.status}
          </span>
          <span class="node-ip">${t.internal_ip}</span>
          <div class="node-resources">
            ${a?E`
                    <div class="resource-bar-container" title="CPU usage">
                      <span class="resource-label">CPU</span>
                      <div class="resource-bar">
                        <div
                          class="resource-bar-fill ${s>80?`bar-warn`:``}"
                          style="width: ${Math.min(s,100)}%"
                        ></div>
                      </div>
                      <span>${s}%</span>
                    </div>
                    <div class="resource-bar-container" title="Memory usage">
                      <span class="resource-label">MEM</span>
                      <div class="resource-bar">
                        <div
                          class="resource-bar-fill ${l>80?`bar-warn`:``}"
                          style="width: ${Math.min(l,100)}%"
                        ></div>
                      </div>
                      <span>${l}%</span>
                    </div>
                  `:E`<span
                    >${t.cpu_cores} CPU &middot; ${t.memory_capacity_gib}
                    GiB</span
                  >`}
          </div>
          <span class="node-age">${V(t.creation_timestamp)}</span>
          <button
            class="action-btn ${t.schedulable?`cordon`:`uncordon`}"
            title=${t.schedulable?`Cordon (stop scheduling new pods)`:`Uncordon`}
            ?disabled=${this._actionInProgress.has(n)}
            @click=${n=>{n.stopPropagation(),this._setSchedulable(e,t,!t.schedulable)}}
          >
            <ha-icon
              icon=${t.schedulable?`mdi:server-off`:`mdi:server`}
            ></ha-icon>
          </button>
        </div>
        ${r?this._renderNodeDetails(t,i):O}
      </ha-card>
    `}_renderNodeDetails(e,t){let n=e.cpu_usage_millicores!=null&&e.memory_usage_mib!=null,r=n?Math.round(e.memory_usage_mib/1024*100)/100:null;return E`
      <div class="node-details">
        <div class="details-grid">
          <div class="detail-item">
            <span class="detail-label">Internal IP</span>
            <span class="detail-value mono">${e.internal_ip}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">External IP</span>
            <span class="detail-value mono">${e.external_ip}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">CPU Cores</span>
            <span class="detail-value">${e.cpu_cores}</span>
          </div>
          ${n?E`
                  <div class="detail-item">
                    <span class="detail-label">CPU Usage</span>
                    <span class="detail-value"
                      >${e.cpu_usage_millicores}m / ${e.cpu_cores*1e3}m</span
                    >
                  </div>
                `:O}
          <div class="detail-item">
            <span class="detail-label">Memory Capacity</span>
            <span class="detail-value">${e.memory_capacity_gib} GiB</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Memory Allocatable</span>
            <span class="detail-value">${e.memory_allocatable_gib} GiB</span>
          </div>
          ${n?E`
                  <div class="detail-item">
                    <span class="detail-label">Memory Usage</span>
                    <span class="detail-value"
                      >${r} / ${e.memory_capacity_gib} GiB</span
                    >
                  </div>
                `:O}
          <div class="detail-item">
            <span class="detail-label">OS Image</span>
            <span class="detail-value">${e.os_image}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Kernel</span>
            <span class="detail-value mono">${e.kernel_version}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Container Runtime</span>
            <span class="detail-value">${e.container_runtime}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Kubelet Version</span>
            <span class="detail-value mono">${e.kubelet_version}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Schedulable</span>
            <span class="detail-value">${e.schedulable?`Yes`:`No`}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Created</span>
            <span class="detail-value">${e.creation_timestamp}</span>
          </div>
        </div>
        ${t.length>0?E`
                <div class="conditions-row">
                  ${t.map(e=>E`
                      <span class="badge badge-condition">
                        ${Je[e]||e}
                      </span>
                    `)}
                </div>
              `:O}
      </div>
    `}};U([R()],J.prototype,`_expandedNodes`,void 0),U([R()],J.prototype,`_statusFilter`,void 0),U([R()],J.prototype,`_searchQuery`,void 0),U([R()],J.prototype,`_actionInProgress`,void 0),U([R()],J.prototype,`_actionError`,void 0),J=U([I(`k8s-nodes-table`)],J);var rt={Running:`badge-running`,Succeeded:`badge-succeeded`,Pending:`badge-pending`,Failed:`badge-failed`,Unknown:`badge-unknown`},it=[{key:`ready`,label:`Ready`},{key:`restarts`,label:`Restarts`},{key:`node`,label:`Node`},{key:`ip`,label:`IP`},{key:`owner`,label:`Owner`},{key:`age`,label:`Age`}],at=new Set(it.map(e=>e.key)),ot=`k8s-pods-columns`;function st(){try{let e=localStorage.getItem(ot);if(e){let t=JSON.parse(e).filter(e=>at.has(e));if(t.length)return new Set(t)}}catch{}return new Set(at)}function ct(e){try{localStorage.setItem(ot,JSON.stringify([...e]))}catch{}}var Y=class extends W{constructor(...e){super(...e),this._searchQuery=``,this._phaseFilter=`all`,this._namespaceFilter=`all`,this._sortField=`name`,this._sortAsc=!0,this._deleteConfirm=null,this._deleting=!1,this._visibleColumns=st(),this._columnMenuOpen=!1,this._actionError=null,this.loadErrorFallback=`Failed to load pods data`,this._boundCloseMenu=()=>{this._columnMenuOpen=!1}}firstUpdated(e){super.firstUpdated(e),document.addEventListener(`click`,this._boundCloseMenu)}disconnectedCallback(){super.disconnectedCallback(),document.removeEventListener(`click`,this._boundCloseMenu)}async fetchData(){let e=await this.hass.callWS({type:`kubernetes/pods/list`});this._data=e}_getNamespaces(e){return[...new Set(e.map(e=>e.namespace))].sort()}_getFilteredPods(e){let t=e;if(this._phaseFilter!==`all`&&(t=t.filter(e=>e.phase===this._phaseFilter)),this._namespaceFilter!==`all`&&(t=t.filter(e=>e.namespace===this._namespaceFilter)),this._searchQuery){let e=this._searchQuery.toLowerCase();t=t.filter(t=>t.name.toLowerCase().includes(e)||t.namespace.toLowerCase().includes(e)||t.node_name.toLowerCase().includes(e)||t.owner_name.toLowerCase().includes(e))}return t=[...t].sort((e,t)=>{let n,r,i=this._sortField;i===`restarts`?(n=e.restart_count,r=t.restart_count):i===`age`?(n=e.creation_timestamp||``,r=t.creation_timestamp||``):(n=e[i]||``,r=t[i]||``);let a=n<r?-1:+(n>r);return this._sortAsc?a:-a}),t}_handleSort(e){this._sortField===e?this._sortAsc=!this._sortAsc:(this._sortField=e,this._sortAsc=!0)}_handleSortKeydown(e,t){(e.key===`Enter`||e.key===` `)&&(e.preventDefault(),this._handleSort(t))}_requestDelete(e,t){this._deleteConfirm={entry_id:e,pod_name:t.name,namespace:t.namespace}}_cancelDelete(){this._deleteConfirm=null}async _confirmDelete(){if(this._deleteConfirm){this._deleting=!0;try{await this.hass.callWS({type:`kubernetes/pods/delete`,entry_id:this._deleteConfirm.entry_id,pod_name:this._deleteConfirm.pod_name,namespace:this._deleteConfirm.namespace}),this._deleteConfirm=null,await this._loadData()}catch(e){this._actionError=H(e,`Failed to delete pod`),this._deleteConfirm=null}finally{this._deleting=!1}}}_sortIcon(e){return this._sortField===e?this._sortAsc?`mdi:arrow-up`:`mdi:arrow-down`:``}static{this.styles=[nt,G,K,q,Ze,Qe,o`
      .cluster-section {
        margin-bottom: 24px;
      }

      .cluster-name {
        font-size: 20px;
        font-weight: 500;
        color: var(--primary-text-color);
        margin-bottom: 12px;
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

      .column-menu-wrapper {
        position: relative;
        margin-left: auto;
      }

      .column-toggle-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 6px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        background: transparent;
        color: var(--secondary-text-color);
        cursor: pointer;
        --mdc-icon-size: 18px;
      }

      .column-toggle-btn:hover {
        color: var(--primary-color);
        border-color: var(--primary-color);
      }

      .column-menu {
        position: absolute;
        top: 100%;
        right: 0;
        margin-top: 4px;
        background: var(--card-background-color, #fff);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 8px 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10;
        min-width: 140px;
      }

      .column-option {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        font-size: 13px;
        color: var(--primary-text-color);
        cursor: pointer;
        white-space: nowrap;
      }

      .column-option:hover {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.06);
      }

      .column-option input[type="checkbox"] {
        accent-color: var(--primary-color);
      }
    `]}render(){let e=this.renderState(!this._data?.clusters.length);return e===O?E`
      ${this._actionError?E`
              <div class="action-error">
                <span>${this._actionError}</span>
                <button
                  class="dismiss-btn"
                  @click=${()=>{this._actionError=null}}
                  title="Dismiss"
                >
                  <ha-icon icon="mdi:close"></ha-icon>
                </button>
              </div>
            `:O}
      ${this._data.clusters.map(e=>this._renderCluster(e))}
      ${this._deleteConfirm?this._renderDeleteDialog():O}
    `:e}_renderCluster(e){let t=this._getFilteredPods(e.pods),n=this._getNamespaces(e.pods),r=[...new Set(e.pods.map(e=>e.phase))].sort();return E`
      <div class="cluster-section">
        ${this._data.clusters.length>1?E`<div class="cluster-name">${e.cluster_name}</div>`:O}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search pods..."
            .value=${this._searchQuery}
            @input=${e=>{this._searchQuery=e.target.value}}
          />

          <select
            class="filter-select"
            .value=${this._namespaceFilter}
            @change=${e=>{this._namespaceFilter=e.target.value}}
          >
            <option value="all">All namespaces</option>
            ${n.map(e=>E`<option value=${e}>${e}</option>`)}
          </select>

          <button
            class="filter-chip"
            ?active=${this._phaseFilter===`all`}
            @click=${()=>{this._phaseFilter=`all`}}
          >
            All
          </button>
          ${r.map(e=>E`
              <button
                class="filter-chip"
                ?active=${this._phaseFilter===e}
                @click=${()=>{this._phaseFilter=e}}
              >
                ${e}
              </button>
            `)}
          ${this._renderColumnMenu()}
        </div>

        <div class="pod-count">${t.length}/${e.pods.length} pods</div>

        ${t.length===0?E`<div class="empty">No pods match your filters.</div>`:E`
                <ha-card>
                  <div class="table-wrapper">
                    <table class="pods-table">
                      <thead>
                        <tr>
                          <th
                            role="button"
                            tabindex="0"
                            @click=${()=>this._handleSort(`namespace`)}
                            @keydown=${e=>this._handleSortKeydown(e,`namespace`)}
                          >
                            Namespace
                            ${this._sortIcon(`namespace`)?E`<ha-icon
                                    icon=${this._sortIcon(`namespace`)}
                                  ></ha-icon>`:O}
                          </th>
                          <th
                            role="button"
                            tabindex="0"
                            @click=${()=>this._handleSort(`name`)}
                            @keydown=${e=>this._handleSortKeydown(e,`name`)}
                          >
                            Name
                            ${this._sortIcon(`name`)?E`<ha-icon
                                    icon=${this._sortIcon(`name`)}
                                  ></ha-icon>`:O}
                          </th>
                          <th
                            role="button"
                            tabindex="0"
                            @click=${()=>this._handleSort(`phase`)}
                            @keydown=${e=>this._handleSortKeydown(e,`phase`)}
                          >
                            Phase
                            ${this._sortIcon(`phase`)?E`<ha-icon
                                    icon=${this._sortIcon(`phase`)}
                                  ></ha-icon>`:O}
                          </th>
                          ${this._colVisible(`ready`)?E`<th>Ready</th>`:O}
                          ${this._colVisible(`restarts`)?E`<th
                                  role="button"
                                  tabindex="0"
                                  @click=${()=>this._handleSort(`restarts`)}
                                  @keydown=${e=>this._handleSortKeydown(e,`restarts`)}
                                >
                                  Restarts
                                  ${this._sortIcon(`restarts`)?E`<ha-icon icon=${this._sortIcon(`restarts`)}></ha-icon>`:O}
                                </th>`:O}
                          ${this._colVisible(`node`)?E`<th
                                  role="button"
                                  tabindex="0"
                                  @click=${()=>this._handleSort(`node_name`)}
                                  @keydown=${e=>this._handleSortKeydown(e,`node_name`)}
                                >
                                  Node
                                  ${this._sortIcon(`node_name`)?E`<ha-icon icon=${this._sortIcon(`node_name`)}></ha-icon>`:O}
                                </th>`:O}
                          ${this._colVisible(`ip`)?E`<th>IP</th>`:O}
                          ${this._colVisible(`owner`)?E`<th>Owner</th>`:O}
                          ${this._colVisible(`age`)?E`<th
                                  role="button"
                                  tabindex="0"
                                  @click=${()=>this._handleSort(`age`)}
                                  @keydown=${e=>this._handleSortKeydown(e,`age`)}
                                >
                                  Age
                                  ${this._sortIcon(`age`)?E`<ha-icon icon=${this._sortIcon(`age`)}></ha-icon>`:O}
                                </th>`:O}
                          <th class="col-actions"></th>
                        </tr>
                      </thead>
                      <tbody>
                        ${t.map(t=>this._renderPodRow(e.entry_id,t))}
                      </tbody>
                    </table>
                  </div>
                </ha-card>
              `}
      </div>
    `}_colVisible(e){return this._visibleColumns.has(e)}_toggleColumn(e){let t=new Set(this._visibleColumns);t.has(e)?t.delete(e):t.add(e),this._visibleColumns=t,ct(t)}_renderColumnMenu(){return E`
      <div class="column-menu-wrapper">
        <button
          class="column-toggle-btn"
          title="Toggle columns"
          @click=${e=>{e.stopPropagation(),this._columnMenuOpen=!this._columnMenuOpen}}
        >
          <ha-icon icon="mdi:table-column"></ha-icon>
        </button>
        ${this._columnMenuOpen?E`
                <div class="column-menu" @click=${e=>e.stopPropagation()}>
                  ${it.map(e=>E`
                      <label class="column-option">
                        <input
                          type="checkbox"
                          .checked=${this._visibleColumns.has(e.key)}
                          @change=${()=>this._toggleColumn(e.key)}
                        />
                        ${e.label}
                      </label>
                    `)}
                </div>
              `:O}
      </div>
    `}_renderPodRow(e,t){let n=rt[t.phase]||`badge-unknown`;return E`
      <tr>
        <td>${t.namespace}</td>
        <td class="pod-name">${t.name}</td>
        <td><span class="badge ${n}">${t.phase}</span></td>
        ${this._colVisible(`ready`)?E`<td>${t.ready_containers}/${t.total_containers}</td>`:O}
        ${this._colVisible(`restarts`)?E`<td class=${t.restart_count>5?`restart-warn`:``}>${t.restart_count}</td>`:O}
        ${this._colVisible(`node`)?E`<td>${t.node_name}</td>`:O}
        ${this._colVisible(`ip`)?E`<td class="mono">${t.pod_ip}</td>`:O}
        ${this._colVisible(`owner`)?E`<td>${t.owner_kind===`N/A`?E`<span class="owner-info">-</span>`:E`<span class="owner-info">${t.owner_kind}/${t.owner_name}</span>`}</td>`:O}
        ${this._colVisible(`age`)?E`<td>${V(t.creation_timestamp)}</td>`:O}
        <td>
          <button
            class="delete-btn"
            title="Delete pod"
            @click=${()=>this._requestDelete(e,t)}
          >
            <ha-icon icon="mdi:delete-outline"></ha-icon>
          </button>
        </td>
      </tr>
    `}_renderDeleteDialog(){let e=this._deleteConfirm;return E`
      <div
        class="confirm-overlay"
        tabindex="-1"
        ${this._autofocusOverlay()}
        @click=${this._deleting?O:this._cancelDelete}
        @keydown=${this._onOverlayKeydown(this._deleting?O:this._cancelDelete)}
      >
        <div class="confirm-dialog" @click=${e=>e.stopPropagation()}>
          <h3>Delete Pod</h3>
          <p>
            Are you sure you want to delete
            <span class="confirm-ref">${e.namespace}/${e.pod_name}</span>?
            This action cannot be undone.
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
              ${this._deleting?`Deleting...`:`Delete`}
            </button>
          </div>
        </div>
      </div>
    `}};U([R()],Y.prototype,`_searchQuery`,void 0),U([R()],Y.prototype,`_phaseFilter`,void 0),U([R()],Y.prototype,`_namespaceFilter`,void 0),U([R()],Y.prototype,`_sortField`,void 0),U([R()],Y.prototype,`_sortAsc`,void 0),U([R()],Y.prototype,`_deleteConfirm`,void 0),U([R()],Y.prototype,`_deleting`,void 0),U([R()],Y.prototype,`_visibleColumns`,void 0),U([R()],Y.prototype,`_columnMenuOpen`,void 0),U([R()],Y.prototype,`_actionError`,void 0),Y=U([I(`k8s-pods-table`)],Y);var lt=[`Ingress`,`LoadBalancer`,`NodePort`,`ClusterIP`,`ExternalName`],X=class extends W{constructor(...e){super(...e),this._services=null,this._ingressError=null,this._servicesError=null,this._searchQuery=``,this._typeFilter=`all`,this.loadErrorFallback=`Failed to load network data`}hasData(){return this._data!==null||this._services!==null}async fetchData(){let[e,t]=await Promise.allSettled([this.hass.callWS({type:`kubernetes/ingresses/list`}),this.hass.callWS({type:`kubernetes/services/list`})]);e.status===`fulfilled`?(this._data=e.value,this._ingressError=null):this._ingressError=H(e.reason,`Failed to load ingress data`),t.status===`fulfilled`?(this._services=t.value,this._servicesError=null):this._servicesError=H(t.reason,`Failed to load service data`)}_getFilteredIngresses(e){if(!this._searchQuery)return e;let t=this._searchQuery.toLowerCase();return e.filter(e=>e.name.toLowerCase().includes(t)||e.namespace.toLowerCase().includes(t)||e.rules.some(e=>(e.host||``).toLowerCase().includes(t)))}_getFilteredServices(e){let t=e;if(this._typeFilter!==`all`&&(t=t.filter(e=>e.type===this._typeFilter)),this._searchQuery){let e=this._searchQuery.toLowerCase();t=t.filter(t=>t.name.toLowerCase().includes(e)||t.namespace.toLowerCase().includes(e)||t.external_ips.some(t=>t.toLowerCase().includes(e)))}return t}_services_of(e){return[...new Set(e.rules.map(e=>e.service_name))].filter(Boolean).join(`, `)}_hasTls(e){return e.tls_hosts.length>0||e.urls.some(e=>e.startsWith(`https://`))}_formatPort(e){let t=e.target_port!=null&&String(e.target_port)!==String(e.port)?`→${e.target_port}`:``,n=e.node_port?` (node ${e.node_port})`:``;return`${e.port}${t}/${e.protocol}${n}`}static{this.styles=[G,K,q,Qe,o`
      /* stateStyles' .empty is 64px padding; network uses .empty for five
       in-section messages, where that much padding doubles up. */
      .empty {
        padding: 32px 16px;
      }

      .inline-error {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 16px;
        margin-bottom: 16px;
        border-radius: 8px;
        background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
        color: var(--error-color, #f44336);
        font-size: 14px;
        --mdc-icon-size: 18px;
      }

      .section-title {
        font-size: 18px;
        font-weight: 500;
        color: var(--primary-text-color);
        margin: 24px 0 12px;
      }

      .section-title:first-of-type {
        margin-top: 0;
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

      .network-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
      }

      .network-table th {
        text-align: left;
        padding: 10px 12px;
        color: var(--secondary-text-color);
        font-weight: 500;
        border-bottom: 2px solid var(--divider-color);
        white-space: nowrap;
      }

      .network-table td {
        padding: 8px 12px;
        border-bottom: 1px solid var(--divider-color);
        vertical-align: middle;
      }

      .network-table tr:last-child td {
        border-bottom: none;
      }

      .network-table tr:hover td {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.04);
      }

      .mono {
        font-family: monospace;
        white-space: nowrap;
      }

      .url-link {
        display: block;
        color: var(--primary-color);
        text-decoration: none;
        white-space: nowrap;
      }

      .url-link:hover {
        text-decoration: underline;
      }

      .badge-type-nodeport {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
        color: var(--primary-color);
      }

      .badge-type-clusterip {
        background: rgba(var(--rgb-secondary-text-color, 114, 114, 114), 0.15);
        color: var(--secondary-text-color);
      }
    `]}render(){if(this._loading)return E`<div class="loading">
        <ha-circular-progress indeterminate></ha-circular-progress>
      </div>`;if(this._ingressError&&this._servicesError)return E`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._ingressError}</p>
            <button class="retry-btn" @click=${()=>this._loadData()}>Retry</button>
          </div>
        </ha-card>
      `;let e=this._data?.clusters??[],t=this._services?.clusters??[],n=e.some(e=>e.ingresses.length>0),r=t.some(e=>e.services.length>0);return!this._ingressError&&!this._servicesError&&!n&&!r?E`<div class="empty">No ingresses or services found.</div>`:E`
      <div class="filters">
        <input
          class="search-input"
          type="text"
          placeholder="Search ingresses and services…"
          .value=${this._searchQuery}
          @input=${e=>this._searchQuery=e.target.value}
        />
        <select
          class="filter-select"
          .value=${this._typeFilter}
          @change=${e=>{this._typeFilter=e.target.value}}
        >
          <option value="all">All types</option>
          ${lt.map(e=>E`<option value=${e}>${e}</option>`)}
        </select>
      </div>

      ${this._typeFilter===`all`||this._typeFilter===`Ingress`?E`
              <h2 class="section-title">Ingresses</h2>
              ${this._ingressError?this._renderInlineError(this._ingressError):n?e.map(e=>this._renderCluster(e)):E`<div class="empty">No ingresses found.</div>`}
            `:O}
      ${this._typeFilter===`Ingress`?O:E`
              <h2 class="section-title">Services</h2>
              ${this._servicesError?this._renderInlineError(this._servicesError):r?t.map(e=>this._renderServiceCluster(e)):E`<div class="empty">No services found.</div>`}
            `}
    `}_renderInlineError(e){return E`
      <div class="inline-error">
        <ha-icon icon="mdi:alert-circle"></ha-icon>
        <span>${e}</span>
      </div>
    `}_renderCluster(e){if(!e.ingresses.length)return O;let t=this._getFilteredIngresses(e.ingresses);return E`
      <div class="cluster-section">
        ${this._data.clusters.length>1?E`<div class="cluster-name">${e.cluster_name}</div>`:O}
        ${t.length===0?E`<div class="empty">No ingresses match your search.</div>`:this._renderTable(t)}
      </div>
    `}_renderTable(e){return E`
      <ha-card>
        <div class="table-wrapper">
          <table class="network-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Namespace</th>
                <th>Class</th>
                <th>URLs</th>
                <th>Service</th>
                <th>TLS</th>
                <th>Age</th>
              </tr>
            </thead>
            <tbody>
              ${e.map(e=>E`
                  <tr>
                    <td>${e.name}</td>
                    <td>${e.namespace}</td>
                    <td>${e.ingress_class||`—`}</td>
                    <td>${this._renderUrls(e.urls)}</td>
                    <td>${this._services_of(e)||`—`}</td>
                    <td>${this._renderTlsBadge(e)}</td>
                    <td>${V(e.creation_timestamp)}</td>
                  </tr>
                `)}
            </tbody>
          </table>
        </div>
      </ha-card>
    `}_renderServiceCluster(e){if(!e.services.length)return O;let t=this._getFilteredServices(e.services);return E`
      <div class="cluster-section">
        ${this._services.clusters.length>1?E`<div class="cluster-name">${e.cluster_name}</div>`:O}
        ${t.length===0?E`<div class="empty">No services match your filters.</div>`:this._renderServicesTable(t)}
      </div>
    `}_renderServicesTable(e){return E`
      <ha-card>
        <div class="table-wrapper">
          <table class="network-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Namespace</th>
                <th>Type</th>
                <th>Cluster IP</th>
                <th>External</th>
                <th>Ports</th>
                <th>Age</th>
              </tr>
            </thead>
            <tbody>
              ${e.map(e=>E`
                  <tr>
                    <td>${e.name}</td>
                    <td>${e.namespace}</td>
                    <td>
                      <span class="badge badge-type-${e.type.toLowerCase()}"
                        >${e.type}</span
                      >
                    </td>
                    <td class="mono">${e.cluster_ip||`—`}</td>
                    <td>${this._renderExternal(e)}</td>
                    <td class="mono">
                      ${e.ports.length?e.ports.map(e=>E`<div>${this._formatPort(e)}</div>`):`—`}
                    </td>
                    <td>${V(e.creation_timestamp)}</td>
                  </tr>
                `)}
            </tbody>
          </table>
        </div>
      </ha-card>
    `}_renderExternal(e){return e.urls.length?this._renderUrls(e.urls):e.external_ips.length?e.external_ips.map(e=>E`<div class="mono">${e}</div>`):`—`}_renderUrls(e){return e.length?e.map(e=>E`
        <a class="url-link" href=${e} target="_blank" rel="noopener noreferrer"
          >${e}</a
        >
      `):`—`}_renderTlsBadge(e){return this._hasTls(e)?E`<span class="badge badge-tls">TLS</span>`:E`<span class="badge badge-plain">HTTP</span>`}};U([R()],X.prototype,`_services`,void 0),U([R()],X.prototype,`_ingressError`,void 0),U([R()],X.prototype,`_servicesError`,void 0),U([R()],X.prototype,`_searchQuery`,void 0),U([R()],X.prototype,`_typeFilter`,void 0),X=U([I(`k8s-network`)],X);var Z={healthy:{badgeClass:`badge-healthy`,label:`Healthy`},degraded:{badgeClass:`badge-degraded`,label:`Degraded`},stopped:{badgeClass:`badge-stopped`,label:`Stopped`}},ut={deployment:{category:`deployments`,icon:`mdi:rocket-launch`,label:`Deployments`,emptyLabel:`deployments`,readyField:`available_replicas`,actionPrefix:`deploy_`},statefulset:{category:`statefulsets`,icon:`mdi:database`,label:`StatefulSets`,emptyLabel:`statefulsets`,readyField:`ready_replicas`,actionPrefix:`sts_`}},Q=class extends W{constructor(...e){super(...e),this._namespaceFilter=`all`,this._categoryFilter=`all`,this._statusFilter=`all`,this._searchQuery=``,this._actionInProgress=/* @__PURE__ */ new Set,this._actionError=null,this._jobDeleteConfirm=null,this._deletingJob=!1,this._collapsedCategories=/* @__PURE__ */ new Set,this._scaleTarget=null,this._scaleValue=0,this._scaling=!1,this.loadErrorFallback=`Failed to load workloads data`}async fetchData(){let e=await this.hass.callWS({type:`kubernetes/workloads/list`});this._data=e}_getNamespaces(e){let t=/* @__PURE__ */ new Set;for(let n of e.deployments)t.add(n.namespace);for(let n of e.statefulsets)t.add(n.namespace);for(let n of e.daemonsets)t.add(n.namespace);for(let n of e.cronjobs)t.add(n.namespace);for(let n of e.jobs)t.add(n.namespace);return[...t].sort()}_toggleCategory(e){let t=new Set(this._collapsedCategories);t.has(e)?t.delete(e):t.add(e),this._collapsedCategories=t}_handleCategoryKeydown(e,t){(e.key===`Enter`||e.key===` `)&&(e.preventDefault(),this._toggleCategory(t))}_matchesNamespace(e){return this._namespaceFilter===`all`||e===this._namespaceFilter}_matchesSearch(e){return!this._searchQuery||e.toLowerCase().includes(this._searchQuery.toLowerCase())}_formatAgo(e){let t=V(e);return t===`N/A`?t:`${t} ago`}async _runAction(e,t){let n=new Set(this._actionInProgress);n.add(e),this._actionInProgress=n;try{await t()}catch(e){let t=H(e,`Action failed`);this._actionError=`Action failed: ${t}`,console.error(`[k8s-workloads] Action failed:`,e)}finally{let t=new Set(this._actionInProgress);t.delete(e),this._actionInProgress=t}}_callService(e,t,n){return this._runAction(n,async()=>{await this.hass.callService(`kubernetes`,e,t),this._scheduleReload(2e3)})}_setCronJobSuspend(e,t,n,r){return this._runAction(r,async()=>{await this.hass.callWS({type:`kubernetes/cronjobs/suspend`,entry_id:e,cronjob_name:t.name,namespace:t.namespace,suspend:n}),await this._loadData()})}static{this.styles=[nt,G,K,q,Ze,o`
      .cluster-section {
        margin-bottom: 24px;
      }

      .cluster-name {
        font-size: 20px;
        font-weight: 500;
        color: var(--primary-text-color);
        margin-bottom: 12px;
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
        cursor: pointer;
        user-select: none;
      }

      .category-header:hover {
        color: var(--primary-color);
      }

      .category-chevron {
        --mdc-icon-size: 18px;
        transition: transform 0.2s;
        margin-left: auto;
      }

      .category-chevron[data-collapsed] {
        transform: rotate(-90deg);
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

      .replica-info {
        font-size: 13px;
        color: var(--secondary-text-color);
        white-space: nowrap;
      }

      .replica-info.scalable {
        cursor: pointer;
        border-radius: 4px;
        padding: 2px 6px;
        transition: background 0.2s;
      }

      .replica-info.scalable:hover,
      .replica-info.scalable:focus {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
        color: var(--primary-color);
        outline: none;
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

      .last-schedule {
        font-size: 12px;
        color: var(--secondary-text-color);
      }

      .scale-controls {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 20px;
      }

      .scale-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border: 1px solid var(--divider-color);
        background: transparent;
        color: var(--primary-text-color);
        cursor: pointer;
        --mdc-icon-size: 18px;
      }

      .scale-btn:hover:not(:disabled) {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
        border-color: var(--primary-color);
        color: var(--primary-color);
      }

      .scale-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .scale-input {
        width: 64px;
        text-align: center;
        font-size: 20px;
        font-weight: 500;
        padding: 6px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        background: var(--card-background-color, var(--primary-background-color));
        color: var(--primary-text-color);
      }

      .scale-input:focus {
        outline: none;
        border-color: var(--primary-color);
      }

      .confirm-actions .scale-action {
        background: var(--primary-color);
        color: var(--text-primary-color, #fff);
        border-color: var(--primary-color);
      }

      .confirm-actions .scale-action:hover:not(:disabled) {
        opacity: 0.9;
      }

      .confirm-actions .scale-action:disabled {
        opacity: 0.6;
        cursor: not-allowed;
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
    `]}render(){let e=this.renderState(!this._data?.clusters.length);return e===O?E`
      ${this._actionError?E`
              <div class="action-error">
                <span>${this._actionError}</span>
                <button
                  class="dismiss-btn"
                  @click=${()=>{this._actionError=null}}
                  title="Dismiss"
                >
                  <ha-icon icon="mdi:close"></ha-icon>
                </button>
              </div>
            `:O}
      ${this._data.clusters.map(e=>this._renderCluster(e))}
      ${this._jobDeleteConfirm?this._renderJobDeleteDialog():O}
      ${this._scaleTarget?this._renderScaleDialog():O}
    `:e}_renderCluster(e){let t=this._getNamespaces(e);return E`
      <div class="cluster-section">
        ${this._data.clusters.length>1?E`<div class="cluster-name">${e.cluster_name}</div>`:O}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search workloads..."
            .value=${this._searchQuery}
            @input=${e=>{this._searchQuery=e.target.value}}
          />

          <select
            class="filter-select"
            .value=${this._namespaceFilter}
            @change=${e=>{this._namespaceFilter=e.target.value}}
          >
            <option value="all">All namespaces</option>
            ${t.map(e=>E`<option value=${e}>${e}</option>`)}
          </select>

          <select
            class="filter-select"
            .value=${this._categoryFilter}
            @change=${e=>{this._categoryFilter=e.target.value}}
          >
            <option value="all">All types</option>
            <option value="deployments">Deployments</option>
            <option value="statefulsets">StatefulSets</option>
            <option value="daemonsets">DaemonSets</option>
            <option value="cronjobs">CronJobs</option>
            <option value="jobs">Jobs</option>
          </select>

          ${[`all`,`healthy`,`degraded`,`stopped`].map(e=>E`
              <button
                class="filter-chip"
                ?active=${this._statusFilter===e}
                @click=${()=>{this._statusFilter=e}}
              >
                ${e.charAt(0).toUpperCase()+e.slice(1)}
              </button>
            `)}
        </div>

        ${this._shouldShowCategory(`deployments`)?this._renderReplicaCategory(`deployment`,e.deployments,e.entry_id):O}
        ${this._shouldShowCategory(`statefulsets`)?this._renderReplicaCategory(`statefulset`,e.statefulsets,e.entry_id):O}
        ${this._shouldShowCategory(`daemonsets`)?this._renderDaemonSets(e.daemonsets,e.entry_id):O}
        ${this._shouldShowCategory(`cronjobs`)?this._renderCronJobs(e.cronjobs,e.entry_id):O}
        ${this._shouldShowCategory(`jobs`)?this._renderJobs(e.entry_id,e.jobs):O}
      </div>
    `}_shouldShowCategory(e){return this._categoryFilter===`all`||this._categoryFilter===e}_getReplicaStatus(e,t){return e.replicas===0?`stopped`:(e[ut[t].readyField]||0)<e.replicas?`degraded`:`healthy`}_getDaemonSetStatus(e){return e.desired_number_scheduled===0?`stopped`:(e.number_available||0)<e.desired_number_scheduled?`degraded`:`healthy`}_matchesStatusFilter(e){return this._statusFilter===`all`||this._statusFilter===e}_renderReplicaCategory(e,t,n){let r=ut[e],i=t.filter(t=>this._matchesNamespace(t.namespace)&&this._matchesSearch(t.name)&&this._matchesStatusFilter(this._getReplicaStatus(t,e)));return i.length===0&&this._categoryFilter!==`all`?E`<div class="empty">No ${r.emptyLabel} match your filters.</div>`:i.length===0?O:E`
      <div class="category-section">
        <div
          class="category-header"
          role="button"
          tabindex="0"
          @click=${()=>this._toggleCategory(r.category)}
          @keydown=${e=>this._handleCategoryKeydown(e,r.category)}
        >
          <ha-icon icon=${r.icon}></ha-icon>
          ${r.label}
          <span class="category-count">(${i.length})</span>
          <ha-icon
            class="category-chevron"
            icon="mdi:chevron-down"
            ?data-collapsed=${this._collapsedCategories.has(r.category)}
          ></ha-icon>
        </div>
        ${this._collapsedCategories.has(r.category)?O:i.map(t=>this._renderReplicaCard(e,t,n))}
      </div>
    `}_renderReplicaCard(e,t,n){let r=ut[e],i=this._getReplicaStatus(t,e),a=`${r.actionPrefix}${t.namespace}_${t.name}`,o=this._actionInProgress.has(a),s=t[r.readyField]??0;return E`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${t.name}</div>
            <div class="workload-namespace">${t.namespace}</div>
          </div>
          <span
            class="replica-info scalable"
            role="button"
            tabindex="0"
            title="Click to scale"
            @click=${()=>this._openScaleDialog(n,t.name,t.namespace,t.replicas)}
            @keydown=${e=>{(e.key===`Enter`||e.key===` `)&&(e.preventDefault(),this._openScaleDialog(n,t.name,t.namespace,t.replicas))}}
          >
            ${s}/${t.replicas} ready
          </span>
          <span class="badge ${Z[i].badgeClass}">
            ${Z[i].label}
          </span>
          <div class="workload-actions">
            ${t.replicas===0?E`
                    <button
                      class="action-btn start"
                      title="Start (scale to 1)"
                      ?disabled=${o}
                      @click=${()=>this._callService(`start_workload`,{workload_name:t.name,namespace:t.namespace,entry_id:n},a)}
                    >
                      <ha-icon icon="mdi:play"></ha-icon>
                    </button>
                  `:E`
                    <button
                      class="action-btn stop"
                      title="Stop (scale to 0)"
                      ?disabled=${o}
                      @click=${()=>this._callService(`stop_workload`,{workload_name:t.name,namespace:t.namespace,entry_id:n},a)}
                    >
                      <ha-icon icon="mdi:stop"></ha-icon>
                    </button>
                  `}
            <button
              class="action-btn restart"
              title="Rolling restart"
              ?disabled=${o}
              @click=${()=>this._callService(`restart_workload`,{workload_name:t.name,namespace:t.namespace,entry_id:n},a)}
            >
              <ha-icon icon="mdi:restart"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `}_renderDaemonSets(e,t){let n=e.filter(e=>this._matchesNamespace(e.namespace)&&this._matchesSearch(e.name)&&this._matchesStatusFilter(this._getDaemonSetStatus(e)));return n.length===0&&this._categoryFilter!==`all`?E`<div class="empty">No daemonsets match your filters.</div>`:n.length===0?O:E`
      <div class="category-section">
        <div
          class="category-header"
          role="button"
          tabindex="0"
          @click=${()=>this._toggleCategory(`daemonsets`)}
          @keydown=${e=>this._handleCategoryKeydown(e,`daemonsets`)}
        >
          <ha-icon icon="mdi:lan"></ha-icon>
          DaemonSets
          <span class="category-count">(${n.length})</span>
          <ha-icon
            class="category-chevron"
            icon="mdi:chevron-down"
            ?data-collapsed=${this._collapsedCategories.has(`daemonsets`)}
          ></ha-icon>
        </div>
        ${this._collapsedCategories.has(`daemonsets`)?O:n.map(e=>this._renderDaemonSetCard(e,t))}
      </div>
    `}_renderDaemonSetCard(e,t){let n=this._getDaemonSetStatus(e),r=`ds_${e.namespace}_${e.name}`,i=this._actionInProgress.has(r);return E`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${e.name}</div>
            <div class="workload-namespace">${e.namespace}</div>
          </div>
          <span class="replica-info">
            ${e.number_available??0}/${e.desired_number_scheduled} available
          </span>
          <span class="badge ${Z[n].badgeClass}">
            ${Z[n].label}
          </span>
          <div class="workload-actions">
            <button
              class="action-btn restart"
              title="Rolling restart"
              ?disabled=${i}
              @click=${()=>this._callService(`restart_workload`,{workload_name:e.name,namespace:e.namespace,entry_id:t},r)}
            >
              <ha-icon icon="mdi:restart"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `}_renderCronJobs(e,t){let n=e.filter(e=>this._matchesNamespace(e.namespace)&&this._matchesSearch(e.name)),r=this._statusFilter===`all`?n:n.filter(e=>this._statusFilter===`stopped`?e.suspend:this._statusFilter===`healthy`&&!e.suspend);return r.length===0&&this._categoryFilter!==`all`?E`<div class="empty">No cronjobs match your filters.</div>`:r.length===0?O:E`
      <div class="category-section">
        <div
          class="category-header"
          role="button"
          tabindex="0"
          @click=${()=>this._toggleCategory(`cronjobs`)}
          @keydown=${e=>this._handleCategoryKeydown(e,`cronjobs`)}
        >
          <ha-icon icon="mdi:clock-outline"></ha-icon>
          CronJobs
          <span class="category-count">(${r.length})</span>
          <ha-icon
            class="category-chevron"
            icon="mdi:chevron-down"
            ?data-collapsed=${this._collapsedCategories.has(`cronjobs`)}
          ></ha-icon>
        </div>
        ${this._collapsedCategories.has(`cronjobs`)?O:r.map(e=>this._renderCronJobCard(e,t))}
      </div>
    `}_renderCronJobCard(e,t){let n=`cj_${e.namespace}_${e.name}`,r=this._actionInProgress.has(n);return E`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${e.name}</div>
            <div class="workload-namespace">${e.namespace}</div>
          </div>
          <span class="schedule-info">${e.schedule}</span>
          ${e.active_jobs_count>0?E`<span class="badge badge-active"
                  >${e.active_jobs_count} active</span
                >`:O}
          ${e.suspend?E`<span class="badge badge-suspended">Suspended</span>`:E`<span class="badge badge-healthy">Active</span>`}
          ${e.last_schedule_time?E`<span class="last-schedule"
                  >Last: ${this._formatAgo(e.last_schedule_time)}</span
                >`:O}
          <div class="workload-actions">
            <button
              class="action-btn ${e.suspend?`start`:`suspend`}"
              title=${e.suspend?`Resume schedule`:`Suspend schedule`}
              ?disabled=${r}
              @click=${()=>this._setCronJobSuspend(t,e,!e.suspend,n)}
            >
              <ha-icon
                icon=${e.suspend?`mdi:play-circle-outline`:`mdi:pause-circle-outline`}
              ></ha-icon>
            </button>
            <button
              class="action-btn start"
              title="Trigger now"
              ?disabled=${r}
              @click=${()=>this._callService(`start_workload`,{workload_name:e.name,namespace:e.namespace,entry_id:t},n)}
            >
              <ha-icon icon="mdi:play"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `}_renderJobs(e,t){let n=t.filter(e=>this._matchesNamespace(e.namespace)&&this._matchesSearch(e.name)),r=this._statusFilter===`all`?n:n.filter(e=>this._statusFilter===`healthy`?e.succeeded>=e.completions:this._statusFilter===`degraded`?e.failed>0&&e.succeeded<e.completions:this._statusFilter!==`stopped`||e.active===0);return r.length===0&&this._categoryFilter!==`all`?E`<div class="empty">No jobs match your filters.</div>`:r.length===0?O:E`
      <div class="category-section">
        <div
          class="category-header"
          role="button"
          tabindex="0"
          @click=${()=>this._toggleCategory(`jobs`)}
          @keydown=${e=>this._handleCategoryKeydown(e,`jobs`)}
        >
          <ha-icon icon="mdi:briefcase-check"></ha-icon>
          Jobs
          <span class="category-count">(${r.length})</span>
          <ha-icon
            class="category-chevron"
            icon="mdi:chevron-down"
            ?data-collapsed=${this._collapsedCategories.has(`jobs`)}
          ></ha-icon>
        </div>
        ${this._collapsedCategories.has(`jobs`)?O:r.map(t=>this._renderJobCard(e,t))}
      </div>
    `}_renderJobCard(e,t){let n=t.succeeded>=t.completions,r=t.failed>0;return E`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${t.name}</div>
            <div class="workload-namespace">${t.namespace}</div>
          </div>
          <span class="replica-info"> ${t.succeeded}/${t.completions} completed </span>
          ${t.active>0?E`<span class="badge badge-active">${t.active} active</span>`:O}
          ${r?E`<span class="badge badge-failed">${t.failed} failed</span>`:O}
          ${n?E`<span class="badge badge-complete">Complete</span>`:O}
          ${t.start_time?E`<span class="last-schedule"
                  >Started: ${this._formatAgo(t.start_time)}</span
                >`:O}
          <div class="workload-actions">
            <button
              class="action-btn delete"
              title="Delete Job"
              ?disabled=${this._deletingJob}
              @click=${()=>this._requestJobDelete(e,t)}
            >
              <ha-icon icon="mdi:delete-outline"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `}_openScaleDialog(e,t,n,r){this._scaleTarget={entry_id:e,workload_name:t,namespace:n,current:r},this._scaleValue=r}_cancelScale(){this._scaleTarget=null}async _confirmScale(){if(this._scaleTarget){this._scaling=!0;try{await this.hass.callService(`kubernetes`,`scale_workload`,{workload_name:this._scaleTarget.workload_name,namespace:this._scaleTarget.namespace,entry_id:this._scaleTarget.entry_id,replicas:this._scaleValue}),this._scaleTarget=null,this._scheduleReload(2e3)}catch(e){this._actionError=H(e,`Failed to scale workload`),this._scaleTarget=null}finally{this._scaling=!1}}}_renderScaleDialog(){let e=this._scaleTarget;return E`
      <div
        class="confirm-overlay"
        tabindex="-1"
        ${this._autofocusOverlay()}
        @click=${this._scaling?O:this._cancelScale}
        @keydown=${this._onOverlayKeydown(this._scaling?O:this._cancelScale)}
      >
        <div class="confirm-dialog" @click=${e=>e.stopPropagation()}>
          <h3>Scale Workload</h3>
          <p>
            <span class="confirm-ref">${e.namespace}/${e.workload_name}</span>
          </p>
          <div class="scale-controls">
            <button
              class="scale-btn"
              ?disabled=${this._scaleValue<=0||this._scaling}
              @click=${()=>this._scaleValue--}
            >
              <ha-icon icon="mdi:minus"></ha-icon>
            </button>
            <input
              class="scale-input"
              type="number"
              min="0"
              .value=${String(this._scaleValue)}
              ?disabled=${this._scaling}
              @input=${e=>{let t=parseInt(e.target.value,10);!isNaN(t)&&t>=0&&(this._scaleValue=t)}}
            />
            <button
              class="scale-btn"
              ?disabled=${this._scaling}
              @click=${()=>this._scaleValue++}
            >
              <ha-icon icon="mdi:plus"></ha-icon>
            </button>
          </div>
          <div class="confirm-actions">
            <button @click=${this._cancelScale} ?disabled=${this._scaling}>
              Cancel
            </button>
            <button
              class="scale-action"
              @click=${this._confirmScale}
              ?disabled=${this._scaling||this._scaleValue===e.current}
            >
              ${this._scaling?`Scaling...`:`Scale`}
            </button>
          </div>
        </div>
      </div>
    `}_requestJobDelete(e,t){this._jobDeleteConfirm={entry_id:e,job_name:t.name,namespace:t.namespace}}_cancelJobDelete(){this._jobDeleteConfirm=null}async _confirmJobDelete(){if(this._jobDeleteConfirm){this._deletingJob=!0;try{await this.hass.callWS({type:`kubernetes/jobs/delete`,entry_id:this._jobDeleteConfirm.entry_id,job_name:this._jobDeleteConfirm.job_name,namespace:this._jobDeleteConfirm.namespace}),this._jobDeleteConfirm=null,await this._loadData()}catch(e){this._actionError=H(e,`Failed to delete job`),this._jobDeleteConfirm=null}finally{this._deletingJob=!1}}}_renderJobDeleteDialog(){let e=this._jobDeleteConfirm;return E`
      <div
        class="confirm-overlay"
        tabindex="-1"
        ${this._autofocusOverlay()}
        @click=${this._deletingJob?O:this._cancelJobDelete}
        @keydown=${this._onOverlayKeydown(this._deletingJob?O:this._cancelJobDelete)}
      >
        <div class="confirm-dialog" @click=${e=>e.stopPropagation()}>
          <h3>Delete Job</h3>
          <p>
            Are you sure you want to delete
            <span class="confirm-ref">${e.namespace}/${e.job_name}</span>?
            This action cannot be undone.
          </p>
          <div class="confirm-actions">
            <button @click=${this._cancelJobDelete} ?disabled=${this._deletingJob}>
              Cancel
            </button>
            <button
              class="delete-action"
              @click=${this._confirmJobDelete}
              ?disabled=${this._deletingJob}
            >
              ${this._deletingJob?`Deleting...`:`Delete`}
            </button>
          </div>
        </div>
      </div>
    `}};U([R()],Q.prototype,`_namespaceFilter`,void 0),U([R()],Q.prototype,`_categoryFilter`,void 0),U([R()],Q.prototype,`_statusFilter`,void 0),U([R()],Q.prototype,`_searchQuery`,void 0),U([R()],Q.prototype,`_actionInProgress`,void 0),U([R()],Q.prototype,`_actionError`,void 0),U([R()],Q.prototype,`_jobDeleteConfirm`,void 0),U([R()],Q.prototype,`_deletingJob`,void 0),U([R()],Q.prototype,`_collapsedCategories`,void 0),U([R()],Q.prototype,`_scaleTarget`,void 0),U([R()],Q.prototype,`_scaleValue`,void 0),U([R()],Q.prototype,`_scaling`,void 0),Q=U([I(`k8s-workloads`)],Q);var dt=class extends W{constructor(...e){super(...e),this.pollMs=0,this.subscribe=!1,this.loadErrorFallback=`Failed to load configuration`,this.emptyMessage=`No Kubernetes entries configured.`}async fetchData(){let e=await this.hass.callWS({type:`kubernetes/config/list`});this._data=e}_navigateToIntegration(){window.open(`/config/integrations/integration/kubernetes`,`_blank`)}static{this.styles=[G,q,o`
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
    `]}render(){let e=this.renderState(!this._data?.entries.length);return e===O?E`${this._data.entries.map(e=>this._renderEntry(e))}`:e}_renderEntry(e){return E`
      <div class="entry-section">
        <div class="entry-header">
          <span class="entry-name">${e.cluster_name}</span>
          ${this._renderHealthBadge(e.healthy)}
        </div>

        <div class="cards-grid">
          ${this._renderConnectionCard(e)} ${this._renderNamespaceCard(e)}
          ${this._renderTimingCard(e)} ${this._renderFeaturesCard(e)}
        </div>

        <div class="actions-bar">
          <button class="action-btn" @click=${this._navigateToIntegration}>
            <ha-icon icon="mdi:cog"></ha-icon>
            Configure Integration
          </button>
        </div>
      </div>
    `}_renderHealthBadge(e){return e===!0?E`<span class="badge badge-healthy">Connected</span>`:e===!1?E`<span class="badge badge-unhealthy">Disconnected</span>`:E`<span class="badge badge-unknown">Unknown</span>`}_renderConnectionCard(e){return E`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:connection"></ha-icon>
          Connection
        </div>
        <div class="setting-row">
          <span class="setting-label">Host</span>
          <span class="setting-value">${e.host}</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Port</span>
          <span class="setting-value">${e.port}</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Verify SSL</span>
          <span class="setting-value">${this._renderBool(e.verify_ssl)}</span>
        </div>
      </ha-card>
    `}_renderNamespaceCard(e){return E`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:folder-multiple"></ha-icon>
          Namespaces
        </div>
        <div class="setting-row">
          <span class="setting-label">Monitor All</span>
          <span class="setting-value"
            >${this._renderBool(e.monitor_all_namespaces)}</span
          >
        </div>
        ${!e.monitor_all_namespaces&&e.namespaces.length>0?E`
                <div class="setting-row">
                  <span class="setting-label">Selected</span>
                  <span class="setting-value">
                    <div class="namespace-tags">
                      ${e.namespaces.map(e=>E`<span class="ns-tag">${e}</span>`)}
                    </div>
                  </span>
                </div>
              `:O}
        <div class="setting-row">
          <span class="setting-label">Device Grouping</span>
          <span class="setting-value"
            >${e.device_grouping_mode===`namespace`?`By Namespace`:`By Cluster`}</span
          >
        </div>
      </ha-card>
    `}_renderTimingCard(e){return E`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:timer-cog"></ha-icon>
          Timing
        </div>
        <div class="setting-row">
          <span class="setting-label">Poll Interval</span>
          <span class="setting-value">${e.switch_update_interval}s</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Scale Timeout</span>
          <span class="setting-value">${e.scale_verification_timeout}s</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Scale Cooldown</span>
          <span class="setting-value">${e.scale_cooldown}s</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Update Mode</span>
          <span class="setting-value"
            >${e.watch_enabled?`Watch (real-time)`:`Polling`}</span
          >
        </div>
      </ha-card>
    `}_renderFeaturesCard(e){return E`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:flask"></ha-icon>
          Features
        </div>
        <div class="setting-row">
          <span class="setting-label">Sidebar Panel</span>
          <span class="setting-value">${this._renderBool(e.panel_enabled)}</span>
        </div>
      </ha-card>
    `}_renderBool(e){return e?E`
        <span class="setting-value-bool bool-true">
          <ha-icon icon="mdi:check-circle"></ha-icon> Enabled
        </span>
      `:E`
      <span class="setting-value-bool bool-false">
        <ha-icon icon="mdi:close-circle-outline"></ha-icon> Disabled
      </span>
    `}};dt=U([I(`k8s-settings`)],dt);var ft=[{id:`overview`,label:`Overview`,icon:`mdi:view-dashboard`},{id:`nodes`,label:`Nodes`,icon:`mdi:server`},{id:`workloads`,label:`Workloads`,icon:`mdi:application-cog`},{id:`pods`,label:`Pods`,icon:`mdi:cube-outline`},{id:`network`,label:`Network`,icon:`mdi:lan`},{id:`settings`,label:`Settings`,icon:`mdi:cog`}],$=class extends F{constructor(...e){super(...e),this.narrow=!1,this._activeTab=`overview`}firstUpdated(e){Fe()}_handleTabChange(e){this._activeTab=e}_toggleSidebar(){this.dispatchEvent(new Event(`hass-toggle-menu`,{bubbles:!0,composed:!0}))}static{this.styles=o`
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
  `}render(){return E`
      <div class="toolbar">
        <div
          class="menu-btn"
          role="button"
          tabindex="0"
          @click=${this._toggleSidebar}
          @keydown=${e=>{(e.key===`Enter`||e.key===` `)&&(e.preventDefault(),this._toggleSidebar())}}
        >
          <ha-icon icon="mdi:menu"></ha-icon>
        </div>
        <h1>Kubernetes</h1>
      </div>
      <div class="tab-bar">
        ${ft.map(e=>E`
            <div
              class="tab"
              role="button"
              tabindex="0"
              ?active=${this._activeTab===e.id}
              @click=${()=>this._handleTabChange(e.id)}
              @keydown=${t=>{(t.key===`Enter`||t.key===` `)&&(t.preventDefault(),this._handleTabChange(e.id))}}
            >
              <ha-icon icon=${e.icon}></ha-icon>
              <span>${e.label}</span>
            </div>
          `)}
      </div>
      <div class="content">${this._renderActiveTab()}</div>
    `}_renderActiveTab(){switch(this._activeTab){case`overview`:return E`<k8s-overview .hass=${this.hass}></k8s-overview>`;case`nodes`:return E`<k8s-nodes-table .hass=${this.hass}></k8s-nodes-table>`;case`pods`:return E`<k8s-pods-table .hass=${this.hass}></k8s-pods-table>`;case`workloads`:return E`<k8s-workloads .hass=${this.hass}></k8s-workloads>`;case`network`:return E`<k8s-network .hass=${this.hass}></k8s-network>`;case`settings`:return E`<k8s-settings .hass=${this.hass}></k8s-settings>`}}};U([L({attribute:!1})],$.prototype,`hass`,void 0),U([L({type:Boolean,reflect:!0})],$.prototype,`narrow`,void 0),U([L({attribute:!1})],$.prototype,`route`,void 0),U([L({attribute:!1})],$.prototype,`panel`,void 0),U([R()],$.prototype,`_activeTab`,void 0),$=U([I(`kubernetes-panel`)],$);export{$ as KubernetesPanel};