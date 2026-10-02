/* Yarn Yardage Calculator — shared data + logic.
   Yardage figures are planning estimates (yards) for an average-size project,
   drawn from standard craft guides (Lion Brand, Craft Yarn Council charts).
   In the browser this file wires up the calculator widget; in Node it can be
   required for testing: const c = require('./calculator.js') */

var YARN_WEIGHTS = [
  { id: "lace",       name: "Lace (0)",                skeinYards100g: 700 },
  { id: "fingering",  name: "Super Fine / Fingering (1)", skeinYards100g: 440 },
  { id: "sport",      name: "Fine / Sport (2)",        skeinYards100g: 330 },
  { id: "dk",         name: "Light / DK (3)",          skeinYards100g: 280 },
  { id: "worsted",    name: "Medium / Worsted (4)",    skeinYards100g: 220 },
  { id: "bulky",      name: "Bulky (5)",               skeinYards100g: 120 },
  { id: "superbulky", name: "Super Bulky (6)",         skeinYards100g: 70 }
];

var WEIGHT_ORDER = ["lace", "fingering", "sport", "dk", "worsted", "bulky", "superbulky"];

/* Estimated yardage (yards) per project per yarn weight. Missing entries mean
   that weight is uncommon for the project; the calculator falls back to the
   nearest available weight and says so. */
var PROJECT_YARDAGE = {
  "baby-blanket":  { lace: 1550, fingering: 1400, sport: 1200, dk: 1150, worsted: 1050, bulky: 900, superbulky: 800 },
  "throw-blanket": { fingering: 3200, sport: 3000, dk: 2600, worsted: 2200, bulky: 1750, superbulky: 1400 },
  "twin-blanket":  { dk: 4000, worsted: 3200, bulky: 2400, superbulky: 1800 },
  "queen-blanket": { dk: 6000, worsted: 4600, bulky: 3400, superbulky: 2600 },
  "king-blanket":  { dk: 8500, worsted: 6500, bulky: 4800, superbulky: 3600 },
  "scarf":         { lace: 700, fingering: 500, sport: 425, dk: 400, worsted: 350, bulky: 300, superbulky: 225 },
  "cowl":          { fingering: 450, sport: 400, dk: 350, worsted: 300, bulky: 250, superbulky: 200 },
  "hat":           { fingering: 300, sport: 280, dk: 225, worsted: 200, bulky: 160, superbulky: 130 },
  "socks":         { fingering: 450, sport: 400, dk: 375 },
  "mittens":       { fingering: 250, sport: 230, dk: 210, worsted: 180, bulky: 150 },
  "sweater":       { fingering: 2000, sport: 1900, dk: 1700, worsted: 1400, bulky: 1050, superbulky: 950 },
  "baby-sweater":  { fingering: 800, sport: 750, dk: 700, worsted: 600, bulky: 500 },
  "cardigan":      { fingering: 2200, sport: 2100, dk: 1900, worsted: 1600, bulky: 1250 },
  "shawl":         { lace: 900, fingering: 700, sport: 550, dk: 500, worsted: 450, bulky: 425 },
  "vest":          { sport: 1100, dk: 1000, worsted: 900, bulky: 750 },
  "market-bag":    { sport: 400, dk: 350, worsted: 300, bulky: 250 },
  "amigurumi":     { fingering: 150, sport: 130, dk: 110, worsted: 90 },
  "rug":           { worsted: 1200, bulky: 1000, superbulky: 800 }
};

var PROJECT_LABELS = {
  "baby-blanket": "Baby blanket",
  "throw-blanket": "Throw blanket",
  "twin-blanket": "Twin-size blanket",
  "queen-blanket": "Queen-size blanket",
  "king-blanket": "King-size blanket",
  "scarf": "Scarf",
  "cowl": "Cowl",
  "hat": "Hat / beanie",
  "socks": "Socks (pair)",
  "mittens": "Mittens",
  "sweater": "Adult sweater",
  "baby-sweater": "Baby sweater",
  "cardigan": "Cardigan",
  "shawl": "Shawl",
  "vest": "Vest",
  "market-bag": "Market bag",
  "amigurumi": "Amigurumi toy",
  "rug": "Rug"
};

function weightById(id) {
  for (var i = 0; i < YARN_WEIGHTS.length; i++) {
    if (YARN_WEIGHTS[i].id === id) return YARN_WEIGHTS[i];
  }
  return null;
}

