/* Vis 5 - Same child, different days: slope chart from each child's lowest- to highest-adult-talk day */
class SameChildVis {
  constructor(parentId, readoutId, data) {
    this.parent = document.getElementById(parentId);
    this.readout = document.getElementById(readoutId);
    this.maxGap = 2;
    this.band = "all";
    this.pairs = [];
    d3.group(data, d => d.child_id).forEach((recs, id) => {
      if (recs.length < 2) return;
      const lo = d3.least(recs, d => d.adult_voc_hr), hi = d3.greatest(recs, d => d.adult_voc_hr);
      if (lo === hi) return;
      this.pairs.push({ id, lo, hi, gap: Math.abs(hi.age_mo - lo.age_mo), band: lo.age_band, n: recs.length });
    });
    this.svg = d3.select(this.parent).append("svg");
    this.g = this.svg.append("g");
    this.render();
    onResize(() => this.render());
  }

  get shown() {
    return this.pairs.filter(p => p.gap <= this.maxGap && (this.band === "all" || p.band === this.band));
  }

  render() {
    const W = this.parent.clientWidth, H = 400;
    const m = { top: 20, right: 30, bottom: 50, left: 54 };
    const w = W - m.left - m.right, h = H - m.top - m.bottom;
    this.svg.attr("width", W).attr("height", H);
    this.g.attr("transform", `translate(${m.left},${m.top})`).selectAll("*").remove();
    const data = this.shown;
    const x = d3.scalePoint().domain(["lo", "hi"]).range([w * 0.18, w * 0.82]);
    const y = d3.scaleLinear().domain([0, Math.max(300, d3.max(data, p => Math.max(p.lo.child_voc_hr, p.hi.child_voc_hr)) || 300)]).range([h, 0]).nice();

    this.g.append("g").attr("class", "grid").call(d3.axisLeft(y).ticks(6).tickSize(-w).tickFormat(""));
    this.g.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(6));
    this.g.append("text").attr("class", "axis-label").attr("transform", "rotate(-90)").attr("x", -h / 2).attr("y", -40)
      .attr("text-anchor", "middle").text("Child speech sounds per hour");
    [["lo", "Child's QUIETEST day", "least adult talk"], ["hi", "Child's BUSIEST day", "most adult talk"]].forEach(([k, a, b]) => {
      this.g.append("text").attr("x", x(k)).attr("y", h + 22).attr("text-anchor", "middle").attr("font-weight", 700).attr("font-size", 13).attr("fill", css("--ink")).text(a);
      this.g.append("text").attr("x", x(k)).attr("y", h + 38).attr("text-anchor", "middle").attr("font-size", 12).attr("fill", css("--muted")).text(b);
      this.g.append("line").attr("x1", x(k)).attr("x2", x(k)).attr("y1", 0).attr("y2", h).attr("stroke", css("--axis"));
    });

    const up = p => p.hi.child_voc_hr > p.lo.child_voc_hr;
    const lines = this.g.append("g").selectAll("line").data(data, p => p.id).join("line")
      .attr("x1", x("lo")).attr("x2", x("hi"))
      .attr("y1", p => y(p.lo.child_voc_hr)).attr("y2", p => y(p.hi.child_voc_hr))
      .attr("stroke", p => up(p) ? css("--child") : css("--axis"))
      .attr("stroke-width", 1.6).attr("opacity", data.length > 150 ? 0.35 : 0.6);
    this.g.append("g").selectAll("circle").data(data.flatMap(p => [[p, "lo"], [p, "hi"]])).join("circle")
      .attr("cx", ([, k]) => x(k)).attr("cy", ([p, k]) => y(p[k].child_voc_hr)).attr("r", 2.6)
      .attr("fill", ([p]) => up(p) ? css("--child") : css("--axis"));

    // median line
    if (data.length) {
      const mlo = d3.median(data, p => p.lo.child_voc_hr), mhi = d3.median(data, p => p.hi.child_voc_hr);
      this.g.append("line").attr("x1", x("lo")).attr("x2", x("hi")).attr("y1", y(mlo)).attr("y2", y(mhi))
        .attr("stroke", css("--ink")).attr("stroke-width", 4).attr("stroke-linecap", "round");
      this.g.append("text").attr("class", "anno").attr("x", x("hi") + 8).attr("y", y(mhi) + 4).text(`median ${fmt0(mhi)}`);
      this.g.append("text").attr("class", "anno").attr("x", x("lo") - 8).attr("y", y(mlo) + 4).attr("text-anchor", "end").text(`${fmt0(mlo)}`);
    }

    // hover: invisible fat lines
    const hl = this.g.append("line").attr("stroke", css("--ink")).attr("stroke-width", 2.5).style("opacity", 0).attr("pointer-events", "none");
    this.g.append("g").selectAll("line").data(data, p => p.id).join("line")
      .attr("x1", x("lo")).attr("x2", x("hi")).attr("y1", p => y(p.lo.child_voc_hr)).attr("y2", p => y(p.hi.child_voc_hr))
      .attr("stroke", "transparent").attr("stroke-width", 8).style("cursor", "pointer")
      .on("mouseenter", (event, p) => {
        hl.attr("x1", x("lo")).attr("x2", x("hi")).attr("y1", y(p.lo.child_voc_hr)).attr("y2", y(p.hi.child_voc_hr)).style("opacity", 1);
        const ch = p.hi.child_voc_hr - p.lo.child_voc_hr;
        Tooltip.show(tipRows(`One child · recorded ${p.n} days`, [
          ["Adult sounds/hr: quiet → busy day", `${fmt0(p.lo.adult_voc_hr)} → ${fmt0(p.hi.adult_voc_hr)}`],
          ["Child sounds/hr: quiet → busy day", `${fmt0(p.lo.child_voc_hr)} → ${fmt0(p.hi.child_voc_hr)}`],
          ["Change in child speech", (ch >= 0 ? "+" : "") + fmt0(ch)],
          ["Age on the two days", `${p.lo.age_mo} and ${p.hi.age_mo} months`]
        ], ch >= 0 ? "Talked more on the busier day." : "Talked less on the busier day."), event);
      })
      .on("mousemove", e => Tooltip.move(e))
      .on("mouseleave", () => { hl.style("opacity", 0); Tooltip.hide(); });

    if (!data.length) this.g.append("text").attr("x", w / 2).attr("y", h / 2).attr("text-anchor", "middle").attr("fill", css("--muted")).text("No children match. Try a wider age gap.");

    const nUp = data.filter(up).length;
    const medCh = d3.median(data, p => p.hi.child_voc_hr - p.lo.child_voc_hr);
    this.readout.innerHTML = `
      <div><b>${data.length}</b>children shown</div>
      <div class="hl"><b>${data.length ? Math.round(100 * nUp / data.length) + "%" : "–"}</b>talked more on their busier day</div>
      <div class="hl"><b>${data.length ? (medCh >= 0 ? "+" : "") + fmt0(medCh) : "–"}</b>median change in child sounds/hr</div>
      <div><b>${data.length ? "+" + fmt0(d3.median(data, p => p.hi.adult_voc_hr - p.lo.adult_voc_hr)) : "–"}</b>median extra adult sounds/hr</div>`;
  }

  setGap(v) { this.maxGap = v; this.render(); }
  setBand(b) { this.band = b; this.render(); }
}
