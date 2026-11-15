/* Visualization 3 (novel view) - "The Echo": mirrored waveform per age band.
   Recordings sorted by adult talk; adult talk drawn upward (blue), child speech downward (orange). */
class EchoVis {
  constructor(parentId, data) {
    this.parent = document.getElementById(parentId);
    this.mode = "rank";            // "rank" | "value"
    this.showQuint = true;
    this.expanded = null;          // age band that is enlarged
    this.bands = AGE_BANDS.map(b => {
      const rows = data.filter(d => d.age_band === b).slice().sort((a, c) => a.adult_voc_hr - c.adult_voc_hr);
      rows.forEach((d, i) => { d._rank = (i + 0.5) / rows.length; });
      return {
        band: b, rows,
        r: pearson(rows, d => d.adult_voc_hr, d => d.child_voc_hr),
        quint: d3.range(5).map(q => {
          const s = rows.filter(d => d.talk_quintile === q + 1);
          return { q, median: d3.median(s, d => d.child_voc_hr), adult: d3.median(s, d => d.adult_voc_hr),
                   x0: d3.min(s, d => d._rank), x1: d3.max(s, d => d._rank),
                   a0: d3.min(s, d => d.adult_voc_hr), a1: d3.max(s, d => d.adult_voc_hr) };
        })
      };
    });
    this.svg = d3.select(this.parent).append("svg");
    this.render();
    onResize(() => this.render());
  }

  rolling(rows, key, k) {
    const half = Math.floor(k / 2);
    return rows.map((d, i) => {
      const w = rows.slice(Math.max(0, i - half), i + half + 1).map(e => e[key]);
      return { d, v: d3.median(w) };
    });
  }

