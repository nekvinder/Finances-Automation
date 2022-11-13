const fs = require('fs');
const puppeteer = require('puppeteer');

(async () => {
  const url = 'http:\\\\127.0.0.1:8050';
  const browser = await puppeteer.launch();
  // use tor
  //const browser = await puppeteer.launch({args:['--proxy-server=socks5://127.0.0.1:9050']});
  const page = await browser.newPage();
  page.setViewport({
    width: 1024,
    height: 720,
  });
  page.on('request', (request) => {
    console.log(`Intercepting: ${request.method} ${request.url}`);
    request.continue();
  });
  await page.goto(url, { waitUntil: 'load' });
  await page.waitForTimeout(10000);

  //const title = await page.title();
  //console.log(title);
  await page.screenshot({ path: 'example.png' });
  const html = await page.content();
  console.log(html);
  await fs.writeFileSync('dash.html', html);
  browser.close();
})();
