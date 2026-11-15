/* Visualization 2 - Age histogram (brush) linked to adult-talk vs child-speech scatter */
class ScatterVis {
  constructor(histId, scatterId, readoutId, legendId, data) {
    this.histEl = document.getElementById(histId);
    this.scEl = document.getElementById(scatterId);
    this.readout = document.getElementById(readoutId);
    this.legendEl = document.getElementById(legendId);
    this.all = data;
    this.range = null;          // [minAge, maxAge] or null for all
    this.typicalOnly = false;
    this.byChild = d3.group(data, d => d.child_id);
    this.init();
  }

  init() {
    // legend
    this.legendEl.innerHTML = `<span class="lt">Dot color = age group:</span>` + AGE_BANDS.map(b => `<span><i style="background:${ageColor(b)}"></i>${b}</span>`).join("") +
      `<span><i style="background:${css("--axis")}"></i>outside selected ages</span>` +
      `<span><i class="ln" style="background:${css("--accent")}"></i>trend for selected ages</span>` +
      `<span><i class="ln" style="background:${css("--ink-2")}"></i>trend for all ages (dashed)</span>`;

    // histogram
    this.hSvg = d3.select(this.histEl).append("svg");
    this.hG = this.hSvg.append("g");
    this.hBars = this.hG.append("g");
    this.hAxis = this.hG.append("g").attr("class", "axis");
    this.hLabel = this.hG.append("text").attr("class", "axis-label").text("How many recordings at each age (months). Drag across these bars to choose ages");
    this.brushG = this.hG.append("g").attr("class", "brush");

    // scatter
    this.sSvg = d3.select(this.scEl).append("svg");
    this.sG = this.sSvg.append("g");
    this.gridG = this.sG.append("g").attr("class", "grid");
    this.xAxisG = this.sG.append("g").attr("class", "axis");
    this.yAxisG = this.sG.append("g").attr("class", "axis");
    this.dotsG = this.sG.append("g");
    this.childLine = this.sG.append("path").attr("fill", "none").attr("stroke", css("--ink")).attr("stroke-width", 1.5);
    this.trend = this.sG.append("line").attr("stroke", css("--accent")).attr("stroke-width", 2.5);
    this.trendAll = this.sG.append("line").attr("stroke", css("--ink-2")).attr("stroke-width", 1.5).attr("stroke-dasharray", "5,4");
    this.trendLabel = this.sG.append("text").attr("font-size", 12).attr("fill", css("--ink")).attr("font-weight", 600);
    this.xLabel = this.sG.append("text").attr("class", "axis-label").attr("text-anchor", "middle").text("Adult vocalizations per hour (talk the child heard)");
    this.yLabel = this.sG.append("text").attr("class", "axis-label").attr("text-anchor", "middle").attr("transform", "rotate(-90)").text("Child vocalizations per hour");

    document.querySelectorAll("[data-range]").forEach(btn => btn.addEventListener("click", () => {
      const v = btn.dataset.range;
      this.setBrush(v === "all" ? null : v.split(",").map(Number));
    }));

    this.render();
    onResize(() => this.render());
  }

  get pool() { return this.typicalOnly ? this.all.filter(d => d.typical) : this.all; }
  inRange(d) { return !this.range || (d.age_mo >= this.range[0] && d.age_mo <= this.range[1]); }

  render() {
    const W = this.scEl.clientWidth;
    this.renderHist(W);
    this.renderScatter(W);
    this.update();
  }

  renderHist(W) {
    const m = { top: 22, right: 16, bottom: 22, left: 52 }, H = 110;
    const w = W - m.left - m.right, h = H - m.top - m.bottom;
    this.hSvg.attr("width", W).attr("height", H);
    this.hG.attr("transform", `translate(${m.left},${m.top})`);
    const x = d3.scaleLinear().domain([0, 49]).range([0, w]);
    this.hx = x;
    const counts = d3.rollups(this.pool, v => v.length, d => d.age_mo);
    const y = d3.scaleLinear().domain([0, d3.max(counts, d => d[1])]).range([h, 0]);
    const bandOf = a => AGE_BANDS[Math.min(3, Math.floor(a / 12))];

    this.hBars.selectAll("rect").data(counts, d => d[0]).join("rect")
      .attr("x", d => x(d[0]) + 1).attr("width", Math.max(1, x(1) - x(0) - 2))
      .attr("y", d => y(d[1])).attr("height", d => h - y(d[1]))
      .attr("rx", 2)
      .attr("fill", d => ageColor(bandOf(d[0])));
    this.hAxis.attr("transform", `translate(0,${h})`).call(d3.axisBottom(x).tickValues([0, 12, 24, 36, 48]).tickSize(3));
    this.hLabel.attr("x", 0).attr("y", -8);

    this.brush = d3.brushX().extent([[0, 0], [w, h]])
      .on("brush end", (event) => {
        if (!event.sourceEvent) return;          // ignore programmatic moves
        if (!event.selection) { this.range = null; }
        else {
          const [a, b] = event.selection.map(x.invert);
          // each month's bar spans [m, m+1); snap to whole months
          this.range = [Math.round(a), Math.max(Math.round(a), Math.round(b) - 1)];
        }
        this.clearButtons();
        this.update();
      });
    this.brushG.call(this.brush);
    if (this.range) this.brushG.call(this.brush.move, [x(this.range[0]), x(this.range[1] + 1)]);
  }

  setBrush(range) {
    this.range = range;
    if (range) this.brushG.call(this.brush.move, [this.hx(range[0]), this.hx(range[1] + 1)]);
    else this.brushG.call(this.brush.move, null);
    this.clearButtons(range);
    this.update();
  }

