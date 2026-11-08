"use strict";

// This describes the shipped small profile; it does not run a tmux command.
const tools = {
  help: ["Know what’s available.", "Inspect registered tools, enabled state and dependency status before launching.", "Direct binding: Prefix + Ctrl-h"],
  shell: ["Shell, in the invoking directory.", "Open a shell over your pane. The default shell popup is 75% wide and 75% high.", "Direct binding: Prefix + T"],
  notes: ["A place for today’s notes.", "Open the daily note in your configured editor. The notes adapter needs an available editor.", "Menu key: N"],
  timer: ["Set a timer without leaving tmux.", "Enter 1–1440 whole minutes; the default is 25. Ctrl-C stops the timer.", "Menu key: P"],
  keys: ["Look up your tmux bindings.", "Inspect the active tmux keys in a popup, including bindings from your configuration.", "Direct binding: Prefix + Ctrl-b"]
};

const choices = document.querySelectorAll("[data-demo]");
for (const button of choices) {
  button.disabled = false;
  button.addEventListener("click", () => {
    const [title, detail, key] = tools[button.dataset.demo];
    for (const choice of choices) choice.setAttribute("aria-pressed", String(choice === button));
    document.querySelector("[data-demo-title]").textContent = title;
    document.querySelector("[data-demo-detail]").textContent = detail;
    document.querySelector("[data-demo-key]").textContent = key;
  });
}
const hint = document.querySelector("[data-demo-hint]");
if (hint) hint.textContent = "Choose a row to explore. This illustration doesn’t run commands or change your terminal.";

for (const button of document.querySelectorAll("[data-copy]")) {
  button.hidden = false;
  button.addEventListener("click", async () => {
    const code = document.getElementById(button.dataset.copy);
    const status = document.querySelector("[data-copy-status]");
    try {
      await navigator.clipboard.writeText(code.textContent);
      button.textContent = "Copied";
      status.textContent = "Copied. Paste into the file or terminal described above.";
    } catch {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(code);
      selection.removeAllRanges();
      selection.addRange(range);
      button.textContent = "Code selected";
      status.textContent = "Clipboard unavailable. The code is selected; use your device’s copy command.";
    }
  });
}
