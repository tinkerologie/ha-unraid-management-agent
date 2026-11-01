var e=globalThis,t=e.ShadowRoot&&(e.ShadyCSS===void 0||e.ShadyCSS.nativeShadow)&&`adoptedStyleSheets`in Document.prototype&&`replace`in CSSStyleSheet.prototype,n=Symbol(),r=new WeakMap,i=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==n)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,n=this.t;if(t&&e===void 0){let t=n!==void 0&&n.length===1;t&&(e=r.get(n)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),t&&r.set(n,e))}return e}toString(){return this.cssText}},a=e=>new i(typeof e==`string`?e:e+``,void 0,n),o=(e,...t)=>new i(e.length===1?e[0]:t.reduce((t,n,r)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if(typeof e==`number`)return e;throw Error(`Value passed to 'css' function must be a 'css' function result: `+e+`. Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.`)})(n)+e[r+1],e[0]),e,n),s=(n,r)=>{if(t)n.adoptedStyleSheets=r.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let t of r){let r=document.createElement(`style`),i=e.litNonce;i!==void 0&&r.setAttribute(`nonce`,i),r.textContent=t.cssText,n.appendChild(r)}},c=t?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t=``;for(let n of e.cssRules)t+=n.cssText;return a(t)})(e):e,{is:l,defineProperty:u,getOwnPropertyDescriptor:d,getOwnPropertyNames:f,getOwnPropertySymbols:p,getPrototypeOf:m}=Object,h=globalThis,g=h.trustedTypes,_=g?g.emptyScript:``,v=h.reactiveElementPolyfillSupport,y=(e,t)=>e,b={toAttribute(e,t){switch(t){case Boolean:e=e?_:null;break;case Object:case Array:e=e==null?e:JSON.stringify(e)}return e},fromAttribute(e,t){let n=e;switch(t){case Boolean:n=e!==null;break;case Number:n=e===null?null:Number(e);break;case Object:case Array:try{n=JSON.parse(e)}catch{n=null}}return n}},x=(e,t)=>!l(e,t),S={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:x};Symbol.metadata??=Symbol(`metadata`),h.litPropertyMetadata??=new WeakMap;var C=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=S){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let n=Symbol(),r=this.getPropertyDescriptor(e,n,t);r!==void 0&&u(this.prototype,e,r)}}static getPropertyDescriptor(e,t,n){let{get:r,set:i}=d(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:r,set(t){let a=r?.call(this);i?.call(this,t),this.requestUpdate(e,a,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??S}static _$Ei(){if(this.hasOwnProperty(y(`elementProperties`)))return;let e=m(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(y(`finalized`)))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(y(`properties`))){let e=this.properties,t=[...f(e),...p(e)];for(let n of t)this.createProperty(n,e[n])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[e,n]of t)this.elementProperties.set(e,n)}this._$Eh=new Map;for(let[e,t]of this.elementProperties){let n=this._$Eu(e,t);n!==void 0&&this._$Eh.set(n,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let n=new Set(e.flat(1/0).reverse());for(let e of n)t.unshift(c(e))}else e!==void 0&&t.push(c(e));return t}static _$Eu(e,t){let n=t.attribute;return!1===n?void 0:typeof n==`string`?n:typeof e==`string`?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let n of t.keys())this.hasOwnProperty(n)&&(e.set(n,this[n]),delete this[n]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return s(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,n){this._$AK(e,n)}_$ET(e,t){let n=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,n);if(r!==void 0&&!0===n.reflect){let i=(n.converter?.toAttribute===void 0?b:n.converter).toAttribute(t,n.type);this._$Em=e,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(e,t){let n=this.constructor,r=n._$Eh.get(e);if(r!==void 0&&this._$Em!==r){let e=n.getPropertyOptions(r),i=typeof e.converter==`function`?{fromAttribute:e.converter}:e.converter?.fromAttribute===void 0?b:e.converter;this._$Em=r;let a=i.fromAttribute(t,e.type);this[r]=a??this._$Ej?.get(r)??a,this._$Em=null}}requestUpdate(e,t,n,r=!1,i){if(e!==void 0){let a=this.constructor;if(!1===r&&(i=this[e]),n??=a.getPropertyOptions(e),!((n.hasChanged??x)(i,t)||n.useDefault&&n.reflect&&i===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,n))))return;this.C(e,t,n)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:n,reflect:r,wrapped:i},a){n&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),!0!==i||a!==void 0)||(this._$AL.has(e)||(this.hasUpdated||n||(t=void 0),this._$AL.set(e,t)),!0===r&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}let e=this.constructor.elementProperties;if(e.size>0)for(let[t,n]of e){let{wrapped:e}=n,r=this[t];!0!==e||this._$AL.has(t)||r===void 0||this.C(t,void 0,n,r)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};C.elementStyles=[],C.shadowRootOptions={mode:`open`},C[y(`elementProperties`)]=new Map,C[y(`finalized`)]=new Map,v?.({ReactiveElement:C}),(h.reactiveElementVersions??=[]).push(`2.1.2`);var w=globalThis,T=e=>e,E=w.trustedTypes,D=E?E.createPolicy(`lit-html`,{createHTML:e=>e}):void 0,O=`$lit$`,k=`lit$${Math.random().toFixed(9).slice(2)}$`,ee=`?`+k,te=`<${ee}>`,A=document,j=()=>A.createComment(``),M=e=>e===null||typeof e!=`object`&&typeof e!=`function`,N=Array.isArray,ne=e=>N(e)||typeof e?.[Symbol.iterator]==`function`,P="[ \t\n\f\r]",F=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,re=/-->/g,ie=/>/g,I=RegExp(`>|${P}(?:([^\\s"'>=/]+)(${P}*=${P}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,`g`),ae=/'/g,oe=/"/g,se=/^(?:script|style|textarea|title)$/i,L=(e=>(t,...n)=>({_$litType$:e,strings:t,values:n}))(1),R=Symbol.for(`lit-noChange`),z=Symbol.for(`lit-nothing`),ce=new WeakMap,B=A.createTreeWalker(A,129);function le(e,t){if(!N(e)||!e.hasOwnProperty(`raw`))throw Error(`invalid template strings array`);return D===void 0?t:D.createHTML(t)}var ue=(e,t)=>{let n=e.length-1,r=[],i,a=t===2?`<svg>`:t===3?`<math>`:``,o=F;for(let t=0;t<n;t++){let n=e[t],s,c,l=-1,u=0;for(;u<n.length&&(o.lastIndex=u,c=o.exec(n),c!==null);)u=o.lastIndex,o===F?c[1]===`!--`?o=re:c[1]===void 0?c[2]===void 0?c[3]!==void 0&&(o=I):(se.test(c[2])&&(i=RegExp(`</`+c[2],`g`)),o=I):o=ie:o===I?c[0]===`>`?(o=i??F,l=-1):c[1]===void 0?l=-2:(l=o.lastIndex-c[2].length,s=c[1],o=c[3]===void 0?I:c[3]===`"`?oe:ae):o===oe||o===ae?o=I:o===re||o===ie?o=F:(o=I,i=void 0);let d=o===I&&e[t+1].startsWith(`/>`)?` `:``;a+=o===F?n+te:l>=0?(r.push(s),n.slice(0,l)+O+n.slice(l)+k+d):n+k+(l===-2?t:d)}return[le(e,a+(e[n]||`<?>`)+(t===2?`</svg>`:t===3?`</math>`:``)),r]},de=class e{constructor({strings:t,_$litType$:n},r){let i;this.parts=[];let a=0,o=0,s=t.length-1,c=this.parts,[l,u]=ue(t,n);if(this.el=e.createElement(l,r),B.currentNode=this.el.content,n===2||n===3){let e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;(i=B.nextNode())!==null&&c.length<s;){if(i.nodeType===1){if(i.hasAttributes())for(let e of i.getAttributeNames())if(e.endsWith(O)){let t=u[o++],n=i.getAttribute(e).split(k),r=/([.?@])?(.*)/.exec(t);c.push({type:1,index:a,name:r[2],strings:n,ctor:r[1]===`.`?me:r[1]===`?`?he:r[1]===`@`?ge:H}),i.removeAttribute(e)}else e.startsWith(k)&&(c.push({type:6,index:a}),i.removeAttribute(e));if(se.test(i.tagName)){let e=i.textContent.split(k),t=e.length-1;if(t>0){i.textContent=E?E.emptyScript:``;for(let n=0;n<t;n++)i.append(e[n],j()),B.nextNode(),c.push({type:2,index:++a});i.append(e[t],j())}}}else if(i.nodeType===8){if(i.data===ee)c.push({type:2,index:a});else{let e=-1;for(;(e=i.data.indexOf(k,e+1))!==-1;)c.push({type:7,index:a}),e+=k.length-1}}a++}}static createElement(e,t){let n=A.createElement(`template`);return n.innerHTML=e,n}};function V(e,t,n=e,r){if(t===R)return t;let i=r===void 0?n._$Cl:n._$Co?.[r],a=M(t)?void 0:t._$litDirective$;return i?.constructor!==a&&(i?._$AO?.(!1),a===void 0?i=void 0:(i=new a(e),i._$AT(e,n,r)),r===void 0?n._$Cl=i:(n._$Co??=[])[r]=i),i!==void 0&&(t=V(e,i._$AS(e,t.values),i,r)),t}var fe=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:n}=this._$AD,r=(e?.creationScope??A).importNode(t,!0);B.currentNode=r;let i=B.nextNode(),a=0,o=0,s=n[0];for(;s!==void 0;){if(a===s.index){let t;s.type===2?t=new pe(i,i.nextSibling,this,e):s.type===1?t=new s.ctor(i,s.name,s.strings,this,e):s.type===6&&(t=new _e(i,this,e)),this._$AV.push(t),s=n[++o]}a!==s?.index&&(i=B.nextNode(),a++)}return B.currentNode=A,r}p(e){let t=0;for(let n of this._$AV)n!==void 0&&(n.strings===void 0?n._$AI(e[t]):(n._$AI(e,n,t),t+=n.strings.length-2)),t++}},pe=class e{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,n,r){this.type=2,this._$AH=z,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=n,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=V(this,e,t),M(e)?e===z||e==null||e===``?(this._$AH!==z&&this._$AR(),this._$AH=z):e!==this._$AH&&e!==R&&this._(e):e._$litType$===void 0?e.nodeType===void 0?ne(e)?this.k(e):this._(e):this.T(e):this.$(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==z&&M(this._$AH)?this._$AA.nextSibling.data=e:this.T(A.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:n}=e,r=typeof n==`number`?this._$AC(e):(n.el===void 0&&(n.el=de.createElement(le(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===r)this._$AH.p(t);else{let e=new fe(r,this),n=e.u(this.options);e.p(t),this.T(n),this._$AH=e}}_$AC(e){let t=ce.get(e.strings);return t===void 0&&ce.set(e.strings,t=new de(e)),t}k(t){N(this._$AH)||(this._$AH=[],this._$AR());let n=this._$AH,r,i=0;for(let a of t)i===n.length?n.push(r=new e(this.O(j()),this.O(j()),this,this.options)):r=n[i],r._$AI(a),i++;i<n.length&&(this._$AR(r&&r._$AB.nextSibling,i),n.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let t=T(e).nextSibling;T(e).remove(),e=t}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},H=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,n,r,i){this.type=1,this._$AH=z,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=i,n.length>2||n[0]!==``||n[1]!==``?(this._$AH=Array(n.length-1).fill(new String),this.strings=n):this._$AH=z}_$AI(e,t=this,n,r){let i=this.strings,a=!1;if(i===void 0)e=V(this,e,t,0),a=!M(e)||e!==this._$AH&&e!==R,a&&(this._$AH=e);else{let r=e,o,s;for(e=i[0],o=0;o<i.length-1;o++)s=V(this,r[n+o],t,o),s===R&&(s=this._$AH[o]),a||=!M(s)||s!==this._$AH[o],s===z?e=z:e!==z&&(e+=(s??``)+i[o+1]),this._$AH[o]=s}a&&!r&&this.j(e)}j(e){e===z?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??``)}},me=class extends H{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===z?void 0:e}},he=class extends H{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==z)}},ge=class extends H{constructor(e,t,n,r,i){super(e,t,n,r,i),this.type=5}_$AI(e,t=this){if((e=V(this,e,t,0)??z)===R)return;let n=this._$AH,r=e===z&&n!==z||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,i=e!==z&&(n===z||r);r&&this.element.removeEventListener(this.name,this,n),i&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH==`function`?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},_e=class{constructor(e,t,n){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(e){V(this,e)}},ve=w.litHtmlPolyfillSupport;ve?.(de,pe),(w.litHtmlVersions??=[]).push(`3.3.3`);var ye=(e,t,n)=>{let r=n?.renderBefore??t,i=r._$litPart$;if(i===void 0){let e=n?.renderBefore??null;r._$litPart$=i=new pe(t.insertBefore(j(),e),e,void 0,n??{})}return i._$AI(e),i},be=globalThis,U=class extends C{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=ye(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return R}};U._$litElement$=!0,U.finalized=!0,be.litElementHydrateSupport?.({LitElement:U});var xe=be.litElementPolyfillSupport;xe?.({LitElement:U}),(be.litElementVersions??=[]).push(`4.2.2`);var Se=`unraid-management-agent-server-card`,Ce=`unraid-management-agent-server-card-editor`,we=`unraid-management-agent-storage-card`,Te=`unraid-management-agent-storage-card-editor`,Ee=`unraid-management-agent-docker-card`,De=`unraid-management-agent-docker-card-editor`,Oe=`unraid-management-agent-ups-card`,ke=`unraid-management-agent-ups-card-editor`,Ae=`unraid-management-agent-vm-card`,je=`unraid-management-agent-vm-card-editor`,Me=`unraid-management-agent-shares-card`,Ne=`unraid-management-agent-shares-card-editor`,Pe=`unraid-management-agent-network-card`,Fe=`unraid-management-agent-network-card-editor`,Ie=`unraid-management-agent-zfs-card`,Le=`unraid-management-agent-zfs-card-editor`,Re=`unraid-management-agent-fans-card`,ze=`unraid-management-agent-fans-card-editor`,Be=`unraid-management-agent-gpu-card`,Ve=`unraid-management-agent-gpu-card-editor`,He=`unraid-management-agent-notifications-card`,Ue=`unraid-management-agent-notifications-card-editor`,We=`unraid-management-agent-maintenance-card`,Ge=`unraid-management-agent-maintenance-card-editor`,Ke=`unraid-management-agent-remote-shares-card`,qe=`unraid-management-agent-remote-shares-card-editor`,Je=`unraid-management-agent-unassigned-devices-card`,Ye=`unraid-management-agent-unassigned-devices-card-editor`,Xe=`unraid-management-agent-dashboard-card`,Ze=`unraid-management-agent-dashboard-card-editor`,Qe=[o`
  :host {
    --unraid-primary: var(
      --primary-color,
      var(--ha-color-fill-primary-loud-resting, #03a9f4)
    );
    --unraid-accent: var(--unraid-primary);
    --unraid-online: var(--success-color, #00883c);
    --unraid-warning: var(--warning-color, #c94e00);
    --unraid-error: var(--error-color, #db4437);
    --unraid-standby: var(--disabled-text-color, #7a7a7a);
    --unraid-info: var(--info-color, var(--unraid-primary));
    --unraid-card-bg: var(--ha-card-background, var(--card-background-color, #ffffff));
    --unraid-border: var(--ha-card-border-color, var(--divider-color, #e0e0e0));
    --unraid-radius: var(--ha-card-border-radius, var(--ha-border-radius-lg, 12px));
    --unraid-text: var(--primary-text-color, var(--ha-color-text-primary, #212121));
    --unraid-subtext: var(
      --secondary-text-color,
      var(--ha-color-text-secondary, #5e5e5e)
    );
    --unraid-focus: var(--ha-color-focus, var(--unraid-text));
  }
`,o`
    :host {
      display: block;
      box-sizing: border-box;
      font-family: var(--ha-card-font-family, var(--ha-font-family-body, inherit));
      font-size: var(--ha-font-size-m, 14px);
    }

    *,
    *::before,
    *::after {
      box-sizing: border-box;
    }

    button,
    input,
    select {
      font: inherit;
    }

    /* Controls that replaced clickable rows and gauges. Zero specificity, so
       each element's own class still sets its look. */
    :where(.interactive) {
      appearance: none;
      inline-size: 100%;
      min-block-size: 40px;
      padding: 0;
      border: none;
      background: transparent;
      color: inherit;
      text-align: start;
      cursor: pointer;
      touch-action: manipulation;
    }

    :where(.interactive:disabled) {
      color: inherit;
      cursor: default;
    }

    :where(.interactive [data-block]) {
      display: block;
      min-width: 0;
    }

    .sr-only {
      position: absolute;
      inline-size: 1px;
      block-size: 1px;
      overflow: hidden;
      clip-path: inset(50%);
      white-space: nowrap;
    }

    ha-card {
      box-sizing: border-box;
      padding: var(--ha-space-4, 16px);
      background: var(--unraid-card-bg);
      border: var(--ha-card-border-width, 1px) solid var(--unraid-border);
      border-radius: var(--unraid-radius);
      color: var(--unraid-text);
    }

    /* Keep containment inside the card so Sections can size the host normally. */
    .uma-card-content {
      container: unraid-card / inline-size;
      display: flex;
      flex-direction: column;
      gap: var(--ha-space-3, 12px);
      min-inline-size: 0;
    }

    .ltr-value {
      direction: ltr;
      unicode-bidi: isolate;
    }

    .vm-labels {
      display: flex;
      flex-direction: column;
      min-inline-size: 0;
    }

    .entity-name {
      min-inline-size: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-weight: var(--ha-font-weight-bold, 600);
      font-size: var(--ha-font-size-m, 14px);
    }

    .gpu-header, .gpu-name {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      min-inline-size: 0;
    }

    .gpu-header {
      justify-content: space-between;
      margin-block-end: var(--ha-space-2, 8px);
      inline-size: 100%;
    }

    .gpu-name { flex: 1; }
    .badge.gpu-driver { white-space: normal; overflow-wrap: anywhere; }

    :host([embedded]) ha-card {
      border: none;
      box-shadow: none;
      background: transparent;
      padding: 0;
    }

    .icon {
      display: inline-block;
      vertical-align: middle;
      fill: currentColor;
      flex-shrink: 0;
    }

    /* Header */
    .header {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: var(--ha-space-2, 8px);
    }

    .header-main {
      display: flex;
      flex: 1 1 auto;
      align-items: center;
      gap: var(--ha-space-3, 12px);
      min-width: 0;
    }

    .header-icon {
      width: 40px;
      height: 40px;
      border-radius: var(--ha-border-radius-lg, 12px);
      background: color-mix(in srgb, var(--unraid-accent) 15%, transparent);
      color: var(--unraid-accent);
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }

    .header-titles {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .header-title {
      font-size: var(--ha-font-size-l, 16px);
      font-weight: var(--ha-font-weight-bold, 700);
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.25;
    }

    .header-subtitle {
      font-size: var(--ha-font-size-s, 12px);
      color: var(--unraid-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      flex-shrink: 0;
    }

    /* Badges / Chips */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      padding: 3px var(--ha-space-2, 8px);
      border-radius: var(--ha-border-radius-md, 8px);
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 600);
      line-height: 1;
      white-space: nowrap;
    }

    .badge-online {
      background: color-mix(in srgb, var(--unraid-online) 15%, transparent);
      color: var(--unraid-online);
      border: 1px solid color-mix(in srgb, var(--unraid-online) 25%, transparent);
    }

    .badge-warning {
      background: color-mix(in srgb, var(--unraid-warning) 15%, transparent);
      color: var(--unraid-warning);
      border: 1px solid color-mix(in srgb, var(--unraid-warning) 25%, transparent);
    }

    .badge-error {
      background: color-mix(in srgb, var(--unraid-error) 15%, transparent);
      color: var(--unraid-error);
      border: 1px solid color-mix(in srgb, var(--unraid-error) 25%, transparent);
    }

    .badge-standby {
      background: color-mix(in srgb, var(--unraid-standby) 15%, transparent);
      color: var(--unraid-standby);
      border: 1px solid color-mix(in srgb, var(--unraid-standby) 25%, transparent);
    }

    .pulse-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: currentColor;
    }

    /* Conic Ring Gauges */
    .rings-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(85px, 1fr));
      gap: var(--ha-space-2, 8px);
    }

    .ups-rings { grid-template-columns: repeat(2, minmax(0, 1fr)); }

    .ring-card {
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      border-radius: var(--ha-border-radius-lg, 12px);
      padding: var(--ha-space-2, 8px) var(--ha-space-2, 8px);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: var(--ha-space-2, 8px);
    }

    .ring-gauge {
      width: 54px;
      height: 54px;
      border-radius: 50%;
      position: relative;
      display: grid;
      place-items: center;
      background: conic-gradient(
        var(--ring-color, var(--unraid-primary)) calc(var(--pct, 0) * 1%),
        color-mix(in srgb, var(--unraid-text) 8%, transparent) 0
      );
      flex-shrink: 0;
    }

    .ring-gauge::after {
      content: "";
      position: absolute;
      inset: 6px;
      border-radius: 50%;
      background: var(--unraid-card-bg);
    }

    .ring-content {
      position: relative;
      z-index: 2;
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 700);
      color: var(--unraid-text);
    }

    .ring-label {
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 600);
      color: var(--unraid-text);
      line-height: 1.1;
    }

    .ring-subtext {
      font-size: var(--ha-font-size-s, 12px);
      color: var(--unraid-subtext);
      line-height: 1.1;
      overflow-wrap: anywhere;
    }

    /* Progress Bars */
    .progress-bar {
      width: 100%;
      height: 6px;
      background: color-mix(in srgb, var(--unraid-text) 10%, transparent);
      border-radius: var(--ha-border-radius-sm, 4px);
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--fill-color, var(--unraid-accent));
      border-radius: var(--ha-border-radius-sm, 4px);
      transition: width 0.3s ease;
    }

    /* Lists / Tables */
    .item-list {
      display: flex;
      flex-direction: column;
      gap: var(--ha-space-2, 8px);
    }

    .list-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--ha-space-2, 8px) var(--ha-space-3, 12px);
      border-radius: var(--ha-border-radius-md, 8px);
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      gap: var(--ha-space-2, 8px);
      font-size: var(--ha-font-size-s, 12px);
      transition: border-color 0.2s ease;
    }

    .list-row:hover {
      border-color: color-mix(in srgb, var(--unraid-accent) 40%, transparent);
    }

    .row-left {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      min-width: 0;
      flex: 1;
    }

    .row-right {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      flex-shrink: 0;
    }

    /* Disk / Storage Item Lists */
    .disk-list {
      display: flex;
      flex-direction: column;
      gap: var(--ha-space-2, 8px);
    }

    .disk-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--ha-space-2, 8px) var(--ha-space-3, 12px);
      border-radius: var(--ha-border-radius-md, 8px);
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      gap: var(--ha-space-2, 8px);
      font-size: var(--ha-font-size-s, 12px);
      transition: border-color 0.2s ease;
    }

    .disk-row:hover {
      border-color: color-mix(in srgb, var(--unraid-accent) 40%, transparent);
    }

    .disk-main {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      min-width: 0;
      flex: 1;
    }

    .disk-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: var(--ha-border-radius-md, 8px);
      flex-shrink: 0;
      background: color-mix(in srgb, var(--unraid-text) 6%, transparent);
      color: var(--unraid-subtext);
    }

    .disk-icon.disk-online {
      background: color-mix(in srgb, var(--unraid-online) 12%, transparent);
      color: var(--unraid-online);
    }

    .disk-icon.disk-standby {
      background: color-mix(in srgb, var(--unraid-standby) 12%, transparent);
      color: var(--unraid-standby);
    }

    .disk-icon.disk-warning {
      background: color-mix(in srgb, var(--unraid-warning) 12%, transparent);
      color: var(--unraid-warning);
    }

    .disk-info {
      display: flex;
      flex-direction: column;
      min-width: 0;
      gap: 2px;
    }

    .disk-name {
      font-weight: var(--ha-font-weight-bold, 600);
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .disk-subtext {
      font-size: var(--ha-font-size-s, 12px);
      color: var(--unraid-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .disk-meta {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      flex-shrink: 0;
    }

    .disk-temp {
      font-weight: var(--ha-font-weight-bold, 600);
      font-size: var(--ha-font-size-s, 12px);
      color: var(--unraid-text);
    }

    /* Empty States */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: var(--ha-space-6, 24px) var(--ha-space-4, 16px);
      gap: var(--ha-space-2, 8px);
      color: var(--unraid-subtext);
    }

    .empty-title {
      font-size: var(--ha-font-size-m, 14px);
      font-weight: var(--ha-font-weight-bold, 600);
      color: var(--unraid-text);
    }

    .empty-subtext {
      font-size: var(--ha-font-size-s, 12px);
      max-width: 320px;
      line-height: 1.3;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--ha-space-2, 8px);
      padding: var(--ha-space-1, 4px) var(--ha-space-3, 12px);
      border-radius: var(--ha-border-radius-md, 8px);
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 600);
      border: 1px solid var(--unraid-border);
      background: color-mix(in srgb, var(--unraid-text) 6%, transparent);
      color: var(--unraid-text);
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn:hover {
      background: color-mix(in srgb, var(--unraid-text) 12%, transparent);
    }

    .btn-danger {
      color: var(--unraid-error);
      border-color: var(--unraid-error);
    }

    .btn-primary {
      background: var(--unraid-accent);
      color: var(--text-primary-color, #fff);
      border-color: transparent;
    }

    .btn-primary:hover {
      filter: brightness(1.1);
    }

    .btn-icon {
      padding: var(--ha-space-2, 8px);
      border-radius: var(--ha-border-radius-md, 8px);
      border: 1px solid transparent;
      background: transparent;
      color: var(--unraid-subtext);
      cursor: pointer;
    }

    .btn-icon:hover {
      background: color-mix(in srgb, var(--unraid-text) 8%, transparent);
      color: var(--unraid-text);
    }

    .btn, .tab-btn {
      min-block-size: 44px;
      min-inline-size: 44px;
    }

    .btn-icon {
      display: inline-grid;
      place-items: center;
      min-block-size: 48px;
      min-inline-size: 48px;
    }

    :where(button, a, input, select, [tabindex]):focus-visible {
      outline: 2px solid var(--unraid-focus);
      outline-offset: 2px;
    }

    button.badge {
      min-block-size: 44px;
    }

    dialog {
      max-width: min(420px, calc(100vw - 64px));
      border: 1px solid var(--unraid-border);
      border-radius: var(--unraid-radius);
      padding: var(--ha-space-6, 24px);
      color: var(--unraid-text);
      background: var(--unraid-card-bg);
    }
    dialog::backdrop { background: var(--mdc-dialog-scrim-color, rgba(0, 0, 0, 0.32)); }
    dialog h2 { margin-block-start: 0; font-size: var(--ha-font-size-xl, 20px); }
    .dialog-actions { display: flex; justify-content: flex-end; gap: var(--ha-space-2, 8px); }

    .btn:disabled, .btn-icon:disabled { cursor: default; opacity: 0.5; }

    @container unraid-card (max-width: 450px) {
      .list-row, .disk-row, .row-left, .row-right, .disk-meta, .container-tile { flex-wrap: wrap; }
      .row-left { min-width: 0; flex-basis: 100%; }
      .row-right, .disk-meta { margin-inline-start: auto; }
      .network-row, .network-row [data-block] { flex-wrap: wrap; }
      .network-row span { min-inline-size: 0; flex-wrap: wrap; }
      .network-row .ltr-value { overflow-wrap: anywhere; }
    }

    @container unraid-card (max-width: 320px) {
      .header { flex-wrap: wrap; }
      .header-main { flex-basis: 100%; }
      .header-actions { flex-wrap: wrap; min-inline-size: 0; max-inline-size: 100%; }
      .header-actions .badge { white-space: normal; overflow-wrap: anywhere; }
      .ring-subtext {
        max-inline-size: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .ups-rings { grid-template-columns: minmax(0, 1fr); }
      .gpu-header { flex-wrap: wrap; }
      .gpu-name { flex-basis: 100%; }
      .gpu-driver { max-inline-size: 100%; }
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        transition: none !important;
        animation: none !important;
      }
    }

    /* Docker Containers Grid View (like Unraid GUI) */
    .container-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 200px), 1fr));
      gap: var(--ha-space-2, 8px);
    }

    .container-tile {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--ha-space-2, 8px) var(--ha-space-2, 8px);
      border-radius: var(--ha-border-radius-md, 8px);
      background: color-mix(in srgb, var(--unraid-text) 4%, transparent);
      border: 1px solid var(--unraid-border);
      gap: var(--ha-space-2, 8px);
      transition: all 0.2s ease;
    }

    .container-tile:hover {
      border-color: var(--unraid-accent);
    }

    .tile-name {
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 600);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      min-width: 0;
    }

    .tile-name.btn {
      min-width: 44px;
      background: transparent;
      border: none;
      padding-inline: 0;
      justify-content: flex-start;
      text-align: start;
      font-size: var(--ha-font-size-s, 14px);
    }


    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .status-dot.online {
      background: var(--unraid-online);
    }

    .status-dot.offline {
      background: var(--unraid-error);
      border-radius: 2px;
    }

    /* Section divider */
    .divider {
      height: 1px;
      background: var(--unraid-border);
      width: 100%;
      margin-block: var(--ha-space-1, 4px);
    }

    /* Details Rows */
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: var(--ha-space-2, 8px);
      font-size: var(--ha-font-size-s, 12px);
    }

    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .detail-label {
      color: var(--unraid-subtext);
      font-size: var(--ha-font-size-s, 12px);
    }

    .detail-val {
      font-weight: var(--ha-font-weight-bold, 600);
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* Tab strip for unified dashboard card */
    .tab-strip {
      display: flex;
      gap: var(--ha-space-2, 8px);
      overflow-x: auto;
      scrollbar-width: thin;
      border-block-end: 1px solid var(--unraid-border);
      padding-block-end: var(--ha-space-2, 8px);
    }

    .tab-btn {
      flex-shrink: 0;
      white-space: nowrap;
      padding: var(--ha-space-1, 4px) var(--ha-space-2, 8px);
      border-radius: var(--ha-border-radius-md, 8px);
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 600);
      background: transparent;
      border: none;
      color: var(--unraid-subtext);
      cursor: pointer;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: var(--ha-space-1, 4px);
      transition: all 0.2s ease;
    }

    .tab-btn:hover {
      color: var(--unraid-text);
      background: color-mix(in srgb, var(--unraid-text) 5%, transparent);
    }

    .tab-btn.active {
      background: color-mix(in srgb, var(--unraid-accent) 15%, transparent);
      color: var(--unraid-accent);
    }
  `];function W(e,t,n,r){let i=new CustomEvent(t,{bubbles:r?.bubbles??!0,cancelable:!!r?.cancelable,composed:r?.composed??!0,detail:n});return e.dispatchEvent(i),i}var G=`M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z`,$e=`M21,19V20H3V19L5,17V11C5,7.9 7.03,5.17 10,4.29C10,4.19 10,4.1 10,4A2,2 0 0,1 12,2A2,2 0 0,1 14,4C14,4.1 14,4.19 14,4.29C16.97,5.17 19,7.9 19,11V17L21,19M14,21A2,2 0 0,1 12,23A2,2 0 0,1 10,21`,et=`M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z`,tt=`M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z`,nt=`M12,3C7.58,3 4,4.79 4,7C4,9.21 7.58,11 12,11C16.42,11 20,9.21 20,7C20,4.79 16.42,3 12,3M4,9V12C4,14.21 7.58,16 12,16C16.42,16 20,14.21 20,12V9C20,11.21 16.42,13 12,13C7.58,13 4,11.21 4,9M4,14V17C4,19.21 7.58,21 12,21C16.42,21 20,19.21 20,17V14C20,16.21 16.42,18 12,18C7.58,18 4,16.21 4,14Z`,rt=`M21.81 10.25C21.75 10.21 21.25 9.82 20.17 9.82C19.89 9.82 19.61 9.85 19.33 9.9C19.12 8.5 17.95 7.79 17.9 7.76L17.61 7.59L17.43 7.86C17.19 8.22 17 8.63 16.92 9.05C16.72 9.85 16.84 10.61 17.25 11.26C16.76 11.54 15.96 11.61 15.79 11.61H2.62C2.28 11.61 2 11.89 2 12.24C2 13.39 2.18 14.54 2.58 15.62C3.03 16.81 3.71 17.69 4.58 18.23C5.56 18.83 7.17 19.17 9 19.17C9.79 19.17 10.61 19.1 11.42 18.95C12.54 18.75 13.62 18.36 14.61 17.79C15.43 17.32 16.16 16.72 16.78 16C17.83 14.83 18.45 13.5 18.9 12.35H19.09C20.23 12.35 20.94 11.89 21.33 11.5C21.59 11.26 21.78 10.97 21.92 10.63L22 10.39L21.81 10.25M3.85 11.24H5.61C5.69 11.24 5.77 11.17 5.77 11.08V9.5C5.77 9.42 5.7 9.34 5.61 9.34H3.85C3.76 9.34 3.69 9.41 3.69 9.5V11.08C3.7 11.17 3.76 11.24 3.85 11.24M6.28 11.24H8.04C8.12 11.24 8.2 11.17 8.2 11.08V9.5C8.2 9.42 8.13 9.34 8.04 9.34H6.28C6.19 9.34 6.12 9.41 6.12 9.5V11.08C6.13 11.17 6.19 11.24 6.28 11.24M8.75 11.24H10.5C10.6 11.24 10.67 11.17 10.67 11.08V9.5C10.67 9.42 10.61 9.34 10.5 9.34H8.75C8.67 9.34 8.6 9.41 8.6 9.5V11.08C8.6 11.17 8.66 11.24 8.75 11.24M11.19 11.24H12.96C13.04 11.24 13.11 11.17 13.11 11.08V9.5C13.11 9.42 13.05 9.34 12.96 9.34H11.19C11.11 9.34 11.04 9.41 11.04 9.5V11.08C11.04 11.17 11.11 11.24 11.19 11.24M6.28 9H8.04C8.12 9 8.2 8.91 8.2 8.82V7.25C8.2 7.16 8.13 7.09 8.04 7.09H6.28C6.19 7.09 6.12 7.15 6.12 7.25V8.82C6.13 8.91 6.19 9 6.28 9M8.75 9H10.5C10.6 9 10.67 8.91 10.67 8.82V7.25C10.67 7.16 10.61 7.09 10.5 7.09H8.75C8.67 7.09 8.6 7.15 8.6 7.25V8.82C8.6 8.91 8.66 9 8.75 9M11.19 9H12.96C13.04 9 13.11 8.91 13.11 8.82V7.25C13.11 7.16 13.04 7.09 12.96 7.09H11.19C11.11 7.09 11.04 7.15 11.04 7.25V8.82C11.04 8.91 11.11 9 11.19 9M11.19 6.72H12.96C13.04 6.72 13.11 6.65 13.11 6.56V5C13.11 4.9 13.04 4.83 12.96 4.83H11.19C11.11 4.83 11.04 4.89 11.04 5V6.56C11.04 6.64 11.11 6.72 11.19 6.72M13.65 11.24H15.41C15.5 11.24 15.57 11.17 15.57 11.08V9.5C15.57 9.42 15.5 9.34 15.41 9.34H13.65C13.57 9.34 13.5 9.41 13.5 9.5V11.08C13.5 11.17 13.57 11.24 13.65 11.24`,it=`M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z`,at=`M7,15H9V18H11V15H13V18H15V15H17V18H19V9H15V6H9V9H5V18H7V15M4.38,3H19.63C20.94,3 22,4.06 22,5.38V19.63A2.37,2.37 0 0,1 19.63,22H4.38C3.06,22 2,20.94 2,19.63V5.38C2,4.06 3.06,3 4.38,3Z`,ot=`M2,7V8.5H3V17H4.5V7C3.7,7 2.8,7 2,7M6,7V7L6,16H7V17H14V16H22V7H6M17.5,9A2.5,2.5 0 0,1 20,11.5A2.5,2.5 0 0,1 17.5,14A2.5,2.5 0 0,1 15,11.5A2.5,2.5 0 0,1 17.5,9Z`,st=`M12,11A1,1 0 0,0 11,12A1,1 0 0,0 12,13A1,1 0 0,0 13,12A1,1 0 0,0 12,11M12.5,2C17,2 17.11,5.57 14.75,6.75C13.76,7.24 13.32,8.29 13.13,9.22C13.61,9.42 14.03,9.73 14.35,10.13C18.05,8.13 22.03,8.92 22.03,12.5C22.03,17 18.46,17.1 17.28,14.73C16.78,13.74 15.72,13.3 14.79,13.11C14.59,13.59 14.28,14 13.88,14.34C15.87,18.03 15.08,22 11.5,22C7,22 6.91,18.42 9.27,17.24C10.25,16.75 10.69,15.71 10.89,14.79C10.4,14.59 9.97,14.27 9.65,13.87C5.96,15.85 2,15.07 2,11.5C2,7 5.56,6.89 6.74,9.26C7.24,10.25 8.29,10.68 9.22,10.87C9.41,10.39 9.73,9.97 10.14,9.65C8.15,5.96 8.94,2 12.5,2Z`,ct=`M7,2V13H10V22L17,10H13L17,2H7Z`,lt=`M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z`,ut=`M6,2H18A2,2 0 0,1 20,4V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V4A2,2 0 0,1 6,2M12,4A6,6 0 0,0 6,10C6,13.31 8.69,16 12.1,16L11.22,13.77C10.95,13.29 11.11,12.68 11.59,12.4L12.45,11.9C12.93,11.63 13.54,11.79 13.82,12.27L15.74,14.69C17.12,13.59 18,11.9 18,10A6,6 0 0,0 12,4M12,9A1,1 0 0,1 13,10A1,1 0 0,1 12,11A1,1 0 0,1 11,10A1,1 0 0,1 12,9M7,18A1,1 0 0,0 6,19A1,1 0 0,0 7,20A1,1 0 0,0 8,19A1,1 0 0,0 7,18M12.09,13.27L14.58,19.58L17.17,18.08L12.95,12.77L12.09,13.27Z`,dt=`M12 9A1 1 0 1 0 13 10A1 1 0 0 0 12 9M12 9A1 1 0 1 0 13 10A1 1 0 0 0 12 9M18 2H6A2 2 0 0 0 4 4V13.09A5.47 5.47 0 0 1 5 13A5.71 5.71 0 0 1 7 13.36A6 6 0 1 1 15.71 14.69L13.79 12.27A1 1 0 0 0 12.42 11.9L11.56 12.4A1 1 0 0 0 11.19 13.77L12.1 16A6.12 6.12 0 0 1 10 15.62A6 6 0 0 1 10.19 22H18A2 2 0 0 0 20 20V4A2 2 0 0 0 18 2M14.58 19.58L12.09 13.27L12.95 12.77L17.17 18.08M12 11A1 1 0 1 0 11 10A1 1 0 0 0 12 11M9 20H6V23H4V20H1V18H4V15H6V18H9Z`,ft=`M13,9H11V7H13M13,17H11V11H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z`,pt=`M4,1C2.89,1 2,1.89 2,3V7C2,8.11 2.89,9 4,9H1V11H13V9H10C11.11,9 12,8.11 12,7V3C12,1.89 11.11,1 10,1H4M4,3H10V7H4V3M3,13V18L3,20H10V18H5V13H3M14,13C12.89,13 12,13.89 12,15V19C12,20.11 12.89,21 14,21H11V23H23V21H20C21.11,21 22,20.11 22,19V15C22,13.89 21.11,13 20,13H14M14,15H20V19H14V15Z`,mt=`M21,16H3V4H21M21,2H3C1.89,2 1,2.89 1,4V16A2,2 0 0,0 3,18H10V20H8V22H16V20H14V18H21A2,2 0 0,0 23,16V4C23,2.89 22.1,2 21,2Z`,ht=`M8,5.14V19.14L19,12.14L8,5.14Z`,gt=`M16.56,5.44L15.11,6.89C16.84,7.94 18,9.83 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12C6,9.83 7.16,7.94 8.88,6.88L7.44,5.44C5.36,6.88 4,9.28 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12C20,9.28 18.64,6.88 16.56,5.44M13,3H11V13H13`,_t=`M12,4C14.1,4 16.1,4.8 17.6,6.3C20.7,9.4 20.7,14.5 17.6,17.6C15.8,19.5 13.3,20.2 10.9,19.9L11.4,17.9C13.1,18.1 14.9,17.5 16.2,16.2C18.5,13.9 18.5,10.1 16.2,7.7C15.1,6.6 13.5,6 12,6V10.6L7,5.6L12,0.6V4M6.3,17.6C3.7,15 3.3,11 5.1,7.9L6.6,9.4C5.5,11.6 5.9,14.4 7.8,16.2C8.3,16.7 8.9,17.1 9.6,17.4L9,19.4C8,19 7.1,18.4 6.3,17.6Z`,vt=`M4,1H20A1,1 0 0,1 21,2V6A1,1 0 0,1 20,7H4A1,1 0 0,1 3,6V2A1,1 0 0,1 4,1M4,9H20A1,1 0 0,1 21,10V14A1,1 0 0,1 20,15H4A1,1 0 0,1 3,14V10A1,1 0 0,1 4,9M4,17H20A1,1 0 0,1 21,18V22A1,1 0 0,1 20,23H4A1,1 0 0,1 3,22V18A1,1 0 0,1 4,17M9,5H10V3H9V5M9,13H10V11H9V13M9,21H10V19H9V21M5,3V5H7V3H5M5,11V13H7V11H5M5,19V21H7V19H5Z`,yt=`M13,19H14A1,1 0 0,1 15,20H22V22H15A1,1 0 0,1 14,23H10A1,1 0 0,1 9,22H2V20H9A1,1 0 0,1 10,19H11V17H4A1,1 0 0,1 3,16V12A1,1 0 0,1 4,11H20A1,1 0 0,1 21,12V16A1,1 0 0,1 20,17H13V19M4,3H20A1,1 0 0,1 21,4V8A1,1 0 0,1 20,9H4A1,1 0 0,1 3,8V4A1,1 0 0,1 4,3M9,7H10V5H9V7M9,15H10V13H9V15M5,5V7H7V5H5M5,13V15H7V13H5Z`,bt=`M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5M11,7H13V13H11M11,15H13V17H11`,xt=`M10,17L6,13L7.41,11.59L10,14.17L16.59,7.58L18,9M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1Z`,St=`M18,18H6V6H18V18Z`,Ct=`M9,16V10H5L12,3L19,10H15V16H9M5,20V18H19V20H5Z`,wt=`M8 15C8.55 15 9 15.45 9 16C9 16.55 8.55 17 8 17C7.45 17 7 16.55 7 16C7 15.45 7.45 15 8 15M15.07 4.69L16.5 6.1L15.07 7.5L13.66 6.1L15.07 4.69M17.9 7.5L19.31 8.93L17.9 10.34L16.5 8.93L17.9 7.5M8 13C6.34 13 5 14.34 5 16C5 17.66 6.34 19 8 19C9.66 19 11 17.66 11 16C11 14.34 9.66 13 8 13M9.77 4.33L10.5 5.08L14.29 1.29C14.47 1.11 14.72 1 15 1C15.28 1 15.53 1.11 15.71 1.29L22.78 8.36L22.78 8.37C22.92 8.54 23 8.76 23 9C23 9.3 22.87 9.57 22.66 9.76L22.66 9.76L18.93 13.5L19.67 14.23L12.95 20.95C11.68 22.22 9.93 23 8 23C4.13 23 1 19.87 1 16C1 14.07 1.78 12.32 3.05 11.05L9.77 4.33M20.59 9L15 3.41L11.93 6.5L17.5 12.08L20.59 9Z`,Tt=`M3,11H11V3H3M3,21H11V13H3M13,21H21V13H13M13,3V11H21V3`,Et=`M9,5V9H21V5M9,19H21V15H9M9,14H21V10H9M4,9H8V5H4M4,19H8V15H4M4,14H8V10H4V14Z`,Dt=`M22.7,19L13.6,9.9C14.5,7.6 14,4.9 12.1,3C10.1,1 7.1,0.6 4.7,1.7L9,6L6,9L1.6,4.7C0.4,7.1 0.9,10.1 2.9,12.1C4.8,14 7.5,14.5 9.8,13.6L18.9,22.7C19.3,23.1 19.9,23.1 20.3,22.7L22.6,20.4C23.1,20 23.1,19.3 22.7,19Z`;function K(e,t=20,n=`icon`){return L`
    <svg
      class="${n}"
      style="width: ${t}px; height: ${t}px;"
      viewBox="0 0 24 24"
    >
      <path d="${e}" fill="currentColor"></path>
    </svg>
  `}var Ot=[`unavailable`,`unknown`,`none`,`--`,``],kt={"bit/s":[1,[`bit/s`,`kbit/s`,`Mbit/s`,`Gbit/s`]],"kbit/s":[1e3,[`bit/s`,`kbit/s`,`Mbit/s`,`Gbit/s`]],"Mbit/s":[1e6,[`bit/s`,`kbit/s`,`Mbit/s`,`Gbit/s`]],"Gbit/s":[1e9,[`bit/s`,`kbit/s`,`Mbit/s`,`Gbit/s`]],"B/s":[1,[`B/s`,`kB/s`,`MB/s`,`GB/s`]],"kB/s":[1e3,[`B/s`,`kB/s`,`MB/s`,`GB/s`]],"MB/s":[1e6,[`B/s`,`kB/s`,`MB/s`,`GB/s`]],"GB/s":[1e9,[`B/s`,`kB/s`,`MB/s`,`GB/s`]]};function q(e){let t=e?.state?.toLowerCase().trim();if(t===void 0||Ot.includes(t))return`--`;let n=parseFloat(t);if(isNaN(n))return`--`;let r=String(e?.attributes?.unit_of_measurement??`MB/s`),i=kt[r];if(!i)return`${n.toFixed(2)} ${r}`;let[a,o]=i;if(n<=0)return`0 ${o[1]}`;let s=n*a,c=Math.max(1,Math.min(o.length-1,Math.floor(Math.log10(s)/3)));return`${(s/10**(c*3)).toFixed(c===1?1:2)} ${o[c]}`}function At(e){let t=e?.state?.toLowerCase().trim();if(t===void 0||Ot.includes(t))return;let n=parseFloat(t);if(isNaN(n))return;let r=[`B`,`kB`,`MB`,`GB`,`TB`,`PB`],i=String(e?.attributes?.unit_of_measurement??``),a=r.indexOf(i);if(a<0)return i?`${n} ${i}`:`${n}`;let o=n;for(;o>=1e3&&a<r.length-1;)o/=1e3,a+=1;return`${o.toFixed(1)} ${r[a]}`}function jt(e){if(!e||e===`unavailable`||e===`unknown`)return`--`;if(e.includes(`T`)||/^\d{4}-\d{2}-\d{2}/.test(e))try{let t=new Date(e);if(!isNaN(t.getTime()))return t.toLocaleDateString(void 0,{month:`short`,day:`numeric`,year:`numeric`})+`, `+t.toLocaleTimeString(void 0,{hour:`2-digit`,minute:`2-digit`,hour12:!1})}catch{}return e}var J=class extends U{static styles=Qe;static editorTag=``;static async getConfigElement(){return document.createElement(this.editorTag)}static getStubConfig(e){let t=Object.values(e?.devices??{}).find(e=>!e.via_device_id&&!e.parent_device_id&&e.identifiers?.some(([e])=>e===`unraid_management_agent`));return t?{server:t.id}:{}}static properties={hass:{attribute:!1},config:{attribute:!1}};_agentStates;_agentStatesHass;_agentStatesConfig;_registryCache;_registryRequest=0;constructor(){super(),this.config={type:``}}slugifyDeviceName(e){return e.normalize(`NFKD`).replace(/[\u0300-\u036f]/g,``).toLowerCase().replace(/[^a-z0-9]+/g,`_`).replace(/^_+|_+$/g,``)}entityName(e,t){try{if(typeof this.hass?.formatEntityName==`function`){let t=this.hass.formatEntityName(e);if(typeof t==`string`&&t.trim())return t}}catch{}return t}willUpdate(e){super.willUpdate(e),this._agentStates=void 0,e.has(`config`)&&(this.config.embedded?this.setAttribute(`embedded`,``):this.removeAttribute(`embedded`))}setConfig(e){if(!e||typeof e!=`object`||Array.isArray(e)||e.type!==void 0&&typeof e.type!=`string`)throw Error(`Invalid card configuration`);this.config={type:``,...e},this.config.embedded?this.setAttribute(`embedded`,``):this.removeAttribute(`embedded`)}getCardSize(){return 4}getGridOptions(){return{columns:12,min_columns:6}}getUnraidDevices(){return this.hass?.devices?Object.values(this.hass.devices).filter(e=>!e.via_device_id&&!e.parent_device_id&&this.isUnraidDevice(e)):[]}isUnraidDevice(e){return e.identifiers?.some(([e])=>e===`unraid_management_agent`)??!1}getActiveDevice(){let e=this.getUnraidDevices();if(e.length!==0){if(this.config.server){let t=e.find(e=>e.id===this.config.server||e.name?.toLowerCase()===this.config.server?.toLowerCase()||e.name_by_user?.toLowerCase()===this.config.server?.toLowerCase());if(t)return t}return this.config.server?void 0:e[0]}}get agentStates(){if(this._agentStates&&this._agentStatesHass===this.hass&&this._agentStatesConfig===this.config)return this._agentStates;let e=this.getActiveDevice();if(!e||!this.hass?.entities)return{};let t=this.getServerDeviceIds(e.id);return this._agentStatesHass=this.hass,this._agentStatesConfig=this.config,this._agentStates=Object.fromEntries(Object.entries(this.hass.states).filter(([e])=>{let n=this.hass?.entities?.[e];return n?.platform===`unraid_management_agent`&&!!n.device_id&&t.has(n.device_id)})),this._agentStates}connectedCallback(){super.connectedCallback(),this.requestUpdate()}disconnectedCallback(){super.disconnectedCallback(),this._registryRequest+=1,this._registryCache=void 0}getServerRegistryEntries(){let e=this.hass;if(!e||!this.isConnected)return;let t=this._registryCache;if(!t||t.entities!==e.entities||t.devices!==e.devices||t.callWS!==e.callWS){t={entities:e.entities,devices:e.devices,callWS:e.callWS},this._registryCache=t;let n=++this._registryRequest;e.callWS&&this.fetchRegistryEntries(e,t,n)}let n=this.getActiveDevice();if(!t.entries||!n)return;let r=this.getServerDeviceIds(n.id);return t.entries.filter(e=>e.platform===`unraid_management_agent`&&!!e.device_id&&r.has(e.device_id))}async fetchRegistryEntries(e,t,n){let r;try{r=await e.callWS({type:`config/entity_registry/list`})}catch{}this.isConnected&&n===this._registryRequest&&t.entities===this.hass?.entities&&t.devices===this.hass?.devices&&t.callWS===this.hass?.callWS&&(t.entries=r,this.requestUpdate())}getServerDeviceIds(e){let t=new Set([e]),n=Object.values(this.hass?.devices??{}).filter(e=>this.isUnraidDevice(e)),r=!0;for(;r;){r=!1;for(let e of n)!t.has(e.id)&&(e.via_device_id&&t.has(e.via_device_id)||e.parent_device_id&&t.has(e.parent_device_id))&&(t.add(e.id),r=!0)}return t}isServerOrChildDevice(e,t){return this.getServerDeviceIds(t).has(e)}getEntity(e,t){if(!this.hass?.states)return;let n=this.getActiveDevice(),r=n?.id;if(this.hass.entities&&r){let n=this.getServerDeviceIds(r);for(let i of[!0,!1])for(let a of Object.values(this.hass.entities))if(a.device_id&&(i?a.device_id===r:n.has(a.device_id))&&a.translation_key===e&&(!t||a.entity_id.startsWith(`${t}.`))){let e=this.agentStates[a.entity_id];if(e)return e}}return Object.values(this.agentStates).find(r=>{if(t&&!r.entity_id.startsWith(`${t}.`))return!1;if(this.hass?.entities){let e=this.hass.entities[r.entity_id];if(e&&e.platform!==`unraid_management_agent`)return!1}let i=r.entity_id.split(`.`)[1]||``,a=i.endsWith(`_${e}`)||i===e||e===`uptime`&&(i.endsWith(`_up_since`)||i===`up_since`)||e===`network_interface_ip`&&i.includes(`_network_`)&&(i.endsWith(`_ip`)||i.endsWith(`_ip_address`));if(n?.name){let e=this.slugifyDeviceName(n.name);return a&&i.includes(e)}return a})}getNetworkInterfaces(){if(!this.hass?.states)return[];let e=this.getActiveDevice(),t=e?.name?this.slugifyDeviceName(e.name):void 0,n=new Map;for(let[r,i]of Object.entries(this.agentStates)){if(t&&!r.includes(t))continue;let a=this.hass.entities?.[r]?.device_id;if(e?.id&&a&&a!==e.id)continue;if(r.startsWith(`binary_sensor.`)&&r.includes(`_network_`)){if(r.includes(`_network_service_`))continue;let e=r.match(/_network_(?:([a-zA-Z0-9_-]+)_link|([a-zA-Z0-9_-]+))$/i),t=e?e[1]||e[2]:null;if(t){n.has(t)||n.set(t,{name:t,displayName:t.toUpperCase()}),n.get(t).link=i;continue}}let o=r.match(/_network_([a-zA-Z0-9_-]+)_(inbound(?:_throughput)?|outbound(?:_throughput)?|rx(?:_throughput)?|tx(?:_throughput)?|speed|ip|ip_address|link)$/i);if(!o||!o[1]||!o[2])continue;let s=o[1],c=o[2].toLowerCase();n.has(s)||n.set(s,{name:s,displayName:s.toUpperCase()});let l=n.get(s);c.startsWith(`inbound`)||c.startsWith(`rx`)?l.rx=i:c.startsWith(`outbound`)||c.startsWith(`tx`)?l.tx=i:c===`speed`?l.speed=i:c===`ip`||c===`ip_address`?l.ip=i:c===`link`&&(l.link=i)}return Array.from(n.values()).sort((e,t)=>e.name.localeCompare(t.name,void 0,{numeric:!0}))}getBootDiskEntity(){if(!this.hass?.states)return;let e=this.getActiveDevice(),t=e?.name?this.slugifyDeviceName(e.name):void 0;return Object.values(this.agentStates).find(e=>!e.entity_id.startsWith(`sensor.`)||t&&!e.entity_id.includes(t)?!1:(e.entity_id.includes(`_disk_flash_`)||e.entity_id.includes(`_disk_boot_`)||e.entity_id.endsWith(`_flash_usage`)||e.entity_id.endsWith(`_boot_usage`))&&e.entity_id.endsWith(`_usage`))}getEntities(e,t){if(!this.hass?.states)return[];let n=this.getActiveDevice(),r=n?.id;if(this.hass.entities&&r){let n=this.getServerDeviceIds(r),i=[];for(let r of Object.values(this.hass.entities)){let a=r.translation_key===e||e===`docker_container`&&(r.translation_key===`container`||r.translation_key===`container_device_running`)||e===`docker_container_autostart`&&(r.translation_key===`container_autostart`||r.translation_key===`container_device_autostart`)||e===`docker_container_restart`&&(r.translation_key===`container_restart`||r.translation_key===`container_device_restart`)||e===`virtual_machine`&&(r.translation_key===`vm`||r.translation_key===`vm_power`)||e===`virtual_machine_status`&&r.translation_key===`vm_status`||e===`vm_reboot`&&(r.translation_key===`vm_restart`||r.translation_key===`vm_reboot`);if(r.device_id&&n.has(r.device_id)&&a&&(!t||r.entity_id.startsWith(`${t}.`))){let e=this.agentStates[r.entity_id];e&&i.push(e)}}if(i.length>0)return i}let i=n?.name?this.slugifyDeviceName(n.name):void 0,a=t=>{if(this.hass?.entities){let e=this.hass.entities[t.entity_id];if(e&&e.platform!==`unraid_management_agent`)return!1}if(e===`docker_container`||e===`container`)return t.entity_id.startsWith(`switch.`)&&(t.entity_id.includes(`_container_`)||t.entity_id.includes(`_docker_`))&&!t.entity_id.includes(`_autostart`);if(e===`docker_container_autostart`||e===`container_autostart`)return t.entity_id.startsWith(`switch.`)&&(t.entity_id.includes(`_container_`)||t.entity_id.includes(`_docker_`))&&t.entity_id.includes(`_autostart`);if(e===`docker_container_restart`||e===`container_restart`)return t.entity_id.startsWith(`button.`)&&(t.entity_id.includes(`_container_`)||t.entity_id.includes(`_docker_`))&&(t.entity_id.includes(`_restart`)||t.entity_id.includes(`_reboot`));if(e===`virtual_machine`||e===`vm`)return t.entity_id.startsWith(`switch.`)&&(t.entity_id.includes(`_vm_`)||t.entity_id.includes(`_virtual_machine_`));if(e===`virtual_machine_status`||e===`vm_status`)return t.entity_id.startsWith(`sensor.`)&&(t.entity_id.includes(`_vm_`)||t.entity_id.includes(`_virtual_machine_`))&&t.entity_id.endsWith(`_status`);if(e===`vm_reboot`||e===`vm_restart`)return t.entity_id.startsWith(`button.`)&&(t.entity_id.includes(`_vm_`)||t.entity_id.includes(`_virtual_machine_`))&&(t.entity_id.includes(`_restart`)||t.entity_id.includes(`_reboot`));if(e===`disk_usage`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`)||t.entity_id.includes(`_boot`)||t.entity_id.includes(`_flash`))&&t.entity_id.endsWith(`_usage`)&&!t.entity_id.includes(`_array_usage`)&&!t.entity_id.includes(`_share_`);if(e===`disk_temperature`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`)||t.entity_id.includes(`_boot`))&&(t.entity_id.endsWith(`_temperature`)||t.entity_id.includes(`_temp`));if(e===`disk_spin`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`))&&t.entity_id.includes(`_spin`);if(e===`disk_health`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`)||t.entity_id.includes(`_boot`))&&(t.entity_id.endsWith(`_health`)||t.entity_id.includes(`_health_`));if(e===`share_usage`||e===`share`)return t.entity_id.includes(`_share_`)&&t.entity_id.endsWith(`_usage`);let n=t.entity_id.split(`.`)[1]||``;return n===e||n.endsWith(`_${e}`)||n.includes(`_${e}_`)||n.startsWith(`${e}_`)},o=Object.values(this.agentStates),s=t?o.filter(e=>e.entity_id.startsWith(`${t}.`)):o;return i?s.filter(e=>e.entity_id.includes(i)&&a(e)):s.filter(e=>a(e))}findEntity(e){if(this.hass?.states)return typeof e==`string`?this.agentStates[e]:Object.values(this.agentStates).find(t=>e.test(t.entity_id))}async toggleEntity(e){if(!this.hass||!this.agentStates[e])return;let t=e.split(`.`)[0]||`homeassistant`;await this.hass.callService(t,`toggle`,{entity_id:e})}async pressButton(e){this.hass&&this.agentStates[e]&&await this.hass.callService(`button`,`press`,{entity_id:e})}openMoreInfo(e){W(this,`hass-more-info`,{entityId:e})}navigate(e,t=!1){e&&(t?window.history.replaceState(null,``,e):window.history.pushState(null,``,e),W(window,`location-changed`,{replace:t}))}renderHeader(e,t,n,r){return this.config.embedded||this.config.hide_header?z:L`
      <div class="header">
        <div class="header-main">
          <div class="header-icon">${K(n,22)}</div>
          <div class="header-titles">
            <span class="header-title">${e}</span>
            <span class="header-subtitle">${t}</span>
          </div>
        </div>
        ${r?L`<div class="header-actions">${r}</div>`:``}
      </div>
    `}},Mt={server:`Unraid Management Agent server`,title:`Custom title`,view_mode:`Default view`,show_system_info:`Show system details`},Y=class extends U{static properties={hass:{attribute:!1},_config:{state:!0}};static styles=o`
    .card-config {
      display: flex;
      flex-direction: column;
      gap: var(--ha-space-4, 16px);
      padding-block: var(--ha-space-2, 8px);
      color: var(--primary-text-color);
    }
  `;_computeLabel=e=>Mt[e.name]??e.name;_computeHelper=e=>e.name===`server`?`Only servers provided by Unraid Management Agent are listed.`:void 0;setConfig(e){this._config={...e}}_valueChanged(e){if(e.stopPropagation(),!this._config)return;let t={...this._config,...e.detail.value};for(let e of[`server`,`title`])t[e]===``&&delete t[e];this._config=t,W(this,`config-changed`,{config:t})}render(){if(!this._config||!this.hass)return L``;let e=Object.values(this.hass.devices??{}).filter(e=>!e.via_device_id&&!e.parent_device_id&&e.identifiers?.some(([e])=>e===`unraid_management_agent`)),t=this._config.server?e.find(e=>e.id===this._config?.server||e.name?.toLowerCase()===this._config?.server?.toLowerCase()||e.name_by_user?.toLowerCase()===this._config?.server?.toLowerCase()):void 0,n=t?.id??this._config.server??``,r=[{value:``,label:`Automatically select an Agent server`},...e.map(e=>({value:e.id,label:e.name_by_user||e.name||e.id}))];n&&!t&&r.push({value:n,label:`Unavailable Agent server: ${n}`});let i=[{name:`server`,selector:{select:{options:r,mode:`dropdown`}}},{name:`title`,selector:{text:{}}},...this._config.type.includes(`docker`)?[{name:`view_mode`,selector:{select:{options:[{value:`grid`,label:`Grid`},{value:`list`,label:`List`}],mode:`dropdown`}}}]:[],...this._config.type.includes(`server`)||this._config.type.includes(`dashboard`)?[{name:`show_system_info`,selector:{boolean:{}}}]:[]];return L`
      <div class="card-config">
        ${e.length===0?L`<ha-alert alert-type="info">No Unraid Management Agent server is available. Set up the integration to display its data.</ha-alert>`:z}
        <ha-form
          .hass=${this.hass}
          .schema=${i}
          .data=${{...this._config,server:n,title:this._config.title??``,...i.some(e=>e.name===`view_mode`)?{view_mode:this._config.view_mode??`grid`}:{},...i.some(e=>e.name===`show_system_info`)?{show_system_info:this._config.show_system_info!==!1}:{}}}
          .computeLabel=${this._computeLabel}
          .computeHelper=${this._computeHelper}
          @value-changed=${this._valueChanged}
        ></ha-form>
      </div>
    `}},Nt=class extends Y{},Pt=class extends Y{},Ft=class extends Y{},It=class extends Y{},Lt=class extends Y{},Rt=class extends Y{},zt=class extends Y{},Bt=class extends Y{},Vt=class extends Y{},Ht=class extends Y{},Ut=class extends Y{},Wt=class extends Y{},Gt=class extends Y{},Kt=class extends Y{},qt=class extends Y{};function Jt(e,t){if(!customElements.get(e))try{customElements.define(e,t)}catch(n){if(n instanceof Error&&(n.name===`NotSupportedError`||n.message.includes(`already been registered`))){class n extends t{}customElements.define(e,n)}else throw n}}function X(e){Jt(e.tag,e.card),Jt(e.editorTag,e.editor),window.customCards??=[],window.customCards.some(t=>t.type===e.tag)||window.customCards.push({type:e.tag,name:e.name.replace(/^Unraid /,`Unraid Management Agent `),description:e.description,preview:!0,documentationURL:`https://github.com/tinkerologie/ha-unraid-management-agent`})}X({tag:Se,editorTag:Ce,card:class extends J{static editorTag=Ce;formatUptime(e){if(!e)return`Unknown`;let t=e.trim(),n=0;if(/^\d+(\.\d+)?$/.test(t))n=Math.floor(Number(t));else{let t=new Date(e);if(!isNaN(t.getTime()))n=Math.max(0,Math.floor((Date.now()-t.getTime())/1e3));else return e}let r=Math.floor(n/86400),i=Math.floor(n%86400/3600),a=Math.floor(n%3600/60);return r>0?`${r}d ${i}h`:i>0?`${i}h ${a}m`:`${a}m`}render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getEntity(`cpu_usage`),r=this.getEntity(`ram_usage`),i=this.getEntity(`array_usage`),a=this.getEntity(`array_state`),o=this.getEntity(`array_started`,`binary_sensor`),s=this.getEntity(`system_temperature`)||this.getEntity(`temperature_average`)||this.getEntity(`cpu_temperature`),c=this.getEntity(`cpu_power`),l=this.getEntity(`uptime`),u=this.getEntity(`notifications_unread_alert`),d=this.getEntity(`network_interface_ip`),f=Math.round(Number(n?.state)||0),p=Math.round(Number(r?.state)||0),m=Math.round(Number(i?.state)||0),h=a?.state?.toLowerCase().trim(),g=o?o.state===`on`:h===`started`||h===`normal`,_=Number(u?.state)||0,v=n?.attributes?.cpu_model||(e?.model??`Multi-Core CPU`),y=r?.attributes?.used||``,b=r?.attributes?.total||``,x=i?.attributes?.capacity_used||``,S=i?.attributes?.capacity_total||``,C=this.getNetworkInterfaces(),w=C.length>0?C[0]:void 0,T=w?.speed?.state||w?.link?.attributes?.speed_mbps||w?.rx?.attributes?.network_speed,E=T==null?void 0:Number(T),D=E?E>=1e3?`${E/1e3} Gbps`:`${E} Mbps`:``,O=q(w?.rx),k=q(w?.tx),ee=O===`--`?``:O,te=k===`--`?``:k,A=ee&&te?`↓ ${ee} • ↑ ${te}`:D||`Active`,j=this.getBootDiskEntity(),M=j?.attributes,N=M?.used||M?.used_size||M?.fs_used,ne=M?.total||M?.total_size||M?.fs_size,P=M?.device||M?.vendor,F=N&&ne?`Flash (${N} / ${ne})`:P?`Flash (${P})`:`Flash (USB)`,re=M?.filesystem?`Device: ${P||`USB`} • FS: ${M.filesystem}`:`USB Flash Boot Drive`,ie=L`
      <span class="badge ${g?`badge-online`:`badge-error`}">
        <span class="pulse-dot"></span>
        <span>Array ${a?.state||(g?`Started`:`Stopped`)}</span>
      </span>
      ${_>0?L`
            <span class="badge badge-error">
              ${K(G,13)}
              <span>${_}</span>
            </span>
          `:z}
    `;return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(t,`${e?.model||`Unraid OS`} • Up ${this.formatUptime(l?.state)}`,vt,ie)}
        <div class="rings-grid">
          <button
            type="button"
            ?disabled=${!n}
            class="interactive ring-card"
            @click=${()=>n&&this.openMoreInfo(n.entity_id)}
            title="Click to view CPU details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${f}; --ring-color: ${f>80?`var(--unraid-error)`:f>50?`var(--unraid-warning)`:`var(--unraid-online)`}"
            >
              <span class="ring-content ltr-value">${f}%</span>
            </span>
            <span class="ring-label">CPU Load</span>
            <span class="ring-subtext">
              ${s?.state?`${s.state}°C`:``}${c?.state?` • ${c.state}W`:``}
            </span>
          </button>
          <button
            type="button"
            ?disabled=${!r}
            class="interactive ring-card"
            @click=${()=>r&&this.openMoreInfo(r.entity_id)}
            title="Click to view Memory details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${p}; --ring-color: ${p>85?`var(--unraid-error)`:`var(--unraid-info)`}"
            >
              <span class="ring-content ltr-value">${p}%</span>
            </span>
            <span class="ring-label">Memory</span>
            <span class="ring-subtext">${y&&b?`${y} / ${b}`:`${p}% used`}</span>
          </button>
          <button
            type="button"
            ?disabled=${!i}
            class="interactive ring-card"
            @click=${()=>i&&this.openMoreInfo(i.entity_id)}
            title="Click to view Array storage details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${m}; --ring-color: var(--unraid-accent)"
            >
              <span class="ring-content ltr-value">${m}%</span>
            </span>
            <span class="ring-label">Array Storage</span>
            <span class="ring-subtext">${x&&S?`${x} / ${S}`:`${m}% used`}</span>
          </button>
        </div>

        ${this.config.show_system_info===!1?z:L`
              <div class="divider"></div>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">Processor</span>
                  <span class="detail-val" title="${v}">${v}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">OS Version</span>
                  <span class="detail-val ltr-value">${e?.sw_version||`Unraid OS`}</span>
                </div>
                <button
                  type="button"
                  ?disabled=${!l}
                  class="interactive detail-item"
                  @click=${()=>l&&this.openMoreInfo(l.entity_id)}
                  title="Click to view Uptime details"
                >
                  <span class="detail-label">System Uptime</span>
                  <span class="detail-val">${this.formatUptime(l?.state)}</span>
                </button>
                <button
                  type="button"
                  ?disabled=${!(w?.rx||d)}
                  class="interactive detail-item"
                  @click=${()=>w?.rx?this.openMoreInfo(w.rx.entity_id):d&&this.openMoreInfo(d.entity_id)}
                  title="Click to view Network details"
                >
                  <span class="detail-label">Primary Network</span>
                  <span class="detail-val ltr-value" title="${w?`${w.name} • ${D}`:`Connected`}">
                    ${w?`${w.name}: `:``}${w?.ip?.state||d?.state||`Connected`}
                  </span>
                </button>
                <button
                  type="button"
                  ?disabled=${!(w?.rx||w?.speed)}
                  class="interactive detail-item"
                  @click=${()=>w?.rx?this.openMoreInfo(w.rx.entity_id):w?.speed&&this.openMoreInfo(w.speed.entity_id)}
                  title="Click to view Network traffic details"
                >
                  <span class="detail-label">Network Traffic</span>
                  <span class="detail-val ltr-value" title="${D?`Link Speed: ${D}`:`Network Speed`}">${A}</span>
                </button>
                <button
                  type="button"
                  ?disabled=${!j}
                  class="interactive detail-item"
                  @click=${()=>j&&this.openMoreInfo(j.entity_id)}
                  title="Click to view Boot device details"
                >
                  <span class="detail-label">Boot Device</span>
                  <span class="detail-val" title="${re}">${F}</span>
                </button>
                <button
                  type="button"
                  ?disabled=${!u}
                  class="interactive detail-item"
                  @click=${()=>u&&this.openMoreInfo(u.entity_id)}
                  title="Click to view Notifications"
                >
                  <span class="detail-label">System Health</span>
                  <span class="detail-val" style="color: ${_===0?`var(--unraid-online)`:`var(--unraid-error)`}">
                    ${_===0?`Normal • Healthy`:`${_} Active Alerts`}
                  </span>
                </button>
              </div>
            `}
      </div>
      </ha-card>
    `}},editor:Nt,name:`Unraid Server Overview Card`,description:`Server metrics, CPU/RAM ring gauges, and hardware health.`});function Yt(e){if(e.spin_state!==void 0)return e.spin_state===`active`;if(e.spinning!==void 0)return!!e.spinning;if(e.standby!==void 0)return!e.standby}function Xt(e){let t=typeof e==`number`?e:parseFloat(String(e));return isNaN(t)?void 0:t}function Zt(e){let t=e.toLowerCase().trim();return t===`on`||t.startsWith(`fail`)?`error`:[`unknown`,`unavailable`,`none`,``].includes(t)?`unknown`:`healthy`}function Qt(e,t){let n=e.trim(),r=n.match(/^(?:.*?\s+)?(?:Disk\s+)?([a-zA-Z0-9_-]+)(?:\s+(?:usage|health|temperature|temp|spin|errors))?$/i);if(r&&r[1]){let e=r[1],t=e.match(/^disk[_\s]?(\d+)$/i);if(t)return`Disk ${t[1]}`;if(/^\d+$/.test(e))return`Disk ${e}`;if(e.toLowerCase()===`parity`)return`Parity`;let n=e.match(/^parity[_\s]?(\d+)$/i);return n?`Parity ${n[1]}`:e.toLowerCase()===`cache`?`Cache`:e.toLowerCase().startsWith(`cache_`)?`Cache (${e.slice(6).toUpperCase()})`:e.toLowerCase()===`boot`||e.toLowerCase()===`flash`?`Flash (Boot)`:e.replace(/\b\w/g,e=>e.toUpperCase())}return n||t}function Z(e){let t=(e.split(`.`)[1]||``).replace(/^.*?_disk_/,``).replace(/_usage$|_temperature$|_temp$|_errors$|_health$|_spin$/,``).toLowerCase().replace(/_/g,``),n=t.match(/^(?:disk)?(\d+)$/);return n?`disk${n[1]}`:t}X({tag:we,editorTag:Te,card:class extends J{static editorTag=Te;getDisks(){let e=this.getEntities(`disk_usage`),t=this.getEntities(`disk_health`),n=this.getEntities(`disk_temperature`),r=this.getEntities(`disk_error_count`),i=this.getEntities(`disk_spin`,`switch`),a=new Map;for(let t of e){let e=Z(t.entity_id),n=Qt(this.entityName(t,t.attributes.friendly_name||e),e),r=n.toLowerCase().includes(`parity`),i=n.toLowerCase().includes(`cache`)||n.toLowerCase().includes(`pool`),o=n.toLowerCase().includes(`boot`)||n.toLowerCase().includes(`flash`),s=Yt(t.attributes)??!1,c=t.attributes.temperature_celsius??t.attributes.temperature,l=Number(t.attributes.num_errors??0),u=t.attributes.status||`DISK_OK`;a.set(e,{id:e,name:n,isParity:r,isCache:i,isBoot:o,usagePct:Math.round(Number(t.state)||0),temp:c==null?`*`:`${c}°C`,tempNum:typeof c==`number`?c:void 0,errors:l,health:`healthy`,statusText:u,isSpinning:s,freeSpace:t.attributes.free,totalSpace:t.attributes.total})}for(let e of t){let t=Z(e.entity_id);if(a.has(t)||/^disk_np/i.test(e.state)||t.includes(`disabled`)||t.includes(`missing`)||t.includes(`invalid`))continue;let n=Qt(this.entityName(e,e.attributes.friendly_name||t),t),r=n.toLowerCase().includes(`parity`),i=n.toLowerCase().includes(`cache`),o=n.toLowerCase().includes(`boot`),s=Yt(e.attributes)??!1,c=Xt(e.attributes.temperature),l=e.attributes.status||`DISK_OK`;a.set(t,{id:t,name:n,isParity:r,isCache:i,isBoot:o,usagePct:0,temp:c==null?`*`:`${c}°C`,tempNum:typeof c==`number`?c:void 0,errors:0,health:Zt(e.state),statusText:l,isSpinning:s})}for(let e of n){let t=Z(e.entity_id),n=a.get(t);n&&e.state!==`unavailable`&&e.state!==`unknown`&&(n.temp=`${e.state}°C`,n.tempNum=parseFloat(e.state))}for(let e of r){let t=Z(e.entity_id),n=a.get(t);if(n){let t=Number(e.state);isNaN(t)||(n.errors=t)}}for(let e of i){let t=Z(e.entity_id),n=a.get(t);n&&(n.isSpinning=e.state===`on`,n.spinEntityId=e.entity_id)}for(let e of t){let t=Z(e.entity_id),n=a.get(t);if(n){e.attributes.status&&(n.statusText=e.attributes.status),n.isSpinning=Yt(e.attributes)??n.isSpinning;let t=Xt(e.attributes.temperature);t!==void 0&&n.temp===`*`&&(n.temp=`${t}°C`,n.tempNum=t),n.health=Zt(e.state)}}for(let e of a.values()){let t=(e.statusText||``).toUpperCase(),n=t.includes(`ERR`)||t.includes(`WRONG`)||t.includes(`INVALID`)||t.includes(`DSBL`)||t.includes(`FAIL`);e.health===`error`||n||e.errors>=10?e.health=`error`:e.errors>0||e.tempNum!==void 0&&e.tempNum>45?e.health=`warning`:e.health!==`unknown`&&(e.health=`healthy`)}return Array.from(a.values()).sort((e,t)=>e.isParity===t.isParity?e.isBoot===t.isBoot?e.isCache===t.isCache?e.name.localeCompare(t.name,void 0,{numeric:!0}):e.isCache?1:-1:e.isBoot?1:-1:e.isParity?-1:1)}isUsable(e){if(!e||!e.state)return!1;let t=e.state.toLowerCase().trim();return t!==`unavailable`&&t!==`unknown`&&t!==`none`&&t!==`--`}getParityViewState(){let e=this.getEntity(`parity_valid`,`binary_sensor`),t=this.getEntity(`parity_check_running`,`binary_sensor`),n=this.getEntity(`parity_status`,`binary_sensor`)??this.getEntity(`parity_status`),r=this.getEntity(`parity_progress`),i=`unknown`;if(this.isUsable(e)){let t=e.state.toLowerCase().trim();t===`off`?i=`valid`:t===`on`&&(i=`invalid`)}else if(this.isUsable(n)){let e=n.state.toLowerCase().trim();if(e===`off`)i=`valid`;else if(e===`on`){let e=String(n.attributes?.status??``).toLowerCase().trim();e!==`running`&&e!==`paused`&&(i=`invalid`)}}let a=`unknown`;if(this.isUsable(t)){let e=t.state.toLowerCase().trim();e===`off`?a=`idle`:e===`on`&&(a=String(t.attributes?.status??``).toLowerCase().trim()===`paused`?`paused`:`running`)}else if(this.isUsable(n)){let e=String(n.attributes?.status??``).toLowerCase().trim();e===`running`?a=`running`:e===`paused`?a=`paused`:n.state.toLowerCase().trim()===`off`&&(a=`idle`)}let o=0;if(this.isUsable(r)){let e=Number(r.state);isNaN(e)||(o=Math.round(e))}return{validity:i,activity:a,progressPct:o}}render(){let e=this.getEntity(`array_usage`),t=this.getEntity(`parity_check`,`switch`),n=this.getEntity(`last_parity_check_date`)||this.getEntity(`last_parity_check`),r=this.getEntity(`last_parity_check_errors`),i=Math.round(Number(e?.state)||0),a=e?.attributes?.capacity_used||``,o=e?.attributes?.capacity_total||``,s=e?.attributes?.capacity_free||``,{validity:c,activity:l,progressPct:u}=this.getParityViewState(),d=l===`running`||l===`paused`,f=`badge-standby`,p=`Parity Status Unknown`,m=bt;c===`valid`?(f=`badge-online`,p=`Parity Valid`,m=xt):c===`invalid`&&(f=`badge-warning`,p=`Parity Check Needed`,m=bt);let h=this.getDisks(),g=L`
      <span class="badge ${f}">
        ${K(m,13)}
        <span>${p}</span>
      </span>
    `,_;_=l===`running`?`Parity Check In Progress (${u}%)`:l===`paused`?`Parity Check Paused (${u}%)`:c===`valid`?`Parity Status: Valid`:c===`invalid`?`Parity Status: Check Needed`:`Parity Status: Unknown`;let v=c===`valid`||d?et:G,y=c===`valid`||d?`var(--unraid-online)`:`var(--unraid-warning)`,b=this.isUsable(n),x=Number(r?.state),S=this.isUsable(r)&&!isNaN(x)&&x>0,C=``;if(b){let e=n.attributes?.result&&n.attributes.result!==`Completed`?` (${n.attributes.result})`:``;C=`Last check: ${jt(n.state)}${e}`}else c===`valid`&&(C=`Parity healthy`);let w=S?` • ${r.state} errors`:``,T=!!(C||w);return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(this.config.title||`Storage Array & Disks`,`${a||`${i}%`} used of ${o||`Array`}${s?` (${s} Free)`:``}`,ut,g)}
        <div style="display: flex; flex-direction: column; gap: var(--ha-space-1, 4px);">
          <div style="display: flex; justify-content: space-between; font-size: var(--ha-font-size-s, 12px); font-weight: var(--ha-font-weight-bold, 600);">
            <span>Array Capacity</span>
            <span>${i}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${i}%;"></div>
          </div>
        </div>
        <div class="list-row" style="background: color-mix(in srgb, var(--unraid-text) 5%, transparent);">
          <div class="row-left">
            <div style="color: ${y}">
              ${K(v,18)}
            </div>
            <div style="display: flex; flex-direction: column; min-width: 0;">
              <span style="font-weight: var(--ha-font-weight-bold, 600); font-size: var(--ha-font-size-s, 12px);">
                ${_}
              </span>
              ${T?L`
                    <span style="font-size: var(--ha-font-size-s, 12px); color: var(--unraid-subtext);">
                      ${C}${w}
                    </span>
                  `:z}
            </div>
          </div>
          <div class="row-right">
            ${t?L`
                  <button
                    class="btn ${d?`btn`:`btn-primary`}"
                    @click=${()=>this.toggleEntity(t.entity_id)}
                  >
                    ${K(d?St:ht,14)}
                    <span>${d?`Cancel`:`Check Now`}</span>
                  </button>
                `:z}
          </div>
        </div>
        <div class="item-list">
          ${h.length>0?h.map(e=>{let t=e.tempNum??parseFloat(e.temp),n=e.isSpinning&&!isNaN(t)&&e.temp!==`*`&&e.temp!==`unavailable`,r=n?t>45?`var(--unraid-error)`:t>36?`var(--unraid-warning)`:`var(--unraid-online)`:`var(--unraid-standby)`,i=n?`${Math.round(t)}°C`:`--`,a=e.health===`unknown`?L`
                      <span
                        class="badge badge-standby"
                        style="font-size: var(--ha-font-size-s, 12px);"
                        title="SMART status can't be read, usually because the disk is spun down"
                      >
                        <span>Unknown</span>
                      </span>
                    `:e.health===`healthy`?L`
                      <span class="badge badge-online" style="font-size: var(--ha-font-size-s, 12px); gap: var(--ha-space-1, 4px);">
                        ${K(et,11)}
                        <span>Healthy</span>
                      </span>
                    `:e.health===`warning`?L`
                      <span class="badge badge-warning" style="font-size: var(--ha-font-size-s, 12px); gap: var(--ha-space-1, 4px);">
                        ${K(G,11)}
                        <span>Warning${e.errors>0?` (${e.errors})`:``}</span>
                      </span>
                    `:L`
                      <span class="badge badge-error" style="font-size: var(--ha-font-size-s, 12px); gap: var(--ha-space-1, 4px);">
                        ${K(G,11)}
                        <span>Error${e.errors>0?` (${e.errors})`:``}</span>
                      </span>
                    `;return L`
                  <div class="list-row">
                    <div class="row-left">
                      ${e.isBoot?L`
                            <span
                              class="badge badge-online"
                              style="font-size: var(--ha-font-size-s, 12px); gap: var(--ha-space-1, 4px); min-width: 60px; justify-content: center;"
                              title="USB Flash Boot Drive"
                            >
                              ${K(wt,11)}
                              <span>Flash</span>
                            </span>
                          `:e.spinEntityId?L`
                            <button
                              class="badge ${e.isSpinning?`badge-online`:`badge-standby`}"
                              style="cursor: pointer; border: none;"
                              title="Click to spin ${e.isSpinning?`down`:`up`}"
                              @click=${()=>this.toggleEntity(e.spinEntityId)}
                            >
                              <span class="status-dot ${e.isSpinning?`online`:`offline`}"></span>
                              <span>${e.isSpinning?`Active`:`Standby`}</span>
                            </button>
                          `:L`
                            <span class="badge ${e.isSpinning?`badge-online`:`badge-standby`}">
                              <span>${e.isSpinning?`Active`:`Standby`}</span>
                            </span>
                          `}

                      <span style="font-weight: var(--ha-font-weight-bold, 600); min-width: 0; flex: 1 1 75px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${e.name}
                      </span>
                    </div>

                    <div class="row-right">
                      <span
                        class="badge"
                        style="color: ${e.isBoot?`var(--unraid-subtext)`:r}; background: color-mix(in srgb, ${e.isBoot?`var(--unraid-subtext)`:r} 12%, transparent); min-width: 44px; justify-content: center;"
                        title="${e.isBoot?`USB Flash Drive`:e.isSpinning?`Temperature: ${i}`:`Disk is in standby`}"
                      >
                        ${e.isBoot?`--`:i}
                      </span>
                      ${a}
                      <div style="display: flex; align-items: center; gap: var(--ha-space-2, 8px); flex: 1 1 85px; min-width: 0;">
                        ${e.isParity?L`
                              <span class="ltr-value" style="font-size: var(--ha-font-size-s, 12px); color: var(--unraid-online); font-weight: var(--ha-font-weight-medium, 500); font-family: var(--ha-font-family-code, monospace);">
                                Parity
                              </span>
                            `:L`
                              <div class="progress-bar" style="height: 4px; flex: 1;">
                                <div
                                  class="progress-fill"
                                  style="width: ${e.usagePct}%; background: ${e.isBoot?`var(--unraid-warning)`:e.isCache?`var(--unraid-info)`:`var(--unraid-accent)`};"
                                ></div>
                              </div>
                              <span class="ltr-value" style="font-size: var(--ha-font-size-s, 12px); font-family: var(--ha-font-family-code, monospace); color: var(--unraid-subtext);">
                                ${e.usagePct}%
                              </span>
                            `}
                      </div>
                    </div>
                  </div>
                `}):L`<div style="text-align: center; color: var(--unraid-subtext); font-size: var(--ha-font-size-s, 12px); padding: var(--ha-space-3, 12px);">No disk devices found</div>`}
        </div>
      </div>
      </ha-card>
    `}},editor:Pt,name:`Unraid Storage & Disks Card`,description:`Array capacity, parity checks, and interactive disk tray with spin state controls.`});function $t(e,t){let n=e.trim(),r=n.match(/^(?:.*?\s+)?Share\s+(.+?)(?:\s+usage)?$/i);return r&&r[1]?r[1].trim():(n=n.replace(/\s+usage$/i,``).replace(/_usage$/i,``).replace(/\s+share$/i,``).replace(/_share$/i,``).trim(),n||t)}X({tag:Me,editorTag:Ne,card:class extends J{static editorTag=Ne;static properties={...J.properties,_searchQuery:{state:!0}};constructor(){super(),this._searchQuery=``}getShares(){let e=this.getEntities(`share_usage`),t=[];for(let n of e){let e=(n.entity_id.split(`.`)[1]||``).replace(/^.*?_share_/,``).replace(/_usage$/,``),r=$t(this.entityName(n,n.attributes.friendly_name||e),e),i=n.attributes.color||``,a=i===`green-on`;t.push({id:e,name:r,entityId:n.entity_id,usagePct:Math.min(100,Math.max(0,Math.round(Number(n.state)||0))),used:n.attributes.used_size||n.attributes.used||``,total:n.attributes.total_size||n.attributes.total||``,free:n.attributes.free_size||n.attributes.free||``,isProtected:a,color:i,allocator:n.attributes.allocator})}return t.sort((e,t)=>e.name.localeCompare(t.name,void 0,{numeric:!0}))}_openMoreInfo(e){W(this,`hass-more-info`,{entityId:e})}render(){let e=this.getShares(),t=this._searchQuery?e.filter(e=>e.name.toLowerCase().includes(this._searchQuery.toLowerCase())):e,n=e.filter(e=>e.isProtected).length,r=e.length-n,i=L`
      <span class="badge ${r===0?`badge-online`:`badge-warning`}">
        ${K(r===0?xt:bt,13)}
        <span>${n} Protected${r>0?` • ${r} Unprotected`:``}</span>
      </span>
    `;return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(this.config.title||`User Shares`,`${e.length} configured shares`,lt,i)}
        ${e.length>4?L`
              <div style="margin-block-end: var(--ha-space-1, 4px);">
                <input
                  type="text"
                  placeholder="Filter shares..."
                  style="
                    width: 100%;
                    padding: var(--ha-space-2, 8px) var(--ha-space-2, 8px);
                    border-radius: var(--ha-border-radius-md, 8px);
                    border: 1px solid var(--unraid-border);
                    background: color-mix(in srgb, var(--unraid-text) 4%, transparent);
                    color: var(--unraid-text);
                    font-size: var(--ha-font-size-s, 12px);
                    box-sizing: border-box;
                  "
                  .value=${this._searchQuery}
                  @input=${e=>this._searchQuery=e.target.value}
                />
              </div>
            `:z}
        <div class="item-list">
          ${t.length>0?t.map(e=>{let t=e.usagePct>90?`var(--unraid-error)`:e.usagePct>75?`var(--unraid-warning)`:`var(--unraid-online)`;return L`
                  <button
                    type="button"
                    class="interactive list-row"
                    title="Click for details on ${e.name}"
                    @click=${()=>this._openMoreInfo(e.entityId)}
                  >
                    <span data-block class="row-left">
                      <span data-block
                        style="color: ${e.isProtected?`var(--unraid-accent)`:`var(--unraid-warning)`}; display: flex; align-items: center;"
                      >
                        ${K(lt,18)}
                      </span>

                      <span data-block style="display: flex; flex-direction: column; min-width: 0;">
                        <span data-block style="display: flex; align-items: center; gap: var(--ha-space-2, 8px);">
                          <span
                            style="font-weight: var(--ha-font-weight-bold, 600); font-size: var(--ha-font-size-s, 12px); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
                          >
                            ${e.name}
                          </span>
                          <span
                            class="badge ${e.isProtected?`badge-online`:`badge-warning`}"
                            style="font-size: var(--ha-font-size-s, 12px); padding: 1px var(--ha-space-2, 8px);"
                            title="${e.isProtected?`Data protected on parity array`:`Data on pool / unprotected storage`}"
                          >
                            ${e.isProtected?`Protected`:`Unprotected`}
                          </span>
                        </span>

                        ${e.used&&e.total?L`<span style="font-size: var(--ha-font-size-s, 12px); color: var(--unraid-subtext);">${e.used} / ${e.total}${e.free?` • ${e.free} free`:``}</span>`:z}
                      </span>
                    </span>

                    <span data-block class="row-right">
                      <span data-block style="display: flex; align-items: center; gap: var(--ha-space-2, 8px); width: 110px;">
                        <span data-block class="progress-bar" style="height: 6px; flex: 1;">
                          <span data-block
                            class="progress-fill"
                            style="width: ${e.usagePct}%; background: ${t};"
                          ></span>
                        </span>
                        <span
                          style="font-size: var(--ha-font-size-s, 12px); font-family: var(--ha-font-family-code, monospace); font-weight: var(--ha-font-weight-bold, 600); color: var(--unraid-text); min-width: 32px; text-align: end;"
                        >
                          ${e.usagePct}%
                        </span>
                      </span>
                    </span>
                  </button>
                `}):L`
                <div style="text-align: center; color: var(--unraid-subtext); font-size: var(--ha-font-size-s, 12px); padding: var(--ha-space-4, 16px);">
                  ${e.length===0?`No user shares found`:`No shares matching filter`}
                </div>
              `}
        </div>
      </div>
      </ha-card>
    `}},editor:Ft,name:`Unraid User Shares Card`,description:`User share storage utilization, capacity allocation, and parity protection status.`}),X({tag:Pe,editorTag:Fe,card:class extends J{static editorTag=Fe;isValidIp(e){return!!e&&![`unavailable`,`unknown`,`none`,`--`].includes(e.toLowerCase().trim())}formatSpeed(e){if(!e)return``;let t=e.toLowerCase().trim();if([`unavailable`,`unknown`,`none`,`--`].includes(t))return``;let n=Number(e);return isNaN(n)?e:n>=1e3?`${n/1e3} Gbps`:`${n} Mbps`}handleMoreInfo(e){e&&W(this,`hass-more-info`,{entityId:e})}sanitizeHttpUrl(e){if(typeof e==`string`&&e.trim())try{let t=new URL(e);if(t.protocol===`http:`||t.protocol===`https:`)return t.toString()}catch{}}render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getNetworkInterfaces(),r=this.getEntity(`network_access`),i=r?.attributes,a=this.sanitizeHttpUrl(i?.LAN_IPv4_ipv4)||this.sanitizeHttpUrl(r?.state),o=this.sanitizeHttpUrl(i?.FQDN_LAN_ipv4),s=n.filter(e=>e.link?.state===`on`||this.isValidIp(e.ip?.state)).length,c=L`
      <span class="badge ${s>0?`badge-online`:`badge-error`}">
        <span class="pulse-dot"></span>
        <span>${s} Connected</span>
      </span>
    `;return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(this.config.title||`${t} Network`,`${e?.model||`Unraid`} • ${n.length} Interface${n.length===1?``:`s`}`,pt,c)}
        <div class="item-list">
          ${n.length>0?n.map(e=>{let t=e.link?.state===`on`||this.isValidIp(e.ip?.state),n=e.rx?.attributes?.network_ip,r=this.isValidIp(e.ip?.state)?e.ip.state:this.isValidIp(n)?n:`--`,i=e.ip?.attributes?.mac_address||e.link?.attributes?.mac_address||``,a=e.link?.attributes?.mtu||e.ip?.attributes?.mtu||void 0,o=e.speed?.state||e.link?.attributes?.speed_mbps||e.rx?.attributes?.network_speed,s=this.formatSpeed(o==null?void 0:String(o)),c=q(e.rx),l=q(e.tx),u=e.rx?.attributes?.total_received||``,d=e.tx?.attributes?.total_sent||``,f=e.ip?.entity_id||e.rx?.entity_id||e.link?.entity_id;return L`
                  <button
                    type="button"
                    class="interactive list-row network-row"
                    style="flex-direction: column; align-items: stretch; gap: var(--ha-space-2, 8px); padding: var(--ha-space-3, 12px) var(--ha-space-3, 12px);"
                    title="Click for details on ${e.name}"
                    @click=${()=>this.handleMoreInfo(f)}
                  >
                    <span data-block style="display: flex; flex-wrap: wrap; gap: var(--ha-space-1, 4px); align-items: center; justify-content: space-between;">
                      <span data-block class="row-left" style="gap: var(--ha-space-2, 8px);">
                        <span class="badge ${t?`badge-online`:`badge-error`}" style="min-width: 50px; justify-content: center;">
                          ${K(at,13)}
                          <span class="ltr-value">${e.name}</span>
                        </span>
                        <span class="ltr-value" style="font-weight: var(--ha-font-weight-bold, 600); font-size: var(--ha-font-size-m, 14px);">
                          ${r}
                        </span>
                      </span>

                      <span data-block class="row-right" style="gap: var(--ha-space-2, 8px);">
                        ${s?L`
                              <span
                                class="badge ltr-value"
                                style="color: var(--unraid-info); background: color-mix(in srgb, var(--unraid-info) 12%, transparent); font-weight: var(--ha-font-weight-bold, 600); font-size: var(--ha-font-size-s, 12px);"
                              >
                                ${s}
                              </span>
                            `:z}
                        <span
                          class="badge ${t?`badge-online`:`badge-standby`}"
                          style="font-size: var(--ha-font-size-s, 12px);"
                        >
                          ${t?`Up`:`Down`}
                        </span>
                      </span>
                    </span>
                    <span data-block style="display: flex; flex-wrap: wrap; gap: var(--ha-space-1, 4px); align-items: center; justify-content: space-between; font-size: var(--ha-font-size-s, 12px); color: var(--unraid-subtext); border-block-start: 1px solid var(--unraid-border); padding-block-start: var(--ha-space-2, 8px);">
                      <span data-block style="display: flex; align-items: center; gap: var(--ha-space-3, 12px);">
                        <span style="display: flex; align-items: center; gap: var(--ha-space-1, 4px);" title="${u?`Total Inbound: ${u}`:`Inbound Transfer Rate`}">
                          <span style="color: var(--unraid-online);">${K(it,13)}</span>
                          <span class="ltr-value" style="font-family: var(--ha-font-family-code, monospace); font-weight: var(--ha-font-weight-medium, 500);">${c}</span>
                          ${u?L`<span class="ltr-value" style="opacity: 0.7; font-size: var(--ha-font-size-s, 12px);">(${u})</span>`:z}
                        </span>

                        <span style="display: flex; align-items: center; gap: var(--ha-space-1, 4px);" title="${d?`Total Outbound: ${d}`:`Outbound Transfer Rate`}">
                          <span style="color: var(--unraid-info);">${K(Ct,13)}</span>
                          <span class="ltr-value" style="font-family: var(--ha-font-family-code, monospace); font-weight: var(--ha-font-weight-medium, 500);">${l}</span>
                          ${d?L`<span class="ltr-value" style="opacity: 0.7; font-size: var(--ha-font-size-s, 12px);">(${d})</span>`:z}
                        </span>
                      </span>

                      <span data-block style="display: flex; align-items: center; gap: var(--ha-space-2, 8px); opacity: 0.8; font-size: var(--ha-font-size-s, 12px);">
                        ${a?L`<span class="ltr-value">MTU ${a}</span>`:z}
                        ${i?L`<span class="ltr-value" style="font-family: var(--ha-font-family-code, monospace);">${i}</span>`:z}
                      </span>
                    </span>
                  </button>
                `}):L`
                <div class="empty-state">
                  No network interfaces discovered for this server.
                </div>
              `}
        </div>

        ${a||o?L`
              <div class="divider"></div>
              <div class="detail-grid">
                ${a?L`
                      <div class="detail-item">
                        <span class="detail-label">LAN WebGUI</span>
                        <a
                          href="${a}"
                          target="_blank"
                          rel="noreferrer"
                          class="detail-val ltr-value"
                          style="color: var(--unraid-accent); text-decoration: none;"
                        >
                          ${a}
                        </a>
                      </div>
                    `:z}
                ${o?L`
                      <div class="detail-item">
                        <span class="detail-label">Remote Access URL</span>
                        <a
                          href="${o}"
                          target="_blank"
                          rel="noreferrer"
                          class="detail-val ltr-value"
                          style="color: var(--unraid-info); text-decoration: none;"
                        >
                          Connect FQDN
                        </a>
                      </div>
                    `:z}
              </div>
            `:z}
      </div>
      </ha-card>
    `}},editor:It,name:`Unraid Network Card`,description:`Network interfaces, link speeds, live throughput, and IP addresses.`});function Q(e){let t=e.split(`.`)[1]||``;return t.replace(/^.*?_container_restart_/,``).replace(/^.*?_docker_container_restart_/,``).replace(/^.*?_container_autostart_/,``).replace(/^.*?_docker_container_autostart_/,``).replace(/^.*?_container_update_/,``).replace(/^.*?_docker_container_update_/,``).replace(/^.*?_docker_container_/,``).replace(/^.*?_container_switch_/,``).replace(/^docker_container_/,``).replace(/^container_switch_/,``).replace(/_cpu$/,``).replace(/_memory_usage$/,``).replace(/_memory$/,``).replace(/_docker_container$/,``).replace(/_container_switch$/,``).replace(/^.*?_container_/,``)||t}X({tag:Ee,editorTag:De,card:class extends J{static editorTag=De;static properties={...J.properties,_filter:{state:!0},_viewMode:{state:!0},_pendingAction:{state:!0},_busy:{state:!0},_error:{state:!0}};constructor(){super(),this._pendingAction=void 0,this._busy=!1,this._error=``,this._filter=`all`,this._viewMode=`grid`}willUpdate(e){super.willUpdate(e),e.has(`config`)&&this.config.view_mode&&e.get(`config`)?.view_mode!==this.config.view_mode&&(this._viewMode=this.config.view_mode)}updated(){let e=this.renderRoot.querySelector(`dialog`);this._pendingAction&&e&&!e.open?e.showModal():!this._pendingAction&&e?.open&&e.close()}handleToggle(e,t,n){this._error=``,t?this._pendingAction={entityId:e,name:n,action:`stop`}:this.runContainerAction(e,`start`)}requestRestart(e,t){this._error=``,this._pendingAction={entityId:e,name:t,action:`restart`}}async runContainerAction(e,t){if(this.hass&&!this._busy){if(!this.agentStates[e])this._pendingAction=void 0,this._error=`This container is no longer available from Unraid Management Agent.`;else{this._busy=!0,this._error=``;try{await this.hass.callService(t===`restart`?`button`:`switch`,t===`restart`?`press`:t===`start`?`turn_on`:`turn_off`,{entity_id:e}),this._pendingAction=void 0}catch{this._error=`The container action failed. Check the server connection and try again.`}finally{this._busy=!1}}}}renderConfirmation(){let e=`${this._pendingAction?.action===`restart`?`Restart`:`Stop`} container?`,t=L`
      <p>${this._pendingAction?.name} will be ${this._pendingAction?.action===`restart`?`restarted`:`stopped`}. Its services will be interrupted.</p>
      ${this._error?L`<p role="alert">${this._error}</p>`:z}
    `,n=L`
      <div class="dialog-actions" slot="footer">
        <button class="btn" autofocus ?disabled=${this._busy} @click=${()=>{this._pendingAction=void 0}}>Cancel</button>
        <button class="btn btn-danger" ?disabled=${this._busy} @click=${()=>{let e=this._pendingAction;e&&this.runContainerAction(e.entityId,e.action)}}>${this._busy?`Working…`:this._pendingAction?.action===`restart`?`Restart`:`Stop`}</button>
      </div>
    `;return customElements.get(`ha-dialog`)?L`<ha-dialog type="alert" width="small" .open=${!!this._pendingAction}
        .headerTitle=${e} .preventScrimClose=${this._busy}
        @closed=${()=>{this._pendingAction=void 0}}>${t}${n}</ha-dialog>`:L`<dialog aria-labelledby="container-action-title"
      @cancel=${e=>{this._busy?e.preventDefault():this._pendingAction=void 0}}
      @close=${()=>{this._pendingAction=void 0}}>
      <h2 id="container-action-title">${e}</h2>${t}${n}
    </dialog>`}getContainers(){let e=this.getEntities(`docker_container_autostart`,`switch`),t=new Set(e.map(e=>e.entity_id)),n=this.getEntities(`docker_container`,`switch`).filter(e=>!t.has(e.entity_id)),r=this.getEntities(`docker_container_restart`,`button`),i=this.getEntities(`container_cpu`),a=this.getEntities(`container_memory_usage`),o=this.getEntities(`docker_container_update`,`update`),s=[],c=this.getActiveDevice(),l=[c?.name_by_user,c?.name].filter(e=>!!e);for(let t of n){let n=Q(t.entity_id),c=this.entityName(t,t.attributes.friendly_name||n);for(let e of l){if(!c.toLowerCase().startsWith(`${e.toLowerCase()} `))continue;let t=c.slice(e.length).trimStart(),n=t.replace(/^(?:docker )?container\s+/i,``);n&&n!==t&&(c=n);break}let u=t.state===`on`,d=r.find(e=>Q(e.entity_id)===n),f=e.find(e=>Q(e.entity_id)===n),p=i.find(e=>Q(e.entity_id)===n),m=a.find(e=>Q(e.entity_id)===n),h=o.find(e=>Q(e.entity_id)===n);s.push({id:n,name:c,isRunning:u,switchEntityId:t.entity_id,restartEntityId:d?.entity_id,autostartEntityId:f?.entity_id,cpuPct:p?.state&&Number.isFinite(parseFloat(p.state))?parseFloat(p.state):void 0,memoryUsage:m?.state&&m.state!==`unavailable`?`${m.state} ${m.attributes.unit_of_measurement||`B`}`:void 0,hasUpdate:h?.state===`on`,updateEntityId:h?.entity_id})}return s.sort((e,t)=>e.isRunning&&!t.isRunning?-1:!e.isRunning&&t.isRunning?1:e.name.localeCompare(t.name))}render(){let e=this.getContainers(),t=e.filter(e=>e.isRunning).length,n=e.length-t,r=e.filter(e=>e.hasUpdate).length,i=this.getEntity(`check_container_updates`,`button`),a=e.filter(e=>this._filter===`running`?e.isRunning:this._filter===`stopped`?!e.isRunning:this._filter!==`updates`||e.hasUpdate),o=L`
      <span class="badge ${t>0?`badge-online`:`badge-standby`}">
        ${t} Running
      </span>
      ${r>0?L`
            <span class="badge badge-warning">
              ${K(G,12)}
              <span>${r} Updates</span>
            </span>
          `:z}
    `;return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(this.config.title||`Docker Containers`,`Unraid Management Agent · ${t} running • ${n} stopped`,rt,o)}
        <div style="display: flex; align-items: center; justify-content: space-between; gap: var(--ha-space-2, 8px); flex-wrap: wrap;">
          <div role="group" aria-label="Container status" style="display: flex; gap: var(--ha-space-1, 4px); overflow-x: auto;">
            <button
              class="tab-btn ${this._filter===`all`?`active`:``}"
              aria-pressed=${this._filter===`all`}
              @click=${()=>this._filter=`all`}
            >
              All (${e.length})
            </button>
            <button
              class="tab-btn ${this._filter===`running`?`active`:``}"
              aria-pressed=${this._filter===`running`}
              @click=${()=>this._filter=`running`}
            >
              Running (${t})
            </button>
            <button
              class="tab-btn ${this._filter===`stopped`?`active`:``}"
              aria-pressed=${this._filter===`stopped`}
              @click=${()=>this._filter=`stopped`}
            >
              Stopped (${n})
            </button>
            ${r>0?L`
                  <button
                    class="tab-btn ${this._filter===`updates`?`active`:``}"
                    style="color: var(--unraid-warning);"
                    aria-pressed=${this._filter===`updates`}
              @click=${()=>this._filter=`updates`}
                  >
                    Updates (${r})
                  </button>
                `:z}
          </div>

          <div style="display: flex; align-items: center; gap: var(--ha-space-2, 8px);">
            ${i?L`
                  <button
                    class="btn"
                    title="Check for updates"
                    @click=${()=>this.pressButton(i.entity_id)}
                  >
                    Check Updates
                  </button>
                `:z}
            <button
              class="btn-icon"
              title="Toggle View Mode"
              aria-label=${this._viewMode===`grid`?`Switch to list view`:`Switch to grid view`}
              @click=${()=>this._viewMode=this._viewMode===`grid`?`list`:`grid`}
            >
              ${K(this._viewMode===`grid`?Et:Tt,18)}
            </button>
          </div>
        </div>
        ${this._error?L`<ha-alert alert-type="error" role="alert">${this._error}</ha-alert>`:z}
        ${this.renderConfirmation()}
        ${this._viewMode===`grid`?L`
              <div class="container-grid">
                ${a.map(e=>L`
                    <div
                      class="container-tile"
                      role="group" aria-label=${e.name}
                    >
                      <div style="display: flex; align-items: center; gap: var(--ha-space-2, 8px); min-width: 0;">
                        <span class="status-dot ${e.isRunning?`online`:`offline`}"></span>
                        <button class="tile-name btn" title=${e.name} aria-label=${`Show details for ${e.name}`}
                          @click=${()=>this.openMoreInfo(e.switchEntityId)}>${e.name}</button>
                      </div>
                      <div style="display: flex; align-items: center; gap: var(--ha-space-1, 4px);">
                        ${e.hasUpdate?L`<span style="color: var(--unraid-warning);">${K(G,14)}</span>`:z}
                        ${e.restartEntityId?L`
                              <button
                                class="btn-icon"
                                style="padding: 2px;"
                                title="Restart ${e.name}" aria-label=${`Restart ${e.name}`} ?disabled=${this._busy}
                                @click=${t=>{t.stopPropagation(),this.requestRestart(e.restartEntityId,e.name)}}
                              >
                                ${K(_t,14)}
                              </button>
                            `:z}
                        <button
                          class="btn-icon"
                          style="padding: 2px; color: ${e.isRunning?`var(--unraid-online)`:`var(--unraid-subtext)`};"
                          title="${e.isRunning?`Stop`:`Start`} ${e.name}"
                          aria-label=${`${e.isRunning?`Stop`:`Start`} ${e.name}`} ?disabled=${this._busy}
                          @click=${t=>{t.stopPropagation(),this.handleToggle(e.switchEntityId,e.isRunning,e.name)}}
                        >
                          ${K(gt,14)}
                        </button>
                      </div>
                    </div>
                  `)}
              </div>
            `:L`
              <div class="item-list">
                ${a.map(e=>L`
                    <div class="list-row">
                      <div class="row-left">
                        <span class="status-dot ${e.isRunning?`online`:`offline`}"></span>
                        <span style="font-weight: var(--ha-font-weight-bold, 600); min-width: 0; flex: 1 1 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                          ${e.name}
                        </span>
                        ${e.cpuPct===void 0?z:L`<span style="font-size: var(--ha-font-size-s, 12px); color: var(--unraid-subtext);">${e.cpuPct}% CPU</span>`}
                        ${e.memoryUsage?L`<span style="font-size: var(--ha-font-size-s, 12px); color: var(--unraid-subtext);">${e.memoryUsage}</span>`:z}
                      </div>
                      <div class="row-right">
                        ${e.hasUpdate?L`
                              <span class="badge badge-warning">Update Available</span>
                            `:z}
                        ${e.restartEntityId?L`
                              <button
                                class="btn"
                                style="padding: 3px var(--ha-space-2, 8px);"
                                aria-label=${`Restart ${e.name}`} ?disabled=${this._busy}
                                @click=${()=>this.requestRestart(e.restartEntityId,e.name)}
                              >
                                ${K(_t,13)}
                                <span>Restart</span>
                              </button>
                            `:z}
                        <button
                          class="btn ${e.isRunning?`btn`:`btn-primary`}"
                          style="padding: 3px var(--ha-space-2, 8px);"
                          aria-label=${`${e.isRunning?`Stop`:`Start`} ${e.name}`} ?disabled=${this._busy}
                          @click=${()=>this.handleToggle(e.switchEntityId,e.isRunning,e.name)}
                        >
                          ${K(gt,13)}
                          <span>${e.isRunning?`Stop`:`Start`}</span>
                        </button>
                      </div>
                    </div>
                  `)}
              </div>
            `}
      </div>
      </ha-card>
    `}},editor:Lt,name:`Unraid Docker Containers Card`,description:`Monitor, start, stop, restart, and update Docker containers in grid or list view.`});function en(e,t){if(!e||e===`unavailable`||e===`unknown`)return null;let n=e.trim();if(!n)return null;if(/[a-zA-Z]/.test(n))return n.replace(/(\b(?:minute|minutes|hour|hours|sec|second|seconds|min|mins)\b.*)\s+min$/i,`$1`);let r=Number(n);if(Number.isFinite(r)){let e=typeof t?.unit_of_measurement==`string`?t.unit_of_measurement.toLowerCase():``,n=r;n=Math.round(e===`s`||e===`sec`||e===`seconds`?r/60:r);let i=Math.floor(n/60),a=n%60;return i>0?a>0?`${i} hour${i>1?`s`:``} ${a} minute${a>1?`s`:``}`:`${i} hour${i>1?`s`:``}`:`${a} minute${a===1?``:`s`}`}return n}X({tag:Oe,editorTag:ke,card:class extends J{static editorTag=ke;render(){let e=this.getEntity(`ups_status`),t=this.getEntity(`ups_connected`,`binary_sensor`),n=this.getEntity(`ups_battery`),r=this.getEntity(`ups_load`),i=this.getEntity(`ups_runtime`),a=this.getEntity(`ups_power`),o=this.getEntity(`ups_output_voltage`),s=this.getEntity(`ups_battery_health`),c=this.getEntity(`ups_energy`),l=t?.state===`on`,u=!!(e&&e.state!==`unavailable`&&e.state!==`unknown`||l),d=e&&e.state!==`unavailable`&&e.state!==`unknown`?e.state:l?`Online`:e?.state||`Unavailable`,f=u&&(d.toLowerCase().includes(`online`)||l),p=u&&(d.toLowerCase().includes(`battery`)||d.toLowerCase().includes(`discharge`)),m=!u||d===`Unavailable`||d===`unavailable`,h=n&&n.state!==`unavailable`&&n.state!==`unknown`&&n?Math.round(Number(n.state)||0):null,g=r&&r.state!==`unavailable`&&r.state!==`unknown`&&r?Math.round(Number(r.state)||0):null,_=a&&a.state!==`unavailable`&&a.state!==`unknown`&&a?`${a.state} W`:null,v=en(i?.state,i?.attributes),y=!!(o&&o.state!==`unavailable`&&o.state!==`unknown`),b=y&&o?`${o.state} V`:null,x=!!(c&&c.state!==`unavailable`&&c.state!==`unknown`),S=x&&c?`${c.state} ${c.attributes?.unit_of_measurement||`kWh`}`:null,C=!!(s&&s.state!==`unavailable`&&s.state!==`unknown`),w=n?.attributes?.ups_status||e?.attributes?.ups_status||(f?`Normal`:l?`Online`:null),T=C&&s?s.state:w,E=L`
      <span class="badge ${m?`badge-standby`:f?`badge-online`:p?`badge-warning`:`badge-error`}">
        ${m?z:L`<span class="pulse-dot"></span>`}
        <span>${m?`Unavailable`:d}</span>
      </span>
    `;return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(this.config.title||`UPS Power & Battery`,e?.attributes?.model||`Uninterruptible Power Supply`,ct,E)}
        <div class="rings-grid ups-rings">
          <button
            type="button"
            ?disabled=${!n}
            class="interactive ring-card"
            @click=${()=>n&&this.openMoreInfo(n.entity_id)}
            title="Click to view Battery details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${h??0}; --ring-color: ${h===null?`var(--unraid-border)`:h<20?`var(--unraid-error)`:h<50?`var(--unraid-warning)`:`var(--unraid-online)`}"
            >
              <span class="ring-content ltr-value">${h===null?`—`:`${h}%`}</span>
            </span>
            <span class="ring-label">Battery Level</span>
            <span class="ring-subtext">${v?`${v} left`:h===null?`No Data`:`Healthy`}</span>
          </button>
          <button
            type="button"
            ?disabled=${!r}
            class="interactive ring-card"
            @click=${()=>r&&this.openMoreInfo(r.entity_id)}
            title="Click to view Load details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${g??0}; --ring-color: ${g===null?`var(--unraid-border)`:g>80?`var(--unraid-error)`:g>50?`var(--unraid-warning)`:`var(--unraid-info)`}"
            >
              <span class="ring-content ltr-value">${g===null?`—`:`${g}%`}</span>
            </span>
            <span class="ring-label">UPS Load</span>
            <span class="ring-subtext">${_||(g===null?`No Data`:`${g}% capacity`)}</span>
          </button>
        </div>

        <div class="divider"></div>
        <div class="detail-grid">
          <button
            type="button"
            ?disabled=${!i}
            class="interactive detail-item"
            @click=${()=>i&&this.openMoreInfo(i.entity_id)}
            title="Click to view Runtime details"
          >
            <span class="detail-label">Runtime Remaining</span>
            <span class="detail-val">${v||`—`}</span>
          </button>
          <button
            type="button"
            ?disabled=${!a}
            class="interactive detail-item"
            @click=${()=>a&&this.openMoreInfo(a.entity_id)}
            title="Click to view Power details"
          >
            <span class="detail-label">Power Consumption</span>
            <span class="detail-val">${_||`—`}</span>
          </button>
          <button
            type="button"
            ?disabled=${!(o||c)}
            class="interactive detail-item"
            @click=${()=>{let e=o||c;e&&this.openMoreInfo(e.entity_id)}}
            title="${o?`Click to view Voltage details`:`Click to view Energy details`}"
          >
            <span class="detail-label">${y?`Output Voltage`:x?`Energy Consumed`:`Output Voltage`}</span>
            <span class="detail-val">${b||S||`—`}</span>
          </button>
          <button
            type="button"
            ?disabled=${!(s||n)}
            class="interactive detail-item"
            @click=${()=>{let e=s||n;e&&this.openMoreInfo(e.entity_id)}}
            title="Click to view Battery Health details"
          >
            <span class="detail-label">Battery Health</span>
            <span class="detail-val" style="${T&&!T.toLowerCase().includes(`fail`)?`color: var(--unraid-online);`:``}">${T||`—`}</span>
          </button>
        </div>
      </div>
      </ha-card>
    `}},editor:Rt,name:`Unraid Power & UPS Card`,description:`Monitor UPS battery level, power draw in Watts, load %, and estimated runtime.`});function tn(e){let t=e.split(`.`)[1]||``;return t.replace(/^.*?_vm_reboot_/,``).replace(/^vm_reboot_/,``).replace(/^.*?_virtual_machine_status_/,``).replace(/^virtual_machine_status_/,``).replace(/^.*?_virtual_machine_/,``).replace(/^virtual_machine_/,``).replace(/_status$/,``).replace(/_virtual_machine$/,``)||t}X({tag:Ae,editorTag:je,card:class extends J{static editorTag=je;handleToggle(e,t,n){(!t||confirm(`Are you sure you want to shut down virtual machine "${n}"?`))&&this.toggleEntity(e)}getVms(){let e=this.getEntities(`virtual_machine`,`switch`),t=this.getEntities(`virtual_machine_status`,`sensor`),n=this.getEntities(`vm_reboot`,`button`),r=[];for(let i of e){let e=tn(i.entity_id),a=this.entityName(i,i.attributes.friendly_name||e),o=i.state===`on`,s=t.find(t=>tn(t.entity_id)===e)?.state||(o?`running`:`shut off`),c=n.find(t=>tn(t.entity_id)===e);r.push({id:e,name:a,isRunning:o,status:s,switchEntityId:i.entity_id,rebootEntityId:c?.entity_id})}return r.sort((e,t)=>e.isRunning&&!t.isRunning?-1:!e.isRunning&&t.isRunning?1:e.name.localeCompare(t.name))}render(){let e=this.getVms(),t=e.filter(e=>e.isRunning).length,n=L`
      <span class="badge ${t>0?`badge-online`:`badge-standby`}">
        ${t} Running
      </span>
    `;return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(this.config.title||`Virtual Machines`,`${t} running of ${e.length} VMs`,mt,n)}

        <div class="item-list">
          ${e.length>0?e.map(e=>L`
                  <div class="list-row">
                    <div class="row-left">
                      <span class="status-dot ${e.isRunning?`online`:`offline`}"></span>
                      <div class="vm-labels">
                        <span class="entity-name" title=${e.name}>${e.name}</span>
                        <span style="font-size: var(--ha-font-size-s, 12px); color: var(--unraid-subtext); text-transform: capitalize;">
                          ${e.status}
                        </span>
                      </div>
                    </div>
                    <div class="row-right">
                      ${e.rebootEntityId?L`
                            <button
                              class="btn"
                              style="padding: 3px var(--ha-space-2, 8px);"
                              title="Reboot VM"
                              @click=${()=>this.pressButton(e.rebootEntityId)}
                            >
                              ${K(_t,13)}
                              <span>Reboot</span>
                            </button>
                          `:z}
                      <button
                        class="btn ${e.isRunning?`btn`:`btn-primary`}"
                        style="padding: 3px var(--ha-space-2, 8px);"
                        @click=${()=>this.handleToggle(e.switchEntityId,e.isRunning,e.name)}
                      >
                        ${K(gt,13)}
                        <span>${e.isRunning?`Stop`:`Start`}</span>
                      </button>
                    </div>
                  </div>
                `):L`<div style="text-align: center; color: var(--unraid-subtext); font-size: var(--ha-font-size-s, 12px); padding: var(--ha-space-3, 12px);">No virtual machines configured</div>`}
        </div>
      </div>
      </ha-card>
    `}},editor:zt,name:`Unraid Virtual Machines Card`,description:`Monitor and manage Unraid virtual machines.`}),X({tag:Ie,editorTag:Le,card:class extends J{static editorTag=Le;getArcData(){let e=this.getEntity(`zfs_arc_hit_ratio`),t=this.getEntity(`zfs_arc_configured_max`),n=e?.state!=null&&!isNaN(Number(e.state))?Math.round(Number(e.state)):void 0,r;if(t?.state!=null){let e=t.state;if(e===`0`||e===`Auto`)r=`Auto`;else{let n=Number(e);r=!isNaN(n)&&n>0?`${(n/1073741824).toFixed(1)} GB`:`${e} ${t.attributes?.unit_of_measurement||``}`.trim()}}return{hitRatio:n,hitRatioEntityId:e?.entity_id,configuredMax:r,configuredMaxEntityId:t?.entity_id,attributes:e?.attributes}}getPoolDeviceEntities(e){let t=this.getActiveDevice();if(!this.hass?.entities||!t)return[];let n=[];for(let r of Object.values(this.hass.entities))if(r.translation_key===e&&r.device_id&&r.device_id!==t.id&&this.isServerOrChildDevice(r.device_id,t.id)){let e=this.agentStates[r.entity_id];e&&n.push(e)}return n}getPools(){let e=this.getPoolDeviceEntities(`zfs_pool_device_usage`),t=[...this.getEntities(`zfs_pool_usage`),...e],n=[...this.getEntities(`zfs_pool_health`),...this.getPoolDeviceEntities(`zfs_pool_device_health`)],r=this.getEntities(`corrupted_files`),i=new Map;for(let t of e){let e=this.hass?.entities?.[t.entity_id]?.device_id,n=t.attributes?.pool_name;e&&n&&i.set(e,n)}let a=this.getPoolDeviceEntities(`zfs_pool_device_corrupted_files`),o=new Map,s=this.getActiveDevice()?.id;if(this.hass?.states)for(let[e,t]of Object.entries(this.agentStates)){if(s&&this.hass.entities){let t=this.hass.entities[e];if(t&&t.device_id&&t.device_id!==s)continue}let n=e.match(/_zfs_([a-zA-Z0-9_-]+)_usage$/i);if(n&&n[1]){let r=t.attributes?.pool_name||n[1];if(!o.has(r)){let n=parseFloat(t.state);o.set(r,{name:t.attributes?.pool_name||r,usagePct:isNaN(n)?0:Math.round(n),totalSize:t.attributes?.total_size,usedSize:t.attributes?.used_size,freeSize:t.attributes?.free_space||t.attributes?.free_size,health:`ONLINE`,usageEntityId:e})}}}for(let e of t){let t=e.attributes?.pool_name||e.entity_id.replace(/^.*?_zfs_/,``).replace(/_usage$/,``),n=parseFloat(e.state);o.has(t)||o.set(t,{name:t,usagePct:isNaN(n)?0:Math.round(n),totalSize:e.attributes?.total_size,usedSize:e.attributes?.used_size,freeSize:e.attributes?.free_space||e.attributes?.free_size,health:`ONLINE`,usageEntityId:e.entity_id})}for(let e of n){let t=e.attributes?.pool_name||e.entity_id.replace(/^.*?_zfs_/,``).replace(/_health$/,``),n=o.get(t);n&&(n.health=e.state||`ONLINE`,n.healthEntityId=e.entity_id,e.attributes?.errors!==void 0&&(n.errors=Number(e.attributes.errors)))}for(let e of[...r,...a]){let t=this.hass?.entities?.[e.entity_id]?.device_id,n=e.attributes?.pool_name||t&&i.get(t)||e.entity_id.replace(/^.*?_zfs_/,``).replace(/_corrupted_files$/,``),r=o.get(n);if(r){let t=parseInt(e.state,10);isNaN(t)||(r.corruptedFiles=t)}}return Array.from(o.values()).sort((e,t)=>e.name.localeCompare(t.name))}render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getArcData(),r=this.getPools(),i=n.hitRatio!==void 0||r.length>0;return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(t,`ZFS Storage & Cache`,nt,L`
            <span class="badge ${r.some(e=>e.health!==`ONLINE`)?`badge-warning`:`badge-online`}">
              <span class="pulse-dot"></span>
              <span>${r.length} Pool${r.length===1?``:`s`}</span>
            </span>
          `)}

        ${i?L`
              ${n.hitRatio===void 0?z:L`
                    <div class="rings-grid">
                      <button
                        type="button"
                        ?disabled=${!n.hitRatioEntityId}
                        class="interactive ring-card"
                        @click=${()=>n.hitRatioEntityId&&this.openMoreInfo(n.hitRatioEntityId)}
                        title="Click to view ARC Cache details"
                      >
                        <span data-block
                          class="ring-gauge"
                          style="--pct: ${n.hitRatio}; --ring-color: ${n.hitRatio>90?`var(--unraid-online)`:n.hitRatio>70?`var(--unraid-warning)`:`var(--unraid-error)`}"
                        >
                          <span class="ring-content ltr-value">${n.hitRatio}%</span>
                        </span>
                        <span class="ring-label">ARC Hit Ratio</span>
                        <span class="ring-subtext">
                          ${n.configuredMax?`Max: ${n.configuredMax}`:`ZFS Adaptive Cache`}
                        </span>
                      </button>
                    </div>
                  `}

              ${r.length>0?L`
                    <div class="divider"></div>
                    <div class="disk-list">
                      ${r.map(e=>{let t=e.health.toUpperCase()!==`ONLINE`,n=(e.corruptedFiles||0)>0;return L`
                          <button
                            type="button"
                            ?disabled=${!e.usageEntityId}
                            class="interactive disk-row"
                            @click=${()=>e.usageEntityId&&this.openMoreInfo(e.usageEntityId)}
                          >
                            <span data-block class="disk-main">
                              <span class="disk-icon ${t?`disk-warning`:`disk-online`}">
                                ${K(t?G:nt,18)}
                              </span>
                              <span data-block class="disk-info">
                                <span class="disk-name">${e.name}</span>
                                <span class="disk-subtext">
                                  ${e.usedSize&&e.totalSize?`${e.usedSize} / ${e.totalSize}`:`${e.usagePct}% used`}
                                  ${n?` • ${e.corruptedFiles} corrupted`:``}
                                </span>
                              </span>
                            </span>
                            <span data-block class="disk-meta">
                              <span class="disk-temp">${e.usagePct}%</span>
                              <span class="badge ${t?`badge-error`:`badge-online`}">
                                ${e.health}
                              </span>
                            </span>
                          </button>
                        `})}
                    </div>
                  `:z}
            `:L`
              <div class="empty-state">
                ${K(nt,32)}
                <div class="empty-title">No ZFS Telemetry Available</div>
                <div class="empty-subtext">Enable the ZFS collector in Unraid Management Agent to monitor pools and ARC cache.</div>
              </div>
            `}
      </div>
      </ha-card>
    `}},editor:Bt,name:`Unraid ZFS Card`,description:`Monitor ZFS pools, pool health, corrupted files, and ARC cache performance`}),X({tag:Re,editorTag:ze,card:class extends J{static editorTag=ze;getFans(){let e=[];if(!this.hass?.states)return e;let t=this.getActiveDevice()?.id,n=new Map;for(let[e,r]of Object.entries(this.agentStates))if(e.startsWith(`number.`)&&(e.includes(`_fan_`)||e.includes(`fan_control`))){if(t&&this.hass.entities){let n=this.hass.entities[e];if(n&&n.device_id&&!this.isServerOrChildDevice(n.device_id,t))continue}let i=this.hass.entities?.[e];if(i&&i.platform!==`unraid_management_agent`&&i.platform!==`unraid`)continue;let a=r.attributes?.fan_id;a!==void 0&&n.set(String(a),e)}for(let[r,i]of Object.entries(this.agentStates)){if(!r.startsWith(`sensor.`))continue;if(t&&this.hass.entities){let e=this.hass.entities[r];if(e&&e.device_id&&!this.isServerOrChildDevice(e.device_id,t))continue}let a=this.hass.entities?.[r];if(a&&a.platform!==`unraid_management_agent`&&a.platform!==`unraid`||!(i.attributes?.unit_of_measurement===`RPM`||i.attributes?.unit_of_measurement===`rpm`||r.includes(`_fan_`)||r.endsWith(`_fan`)))continue;let o=parseInt(i.state,10),s=i.attributes?.is_failed===!0||i.attributes?.status===`failed`,c=i.attributes?.fan_id,l=this.entityName(i,i.attributes?.original_name||i.attributes?.friendly_name||r.split(`.`)[1]||`Fan`).replace(/^(?:.*?\s+)?Fan\s+/i,`Fan `).replace(/\s+RPM$/i,``).replace(/\s+Speed$/i,``).trim();e.push({id:r,name:l,rpm:isNaN(o)?0:o,rpmText:isNaN(o)?`--`:`${o} RPM`,noReading:isNaN(o),isFailed:s,fanId:c,controlEntityId:c===void 0?void 0:n.get(String(c)),rpmEntityId:r})}if(e.length===0)for(let[n,r]of Object.entries(this.agentStates)){if(!n.startsWith(`number.`))continue;if(t&&this.hass.entities){let e=this.hass.entities[n];if(e&&e.device_id&&!this.isServerOrChildDevice(e.device_id,t))continue}let i=this.hass.entities?.[n];if(i&&i.platform!==`unraid_management_agent`&&i.platform!==`unraid`||!n.includes(`_fan_`))continue;let a=r.attributes?.fan_id,o=r.attributes?.rpm==null?NaN:Number(r.attributes.rpm),s=parseFloat(r.state),c=isNaN(o)?0:o,l=isNaN(o)?isNaN(s)?r.state:`${Math.round(s)}%`:`${o} RPM`,u=this.entityName(r,r.attributes?.original_name||r.attributes?.friendly_name||n.split(`.`)[1]||`Fan`).replace(/^(?:.*?\s+)?Fan\s+/i,`Fan `).replace(/\s+RPM$/i,``).replace(/\s+Speed$/i,``).trim();e.push({id:n,name:u,rpm:c,rpmText:l,isFailed:!1,fanId:a,controlEntityId:n,rpmEntityId:n})}return e.sort((e,t)=>e.name.localeCompare(t.name,void 0,{numeric:!0}))}render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getFans(),r=n.length===0?this.getServerRegistryEntries()?.filter(e=>e.entity_id.startsWith(`sensor.`)&&(e.translation_key===`fan`||e.translation_key===`hwmon_device_fan`||e.config_entry_id&&e.unique_id.startsWith(`${e.config_entry_id}_fan_`)))??[]:[],i=r.filter(e=>e.disabled_by).length,a=r.filter(e=>!e.disabled_by&&!this.hass?.states[e.entity_id]),o=i>0?`Fan sensors are disabled`:a.length>0?`Fan sensors are registered but have no state`:`No Fan Sensors Found`,s=i>0?`${i} fan sensor${i===1?` is`:`s are`} disabled. Enable them in Settings → Entities.`:a.length>0?`Check the integration options and diagnostics for fan sensor data.`:`Check the selected server, its fan entities in Settings → Entities, and the integration diagnostics for reported fans.`;return L`
      <ha-card>
        <div class="card-content">
        ${this.renderHeader(t,`Cooling & Fans`,st,n.length>0?L`
            <span class="badge ${n.some(e=>e.isFailed)?`badge-error`:`badge-online`}">
              <span class="pulse-dot"></span>
              <span>${n.length} Fan${n.length===1?``:`s`}</span>
            </span>
          `:void 0)}

        ${n.length===0?L`
              <div class="empty-state">
                ${K(st,32)}
                <div class="empty-title">${o}</div>
                <div class="empty-subtext">${s}</div>
              </div>
            `:L`
              <div class="disk-list">
                ${n.map(e=>L`
                    <button
                      type="button"
                      class="interactive disk-row"
                      @click=${()=>this.openMoreInfo(e.controlEntityId||e.rpmEntityId)}
                      title="Click to view fan details / controls"
                    >
                      <span data-block class="disk-main">
                        <span class="disk-icon ${e.isFailed?`disk-warning`:`disk-online`}">
                          ${K(e.isFailed?G:st,18)}
                        </span>
                        <span data-block class="disk-info">
                          <span class="disk-name">${e.name}</span>
                          <span class="disk-subtext">
                            ${e.isFailed?`Fan Fault Detected`:e.noReading?`No reading`:e.rpm>0?`Operating Normally`:`Stopped / Idle`}
                          </span>
                        </span>
                      </span>
                      <span data-block class="disk-meta">
                        <span class="disk-temp" style="color: ${e.isFailed?`var(--unraid-error)`:e.rpm>2e3?`var(--unraid-warning)`:`var(--unraid-text)`};">
                          ${e.rpmText}
                        </span>
                        ${e.isFailed?L`<span class="badge badge-error">FAULT</span>`:e.noReading?z:e.rpm>0?L`<span class="badge badge-online">ACTIVE</span>`:L`<span class="badge">OFF</span>`}
                      </span>
                    </button>
                  `)}
              </div>
            `}
      </div>
      </ha-card>
    `}},editor:Vt,name:`Unraid Fans Card`,description:`Monitor system cooling fans, RPM speeds, and control statuses`});var nn={gpu_device_utilization:`utilization`,gpu_device_temperature:`temperature`,gpu_device_power:`power`,gpu_device_energy:`energy`,gpu_device_vram_usage:`vram_usage`};X({tag:Be,editorTag:Ve,card:class extends J{static editorTag=Ve;getGpus(){let e=new Map;if(!this.hass?.states)return[];let t=this.getActiveDevice(),n=t?.id,r=t?.name?this.slugifyDeviceName(t.name):void 0;for(let[t,i]of Object.entries(this.agentStates)){if(!t.startsWith(`sensor.`))continue;let a=this.hass.entities?.[t],o=a?.device_id?this.hass.devices?.[a.device_id]:void 0,s=o?.parent_device_id?o:void 0;if(n&&a?.device_id){if(a.device_id!==n&&s?.parent_device_id!==n)continue}else if(r&&!t.includes(r))continue;let c=s?void 0:t.match(/_gpu_(?:(.+?)_)?(utilization|temperature|power|energy|memory_utilization|vram_usage)(?:_(\d+))?$/i),l=s?nn[a?.translation_key??``]:c?.[2]?.toLowerCase();if(!l)continue;let u=s?s.id:c?.[1]||`0`,d=s?`device:${s.id}`:`${u.toLowerCase()}${c?.[3]?`#${c[3]}`:``}`;if(!e.has(d)){let t=parseInt(u,10),n=isNaN(t)?e.size:t,r=typeof i.attributes?.friendly_name==`string`?i.attributes.friendly_name.replace(/^(?:.*?\s+)?(?:GPU\s+)?/i,``).replace(/\s+(?:Utilization|Temperature|Power|Energy|VRAM|Usage).*$/i,``):void 0,a=s?.name_by_user||s?.name?.replace(/^GPU\s*·\s*/i,``)||void 0,o=this.entityName(i,a||(typeof i.attributes?.gpu_name==`string`?i.attributes.gpu_name:void 0)||r||(u===`0`?`GPU ${n}`:u.replace(/_/g,` `).replace(/\b\w/g,e=>e.toUpperCase()))),c=i.attributes?.gpu_driver_version||i.attributes?.driver_version||void 0;e.set(d,{index:n,name:o,nameFromDevice:a!==void 0,driver:c})}let f=e.get(d);i.attributes?.gpu_name&&!f.nameFromDevice&&(!f.name||f.name.startsWith(`GPU `))&&(f.name=i.attributes.gpu_name),(i.attributes?.gpu_driver_version||i.attributes?.driver_version)&&!f.driver&&(f.driver=i.attributes.gpu_driver_version||i.attributes.driver_version);let p=parseFloat(i.state);l===`utilization`?(f.utilizationPct=isNaN(p)?void 0:Math.round(p),f.utilizationEntityId=t):l===`temperature`?(f.temp=isNaN(p)?void 0:Math.round(p),f.tempEntityId=t):l===`power`?(f.power=isNaN(p)?void 0:Math.round(p),f.powerEntityId=t):l===`energy`?(f.energy=isNaN(p)?void 0:Number(p.toFixed(2)),f.energyEntityId=t):(l===`memory_utilization`||l===`vram_usage`)&&(f.memUtilPct=isNaN(p)?void 0:Math.round(p),f.memUtilEntityId=t)}return Array.from(e.values()).sort((e,t)=>e.index-t.index)}render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getGpus();return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(t,`GPU Accelerators`,ot,L`
            <span class="badge ${n.length>0?`badge-online`:``}">
              <span class="pulse-dot"></span>
              <span>${n.length} GPU${n.length===1?``:`s`}</span>
            </span>
          `)}

        ${n.length===0?L`
              <div class="empty-state">
                ${K(ot,32)}
                <div class="empty-title">No GPU Telemetry Available</div>
                <div class="empty-subtext">Enable GPU monitoring or install NVIDIA / Intel GPU plugins to view GPU stats.</div>
              </div>
            `:L`
              <div class="gpu-grid" style="display: flex; flex-direction: column; gap: var(--ha-space-3, 12px);">
                ${n.map(e=>{let t=e.utilizationPct??0;return L`
                    <div class="ring-card" style="padding: var(--ha-space-3, 12px); background: color-mix(in srgb, var(--unraid-text) 3%, transparent); border-radius: var(--ha-border-radius-md, 8px);">
                      <div class="gpu-header">
                        <div class="gpu-name">
                          ${K(ot,20)}
                          <span class="entity-name" title=${e.name}>${e.name}</span>
                        </div>
                        ${e.driver?L`<span class="badge gpu-driver ltr-value">${e.driver}</span>`:z}
                      </div>

                      <div class="rings-grid" style="grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));">
                        ${e.utilizationPct===void 0?z:L`
                              <button
                                type="button"
                                ?disabled=${!e.utilizationEntityId}
                                class="interactive ring-card"
                                @click=${()=>e.utilizationEntityId&&this.openMoreInfo(e.utilizationEntityId)}
                                title="Click for GPU load details"
                              >
                                <span data-block
                                  class="ring-gauge"
                                  style="--pct: ${t}; --ring-color: ${t>80?`var(--unraid-error)`:t>50?`var(--unraid-warning)`:`var(--unraid-online)`}"
                                >
                                  <span class="ring-content ltr-value">${t}%</span>
                                </span>
                                <span class="ring-label">GPU Load</span>
                              </button>
                            `}

                        ${e.temp===void 0?z:L`
                              <button
                                type="button"
                                ?disabled=${!e.tempEntityId}
                                class="interactive ring-card"
                                @click=${()=>e.tempEntityId&&this.openMoreInfo(e.tempEntityId)}
                                title="Click for Temperature details"
                              >
                                <span data-block
                                  class="ring-gauge"
                                  style="--pct: ${Math.min(100,Math.round(e.temp/90*100))}; --ring-color: ${e.temp>80?`var(--unraid-error)`:e.temp>65?`var(--unraid-warning)`:`var(--unraid-info)`}"
                                >
                                  <span class="ring-content ltr-value">${e.temp}°C</span>
                                </span>
                                <span class="ring-label">Temperature</span>
                              </button>
                            `}

                        ${e.power===void 0?z:L`
                              <button
                                type="button"
                                ?disabled=${!e.powerEntityId}
                                class="interactive ring-card"
                                @click=${()=>e.powerEntityId&&this.openMoreInfo(e.powerEntityId)}
                                title="Click for Power details"
                              >
                                <span data-block class="ring-gauge" style="--pct: 60; --ring-color: var(--unraid-accent)">
                                  <span class="ring-content ltr-value">${e.power}W</span>
                                </span>
                                <span class="ring-label">Power Draw</span>
                                ${e.energy===void 0?z:L`<span class="ring-subtext">${e.energy} kWh</span>`}
                              </button>
                            `}

                        ${e.memUtilPct===void 0?z:L`
                              <button
                                type="button"
                                ?disabled=${!e.memUtilEntityId}
                                class="interactive ring-card"
                                @click=${()=>e.memUtilEntityId&&this.openMoreInfo(e.memUtilEntityId)}
                                title="Click for VRAM details"
                              >
                                <span data-block class="ring-gauge" style="--pct: ${e.memUtilPct}; --ring-color: var(--unraid-info)">
                                  <span class="ring-content ltr-value">${e.memUtilPct}%</span>
                                </span>
                                <span class="ring-label">VRAM Usage</span>
                              </button>
                            `}
                      </div>
                    </div>
                  `})}
              </div>
            `}
      </div>
      </ha-card>
    `}},editor:Ht,name:`Unraid GPU Card`,description:`Monitor graphics cards utilization, temperature, power draw, and VRAM`}),X({tag:He,editorTag:Ue,card:class extends J{static editorTag=Ue;render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getEntity(`notifications_unread_alert`),r=this.getEntity(`notifications_unread_warning`),i=this.getEntity(`notifications_unread_info`),a=this.getEntity(`notification_count`)||this.getEntity(`notifications`),o=this.getEntity(`notification_event`,`event`)||this.getEntity(`notification`,`event`),s=Number(n?.state)||0,c=Number(r?.state)||0,l=Number(i?.state)||0,u=Number(a?.state)||s+c+l,d=u>0,f=!!o?.state&&o?.state!==`unavailable`&&o?.state!==`unknown`,p=!!(o?.attributes?.subject||o?.attributes?.description||o?.attributes?.message),m=f&&p?o?.attributes:void 0;return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(t,`Notifications Center`,$e,L`
            <span class="badge ${s>0?`badge-error`:c>0?`badge-warning`:`badge-online`}">
              <span class="pulse-dot"></span>
              <span>${u} Unread</span>
            </span>
          `)}

        <div class="rings-grid">
          <button
            type="button"
            ?disabled=${!n}
            class="interactive ring-card"
            @click=${()=>n&&this.openMoreInfo(n.entity_id)}
            title="Click for Alerts"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${s>0?100:0}; --ring-color: var(--unraid-error)"
            >
              <span class="ring-content">${s}</span>
            </span>
            <span class="ring-label">Alerts</span>
            <span class="ring-subtext">Critical Issues</span>
          </button>

          <button
            type="button"
            ?disabled=${!r}
            class="interactive ring-card"
            @click=${()=>r&&this.openMoreInfo(r.entity_id)}
            title="Click for Warnings"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${c>0?100:0}; --ring-color: var(--unraid-warning)"
            >
              <span class="ring-content">${c}</span>
            </span>
            <span class="ring-label">Warnings</span>
            <span class="ring-subtext">Action Required</span>
          </button>

          <button
            type="button"
            ?disabled=${!i}
            class="interactive ring-card"
            @click=${()=>i&&this.openMoreInfo(i.entity_id)}
            title="Click for Informational"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${l>0?100:0}; --ring-color: var(--unraid-info)"
            >
              <span class="ring-content">${l}</span>
            </span>
            <span class="ring-label">Notices</span>
            <span class="ring-subtext">System Information</span>
          </button>
        </div>

        ${!d&&!m?L`
              <div class="divider"></div>
              <div class="empty-state">
                ${K(et,32)}
                <div class="empty-title">All Clear</div>
                <div class="empty-subtext">There are no unread notifications on this Unraid server.</div>
              </div>
            `:m?L`
              <div class="divider"></div>
              <div class="disk-list">
                <div class="disk-row">
                  <div class="disk-main">
                    <span class="disk-icon ${m.importance===`alert`?`disk-warning`:`disk-online`}">
                      ${K(m.importance===`alert`||m.importance===`warning`?G:ft,18)}
                    </span>
                    <div class="disk-info">
                      <span class="disk-name">${m.subject||`Latest Notification`}</span>
                      <span class="disk-subtext">${m.description||m.message||`No message content`}</span>
                    </div>
                  </div>
                  <div class="disk-meta">
                    <span class="badge ${m.importance===`alert`?`badge-error`:m.importance===`warning`?`badge-warning`:`badge-online`}">
                      ${m.importance||`Info`}
                    </span>
                  </div>
                </div>
              </div>
            `:z}
      </div>
      </ha-card>
    `}},editor:Ut,name:`Unraid Notifications Card`,description:`View Unraid notification counts, severity alerts, and latest messages`}),X({tag:We,editorTag:Ge,card:class extends J{static editorTag=Ge;render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getEntity(`last_parity_check`),r=this.getEntity(`next_parity_check`),i=this.getEntity(`parity_check_running`,`binary_sensor`),a=this.getEntity(`parity_valid`,`binary_sensor`),o=this.getEntity(`flash_usage`),s=this.getEntity(`flash_free_space`),c=this.getEntity(`plugins_with_updates`)||this.getEntity(`plugin_updates`),l=this.getEntity(`container_updates_available`),u=i?.state===`on`,d=a?.state===`on`,f=At(s),p=Math.round(Number(o?.state)||0),m=Number(c?.state)||0,h=Number(l?.state)||0,g=m+h,_=n?.attributes?.duration||n?.attributes?.last_duration,v=n?.attributes?.result||n?.state,y=n?.attributes?.errors;return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(t,`Maintenance & Operations`,Dt,L`
            <span class="badge ${g>0?`badge-warning`:`badge-online`}">
              <span class="pulse-dot"></span>
              <span>${g>0?`${g} Updates`:`Up to Date`}</span>
            </span>
          `)}

        <div class="rings-grid">
          <button
            type="button"
            ?disabled=${!o}
            class="interactive ring-card"
            @click=${()=>o&&this.openMoreInfo(o.entity_id)}
            title="Click for Flash USB details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${p}; --ring-color: ${p>80?`var(--unraid-error)`:p>60?`var(--unraid-warning)`:`var(--unraid-online)`}"
            >
              <span class="ring-content">${p}%</span>
            </span>
            <span class="ring-label">Flash Boot Drive</span>
            <span class="ring-subtext">${f?`${f} Free`:`USB Boot Drive`}</span>
          </button>

          <button
            type="button"
            ?disabled=${!n}
            class="interactive ring-card"
            @click=${()=>n&&this.openMoreInfo(n.entity_id)}
            title="Click for Parity status"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${u?50:100}; --ring-color: ${d?`var(--unraid-error)`:`var(--unraid-online)`}"
            >
              <span class="ring-content">${u?`SYNC`:d?`FAIL`:`OK`}</span>
            </span>
            <span class="ring-label">Parity Health</span>
            <span class="ring-subtext">${y===void 0?`Parity Protected`:`${y} Sync Errors`}</span>
          </button>
        </div>

        <div class="divider"></div>

        <div class="disk-list">
          <button
            type="button"
            ?disabled=${!n}
            class="interactive disk-row"
            @click=${()=>n&&this.openMoreInfo(n.entity_id)}
          >
            <span data-block class="disk-main">
              <span class="disk-icon ${y?`disk-warning`:`disk-online`}">
                ${K(xt,18)}
              </span>
              <span data-block class="disk-info">
                <span class="disk-name">Last Parity Check</span>
                <span class="disk-subtext">
                  ${v&&v!==n?.state?v:`Completed`}
                  ${_?` • Duration: ${_}`:``}
                  ${y===void 0?``:y===0?` • 0 sync errors`:` • ${y} errors`}
                </span>
              </span>
            </span>
            <span data-block class="disk-meta">
              <span class="disk-temp">${jt(n?.state)}</span>
            </span>
          </button>

          ${r?.state&&r.state!==`unavailable`&&r.state!==`unknown`?L`
                <button
                  type="button"
                  class="interactive disk-row"
                  @click=${()=>this.openMoreInfo(r.entity_id)}
                >
                  <span data-block class="disk-main">
                    <span class="disk-icon disk-online">
                      ${K(tt,18)}
                    </span>
                    <span data-block class="disk-info">
                      <span class="disk-name">Next Scheduled Parity</span>
                      <span class="disk-subtext">
                        Automated Parity Verification${r.attributes?.mode?` (${typeof r.attributes.mode==`string`?r.attributes.mode.charAt(0).toUpperCase()+r.attributes.mode.slice(1):r.attributes.mode})`:``}
                      </span>
                    </span>
                  </span>
                  <span data-block class="disk-meta">
                    <span class="disk-temp">${jt(r.state)}</span>
                  </span>
                </button>
              `:z}

          ${c?L`
                <button
                  type="button"
                  class="interactive disk-row"
                  @click=${()=>this.openMoreInfo(c.entity_id)}
                >
                  <span data-block class="disk-main">
                    <span class="disk-icon ${m>0?`disk-warning`:`disk-online`}">
                      ${K(it,18)}
                    </span>
                    <span data-block class="disk-info">
                      <span class="disk-name">Plugin Updates</span>
                      <span class="disk-subtext">${m>0?`${m} plugin updates pending`:`All plugins are up to date`}</span>
                    </span>
                  </span>
                  <span data-block class="disk-meta">
                    <span class="badge ${m>0?`badge-warning`:`badge-online`}">
                      ${m>0?`${m} NEW`:`CURRENT`}
                    </span>
                  </span>
                </button>
              `:z}

          ${l?L`
                <button
                  type="button"
                  class="interactive disk-row"
                  @click=${()=>this.openMoreInfo(l.entity_id)}
                >
                  <span data-block class="disk-main">
                    <span class="disk-icon ${h>0?`disk-warning`:`disk-online`}">
                      ${K(it,18)}
                    </span>
                    <span data-block class="disk-info">
                      <span class="disk-name">Docker Image Updates</span>
                      <span class="disk-subtext">${h>0?`${h} container image updates available`:`All container images are current`}</span>
                    </span>
                  </span>
                  <span data-block class="disk-meta">
                    <span class="badge ${h>0?`badge-warning`:`badge-online`}">
                      ${h>0?`${h} NEW`:`CURRENT`}
                    </span>
                  </span>
                </button>
              `:z}
        </div>
      </div>
      </ha-card>
    `}},editor:Wt,name:`Unraid Maintenance Card`,description:`Parity verification history, flash drive health, and plugin/container update status`}),X({tag:Ke,editorTag:qe,card:class extends J{static editorTag=qe;getRemoteShares(){let e=new Map;if(!this.hass?.states)return[];let t=this.getActiveDevice()?.id;for(let[n,r]of Object.entries(this.agentStates)){if(t&&this.hass.entities){let e=this.hass.entities[n];if(e&&e.device_id&&e.device_id!==t)continue}let i=n.match(/_remote_share_([a-zA-Z0-9_-]+)_(usage|mounted|mount)$/i);if(!i||!i[1]||!i[2])continue;let a=i[1].toLowerCase(),o=this.entityName(r,r.attributes?.friendly_name||i[1]||`Remote Share`).replace(/^(?:.*?\s+)?Remote Share\s+/i,``).replace(/\s+(?:usage|mounted|mount)$/i,``).trim();e.has(a)||e.set(a,{name:o,isMounted:!0});let s=e.get(a),c=i[2].toLowerCase();if(c===`usage`){s.usageEntityId=n;let e=parseFloat(r.state);s.usagePct=isNaN(e)?void 0:Math.round(e),s.used=r.attributes?.used,s.total=r.attributes?.total,s.free=r.attributes?.free}else c===`mounted`?(s.mountedEntityId=n,s.isMounted=r.state===`on`||r.state===`true`):c===`mount`&&(s.mountSwitchEntityId=n,s.mountedEntityId||(s.isMounted=r.state===`on`))}return Array.from(e.values()).sort((e,t)=>e.name.localeCompare(t.name))}handleToggleMount(e){e.mountSwitchEntityId&&(!e.isMounted||confirm(`Are you sure you want to unmount remote share "${e.name}"?`))&&this.toggleEntity(e.mountSwitchEntityId)}render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getRemoteShares();return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(t,`Remote SMB & NFS Shares`,yt,L`
            <span class="badge ${n.some(e=>e.isMounted)?`badge-online`:``}">
              <span class="pulse-dot"></span>
              <span>${n.length} Discovered</span>
            </span>
          `)}

        ${n.length===0?L`
              <div class="empty-state">
                ${K(yt,32)}
                <div class="empty-title">No Remote Shares Found</div>
                <div class="empty-subtext">Mount remote SMB or NFS shares using the Unassigned Devices plugin on Unraid.</div>
              </div>
            `:L`
              <div class="disk-list">
                ${n.map(e=>L`
                    <div class="disk-row">
                      <button
                        type="button"
                        ?disabled=${!e.usageEntityId}
                        class="interactive disk-main"
                        @click=${()=>e.usageEntityId&&this.openMoreInfo(e.usageEntityId)}
                      >
                        <span class="disk-icon ${e.isMounted?`disk-online`:`disk-standby`}">
                          ${K(lt,18)}
                        </span>
                        <span data-block class="disk-info">
                          <span class="disk-name">${e.name}</span>
                          <span class="disk-subtext">
                            ${e.isMounted?e.used&&e.total?`${e.used} / ${e.total}`:e.usagePct===void 0?`Mounted`:`${e.usagePct}% used`:`Unmounted`}
                          </span>
                        </span>
                      </button>

                      <div class="disk-meta" style="align-items: center; gap: var(--ha-space-2, 8px);">
                        ${e.usagePct===void 0?z:L`<span class="disk-temp">${e.usagePct}%</span>`}
                        ${e.mountSwitchEntityId?L`
                              <button
                                class="btn-icon ${e.isMounted?`active`:``}"
                                @click=${()=>this.handleToggleMount(e)}
                                title="${e.isMounted?`Unmount Remote Share`:`Mount Remote Share`}"
                                style="border: none; background: transparent; cursor: pointer; color: ${e.isMounted?`var(--unraid-online)`:`var(--unraid-subtext)`}; padding: var(--ha-space-1, 4px);"
                              >
                                ${K(gt,18)}
                              </button>
                            `:L`
                              <span class="badge ${e.isMounted?`badge-online`:``}">
                                ${e.isMounted?`MOUNTED`:`UNMOUNTED`}
                              </span>
                            `}
                      </div>
                    </div>
                  `)}
              </div>
            `}
      </div>
      </ha-card>
    `}},editor:Gt,name:`Unraid Remote Shares Card`,description:`Monitor and mount remote network SMB/NFS storage shares`}),X({tag:Je,editorTag:Ye,card:class extends J{static editorTag=Ye;getDevices(){let e=new Map;if(!this.hass?.states)return[];let t=this.getActiveDevice()?.id;for(let[n,r]of Object.entries(this.agentStates)){if(t&&this.hass.entities){let e=this.hass.entities[n];if(e&&e.device_id&&e.device_id!==t)continue}let i=n.match(/_unassigned_device_([a-zA-Z0-9_-]+)_(size|usage|mounted|temperature|temp)$/i);if(!i||!i[1]||!i[2])continue;let a=i[1].toLowerCase(),o=this.entityName(r,r.attributes?.friendly_name||i[1]||`Unassigned Device`).replace(/^(?:.*?\s+)?Unassigned Device\s+/i,``).replace(/\s+(?:size|usage|mounted|temperature|temp)$/i,``).trim();e.has(a)||e.set(a,{id:i[1],name:o,isMounted:!1});let s=e.get(a),c=i[2].toLowerCase();if(c===`size`)s.sizeEntityId=n,s.size=`${r.state} ${r.attributes?.unit_of_measurement||``}`.trim(),s.fsType=r.attributes?.filesystem;else if(c===`usage`){let e=parseFloat(r.state);s.usagePct=isNaN(e)?void 0:Math.round(e)}else c===`mounted`?(s.mountedEntityId=n,s.isMounted=r.state===`on`||r.state===`true`):(c===`temperature`||c===`temp`)&&(s.temp=`${r.state}°C`)}return Array.from(e.values()).sort((e,t)=>e.name.localeCompare(t.name))}render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getDevices();return L`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(t,`Unassigned Storage Devices`,dt,L`
            <span class="badge ${n.length>0?`badge-online`:``}">
              <span class="pulse-dot"></span>
              <span>${n.length} Connected</span>
            </span>
          `)}

        ${n.length===0?L`
              <div class="empty-state">
                ${K(dt,32)}
                <div class="empty-title">No Unassigned Disks Found</div>
                <div class="empty-subtext">All connected disks are assigned to the array or pools.</div>
              </div>
            `:L`
              <div class="disk-list">
                ${n.map(e=>L`
                    <button
                      type="button"
                      class="interactive disk-row"
                      @click=${()=>(e.sizeEntityId||e.mountedEntityId)&&this.openMoreInfo(e.sizeEntityId||e.mountedEntityId)}
                    >
                      <span data-block class="disk-main">
                        <span class="disk-icon ${e.isMounted?`disk-online`:`disk-standby`}">
                          ${K(ut,18)}
                        </span>
                        <span data-block class="disk-info">
                          <span class="disk-name">${e.name}</span>
                          <span class="disk-subtext">
                            ${e.size?e.size:`Disk`}
                            ${e.fsType?` • ${e.fsType}`:``}
                            ${e.temp?` • ${e.temp}`:``}
                          </span>
                        </span>
                      </span>
                      <span data-block class="disk-meta">
                        ${e.usagePct===void 0?z:L`<span class="disk-temp">${e.usagePct}%</span>`}
                        <span class="badge ${e.isMounted?`badge-online`:``}">
                          ${e.isMounted?`MOUNTED`:`UNMOUNTED`}
                        </span>
                      </span>
                    </button>
                  `)}
              </div>
            `}
      </div>
      </ha-card>
    `}},editor:Kt,name:`Unraid Unassigned Devices Card`,description:`Monitor unassigned storage drives, partitions, and external USB disks`});var $=[[`overview`,vt,`Overview`],[`storage`,ut,`Storage`],[`zfs`,nt,`ZFS`],[`shares`,lt,`Shares`],[`remote-shares`,yt,`Remote`],[`unassigned`,dt,`Unassigned`],[`network`,pt,`Network`],[`docker`,rt,`Docker`],[`vms`,mt,`VMs`],[`fans`,st,`Fans`],[`gpu`,ot,`GPU`],[`ups`,ct,`UPS`],[`maintenance`,Dt,`Maintenance`],[`notifications`,$e,`Notifications`]];X({tag:Xe,editorTag:Ze,card:class extends J{static editorTag=Ze;static properties={...J.properties,_activeTab:{state:!0}};constructor(){super(),this._activeTab=`overview`}_onTabKeydown=async e=>{let t=$.findIndex(([e])=>e===this._activeTab),n=getComputedStyle(this).direction===`rtl`,r={ArrowRight:t+(n?-1:1),ArrowLeft:t+(n?1:-1),Home:0,End:$.length-1}[e.key];r!==void 0&&(e.preventDefault(),this._activeTab=$[(r+$.length)%$.length][0],await this.updateComplete,this.shadowRoot?.querySelector(`#tab-${this._activeTab}`)?.focus())};render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`;return L`
      <ha-card>
        <div class="uma-card-content">
        <div class="header">
          <div class="header-main">
            <div class="header-icon">${K(vt,22)}</div>
            <div class="header-titles">
              <span class="header-title">${t} Dashboard</span>
              <span class="header-subtitle">Unraid Management Agent</span>
            </div>
          </div>
        </div>
        <div class="tab-strip" role="tablist" aria-label="Dashboard section" @keydown=${this._onTabKeydown}>
          ${$.map(([e,t,n])=>L`
              <button
                type="button"
                role="tab"
                id="tab-${e}"
                class="tab-btn ${this._activeTab===e?`active`:``}"
                aria-selected=${this._activeTab===e}
                aria-controls="dashboard-panel"
                tabindex=${this._activeTab===e?0:-1}
                @click=${t=>{this._activeTab=e,t.currentTarget.scrollIntoView?.({block:`nearest`,inline:`nearest`})}}
              >
                ${K(t,14)} ${n}
              </button>
            `)}
        </div>
        <div role="tabpanel" id="dashboard-panel" aria-labelledby="tab-${this._activeTab}">
          ${this._activeTab===`overview`?L`<unraid-management-agent-server-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-server-card`,embedded:!0}}></unraid-management-agent-server-card>`:z}
          ${this._activeTab===`storage`?L`<unraid-management-agent-storage-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-storage-card`,embedded:!0}}></unraid-management-agent-storage-card>`:z}
          ${this._activeTab===`zfs`?L`<unraid-management-agent-zfs-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-zfs-card`,embedded:!0}}></unraid-management-agent-zfs-card>`:z}
          ${this._activeTab===`shares`?L`<unraid-management-agent-shares-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-shares-card`,embedded:!0}}></unraid-management-agent-shares-card>`:z}
          ${this._activeTab===`remote-shares`?L`<unraid-management-agent-remote-shares-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-remote-shares-card`,embedded:!0}}></unraid-management-agent-remote-shares-card>`:z}
          ${this._activeTab===`unassigned`?L`<unraid-management-agent-unassigned-devices-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-unassigned-devices-card`,embedded:!0}}></unraid-management-agent-unassigned-devices-card>`:z}
          ${this._activeTab===`network`?L`<unraid-management-agent-network-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-network-card`,embedded:!0}}></unraid-management-agent-network-card>`:z}
          ${this._activeTab===`docker`?L`<unraid-management-agent-docker-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-docker-card`,embedded:!0}}></unraid-management-agent-docker-card>`:z}
          ${this._activeTab===`vms`?L`<unraid-management-agent-vm-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-vm-card`,embedded:!0}}></unraid-management-agent-vm-card>`:z}
          ${this._activeTab===`fans`?L`<unraid-management-agent-fans-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-fans-card`,embedded:!0}}></unraid-management-agent-fans-card>`:z}
          ${this._activeTab===`gpu`?L`<unraid-management-agent-gpu-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-gpu-card`,embedded:!0}}></unraid-management-agent-gpu-card>`:z}
          ${this._activeTab===`ups`?L`<unraid-management-agent-ups-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-ups-card`,embedded:!0}}></unraid-management-agent-ups-card>`:z}
          ${this._activeTab===`maintenance`?L`<unraid-management-agent-maintenance-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-maintenance-card`,embedded:!0}}></unraid-management-agent-maintenance-card>`:z}
          ${this._activeTab===`notifications`?L`<unraid-management-agent-notifications-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-management-agent-notifications-card`,embedded:!0}}></unraid-management-agent-notifications-card>`:z}
        </div>
      </div>
      </ha-card>
    `}},editor:qt,name:`Unraid Unified Dashboard Card`,description:`All-in-one Unraid master card with tabbed overview, storage, ZFS, docker, UPS, and VM monitoring.`});