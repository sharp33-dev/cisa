// 최소 서비스워커 — PWA 설치 가능 요건 충족용 (http/https 로 서빙될 때만 등록됨)
const CACHE = 'cisa-study-v1';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(clients.claim());
});

// 네트워크 우선, 실패 시 캐시 (오프라인 최소 지원)
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
