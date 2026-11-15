/* Guided story: 3-step opening game, unlocking the story, scroll reveals, progress + nav highlight */
const Story = (() => {
  let unlocked = false;
  const onUnlock = [];

  function setStep(n) {
    document.querySelectorAll(".game-step").forEach(s => s.classList.toggle("active", +s.dataset.step === n));
    document.querySelectorAll(".game-steps i").forEach((i, k) => i.classList.toggle("done", k < n));
  }

  function setupGame(summary) {
    const quiet = summary.by_age_band[3].quintile_medians[0];
    const loud = summary.by_age_band[3].quintile_medians[4];
    let pick = null;

    document.querySelectorAll(".option").forEach(btn => btn.addEventListener("click", () => {
      document.querySelectorAll(".option").forEach(b => b.classList.remove("picked"));
      btn.classList.add("picked");
      pick = btn.dataset.guess;
      setTimeout(() => setStep(2), 350);
    }));

    const slider = document.getElementById("guess-slider");
    const val = document.getElementById("guess-val");
    slider.addEventListener("input", () => { val.textContent = slider.value; });

    document.getElementById("guess-lock").addEventListener("click", () => {
      const guess = +slider.value;
      setStep(3);
      const max = Math.max(loud, guess, quiet) * 1.1;
      const rows = [
        { lab: "Least adult talk", v: quiet, c: "var(--age-1)" },
        { lab: "Your guess", v: guess, c: "var(--muted)" },
        { lab: "Most adult talk (real)", v: loud, c: "var(--accent)" }
      ];
      document.getElementById("reveal-bars").innerHTML = rows.map(r =>
        `<div class="rb"><span>${r.lab}</span><div class="track"><div class="fill" style="background:${r.c}" data-w="${(r.v / max) * 100}"></div></div><span class="num">${Math.round(r.v)}</span></div>`
      ).join("");
      requestAnimationFrame(() => setTimeout(() => {
        document.querySelectorAll("#reveal-bars .fill").forEach(f => { f.style.width = f.dataset.w + "%"; });
      }, 30));
      const diff = Math.round(guess - loud);
      const close = Math.abs(diff) <= 40;
      const guessLine = close ? `Nice, your guess was within ${Math.abs(diff)} of the real answer.`
        : diff < 0 ? `The real number is ${Math.abs(diff)} higher than you guessed.`
        : `The real number is ${diff} lower than you guessed.`;
      const pickLine = pick === "talk"
        ? "And in step 1 you picked adult talk, which matches the data: it is the more consistent clue."
        : pick === "background"
          ? "In step 1 you picked family background. It's a common assumption, but in this data it's the weaker clue. The story shows why."
          : "";
      document.getElementById("verdict").innerHTML =
        `<strong>${guessLine}</strong> That's about ${(loud / quiet).toFixed(1)}× as many speech sounds for a child in the most talkative fifth of homes. ${pickLine}`;
    });

    document.getElementById("start-story").addEventListener("click", () => unlock(true));
    document.getElementById("skip-game").addEventListener("click", () => unlock(true));
  }

  function unlock(scroll) {
    if (!unlocked) {
      unlocked = true;
      document.body.classList.remove("locked");
      document.querySelectorAll(".locked-link").forEach(a => a.classList.remove("locked-link"));
      document.getElementById("skip-game").style.display = "none";
      onUnlock.forEach(fn => fn());
      setupReveal();
    }
    if (scroll) document.getElementById("growing").scrollIntoView({ behavior: "smooth" });
  }

  function setupReveal() {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add("visible"); obs.unobserve(e.target); } });
    }, { threshold: 0.12 });
    document.querySelectorAll(".reveal").forEach(el => obs.observe(el));
  }

  function setupNavAndProgress() {
    const bar = document.getElementById("progress-bar");
    window.addEventListener("scroll", () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? (window.scrollY / h) * 100 : 0) + "%";
    }, { passive: true });
    const links = [...document.querySelectorAll(".nav a")];
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) links.forEach(a => {
          const on = a.getAttribute("href") === "#" + e.target.id;
          a.classList.toggle("active", on);
          if (on) a.scrollIntoView({ block: "nearest", inline: "center" });
        });
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    document.querySelectorAll("section").forEach(s => obs.observe(s));
    // clicking a chapter link while locked unlocks the story first
    links.forEach(a => a.addEventListener("click", () => { if (!unlocked && a.getAttribute("href") !== "#hook") unlock(false); }));
  }

  return {
    init(summary) { setupGame(summary); setupNavAndProgress(); if (location.hash && location.hash !== "#hook") unlock(false); },
    whenUnlocked(fn) { unlocked ? fn() : onUnlock.push(fn); },
    unlock
  };
})();
