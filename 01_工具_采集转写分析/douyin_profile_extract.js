const fs = require("node:fs");

const DEBUG_HOST = process.env.EDGE_DEBUG_HOST || "http://127.0.0.1:9222";
const PROFILE_URL = process.argv[2];
const OUTPUT_PATH = process.argv[3];

if (!PROFILE_URL) {
  console.error("Usage: node douyin_profile_extract.js <profile-url>");
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

async function main() {
  const target = await createTarget("about:blank");
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  const pending = new Map();
  const responseBodies = [];
  let nextId = 1;

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

  socket.addEventListener("message", async (event) => {
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
    if (!/aweme\/post|aweme\/detail|search|share\/user|\/user\/|mix|collection|series|playlet/.test(response.url)) return;
    try {
      const result = await send("Network.getResponseBody", { requestId });
      responseBodies.push({
        url: response.url,
        status: response.status,
        mimeType: response.mimeType,
        body: result.body,
      });
    } catch {
      responseBodies.push({
        url: response.url,
        status: response.status,
        mimeType: response.mimeType,
        body: "",
      });
    }
  });

  await send("Page.enable");
  await send("Network.enable");
  await send("Runtime.enable");
  await send("Page.navigate", { url: PROFILE_URL });
  await sleep(12000);

  for (let index = 0; index < 6; index += 1) {
    await send("Runtime.evaluate", {
      expression: "window.scrollTo(0, document.body.scrollHeight)",
    });
    await sleep(2500);
  }

  const dom = await send("Runtime.evaluate", {
    expression: `JSON.stringify({
      title: document.title,
      href: location.href,
      bodyText: document.body.innerText.slice(0, 12000),
      links: [...document.querySelectorAll("a[href]")]
        .map((a) => a.href)
        .filter((href) => /\\/video\\/\\d+/.test(href)),
    })`,
    returnByValue: true,
  });

  const output = JSON.stringify(
    {
      dom: JSON.parse(dom.result.value),
      responseBodies,
    },
    null,
    2,
  );
  if (OUTPUT_PATH) {
    fs.writeFileSync(OUTPUT_PATH, output);
    console.log(`Wrote ${OUTPUT_PATH}`);
  } else {
    console.log(output);
  }
  socket.close();
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
