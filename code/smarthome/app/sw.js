// Service worker: lets the phone app open instantly and keep working with the last data when WiFi drops.
const CACHE = "x1-app-v1";
self.addEventListener("install", e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(["./", "app.html", "manifest.json"]))));
self.addEventListener("fetch", e => {
  if (e.request.url.includes("/api/")) return;            // live data always comes from the hub
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
