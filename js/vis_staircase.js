/* Vis 4 - Talk staircase: median child speech per fifth of adult talk, small multiples by age band */
class StaircaseVis {
  constructor(parentId, data) {
    this.parent = document.getElementById(parentId);
    this.showDots = false;
    this.shared = true;
    this.panels = AGE_BANDS.map(band => {
      const rows = data.filter(d => d.age_band === band);
      rows.forEach(d => { d._sj = (Math.random() - 0.5) * 0.6; });
      const steps = d3.range(1, 6).map(q => {
        const v = rows.filter(d => d.talk_quintile === q).map(d => d.child_voc_hr).sort(d3.ascending);
        const a = rows.filter(d => d.talk_quintile === q).map(d => d.adult_voc_hr);
        return { q, n: v.length, median: d3.quantileSorted(v, .5), q1: d3.quantileSorted(v, .25), q3: d3.quantileSorted(v, .75),
                 a0: d3.min(a), a1: d3.max(a) };
      });
      return { band, rows, steps };
    });
    this.svg = d3.select(this.parent).append("svg");
    this.render();
    onResize(() => this.render());
  }

  render() {
    const W = this.parent.clientWidth;
    const cols = W < 560 ? 2 : 4, rowsN = Math.ceil(4 / cols);
    const gapX = 14, gapY = 34, m = { top: 8, right: 6, bottom: 34, left: 44 };
    const pw = (W - m.left - m.right - gapX * (cols - 1)) / cols, ph = 230;
    const H = m.top + rowsN * ph + (rowsN - 1) * gapY + m.bottom;
    this.svg.attr("width", W).attr("height", H);
    this.svg.selectAll("*").remove();
    const root = this.svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
    const yMaxShared = this.showDots ? 520 : 360;

    this.panels.forEach((p, i) => {
      const cx = (i % cols) * (pw + gapX), cy = Math.floor(i / cols) * (ph + gapY);
      const g = root.append("g").attr("transform", `translate(${cx},${cy})`);
      const ih = ph - 34;
      const x = d3.scaleLinear().domain([0.5, 5.5]).range([0, pw]);
      const yMax = this.shared ? yMaxShared : (this.showDots ? d3.max(p.rows, d => d.child_voc_hr) : d3.max(p.steps, s => s.q3)) * 1.08;
      const y = d3.scaleLinear().domain([0, yMax]).range([ih, 22]).nice();
      const col = ageColor(p.band);

      g.append("rect").attr("width", pw).attr("height", ih).attr("y", 0).attr("fill", css("--surface"));
      g.append("g").attr("class", "grid").call(d3.axisLeft(y).ticks(4).tickSize(-pw).tickFormat(""));
      if (i % cols === 0 || !this.shared) g.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(4));
      g.append("g").attr("class", "axis").attr("transform", `translate(0,${ih})`)
        .call(d3.axisBottom(x).tickValues([1, 2, 3, 4, 5]).tickFormat(d => ["1st", "2nd", "3rd", "4th", "5th"][d - 1]).tickSize(3));
      g.append("text").attr("x", 0).attr("y", 12).attr("font-weight", 700).attr("font-size", 14).attr("fill", css("--ink")).text(p.band);

      if (this.showDots) {
        g.append("g").selectAll("circle").data(p.rows).join("circle")
          .attr("cx", d => x(d.talk_quintile + d._sj)).attr("cy", d => y(Math.min(d.child_voc_hr, y.domain()[1])))
          .attr("r", 1.8).attr("fill", col).attr("opacity", 0.3);
      }
      // IQR boxes (light)
      g.append("g").selectAll("rect").data(p.steps).join("rect")
        .attr("x", s => x(s.q - 0.42)).attr("width", x(1.84) - x(1)).attr("y", s => y(s.q3)).attr("height", s => y(s.q1) - y(s.q3))
        .attr("fill", col).attr("opacity", this.showDots ? 0.08 : 0.14).attr("rx", 3);
      // staircase line
      const pts = [];
      p.steps.forEach(s => { pts.push([x(s.q - 0.5), y(s.median)]); pts.push([x(s.q + 0.5), y(s.median)]); });
      g.append("path").attr("d", d3.line()(pts)).attr("fill", "none").attr("stroke", col).attr("stroke-width", 3.5).attr("stroke-linejoin", "round");
      g.append("g").selectAll("text").data(p.steps).join("text")
        .attr("x", s => x(s.q)).attr("y", s => y(s.median) - 7).attr("text-anchor", "middle")
        .attr("font-size", 11.5).attr("font-weight", 700).attr("fill", css("--ink"))
        .attr("paint-order", "stroke").attr("stroke", css("--surface")).attr("stroke-width", 3)
        .text(s => fmt0(s.median));

      // annotations on first and last panel
      const first = p.steps[0], last = p.steps[4];
      if (i === 0) g.append("text").attr("class", "anno").attr("x", pw - 2).attr("y", y(last.median) + 24).attr("text-anchor", "end").text("levels off");
      if (i === 3) g.append("text").attr("class", "anno").attr("x", 4).attr("y", 30).text(`${(last.median / first.median).toFixed(1)}× from 1st to 5th`);

      // hover targets
      const hl = g.append("rect").attr("fill", "none").attr("stroke", css("--ink")).attr("stroke-width", 1.5).attr("rx", 4).style("opacity", 0);
      g.append("g").selectAll("rect").data(p.steps).join("rect")
        .attr("x", s => x(s.q - 0.5)).attr("width", x(2) - x(1)).attr("y", 0).attr("height", ih).attr("fill", "transparent")
        .on("mouseenter", (event, s) => {
          hl.attr("x", x(s.q - 0.46)).attr("width", x(1.92) - x(1)).attr("y", y(s.q3) - 3).attr("height", y(s.q1) - y(s.q3) + 6).style("opacity", 1);
          Tooltip.show(tipRows(`${p.band} · ${["quietest", "2nd", "3rd", "4th", "most talkative"][s.q - 1]} fifth`, [
            ["Adult sounds heard / hr", `${fmt0(s.a0)}–${fmt0(s.a1)}`],
            ["Typical child sounds / hr", fmt0(s.median)],
            ["Middle half of children", `${fmt0(s.q1)}–${fmt0(s.q3)}`],
            ["Recordings", s.n]
          ], "Shaded box = middle half of children in this fifth."), event);
        })
        .on("mousemove", e => Tooltip.move(e))
        .on("mouseleave", () => { hl.style("opacity", 0); Tooltip.hide(); });
    });
    root.append("text").attr("class", "axis-label").attr("x", (W - m.left - m.right) / 2).attr("y", H - m.top - 4).attr("text-anchor", "middle")
      .text(W < 560 ? "Fifth of adult talk (1st = quietest)" : "Fifth of adult talk heard, within each age group (1st = quietest homes, 5th = most talkative)");
    root.append("text").attr("class", "axis-label").attr("transform", "rotate(-90)").attr("x", -(H - m.bottom) / 2).attr("y", -34)
      .attr("text-anchor", "middle").text("Child speech sounds per hour");
  }

  setDots(v) { this.showDots = v; this.render(); }
  setShared(v) { this.shared = v; this.render(); }
}
