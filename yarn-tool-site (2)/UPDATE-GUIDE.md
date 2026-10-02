# Update Guide — YarnYardage Site

Everything on this site is generated from two data files plus one script.
You never edit the HTML by hand — edit the data, rebuild, re-zip, deploy.

## The files

| File | What it is |
|---|---|
| `projects.json` | The 18 calculator project pages (blankets, sweaters, …). Each entry: `slug`, `key` (must match a key in `calculator.js` → `PROJECT_YARDAGE`), `keyword`, `h1`, `dims`, `intro` (2 paragraphs), `secondary` (alt search phrases), `faqs` (4 Q&As), `title`, `meta_desc`. |
| `guides.json` | The 8 guide articles. Each entry: `slug`, `title` (50–60 chars), `meta_desc` (150–160 chars), `h1`, `lede`, `sections` (each: `h2` + `html` with inline links), `faqs`. |
| `calculator.js` | Yardage data (`PROJECT_YARDAGE`) + widget logic. Charts on project pages are generated from this file, so they can never go stale. |
| `build.py` | The generator. Writes all HTML, `sitemap.xml`, `robots.txt`. Enforces SEO rules (title/meta lengths, JSON-LD validity) and prints problems. |
| `styles.css` | All styling. Mobile-first; ad slots, cookie banner, and accessibility styles live at the bottom. |

## 1. Add a new long-tail project page

The keyword sheet (`yarn-keywords-seo.xlsx`) flags 10 expansion keywords
(dog sweater, slippers, headband, …) with no page yet. To add one:

1. Add the yardage numbers to `PROJECT_YARDAGE` in `calculator.js`, e.g.:
   `"dog-sweater": { sport: 400, dk: 350, worsted: 300 }`
   and a label in `PROJECT_LABELS`.
2. Append an entry to `projects.json` with a unique `slug`, keyword, H1,
   2-paragraph intro (first paragraph = the "quick answer"), 4 FAQs, and
   3–6 secondary search phrases.
3. Run `python3 build.py`. The page, nav links, related-project links,
   sitemap, and JSON-LD are generated automatically. Fix anything the
   build's SEO check flags.
4. Re-zip (see §4) and deploy.

## 2. Add a new guide article

1. Append an entry to `guides.json` following the existing shape:
   400–700 words of genuinely useful content, 3–4 FAQs, 2–4 contextual
   internal links to project pages (`../projects/<slug>.html`) and to
   other guides (`<slug>.html`).
2. Run `python3 build.py`, re-zip, deploy.

## 3. Change the domain / go live

1. In `build.py`, set `SITE_URL = "https://www.yourdomain.com"` (no trailing
   slash) and `CONTACT_EMAIL` to a real address.
2. Run `python3 build.py` — canonical tags, sitemap, and JSON-LD URLs update.
3. Re-zip and deploy (see §4).
4. After deploying: submit the sitemap in Google Search Console
   (`https://www.yourdomain.com/sitemap.xml`), request indexing for the
   homepage, and verify `robots.txt` loads.

## 4. Rebuild the zip & deploy to Cloudflare Pages

```bash
cd ~/workspace/tool-site-yarn
python3 build.py
rm -f yarn-tool-site.zip
zip -r yarn-tool-site.zip index.html projects guides styles.css calculator.js \
  sitemap.xml robots.txt build.py projects.json guides.json \
  yarn-keywords-seo.xlsx DOMAIN-IDEAS.md UPDATE-GUIDE.md
```

Deploy options:
- **Direct upload:** Cloudflare dashboard → Pages → Upload assets → drop the
  unzipped folder (or the zip's contents).
- **Git:** push the folder to a repo, connect it in Pages, build command
  `python3 build.py`, output directory `.` (or repo root).

## 5. Turn on real ads (AdSense)

1. Apply for AdSense and get approved with the domain live.
2. Each page has 3 clearly-marked placeholder slots
   (`<!-- AdSense: … -->` + `<div class="ad-slot">`). Replace each placeholder
   div with your responsive ad unit snippet. Keep the `min-height` reserved
   space (or the ad unit's own sizing) to avoid layout shift.
3. The cookie banner, privacy policy (with AdSense/third-party-vendor
   disclosure), and footer disclosure are already in place — AdSense policy
   requirements.

## 6. Quarterly SEO maintenance checklist

- [ ] **Rankings:** check Search Console for the top-10 target keywords; note
      which pages gained/lost impressions.
- [ ] **Expansion keywords:** build pages for any of the 10 flagged long-tails
      still missing (see §1).
- [ ] **Thin pages:** any project page with < 300 words of unique text beyond
      the chart — expand the intro or add a FAQ.
- [ ] **Freshness:** update year references, "recently" language, and any
      dated claims in guides.
- [ ] **Internal links:** every new page should be linked from the homepage
      grid or guides index, and link back. Run the link checker:
      `python3 -c` snippet in build verification (see build.py `main()`).
- [ ] **Broken links:** re-run the full build — it validates internal links,
      JSON-LD, and title/meta lengths automatically.
- [ ] **New competitors:** re-check the SERP for "yarn yardage calculator"
      and the top long-tails; if a strong new tool appears, differentiate
      (more weights, better charts, video).
- [ ] **Core Web Vitals:** keep total page weight low (no frameworks, no
      render-blocking externals); re-test mobile PageSpeed after any change.
