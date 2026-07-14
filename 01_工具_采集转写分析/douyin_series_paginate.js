const fs = require("node:fs");

const DEBUG_HOST = process.env.EDGE_DEBUG_HOST || "http://127.0.0.1:9222";
const COLLECTION_EXTRACT_PATH = process.argv[2];
const OUTPUT_PATH = process.argv[3];

if (!COLLECTION_EXTRACT_PATH || !OUTPUT_PATH) {
  console.error(
    "Usage: node douyin_series_paginate.js <collection-extract-json> <output-json>",
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

async function main() {
  const extract = JSON.parse(fs.readFileSync(COLLECTION_EXTRACT_PATH, "utf8"));
  const firstResponse = extract.responseBodies.find(
    (entry) => entry.url.includes("/series/aweme/") && entry.body.length > 1000,
  );
  if (!firstResponse) {
    throw new Error("No non-empty series response found in collection extract");
  }

  const firstPayload = JSON.parse(firstResponse.body);
  const collectionUrl = new URL(firstResponse.url);
  const seriesId = collectionUrl.searchParams.get("series_id");
  const target = await createTarget(
    `https://www.douyin.com/collection/${seriesId}`,
  );
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  const pending = new Map();
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

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (!message.id) return;
    const handler = pending.get(message.id);
    if (!handler) return;
    pending.delete(message.id);
    if (message.error) handler.reject(new Error(JSON.stringify(message.error)));
    else handler.resolve(message.result);
  });

  await send("Page.enable");
  await send("Runtime.enable");
  await sleep(5000);

  const pages = [{ cursor: 0, payload: firstPayload }];
  let payload = firstPayload;
  while (payload.has_more) {
    const cursor = payload.max_cursor;
    const nextUrl = new URL(firstResponse.url);
    nextUrl.searchParams.set("cursor", String(cursor));
    nextUrl.searchParams.set("count", "20");
    nextUrl.searchParams.delete("a_bogus");
    nextUrl.searchParams.delete("timestamp");
    nextUrl.searchParams.delete("x-secsdk-web-signature");

    const expression = `(async () => {
      const response = await fetch(${JSON.stringify(nextUrl.toString())}, {
        credentials: "include",
      });
      return JSON.stringify({ status: response.status, body: await response.text() });
    })()`;
    const result = await send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    const response = JSON.parse(result.result.value);
    if (response.status !== 200 || !response.body) {
      throw new Error(`Series page cursor ${cursor} failed: ${response.status}`);
    }
    payload = JSON.parse(response.body);
    if (payload.status_code !== 0) {
      throw new Error(
        `Series page cursor ${cursor} returned status ${payload.status_code}: ${payload.status_msg || ""}`,
      );
    }
    pages.push({ cursor, payload });
    console.log(
      `cursor=${cursor} items=${payload.aweme_list?.length || 0} has_more=${payload.has_more}`,
    );
    await sleep(500);
  }

  const seen = new Set();
  const awemeList = [];
  for (const page of pages) {
    for (const item of page.payload.aweme_list || []) {
      if (seen.has(item.aweme_id)) continue;
      seen.add(item.aweme_id);
      awemeList.push(item);
    }
  }
  awemeList.sort(
    (a, b) =>
      (a.series_play_info?.series_aweme_index || 0) -
      (b.series_play_info?.series_aweme_index || 0),
  );

  fs.writeFileSync(
    OUTPUT_PATH,
    JSON.stringify(
      {
        collectedAt: new Date().toISOString(),
        seriesId,
        pageCount: pages.length,
        awemeCount: awemeList.length,
        aweme_list: awemeList,
      },
      null,
      2,
    ),
  );
  console.log(`Wrote ${awemeList.length} series items to ${OUTPUT_PATH}`);
  socket.close();
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