  render() {
    const W = this.parent.clientWidth;
    const m = { top: 8, right: 46, bottom: 58, left: 118 };
    const w = W - m.left - m.right;
    const baseH = 150, bigH = 280, smallH = 96, gap = 18;
    const heights = this.bands.map(b => this.expanded ? (b.band === this.expanded ? bigH : smallH) : baseH);
    const H = m.top + d3.sum(heights) + gap * (this.bands.length - 1) + m.bottom;
    this.svg.attr("width", W).attr("height", H);
    this.svg.selectAll("*").remove();
    const root = this.svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

    const xRank = d3.scaleLinear().domain([0, 1]).range([0, w]);
    const xVal = d3.scaleLinear().domain([0, 660]).range([0, w]);
    const xOf = d => this.mode === "rank" ? xRank(d._rank) : xVal(d.adult_voc_hr);

    let yOff = 0;
    this.bands.forEach((b, bi) => {
      const hh = heights[bi], half = hh / 2;
      const isBig = this.expanded === b.band;
      const g = root.append("g").attr("transform", `translate(0,${yOff})`)
        .attr("class", "echo-band" + (isBig ? " expanded" : ""));
      const toggle = () => {
        this.expanded = isBig ? null : b.band; Tooltip.hide();
        if (this.onInteract) this.onInteract();
        this.render();
      };
      const yUp = d3.scaleLinear().domain([0, 480]).range([half, 4]).clamp(true);
      const yDn = d3.scaleLinear().domain([0, 480]).range([half, hh - 4]).clamp(true);
      const bw = this.mode === "rank" ? Math.max(0.6, w / b.rows.length - 0.3) : 1.2;

      // background + labels
      g.append("rect").attr("x", -m.left + 4).attr("width", W - 8).attr("y", -4).attr("height", hh + 8)
        .attr("fill", "transparent");
      g.append("text").attr("x", -m.left + 8).attr("y", half - 8).attr("font-weight", 700).attr("font-size", 14)
        .attr("fill", css("--ink")).text(b.band);
      g.append("text").attr("x", -m.left + 8).attr("y", half + 10).attr("font-size", 12).attr("fill", css("--ink-2"))
        .text(`${b.rows.length} recordings`);
      g.append("text").attr("x", -m.left + 8).attr("y", half + 26).attr("font-size", 12).attr("fill", css("--ink-2"))
        .text(`r = ${fmt2(b.r)}`);
      // visible expand / collapse button
      const btn = g.append("g").attr("transform", `translate(${w + 10},${half - 13})`).style("cursor", "pointer")
        .attr("role", "button").attr("tabindex", 0).attr("aria-label", (isBig ? "Shrink " : "Enlarge ") + b.band)
        .on("click", toggle).on("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
      btn.append("rect").attr("width", 26).attr("height", 26).attr("rx", 7).attr("fill", isBig ? css("--ink") : css("--surface"))
        .attr("stroke", css("--axis"));
      btn.append("path").attr("d", isBig ? "M9 9l8 8M17 9l-8 8" : "M7 11V7h4M19 11V7h-4M7 15v4h4M19 15v4h-4")
        .attr("fill", "none").attr("stroke", isBig ? "#fff" : css("--ink")).attr("stroke-width", 1.8).attr("stroke-linecap", "round");

      // quintile shading
      if (this.showQuint && this.mode === "rank") {
        b.quint.forEach((q, qi) => {
          if (qi % 2 === 1) g.append("rect").attr("x", xRank(q.x0 - 0.5 / b.rows.length)).attr("width", xRank(q.x1) - xRank(q.x0) + w / b.rows.length)
            .attr("y", 0).attr("height", hh).attr("fill", css("--grid")).attr("opacity", 0.45);
        });
      }

      // bars
      g.append("g").selectAll("rect").data(b.rows).join("rect")
        .attr("x", d => xOf(d) - bw / 2).attr("width", bw)
        .attr("y", d => yUp(d.adult_voc_hr)).attr("height", d => half - yUp(d.adult_voc_hr))
        .attr("fill", css("--adult")).attr("opacity", 0.35);
      g.append("g").selectAll("rect").data(b.rows).join("rect")
        .attr("x", d => xOf(d) - bw / 2).attr("width", bw)
        .attr("y", half).attr("height", d => yDn(d.child_voc_hr) - half)
        .attr("fill", css("--child")).attr("opacity", 0.35);

      // rolling medians
      const k = Math.max(15, Math.round(b.rows.length * 0.15));
      const upLine = d3.line().curve(d3.curveMonotoneX).x(p => xOf(p.d)).y(p => yUp(p.v));
      const dnLine = d3.line().curve(d3.curveMonotoneX).x(p => xOf(p.d)).y(p => yDn(p.v));
      g.append("path").attr("d", upLine(this.rolling(b.rows, "adult_voc_hr", k)))
        .attr("fill", "none").attr("stroke", css("--adult")).attr("stroke-width", 2.5);
      // child speech: median of each fifth drawn as a step ("staircase") so the widening gap is legible
      if (this.mode === "rank") {
        b.quint.forEach(q => {
          const xa = xRank(q.x0 - 0.5 / b.rows.length), xb = xRank(q.x1 + 0.5 / b.rows.length);
          g.append("line").attr("x1", xa + 2).attr("x2", xb - 2).attr("y1", yDn(q.median)).attr("y2", yDn(q.median))
            .attr("stroke", css("--child")).attr("stroke-width", 3).attr("stroke-linecap", "round");
        });
      } else {
        g.append("path").attr("d", dnLine(this.rolling(b.rows, "child_voc_hr", k)))
          .attr("fill", "none").attr("stroke", css("--child")).attr("stroke-width", 2.5);
      }

      // baseline
      g.append("line").attr("x1", 0).attr("x2", w).attr("y1", half).attr("y2", half).attr("stroke", css("--ink-2"));

      // quintile labels (median child speech in each fifth)
      if (this.showQuint && this.mode === "rank" && hh >= 120) {
        b.quint.forEach(q => {
          g.append("text").attr("x", xRank((q.x0 + q.x1) / 2)).attr("y", Math.min(hh - 2, yDn(q.median) + 15)).attr("text-anchor", "middle")
            .attr("font-size", 12).attr("font-weight", 600).attr("fill", css("--ink"))
            .attr("paint-order", "stroke").attr("stroke", css("--surface")).attr("stroke-width", 3)
            .text(`${fmt0(q.median)}`);
        });
      }

      // hover overlay
      const hl = g.append("rect").attr("fill", "none").attr("stroke", css("--ink")).attr("stroke-width", 1.2).style("opacity", 0);
      g.append("rect").attr("width", w).attr("height", hh).attr("fill", "transparent")
        .on("mousemove", (event) => {
          const [mx] = d3.pointer(event);
          let d;
          if (this.mode === "rank") {
            d = b.rows[Math.max(0, Math.min(b.rows.length - 1, Math.floor(xRank.invert(mx) * b.rows.length)))];
          } else {
            const v = xVal.invert(mx);
            d = b.rows[Math.min(b.rows.length - 1, d3.bisector(e => e.adult_voc_hr).center(b.rows, v))];
          }
          hl.attr("x", xOf(d) - Math.max(bw, 3) / 2 - 1).attr("width", Math.max(bw, 3) + 2)
            .attr("y", yUp(d.adult_voc_hr)).attr("height", yDn(d.child_voc_hr) - yUp(d.adult_voc_hr)).style("opacity", 1);
          Tooltip.show(tipRows(`One recorded day · ${d.age_mo} months old`, [
            ["Adult sounds heard / hr", fmt0(d.adult_voc_hr)],
            ["Child's own sounds / hr", fmt0(d.child_voc_hr)],
            ["Adult-talk fifth", `${d.talk_quintile} of 5`],
            ["Typical child in this fifth", fmt0(b.quint[d.talk_quintile - 1].median)]
          ], isBig ? "Click to shrink back" : "Click to enlarge this age band"), event);
        })
        .on("mouseleave", () => { hl.style("opacity", 0); Tooltip.hide(); })
        .on("click", toggle);

      yOff += hh + gap;
    });

    // x axis
    const axG = root.append("g").attr("class", "axis").attr("transform", `translate(0,${yOff - gap + 4})`);
    if (this.mode === "rank") {
      axG.call(d3.axisBottom(xRank).tickValues([0, .2, .4, .6, .8, 1]).tickFormat(d => d === 0 ? "least talk" : d === 1 ? "most talk" : d3.format(".0%")(d)));
      axG.selectAll(".tick text").attr("text-anchor", (d) => d === 0 ? "start" : d === 1 ? "end" : "middle");
      root.append("text").attr("class", "axis-label").attr("x", w / 2).attr("y", yOff - gap + 44).attr("text-anchor", "middle")
        .text("Recordings ranked by adult talk heard (within age band); orange steps & numbers = typical child speech sounds/hr in each fifth");
    } else {
      axG.call(d3.axisBottom(xVal).ticks(7));
      root.append("text").attr("class", "axis-label").attr("x", w / 2).attr("y", yOff - gap + 44).attr("text-anchor", "middle")
        .text("Adult vocalizations per hour heard");
    }
  }

  setMode(m) { this.mode = m; this.render(); }
  setQuint(v) { this.showQuint = v; this.render(); }
}
