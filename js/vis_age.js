/* Visualization 1 - Child speech by age (strip plot + rolling median + IQR band) */
class AgeVis {
  constructor(parentId, data) {
    this.parent = document.getElementById(parentId);
    this.all = data;
    this.typicalOnly = false;
    this.showIQR = true;
    this.margin = { top: 12, right: 16, bottom: 44, left: 52 };
    // fixed jitter per recording so dots don't jump on re-render
    this.all.forEach(d => { d._jit = (Math.random() - 0.5) * 0.8; });
    this.init();
  }

  init() {
    this.svg = d3.select(this.parent).append("svg");
    this.g = this.svg.append("g");
    this.gridG = this.g.append("g").attr("class", "grid");
    this.xAxisG = this.g.append("g").attr("class", "axis");
    this.yAxisG = this.g.append("g").attr("class", "axis");
    this.dotsG = this.g.append("g");
    this.band = this.g.append("path").attr("fill", css("--age-1")).attr("fill-opacity", 0.16);
    this.line = this.g.append("path").attr("fill", "none").attr("stroke", css("--ink")).attr("stroke-width", 2.5);
    this.hoverRule = this.g.append("line").attr("stroke", css("--ink-2")).attr("stroke-dasharray", "3,3").style("opacity", 0);
    this.hoverDot = this.g.append("circle").attr("r", 5).attr("fill", css("--ink"))
      .attr("stroke", css("--surface")).attr("stroke-width", 2).style("opacity", 0);
    this.xLabel = this.g.append("text").attr("class", "axis-label").attr("text-anchor", "middle").text("Child's age (months)");
    this.yLabel = this.g.append("text").attr("class", "axis-label").attr("text-anchor", "middle")
      .attr("transform", "rotate(-90)").text("Child vocalizations per hour");
    this.overlay = this.g.append("rect").attr("fill", "transparent");
    this.wrangle();
    this.render();
    onResize(() => this.render());
  }

  wrangle() {
    this.data = this.typicalOnly ? this.all.filter(d => d.typical) : this.all;
    // rolling median over a centered 3-month window, for each month 2..48
    this.summary = d3.range(2, 49).map(m => {
      const w = this.data.filter(d => Math.abs(d.age_mo - m) <= 1).map(d => d.child_voc_hr).sort(d3.ascending);
      return w.length >= 8 ? {
        age: m, n: w.length,
        median: d3.quantileSorted(w, 0.5), q1: d3.quantileSorted(w, 0.25), q3: d3.quantileSorted(w, 0.75)
      } : null;
    }).filter(Boolean);
  }

  render() {
    const W = this.parent.clientWidth, H = Math.max(320, Math.min(440, W * 0.6));
    const m = this.margin, w = W - m.left - m.right, h = H - m.top - m.bottom;
    this.svg.attr("width", W).attr("height", H);
    this.g.attr("transform", `translate(${m.left},${m.top})`);

    const x = d3.scaleLinear().domain([0, 49]).range([0, w]);
    const y = d3.scaleLinear().domain([0, 650]).range([h, 0]).nice();
    this.x = x; this.y = y;

    this.gridG.call(d3.axisLeft(y).ticks(6).tickSize(-w).tickFormat(""));
    this.xAxisG.attr("transform", `translate(0,${h})`).call(d3.axisBottom(x).tickValues([0, 6, 12, 18, 24, 30, 36, 42, 48]));
    this.yAxisG.call(d3.axisLeft(y).ticks(6));
    this.xLabel.attr("x", w / 2).attr("y", h + 38);
    this.yLabel.attr("x", -h / 2).attr("y", -40);

    this.dotsG.selectAll("circle")
      .data(this.data, d => d.recording_id)
      .join(
        enter => enter.append("circle").attr("r", 2.4).attr("opacity", 0),
        update => update,
        exit => exit.transition().duration(300).attr("opacity", 0).remove()
      )
      .attr("cx", d => x(d.age_mo + d._jit))
      .attr("cy", d => y(d.child_voc_hr))
      .attr("fill", d => ageColor(d.age_band))
      .transition().duration(300).attr("opacity", 0.45);

    const area = d3.area().curve(d3.curveMonotoneX).x(d => x(d.age)).y0(d => y(d.q1)).y1(d => y(d.q3));
    const line = d3.line().curve(d3.curveMonotoneX).x(d => x(d.age)).y(d => y(d.median));
    this.band.datum(this.summary).attr("d", area).style("display", this.showIQR ? null : "none");
    this.line.datum(this.summary).attr("d", line);

    // Crosshair + tooltip on the median line
    const bis = d3.bisector(d => d.age).center;
    this.overlay.attr("width", w).attr("height", h)
      .on("mousemove", (event) => {
        const [mx] = d3.pointer(event);
        const s = this.summary[bis(this.summary, x.invert(mx))];
        if (!s) return;
        this.hoverRule.attr("x1", x(s.age)).attr("x2", x(s.age)).attr("y1", 0).attr("y2", h).style("opacity", 1);
        this.hoverDot.attr("cx", x(s.age)).attr("cy", y(s.median)).style("opacity", 1);
        Tooltip.show(tipRows(`Age ${s.age} months`, [
          ["Typical child (median)", fmt0(s.median)],
          ["Middle 50%", `${fmt0(s.q1)}–${fmt0(s.q3)}`],
          ["Recordings (±1 month)", s.n]
        ], "Speech sounds per hour. Half of children fall in the middle range."), event);
      })
      .on("mouseleave", () => {
        this.hoverRule.style("opacity", 0); this.hoverDot.style("opacity", 0); Tooltip.hide();
      });
  }

  setTypical(v) { this.typicalOnly = v; this.wrangle(); this.render(); }
  setIQR(v) { this.showIQR = v; this.render(); }
}
