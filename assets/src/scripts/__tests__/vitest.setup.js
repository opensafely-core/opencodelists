// Patch the timezone to confirm 1 hour difference is applied to UTC strings
process.env.TZ = "Etc/GMT-1";

// Patch navigator.language to default to en-GB for testing date and
// time strings
if (typeof global.navigator !== "undefined") {
  Object.defineProperty(global.navigator, "language", {
    value: "en-GB",
    configurable: true,
  });
}
