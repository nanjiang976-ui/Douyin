const fs = require("node:fs");

const DEBUG_HOST = process.env.EDGE_DEBUG_HOST || "http://127.0.0.1:9222";
const PROFILE_EXTRACT_PATH = process.argv[2];
const OUTPUT_PATH = process.argv[3];

if (!PROFILE_EXTRACT_PATH || !OUTPUT_PATH) {
  console.error(
    "Usage: node douyin_batch_detail_extract.js <profile-extract-json> <output-json>",
  );
  process.exit(1);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function createTarget(url) {
  const response = await fetch(`${DEBUG_HOST}/json/new?${encodeURIComponent(url)}`, {
    method: "PUT",
  });
  if (!response.ok) {
    throw new Error(`Failed to create browser target: ${response.status}`);
  }
  return response.json();
}

function videoIdFromUrl(url) {
  return url.match(/\/video\/(\d+)/)?.[1] || "";
}

async function main() {
  const profileExtract = JSON.parse(
    fs.readFileSync(PROFILE_EXTRACT_PATH, "utf8"),
  );
  const urls = [
    ...new Set(
      profileExtract.dom.links
        .filter((url) => /\/video\/\d+/.test(url) && !url.includes("source="))
        .map((url) => url.split("?")[0]),
    ),
  ];

  const target = await createTarget("about:blank");
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  const pending = new Map();
  const bodiesByVideoId = new Map();
  let nextId = 1;
  let currentVideoId = "";

  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });

  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const id = nextId++;
      pending.set(id, { resolve, reject });
      socket.send(JSON.stringify({ id, method, params }));
    });

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const handler = pending.get(message.id);
      if (!handler) return;
      pending.delete(message.id);
      if (message.error) handler.reject(new Error(JSON.stringify(message.error)));
      else handler.resolve(message.result);
      return;
    }

    if (message.method !== "Network.responseReceived") return;
    const { requestId, response } = message.params;
    if (!/aweme\/detail/.test(response.url) || !currentVideoId) return;

    const capturedVideoId = currentVideoId;
    send("Network.getResponseBody", { requestId })
      .then((result) => {
        if (!result.body) return;
        const entries = bodiesByVideoId.get(capturedVideoId) || [];
        entries.push({ url: response.url, status: response.status, body: result.body });
        bodiesByVideoId.set(capturedVideoId, entries);
      })
      .catch(() => {});
  });

  await send("Page.enable");
  await send("Network.enable");
  await send("Runtime.enable");

  const items = [];
  for (let index = 0; index < urls.length; index += 1) {
    const url = urls[index];
    currentVideoId = videoIdFromUrl(url);
    console.log(`[${index + 1}/${urls.length}] ${currentVideoId}`);
    await send("Page.navigate", { url });
    await sleep(4500);

    const dom = await send("Runtime.evaluate", {
      expression: `JSON.stringify({
        title: document.title,
        href: location.href,
        bodyText: document.body.innerText.slice(0, 20000),
        meta: [...document.querySelectorAll("meta")]
          .map((node) => ({
            name: node.getAttribute("name") || node.getAttribute("property") || "",
            content: node.getAttribute("content") || "",
          }))
          .filter((entry) => entry.name && entry.content),
      })`,
      returnByValue: true,
    });
    await sleep(500);
    items.push({
      aweme_id: currentVideoId,
      url,
      dom: JSON.parse(dom.result.value),
      responseBodies: bodiesByVideoId.get(currentVideoId) || [],
    });
  }

  fs.writeFileSync(
    OUTPUT_PATH,
    JSON.stringify({ collectedAt: new Date().toISOString(), items }, null, 2),
  );
  console.log(`Wrote ${items.length} items to ${OUTPUT_PATH}`);
  socket.close();
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
