Use `puppeteer` and `google-news-scraper` in a docker container.

Run Node.js REPL:
```sh
docker build -f Dockerfile-puppeteer -t puppeteer .
docker run -it puppeteer
```

Use `google-news-scraper` (REPL):
```js
const { default: googleNewsScraper } = await import("google-news-scraper");

articles = await googleNewsScraper({
    searchTerm: "The Oscars",
    puppeteerArgs: ['--no-sandbox', '--disable-setuid-sandbox']
});
```

Use `puppeteer` (...):
```js
...

puppeteer.launch({args: ['--no-sandbox', '--disable-setuid-sandbox']});
```

Sources:
- https://stackoverflow.com/a/72291691