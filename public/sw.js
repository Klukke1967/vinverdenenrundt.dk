// Service Worker for VinVerdenenRundt (Network-First strategy)
const CACHE_NAME = 'vinverden-cache-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// Network-First for HTML/navigation, Cache-First for static assets
self.addEventListener('fetch', (event) => {
  const request = event.request;
  
  if (request.method !== 'GET') return;

  // Never cache-first on HTML / navigation / version.json
  if (request.mode === 'navigate' || request.url.includes('version.json') || request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          return response;
        })
        .catch(() => {
          return caches.match(request);
        })
    );
    return;
  }

  // Assets (images, fonts, css)
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        const toCache = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(request, toCache);
        });
        return response;
      });
    })
  );
});
