const CACHE_NAME = 'vrs-cafe-v1';
const ASSETS = [
  './',
  './index.html',
  './customer.html',
  './admin.html',
  './kitchen.html',
  './styles.css',
  './data.js',
  './manifest.json',
  'https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css',
  'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request))
  );
});
