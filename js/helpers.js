/* Shared helpers for all visualizations */
const AGE_BANDS = ["0–11 mo", "12–23 mo", "24–35 mo", "36–48 mo"];
const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const ageColor = d3.scaleOrdinal()
  .domain(AGE_BANDS)
  .range(["--age-0", "--age-1", "--age-2", "--age-3"].map(css));

const fmt0 = d3.format(",.0f");
const fmt2 = d3.format(".2f");

const Tooltip = (() => {
  const el = document.getElementById("tooltip");
  return {
    show(html, event) {
      el.innerHTML = html;
      el.style.opacity = 1;
      this.move(event);
    },
    move(event) {
      const pad = 14, w = el.offsetWidth, h = el.offsetHeight;
      let x = event.clientX + pad, y = event.clientY + pad;
      if (x + w > window.innerWidth - 8) x = event.clientX - w - pad;
      if (y + h > window.innerHeight - 8) y = event.clientY - h - pad;
      el.style.left = x + "px";
      el.style.top = y + "px";
    },
    hide() { el.style.opacity = 0; }
  };
})();

function tipRows(title, rows, foot) {
  return `<div class="t-head">${title}</div>` +
    rows.map(([k, v]) => `<div class="t-row"><span>${k}</span><b>${v}</b></div>`).join("") +
    (foot ? `<div class="t-foot">${foot}</div>` : "");
}

function pearson(data, fx, fy) {
  const n = data.length;
  if (n < 3) return NaN;
  const mx = d3.mean(data, fx), my = d3.mean(data, fy);
  let sxy = 0, sxx = 0, syy = 0;
  data.forEach(d => {
    const dx = fx(d) - mx, dy = fy(d) - my;
    sxy += dx * dy; sxx += dx * dx; syy += dy * dy;
  });
  return sxy / Math.sqrt(sxx * syy);
}

function linreg(data, fx, fy) {
  const mx = d3.mean(data, fx), my = d3.mean(data, fy);
  let sxy = 0, sxx = 0;
  data.forEach(d => { const dx = fx(d) - mx; sxy += dx * (fy(d) - my); sxx += dx * dx; });
  const slope = sxy / sxx;
  return { slope, intercept: my - slope * mx };
}

/* Re-render on container resize (debounced) */
function onResize(fn) {
  let t;
  window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(fn, 150); });
}
