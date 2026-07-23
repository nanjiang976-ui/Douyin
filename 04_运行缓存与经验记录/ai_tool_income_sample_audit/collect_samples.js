const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const samples = [
  ["7650793954459283813", "梦花寻影"],
  ["7614808385040518434", "李喵喵"],
  ["7636694641883473905", "松小鼠呀"],
  ["7616596634591530249", "六耳玩AI"],
  ["7611150020510846246", "排毒报告（袁希的水卢教育）"],
  ["7657518242554023195", "六耳玩AI"],
  ["7654930914341883179", "六耳玩AI"],
  ["7627567027091213602", "青阳（奥启敏）"],
];

const outputDir = __dirname;
const edgePath = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const profileDir = path.resolve(
  __dirname,
  "../../03_浏览器运行环境_勿上传/.edge-video-cdp",
);

async function main() {
  const context = await chromium.launchPersistentContext(profileDir, {
    executablePath: edgePath,
    headless: true,
    args: ["--disable-gpu", "--autoplay-policy=no-user-gesture-required"],
    viewport: { width: 1440, height: 1000 },
  });
  const page = context.pages()[0] || (await context.newPage());
  const results = [];

  for (const [awemeId, expectedAuthor] of samples) {
    const detailBodies = [];
    const commentBodies = [];
    const onResponse = async (response) => {
      const url = response.url();
      if (!url.includes("aweme/detail") && !url.includes("comment/list")) return;
      try {
        const body = await response.json();
        if (url.includes("aweme/detail")) detailBodies.push({ url, body });
        if (url.includes("comment/list")) commentBodies.push({ url, body });
      } catch {}
    };
    page.on("response", onResponse);

    const url = `https://www.douyin.com/video/${awemeId}`;
    console.log(`OPEN ${awemeId}`);
    let navigationError = "";
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
      await page.waitForTimeout(8000);
    } catch (error) {
      navigationError = `${error.name}: ${error.message}`;
    }

    const dom = await page.evaluate(() => ({
      title: document.title,
      href: location.href,
      bodyText: document.body.innerText.slice(0, 30000),
      meta: [...document.querySelectorAll("meta")]
        .map((node) => ({
          name: node.getAttribute("name") || node.getAttribute("property") || "",
          content: node.getAttribute("content") || "",
        }))
        .filter((entry) => entry.name && entry.content),
    }));

    const detailEntry = [...detailBodies]
      .reverse()
      .find((entry) => String(entry.body?.aweme_detail?.aweme_id || "") === awemeId);
    const comments = commentBodies.flatMap((entry) => entry.body?.comments || []);
    results.push({
      awemeId,
      expectedAuthor,
      url,
      collectedAt: new Date().toISOString(),
      navigationError,
      dom,
      detail: detailEntry?.body?.aweme_detail || null,
      comments,
      capturedDetailResponses: detailBodies.length,
      capturedCommentResponses: commentBodies.length,
    });
    page.off("response", onResponse);
  }

  fs.writeFileSync(
    path.join(outputDir, "samples.raw.json"),
    JSON.stringify({ samples: results }, null, 2),
  );
  await context.close();
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
