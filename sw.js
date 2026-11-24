const CACHE_NAME = "radar-approche-v1";
const ASSETS_STATIQUES = [
  "/",
  "/index.html",
  "/manifest.json",
  "/icon.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_STATIQUES))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  if (url.pathname.startsWith("/api/")) {
    return;
  }

  if (event.request.method === "GET" && url.origin === self.location.origin) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        const networkFetch = fetch(event.request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              const clone = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
            }
            return networkResponse;
          })
          .catch(() => cachedResponse);

        return cachedResponse || networkFetch;
      })
    );
  }
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const hexCible = event.notification.data?.hex || "";
  const zoneCible = event.notification.data?.zone || "";

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ("focus" in client) {
          client.postMessage({ type: "VERROUILLER_AVION_RARE", hex: hexCible, zone: zoneCible });
          return client.focus();
        }
      }
      if (clients.openWindow) {
        const url = zoneCible ? `/?zone=${encodeURIComponent(zoneCible)}&hex=${encodeURIComponent(hexCible)}` : "/";
        return clients.openWindow(url);
      }
    })
  );
});
