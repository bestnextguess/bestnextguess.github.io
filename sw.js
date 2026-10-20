// Best Next Guess service worker: lets the site be installed as an app and open without internet.
// Always tries the network first, so updates show up right away; the saved copy is only used offline.
const CACHE = 'bng-v2.0.1-a';
const CORE = ['./', 'index.html', 'stats.html', 'about.html', 'past.txt', 'log.txt', 'logo.svg',
              'logo-180.png', 'logo-192.png', 'logo-512.png', 'logo-maskable.png', 'manifest.webmanifest'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE)
    .then(c => Promise.all(CORE.map(u => c.add(new Request(u, { cache: 'reload' })).catch(() => {}))))
    .then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;      // visit counter and anything else: straight to the network
  const key = url.origin + url.pathname;                  // one saved copy per page, whatever ?ref= it came with
  e.respondWith((async () => {
    try {
      const res = await fetch(req);
      if (res.ok && res.type === 'basic') { const copy = res.clone(); caches.open(CACHE).then(c => c.put(key, copy)); }
      return res;
    } catch (err) {
      return (await caches.match(key))
        || (req.mode === 'navigate' && await caches.match(url.origin + '/'))
        || new Response('You are offline.', { status: 503, headers: { 'Content-Type': 'text/plain' } });
    }
  })());
});
