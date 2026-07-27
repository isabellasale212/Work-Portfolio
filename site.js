// shared: theme toggle (persists across pages) + scroll reveal
(function(){
  var root = document.documentElement;
  root.classList.add("js"); // enables scroll-reveal; without JS, content stays visible
  try { var saved = localStorage.getItem("theme"); if (saved) root.setAttribute("data-theme", saved); } catch(e){}
  function cur(){ return root.getAttribute("data-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); }
  document.addEventListener("click", function(e){
    var btn = e.target.closest("#theme"); if(!btn) return;
    var next = cur() === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch(err){}
    if (typeof window.__redrawPitch === "function") window.__redrawPitch();
  });

  function reveal(){
    var els = document.querySelectorAll(".reveal");
    if(!("IntersectionObserver" in window)){ els.forEach(function(e){ e.classList.add("in"); }); return; }
    var io = new IntersectionObserver(function(en){ en.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add("in"); io.unobserve(e.target); } }); }, { threshold:.12 });
    els.forEach(function(e){ io.observe(e); });
  }
  if(document.readyState !== "loading") reveal(); else document.addEventListener("DOMContentLoaded", reveal);

  // count-up: animate numbers on scroll into view (reads the element's own text as the target)
  function countups(){
    var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    var els = [].slice.call(document.querySelectorAll(".countup"));
    els.forEach(function(el){
      var node = el.firstChild; while(node && node.nodeType!==3) node = node.nextSibling;
      if(!node) return;
      var raw = node.nodeValue.trim();
      var neg = /^[−-]/.test(raw);
      var num = parseFloat(raw.replace(/[,−-]/g,""));
      if(isNaN(num)){ return; }
      var dec = (raw.split(".")[1]||"").length;
      var comma = /,/.test(raw);
      el._cu = { node:node, to:num, dec:dec, neg:neg, comma:comma };
      set(el, reduce ? num : 0);
    });
    function set(el,v){
      var cu=el._cu, s=v.toLocaleString(undefined,{minimumFractionDigits:cu.dec,maximumFractionDigits:cu.dec});
      if(!cu.comma) s=s.replace(/,/g,"");
      cu.node.nodeValue=(cu.neg?"−":"")+s;
    }
    if(reduce) return;
    function run(el){
      var cu=el._cu, dur=1150, t0=null;
      function step(ts){ if(!t0)t0=ts; var p=Math.min(1,(ts-t0)/dur); var e=1-Math.pow(1-p,3); set(el, cu.to*e); if(p<1) requestAnimationFrame(step); else set(el, cu.to); }
      requestAnimationFrame(step);
    }
    if(!("IntersectionObserver" in window)){ els.forEach(function(el){ if(el._cu) run(el); }); return; }
    var io=new IntersectionObserver(function(en){ en.forEach(function(e){ if(e.isIntersecting && e.target._cu){ run(e.target); io.unobserve(e.target); } }); },{threshold:.4});
    els.forEach(function(el){ if(el._cu) io.observe(el); });
  }
  if(document.readyState !== "loading") countups(); else document.addEventListener("DOMContentLoaded", countups);
})();