  clearButtons(range) {
    document.querySelectorAll("[data-range]").forEach(b => {
      const v = b.dataset.range;
      b.classList.toggle("on", range ? v === range.join(",") : (v === "all" && !this.range));
    });
  }

  renderScatter(W) {
    const m = { top: 16, right: 20, bottom: 46, left: 52 };
    const H = Math.max(360, Math.min(520, W * 0.55));
    const w = W - m.left - m.right, h = H - m.top - m.bottom;
    this.sw = w; this.sh = h;
    this.sSvg.attr("width", W).attr("height", H);
    this.sG.attr("transform", `translate(${m.left},${m.top})`);
    this.x = d3.scaleLinear().domain([0, 660]).range([0, w]);
    this.y = d3.scaleLinear().domain([0, 660]).range([h, 0]);
    this.gridG.call(d3.axisLeft(this.y).ticks(6).tickSize(-w).tickFormat(""));
    this.xAxisG.attr("transform", `translate(0,${h})`).call(d3.axisBottom(this.x).ticks(7));
    this.yAxisG.call(d3.axisLeft(this.y).ticks(6));
    this.xLabel.attr("x", w / 2).attr("y", h + 38);
    this.yLabel.attr("x", -h / 2).attr("y", -40);
  }

  update() {
    const x = this.x, y = this.y;
    const pool = this.pool;
    const sel = pool.filter(d => this.inRange(d));

    this.dotsG.selectAll("circle")
      .data(pool, d => d.recording_id)
      .join(enter => enter.append("circle").attr("r", 3.2).attr("cx", d => x(d.adult_voc_hr)).attr("cy", d => y(d.child_voc_hr)))
      .attr("cx", d => x(d.adult_voc_hr)).attr("cy", d => y(d.child_voc_hr))
      .attr("stroke", css("--surface")).attr("stroke-width", 0.6)
      .on("mouseenter", (event, d) => this.hover(event, d))
      .on("mousemove", (event) => Tooltip.move(event))
      .on("mouseleave", () => { this.childLine.attr("d", null); Tooltip.hide(); this.dotsG.selectAll("circle").attr("r", 3.2); })
      .transition().duration(250)
      .attr("fill", d => this.inRange(d) ? ageColor(d.age_band) : css("--axis"))
      .attr("opacity", d => this.inRange(d) ? 0.75 : 0.18);
    // keep selected dots on top
    this.dotsG.selectAll("circle").filter(d => this.inRange(d)).raise();

    // trend lines
    const drawLine = (sel2, data) => {
      if (data.length < 5) { sel2.attr("opacity", 0); return null; }
      const { slope, intercept } = linreg(data, d => d.adult_voc_hr, d => d.child_voc_hr);
      const [x0, x1] = d3.extent(data, d => d.adult_voc_hr);
      sel2.transition().duration(300).attr("opacity", 1)
        .attr("x1", x(x0)).attr("y1", y(intercept + slope * x0))
        .attr("x2", x(x1)).attr("y2", y(intercept + slope * x1));
      return { slope, intercept, x1 };
    };
    const allFit = drawLine(this.trendAll, pool);
    this.trendAll.attr("opacity", this.range ? 1 : 0);
    const fit = drawLine(this.trend, sel);
    if (fit) {
      const yEnd = Math.max(12, y(fit.intercept + fit.slope * fit.x1) - 8);
      this.trendLabel.attr("x", Math.min(x(fit.x1), this.sw - 4)).attr("y", yEnd).attr("text-anchor", "end")
        .text(this.range ? "Trend, selected ages" : "Trend, all ages");
    }

    // readout
    const r = pearson(sel, d => d.adult_voc_hr, d => d.child_voc_hr);
    const label = this.range ? `${this.range[0]}–${this.range[1]} months` : "All ages";
    this.readout.innerHTML = `
      <div><b>${label}</b>selected ages</div>
      <div><b>${fmt0(sel.length)}</b>recordings · ${fmt0(new Set(sel.map(d => d.child_id)).size)} children</div>
      <div class="hl"><b>${isNaN(r) ? "–" : fmt2(r)}</b>correlation r (0 = none, 1 = perfect)</div>
      <div class="hl"><b>${fit ? "+" + fmt0(fit.slope * 100) : "–"}</b>more child sounds per +100 adult sounds</div>
      <div><b>${allFit ? "+" + fmt0(allFit.slope * 100) : "–"}</b>same, all ages (dashed)</div>`;
  }

  hover(event, d) {
    const rec = (this.byChild.get(d.child_id) || []).filter(e => !this.typicalOnly || e.typical)
      .slice().sort((a, b) => a.age_mo - b.age_mo);
    this.childLine.attr("d", rec.length > 1 ? d3.line().x(e => this.x(e.adult_voc_hr)).y(e => this.y(e.child_voc_hr))(rec) : null).raise();
    this.dotsG.selectAll("circle").attr("r", e => e.child_id === d.child_id ? 5.5 : 3.2);
    Tooltip.show(tipRows(`One recorded day · ${d.age_mo}-month-old ${d.sex.toLowerCase()}`, [
      ["Adult sounds heard / hr", fmt0(d.adult_voc_hr)],
      ["Child's own sounds / hr", fmt0(d.child_voc_hr)],
      ["Language at home", d.language_bg],
      ["Mother's education", d.mother_ed],
      ["Days recorded for this child", rec.length]
    ], rec.length > 1 ? "The black line links this child's other recorded days." : "This child was recorded once."), event);
  }

  setTypical(v) { this.typicalOnly = v; this.render(); }
}
