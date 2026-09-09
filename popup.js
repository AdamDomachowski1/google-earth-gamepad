/* gepad - the settings popup, and the live pad readout: press a button and
 * read off the number to put in the mapping below it. */

const SLIDERS = ["deadzone", "radiusFrac", "smoothIn", "smoothOut"];
const CHECKS = ["invertPitch", "hud"];
const MAPPING = {
  axRoll: "roll axis",
  axPitch: "pitch axis",
  btnClick: "click",
  btnEsc: "escape",
  btnLT: "left trigger",
  btnRT: "right trigger",
  btnArm: "arm",
  btnYokeMode: "yoke mode",
};

const $ = (id) => document.getElementById(id);
const save = (patch) => chrome.storage.sync.set(patch);

for (const [key, label] of Object.entries(MAPPING)) {
  $("map").insertAdjacentHTML(
    "beforeend",
    `<label for="${key}">${label}</label><input type="number" id="${key}" min="0" max="31">`,
  );
}

function paint(cfg) {
  for (const key of SLIDERS) {
    $(key).value = cfg[key];
    $(`${key}-out`).textContent = Number(cfg[key]).toFixed(2);
  }
  for (const key of CHECKS) $(key).checked = !!cfg[key];
  for (const key of Object.keys(MAPPING)) $(key).value = cfg[key];
  $("yokeMode").value = cfg.yokeMode;
}

for (const key of SLIDERS) {
  $(key).addEventListener("input", (e) => {
    const value = Number(e.target.value);
    $(`${key}-out`).textContent = value.toFixed(2);
    save({ [key]: value });
  });
}
for (const key of CHECKS) {
  $(key).addEventListener("change", (e) => save({ [key]: e.target.checked }));
}
for (const key of Object.keys(MAPPING)) {
  $(key).addEventListener("change", (e) => save({ [key]: Number(e.target.value) }));
}
$("yokeMode").addEventListener("change", (e) => save({ yokeMode: e.target.value }));
$("reset").addEventListener("click", () => {
  chrome.storage.sync.set(gepad.DEFAULTS, () => paint(gepad.DEFAULTS));
});

chrome.storage.sync.get(gepad.DEFAULTS, paint);

/* Live readout. The popup is its own document, so it needs its own gamepad
 * gesture: the pad stays invisible here until a button is pressed with the
 * popup focused, which is exactly the thing you opened this panel to do. */
function poll() {
  requestAnimationFrame(poll);
  const pad = [...(navigator.getGamepads?.() ?? [])].find((p) => p?.connected);
  if (!pad) return;
  const axes = pad.axes.map((v) => v.toFixed(2)).join(" ");
  const pressed = pad.buttons
    .map((b, i) => (b.value > 0.5 ? i : null))
    .filter((i) => i !== null);
  $("live").innerHTML =
    `<b>${pad.id.slice(0, 40)}</b><br>axes ${axes}<br>pressed ${
      pressed.length ? pressed.join(", ") : "-"
    }`;
}
poll();
