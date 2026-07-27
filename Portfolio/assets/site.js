// shared: theme toggle (persists across pages) + scroll reveal
(function(){
  var root = document.documentElement;
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
})();
