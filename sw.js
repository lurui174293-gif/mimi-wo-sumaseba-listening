const CACHE = 'mimi-listening-v1';
self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith((async () => {
    const path=new URL(event.request.url).pathname;
    if(event.request.mode==='navigate'||/\.(html|js)$/.test(path)){
      try{
        const fresh=await fetch(event.request);
        if(fresh.ok){const cache=await caches.open(CACHE);await cache.put(event.request,fresh.clone());return fresh}
      }catch{}
    }
    const cached = await caches.match(event.request, {ignoreSearch:true, ignoreVary:true});
    if (cached) {
      const range = event.request.headers.get('Range');
      if (range) {
        const m = /^bytes=(\d+)-(\d*)$/.exec(range);
        if (m) {
          const bytes = await cached.arrayBuffer();
          const start = Number(m[1]), end = m[2] ? Math.min(Number(m[2]), bytes.byteLength-1) : bytes.byteLength-1;
          if (start < bytes.byteLength && end >= start) return new Response(bytes.slice(start,end+1), {
            status:206,headers:{'Content-Type':cached.headers.get('Content-Type')||'audio/mpeg','Content-Range':`bytes ${start}-${end}/${bytes.byteLength}`,'Content-Length':String(end-start+1),'Accept-Ranges':'bytes'}
          });
        }
      }
      return cached;
    }
    return fetch(event.request);
  })());
});
