/* Main: load cleaned data + summary, run the opening game, then build every chart once the story is unlocked */
Promise.all([
  d3.csv("data/el1000_clean.csv", d => ({
    ...d,
    age_mo: +d.age_mo,
    adult_voc_hr: +d.adult_voc_hr,
    child_voc_hr: +d.child_voc_hr,
    talk_quintile: +d.talk_quintile,
    ses_code: +d.ses_code,
    typical: d.typical === "True",
    n_recordings_child: +d.n_recordings_child
  })),
  d3.json("data/summary.json")
]).then(([data, summary]) => {
  fillNumbers(summary);
  fillMethods(summary);
  Story.init(summary);
  // charts are built only after the story is revealed, so they can measure their containers
  Story.whenUnlocked(() => requestAnimationFrame(() => buildCharts(data, summary)));
}).catch(err => {
  console.error(err);
  document.body.classList.remove("locked");
  document.body.insertAdjacentHTML("afterbegin",
    `<p style="background:#fde8e8;padding:12px;margin:0">Could not load the data. Serve this folder with a local web server
     (for example <code>python3 -m http.server</code>) instead of opening the file directly.</p>`);
});

function buildCharts(data, summary) {
  const ageVis = new AgeVis("vis-age", data);
  const scatter = new ScatterVis("vis-hist", "vis-scatter", "sc-readout", "sc-legend", data);
  const echo = new EchoVis("vis-echo", data);
  const stair = new StaircaseVis("vis-staircase", data);
  const same = new SameChildVis("vis-samechild", "samechild-readout", data);
  const bg = new BackgroundVis("vis-background", "bg-note", summary.group_differences);
  new RecapVis("recap", data, summary);

  d3.select("#age-typical").on("change", function () { ageVis.setTypical(this.checked); });
  d3.select("#age-iqr").on("change", function () { ageVis.setIQR(this.checked); });
  d3.select("#sc-typical").on("change", function () { scatter.setTypical(this.checked); });
  scatter.clearButtons();

  // Echo: spacing toggle, quintile shading, hide the "click to enlarge" hint after first use
  d3.select("#echo-quint").on("change", function () { echo.setQuint(this.checked); });
  d3.selectAll("[data-echo]").on("click", function () {
    d3.selectAll("[data-echo]").classed("on", false);
    d3.select(this).classed("on", true);
    echo.setMode(this.dataset.echo);
  });
  echo.onInteract = () => document.getElementById("echo-hint").classList.add("gone");

  d3.select("#st-dots").on("change", function () { stair.setDots(this.checked); });
  d3.select("#st-shared").on("change", function () { stair.setShared(this.checked); });

  d3.select("#sc-gap").on("input", function () { d3.select("#sc-gap-val").text(this.value); same.setGap(+this.value); });
  d3.selectAll("#sc-band button").on("click", function () {
    d3.selectAll("#sc-band button").classed("on", false);
    d3.select(this).classed("on", true);
    same.setBand(this.dataset.band);
  });

  const setBg = m => {
    d3.selectAll("#bg-mode button").classed("on", function () { return this.dataset.mode === m; });
    bg.setMode(m);
  };
  d3.selectAll("#bg-mode button").on("click", function () { setBg(this.dataset.mode); });
  d3.select("#bg-play").on("click", () => { setBg("raw"); setTimeout(() => setBg("adj"), 1300); });
}

function getPath(obj, path) {
  return path.split(".").reduce((o, k) => (o == null ? o : o[k]), obj);
}

function fillNumbers(summary) {
  document.querySelectorAll("[data-s]").forEach(el => {
    const v = getPath(summary, el.dataset.s);
    if (v == null) return;
    if (el.dataset.round === "0") { el.textContent = fmt0(v); return; }
    el.textContent = Number.isInteger(v) ? d3.format(",")(v)
      : Math.abs(v) < 1 ? fmt2(v) : d3.format(".1f")(v).replace(/\.0$/, "");
  });
}

function fillMethods(summary) {
  const mm = summary.mixed_model;
  if (!mm || !mm.available) return;
  document.getElementById("mm-formula").textContent = mm.formula;
  document.getElementById("mm-table").innerHTML =
    `<tr><th>Term</th><th class="n">Estimate (sounds/hr)</th><th class="n">SE</th><th class="n">p</th></tr>` +
    mm.terms.map(t => `<tr><td>${t.term}</td><td class="n">${t.estimate > 0 ? "+" : ""}${t.estimate}</td><td class="n">${t.se}</td><td class="n">${t.p < 0.001 ? "&lt; 0.001" : t.p.toFixed(2)}</td></tr>`).join("");
}
