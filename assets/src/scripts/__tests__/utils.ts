// biome-ignore lint/suspicious/noExplicitAny: we can pass in any data in this test
export function setScript(id: string, value: any) {
  const el = document.createElement("script");
  el.id = id;
  el.type = "application/json";
  el.textContent = JSON.stringify(value);
  document.body.appendChild(el);
}

export function cleanupScriptTags(scriptTags: string[]) {
  scriptTags.forEach((id) => document.getElementById(id)?.remove());
}
