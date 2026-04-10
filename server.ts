Bun.serve({
  port: 7778,
  fetch: async (r) => {
    const u = new URL(r.url);
    let p = u.pathname === "/" ? "/viz/index.html" : u.pathname;
    const f = Bun.file("/home/yurii/.openclaw/workspace/projects/box-box" + p);
    if (await f.exists()) return new Response(f);
    return new Response("Not found", { status: 404 });
  }
});
console.log("🏎️ Box-box viz server on http://192.168.10.19:7778");
