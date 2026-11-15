/* Vis 6 - Background comparison: group difference from average child, raw vs. same-age/same-talk/same-team */
class BackgroundVis {
  constructor(parentId, noteId, groupDiffs) {
    this.parent = document.getElementById(parentId);
    this.note = document.getElementById(noteId);
    this.mode = "raw";
    const titles = { sex: "Boy or girl", language_bg: "Languages at home", mother_ed: "Mother's education" };
    this.rows = [];
    Object.entries(groupDiffs).forEach(([key, groups]) => {
      this.rows.push({ header: titles[key] });
      groups.forEach(g => this.rows.push({ ...g, key }));
    });
    this.svg = d3.select(this.parent).append("svg");
    this.root = this.svg.append("g");
    this.layout();
    onResize(() => { this.layout(); });
  }

  layout() {
    const W = this.parent.clientWidth;
    const labelW = Math.min(230, W * 0.36);
    this.m = { top: 30, right: 24, bottom: 44, left: labelW };
    const rowH = 30, headH = 34;
    let yy = 0;
    this.rows.forEach(r => { r.y = yy + (r.header ? headH - 10 : rowH / 2); yy += r.header ? headH : rowH; });
    const h = yy, w = W - this.m.left - this.m.right;
    this.w = w; this.h = h;
    this.svg.attr("width", W).attr("height", h + this.m.top + this.m.bottom);
    this.root.attr("transform", `translate(${this.m.left},${this.m.top})`).selectAll("*").remove();
    this.x = d3.scaleLinear().domain([-35, 65]).range([0, w]);
    const x = this.x;

    this.root.append("g").attr("class", "grid").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x).ticks(6).tickSize(-h).tickFormat(""));
    this.root.append("g").attr("class", "axis").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x).ticks(6).tickFormat(d => (d > 0 ? "+" : "") + d));
    this.root.append("text").attr("class", "axis-label").attr("x", w / 2).attr("y", h + 36).attr("text-anchor", "middle")
      .text("Difference from the average child, in speech sounds per hour");
    this.root.append("line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", -8).attr("y2", h).attr("stroke", css("--accent")).attr("stroke-width", 2);
    this.zeroLab = this.root.append("text").attr("class", "anno").attr("x", x(0) + 6).attr("y", -14).attr("fill", css("--accent"));
    this.root.append("text").attr("class", "anno").attr("x", x(-35)).attr("y", -14).attr("fill", css("--muted")).text("← fewer sounds");
    this.root.append("text").attr("class", "anno").attr("x", x(65)).attr("y", -14).attr("text-anchor", "end").attr("fill", css("--muted")).text("more sounds →");

    // labels
    this.rows.forEach(r => {
      if (r.header) {
        this.root.append("text").attr("x", -this.m.left + 4).attr("y", r.y).attr("font-weight", 800).attr("font-size", 13)
          .attr("fill", css("--accent")).text(r.header.toUpperCase()).attr("letter-spacing", ".05em");
      } else {
        this.root.append("text").attr("x", -12).attr("y", r.y + 4).attr("text-anchor", "end").attr("font-size", 13.5)
          .attr("fill", css("--ink")).text(r.group);
        this.root.append("text").attr("x", -12).attr("y", r.y + 17).attr("text-anchor", "end").attr("font-size", 10.5)
          .attr("fill", css("--muted")).text(`${r.n} recordings`);
      }
    });
    const data = this.rows.filter(r => !r.header);
    this.ranges = this.root.append("g").selectAll("rect").data(data).join("rect")
      .attr("y", r => r.y - 4).attr("height", 8).attr("rx", 4).attr("fill", css("--ink")).attr("opacity", 0.16);
    this.dots = this.root.append("g").selectAll("circle").data(data).join("circle")
      .attr("cy", r => r.y).attr("r", 7).attr("fill", css("--ink")).attr("stroke", css("--surface")).attr("stroke-width", 2);
    this.vals = this.root.append("g").selectAll("text").data(data).join("text")
      .attr("y", r => r.y + 4).attr("font-size", 12).attr("font-weight", 700).attr("fill", css("--ink"));
    // hover rows
    this.root.append("g").selectAll("rect").data(data).join("rect")
      .attr("x", -this.m.left).attr("width", this.m.left + w).attr("y", r => r.y - 14).attr("height", 28).attr("fill", "transparent")
      .on("mouseenter", (event, r) => {
        const v = r[this.mode], lo = r[this.mode + "_lo"], hi = r[this.mode + "_hi"];
        Tooltip.show(tipRows(r.group, [
          [this.mode === "raw" ? "Raw difference" : "Fair-comparison difference", (v > 0 ? "+" : "") + v.toFixed(1) + "/hr"],
          ["95% range", `${lo.toFixed(0)} to ${hi.toFixed(0)}`],
          ["Recordings · children", `${r.n} · ${r.children}`],
          ["Average age", `${r.mean_age} months`]
        ], lo <= 0 && hi >= 0 ? "Range crosses 0: no clear difference." : "Range doesn't cross 0: a clear difference in this view."), event);
      })
      .on("mousemove", e => Tooltip.move(e))
      .on("mouseleave", () => Tooltip.hide());
    this.update(false);
  }

  update(animate = true) {
    const x = this.x, k = this.mode, t = animate ? 900 : 0;
    const clampX = v => x(Math.max(-35, Math.min(65, v)));
    this.ranges.transition().duration(t).attr("x", r => clampX(r[k + "_lo"])).attr("width", r => clampX(r[k + "_hi"]) - clampX(r[k + "_lo"]));
    this.dots.transition().duration(t).attr("cx", r => clampX(r[k]))
      .attr("fill", r => (r[k + "_lo"] > 0 || r[k + "_hi"] < 0) ? css("--accent") : css("--ink"));
    this.vals.transition().duration(t).attr("x", r => clampX(r[k + "_hi"]) + 8).text(r => { const v = Math.round(r[k]); return (v > 0 ? "+" : "") + (v === 0 ? "0" : v); });
    this.zeroLab.text(k === "raw" ? "0 = average child" : "0 = what age, adult talk & team predict");
    this.note.innerHTML = k === "raw"
      ? "<b>Raw averages:</b> orange dots differ clearly from the average child. The less-than-high-school group looks well ahead, but it's older and mostly from one team."
      : "<b>Fair comparison</b> (same age, same adult talk, same research team): every range crosses zero. Background adds little once these are accounted for. A mixed model agrees (see Methods at the bottom).";
  }

  setMode(m) { this.mode = m; this.update(true); }
}
