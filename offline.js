(async()=>{
  if (!('serviceWorker' in navigator) || !('caches' in window)) return;
  await navigator.serviceWorker.register(new URL('sw.js',location.href));
  const controls=document.querySelector('.controls');
  const button=document.createElement('button');
  button.textContent='下载全部到手机';
  const status=document.createElement('span');
  status.style.cssText='font-size:12px;color:#64777c';
  controls.append(button,status);
  const base=new URL('.',location.href);
  const files=['','index.html','data.js','offline.js','sw.js','manifest.webmanifest',...Array.from({length:5},(_,i)=>`part-${i+1}.mp3`)].map(x=>new URL(x,base).href);
  button.onclick=async()=>{
    button.disabled=true;
    try{
      const cache=await caches.open('mimi-listening-v1');
      for(let i=0;i<files.length;i++){
        status.textContent=`下载中 ${i+1}/${files.length}`;
        await cache.add(new Request(files[i],{cache:'reload'}));
      }
      status.textContent='已下载。请用 Safari“添加到主屏幕”，以后点图标可离线播放。';
      button.textContent='已下载到手机';
    }catch(e){status.textContent='下载中断，请保持网页打开并重试。';button.disabled=false}
  };
  const cache=await caches.open('mimi-listening-v1');
  const saved=await Promise.all(files.map(x=>cache.match(x)));
  if(saved.every(Boolean)){button.textContent='已下载到手机';status.textContent='添加到主屏幕，之后可离线播放。'}
})();