/* Pure calculation: returns { yards, bufferedYards, meters, skeins, usedWeight, fellBack } */
function calculate(projectKey, weightId, skeinYards, bufferPct) {
  var table = PROJECT_YARDAGE[projectKey];
  if (!table) return null;
  var usedWeight = weightId, fellBack = false;
  if (table[weightId] == null) {
    // fall back to the nearest weight that has data for this project
    var target = WEIGHT_ORDER.indexOf(weightId);
    var best = null, bestDist = 99;
    for (var w in table) {
      if (!table.hasOwnProperty(w)) continue;
      var d = Math.abs(WEIGHT_ORDER.indexOf(w) - target);
      if (d < bestDist) { bestDist = d; best = w; }
    }
    usedWeight = best; fellBack = true;
  }
  var yards = table[usedWeight];
  var buffered = Math.round(yards * (1 + bufferPct / 100));
  var skeins = Math.ceil(buffered / skeinYards);
  return {
    yards: yards,
    bufferedYards: buffered,
    meters: Math.round(buffered * 0.9144),
    skeins: skeins,
    usedWeight: usedWeight,
    fellBack: fellBack
  };
}

/* ---- browser widget wiring ---- */
function initCalculator(rootId) {
  var root = document.getElementById(rootId || "yarn-calc");
  if (!root) return;
  var projSel = root.querySelector("[data-field=project]");
  var weightSel = root.querySelector("[data-field=weight]");
  var skeinInput = root.querySelector("[data-field=skein]");
  var bufferInput = root.querySelector("[data-field=buffer]");
  var out = root.querySelector("[data-field=result]");

  // populate selects
  Object.keys(PROJECT_LABELS).forEach(function (k) {
    var o = document.createElement("option");
    o.value = k; o.textContent = PROJECT_LABELS[k];
    projSel.appendChild(o);
  });
  YARN_WEIGHTS.forEach(function (w) {
    var o = document.createElement("option");
    o.value = w.id; o.textContent = w.name;
    weightSel.appendChild(o);
  });

  var preset = root.getAttribute("data-preset-project");
  if (preset && PROJECT_LABELS[preset]) projSel.value = preset;
  weightSel.value = "worsted";

  function refreshSkeinDefault() {
    var w = weightById(weightSel.value);
    if (w && !skeinInput.dataset.touched) skeinInput.value = w.skeinYards100g;
  }
  skeinInput.addEventListener("input", function () { skeinInput.dataset.touched = "1"; });
  weightSel.addEventListener("change", function () {
    delete skeinInput.dataset.touched;
    refreshSkeinDefault();
    render();
  });

  function render() {
    var skeinYards = parseFloat(skeinInput.value);
    if (!(skeinYards > 0)) skeinYards = weightById(weightSel.value).skeinYards100g;
    var buffer = parseFloat(bufferInput.value);
    if (!(buffer >= 0)) buffer = 10;
    var r = calculate(projSel.value, weightSel.value, skeinYards, buffer);
    var note = r.fellBack
      ? "<p class='note'>Estimate shown for " + weightById(r.usedWeight).name +
        " (closest available weight for this project).</p>"
      : "";
    out.innerHTML =
      "<div class='result-grid'>" +
      "<div class='result-box'><span class='result-num'>" + r.bufferedYards.toLocaleString() + "</span>" +
      "<span class='result-label'>yards needed (" + r.meters.toLocaleString() + " m)</span></div>" +
      "<div class='result-box'><span class='result-num'>" + r.skeins + "</span>" +
      "<span class='result-label'>skeins of " + Math.round(skeinYards) + " yd</span></div>" +
      "</div>" + note +
      "<p class='note'>Includes a " + buffer + "% buffer for gauge differences and mistakes. " +
      "Base estimate before buffer: " + r.yards.toLocaleString() + " yards.</p>";
  }

  projSel.addEventListener("change", render);
  skeinInput.addEventListener("input", render);
  bufferInput.addEventListener("input", render);
  refreshSkeinDefault();
  render();
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", function () {
    var widgets = document.querySelectorAll("#yarn-calc");
    for (var i = 0; i < widgets.length; i++) initCalculator(widgets[i].id);
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    YARN_WEIGHTS: YARN_WEIGHTS,
    PROJECT_YARDAGE: PROJECT_YARDAGE,
    PROJECT_LABELS: PROJECT_LABELS,
    calculate: calculate,
    weightById: weightById
  };
}
