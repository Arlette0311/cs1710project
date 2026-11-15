/* Vis 7 - Main-message recap: three tiles, each with a headline number and a mini chart */
class RecapVis {
  constructor(parentId, data, summary) {
    this.parent = document.getElementById(parentId);
    this.data = data; this.s = summary;
    this.drawn = false;
    const bands = summary.by_age_band;
    const gd = Object.values(summary.group_differences).flat();
    const maxAdj = d3.max(gd, g => Math.abs(g.adj)), maxRaw = d3.max(gd, g => Math.abs(g.raw));
    const med6 = this.medianAt(6), med36 = this.medianAt(36);
    this.tiles = [
      { num: `${(med36 / med6).toFixed(1)}×`, lab: `more speech sounds at 3 years (${fmt0(med36)}/hr) than at 6 months (${fmt0(med6)}/hr)`, draw: el => this.spark(el), go: "#growing" },
      { num: `r ${fmt2(bands[0].r)} → ${fmt2(bands[3].r)}`, lab: "the talk–speech link from babies to 3–4-year-olds. It strengthens with age.", draw: el => this.rBars(el), go: "#talk" },
      { num: `${fmt0(maxRaw)} → ${fmt0(maxAdj)}/hr`, lab: "largest background gap: raw vs. same age, same talk, same team", draw: el => this.bgDots(el), go: "#background" }
    ];
    const sel = d3.select(this.parent).selectAll(".tile").data(this.tiles).join("div").attr("class", "tile");
    sel.html(t => `<div class="tnum">${t.num}</div><div class="tlab">${t.lab}</div><div class="mini"></div>
      <a href="${t.go}" style="color:#ffb48f;font-size:13px;font-weight:600;text-decoration:none">Revisit chart ↑</a>`);
    // draw (and animate) when scrolled into view
    const obs = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting && !this.drawn) { this.drawn = true; this.drawAll(); } }), { threshold: 0.3 });
    obs.observe(this.parent);
    onResize(() => { if (this.drawn) this.drawAll(); });
  }

  medianAt(m) { return d3.median(this.data.filter(d => Math.abs(d.age_mo - m) <= 1), d => d.child_voc_hr); }

  drawAll() {
    d3.select(this.parent).selectAll(".mini").each((t, i, nodes) => {
      const el = d3.select(nodes[i]); el.selectAll("*").remove();
      this.tiles[i].draw(el);
    });
  }

  frame(el) {
    const W = el.node().clientWidth || 280, H = 96;
    return { svg: el.append("svg").attr("width", W).attr("height", H), W, H };
  }

  spark(el) {
    const { svg, W, H } = this.frame(el);
    const pts = d3.range(2, 49).map(a => ({ a, v: this.medianAt(a) })).filter(p => p.v != null);
    const x = d3.scaleLinear().domain([2, 48]).range([4, W - 4]);
    const y = d3.scaleLinear().domain([0, 280]).range([H - 16, 4]);
    const path = svg.append("path").datum(pts).attr("fill", "none").attr("stroke", "#ffb48f").attr("stroke-width", 2.5)
      .attr("d", d3.line().curve(d3.curveMonotoneX).x(p => x(p.a)).y(p => y(p.v)));
    const L = path.node().getTotalLength();
    path.attr("stroke-dasharray", L).attr("stroke-dashoffset", L).transition().duration(1400).attr("stroke-dashoffset", 0);
    [[6, "6 mo"], [36, "3 yrs"]].forEach(([a, lab]) => {
      svg.append("circle").attr("cx", x(a)).attr("cy", y(this.medianAt(a))).attr("r", 4).attr("fill", "#fff");
      svg.append("text").attr("x", x(a)).attr("y", H - 2).attr("text-anchor", "middle").attr("font-size", 11).attr("fill", "#9fb0d3").text(lab);
    });
  }

  rBars(el) {
    const { svg, W, H } = this.frame(el);
    const b = this.s.by_age_band;
    const x = d3.scaleBand().domain(b.map(d => d.band)).range([0, W]).padding(0.28);
    const y = d3.scaleLinear().domain([0, 0.6]).range([H - 16, 6]);
    svg.selectAll("rect").data(b).join("rect").attr("x", d => x(d.band)).attr("width", x.bandwidth()).attr("rx", 4)
      .attr("y", y(0)).attr("height", 0).attr("fill", d => ageColor(d.band))
      .transition().duration(900).delay((d, i) => i * 150).attr("y", d => y(d.r)).attr("height", d => y(0) - y(d.r));
    svg.selectAll(".v").data(b).join("text").attr("x", d => x(d.band) + x.bandwidth() / 2).attr("y", d => y(d.r) - 4)
      .attr("text-anchor", "middle").attr("font-size", 11).attr("font-weight", 700).attr("fill", "#fff").text(d => fmt2(d.r));
    svg.selectAll(".l").data(b).join("text").attr("x", d => x(d.band) + x.bandwidth() / 2).attr("y", H - 2)
      .attr("text-anchor", "middle").attr("font-size", 10.5).attr("fill", "#9fb0d3").text(d => d.band.replace(" mo", ""));
  }

  bgDots(el) {
    const { svg, W, H } = this.frame(el);
    const gd = Object.values(this.s.group_differences).flat();
    const x = d3.scaleLinear().domain([-25, 50]).range([6, W - 6]);
    svg.append("line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", 4).attr("y2", H - 16).attr("stroke", "#ffb48f").attr("stroke-width", 1.5);
    [["raw", 28, "raw"], ["adj", 62, "fair"]].forEach(([k, yy, lab]) => {
      svg.append("text").attr("x", 0).attr("y", yy - 12).attr("font-size", 10.5).attr("fill", "#9fb0d3").text(lab);
      svg.selectAll(".d" + k).data(gd).join("circle").attr("cy", yy).attr("r", 4.5)
        .attr("cx", x(0)).attr("fill", k === "raw" ? "#6d82ad" : "#fff").attr("opacity", 0.9)
        .transition().duration(1000).attr("cx", g => x(g[k]));
    });
    svg.append("text").attr("x", x(0)).attr("y", H - 2).attr("text-anchor", "middle").attr("font-size", 10.5).attr("fill", "#9fb0d3").text("0 = no difference");
  }
}
