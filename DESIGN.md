# "Is this a food?" — design notes

An interactive webpage by Yue Yin: a creative, public-facing demo of the Michelin
foreign-words (culinary loanwords) research. Self-contained single file, meant to be
shared (e.g. with professors / as a portfolio piece) and hosted on GitHub Pages.

## Files (all new; the original project CSVs/notebooks are never modified)
- `index.html`         — the whole site. Data is inlined as `const DATA = {...}`, so it
                         works by double-click (needs internet only for the Plotly CDN
                         and the Cormorant Garamond web font) and deploys as-is.
- `build_data.py`      — reproducible builder. READS the original CSVs in the parent
                         `michelin/` folder and writes the two files below. Never writes
                         to the originals.
- `michelin_foreign_words.json` — word-level data the site uses (also inlined in index.html).
- `michelin_foreign_words.csv`  — flat reference table (no nested examples).

Rebuild:  `cd foreign_words_site && python3 build_data.py`
Deploy:   drop `index.html` at a repo root, enable GitHub Pages (repo
          github.com/yuy123337/culinary-loanwords). It is one static file, no build step.

## Data
- Source: the **US English Michelin Guide**, scraped ~May 2026. 18,812 restaurants,
  52 countries (from `michelin_details.parquet` via the project's July pipeline).
- Built from three original CSVs (read-only here): `contexts_with_probs_v2.csv`
  (per-sentence contexts + price_skew + price_level), `word_etymology.csv` (Merriam-Webster
  definition / etymology / year / origin), `word_etymology_classified.csv`
  (origin_final / gpt_origin / ud_pos / is_fragment).
- ~1,891 borrowed words kept (word appears in >=3 sentences, has a real foreign origin,
  not a bare fragment, not in the manual DROP list).

## The three measures (per word) — framed as "framing", not "the word's meaning"
- **skew** = mean "framing" of the sentences a word appears in, 1 (casual) .. 4 (upscale),
  from a price-tier classifier on sentence embeddings (all-MiniLM-L6-v2). Shown as
  "How is it usually framed?" -> Casual / Middle / Upscale (percentile/tertile cuts).
- **r** = within-word Pearson(actual price level, skew). "Does its framing change with
  restaurant price?" -> Fancier when pricier / ... / Framed the same at any price.
  Low r is the commodification point: fanciness rides on the name, not the bill.
- **sigma** = std of skew. "Does its framing vary across descriptions?" ->
  Framed consistently / Somewhat varied / Framed all kinds of ways.

## Page structure (top -> bottom)
1. **Cover** — full-screen canvas of translucent, colliding word-bubbles (soothing
   menu-paper palette). A pixel waiter greets "welcome!" then nudges "please order!" if
   you hesitate. Game: "Is this a food?" Tap a bubble -> a hungry-customer pixel pops up
   with a random line, and a verdict popup (food / not a food) with the definition, a
   Wikipedia link if it is not in Merriam-Webster, and "how it's used ->". A pixel
   **service bell = "new batch"** reshuffles the bubbles from all words.
2. **Jurafsky epigraph** — "The fancier the restaurant, the more foreign the words on its
   menu." (a finding from Dan Jurafsky, The Language of Food, 2014).
3. **The 3-D map** — Plotly scatter3d. x = casual->upscale, z = changes-with-price (vertical),
   y = varies-across-descriptions (depth). Fixed camera by default (no spin); click a dot
   to drop guide-lines to each axis and zoom/rotate onto it. ~299 words (those with r).
4. **Explore** — bar chart (framing of each word; fixed bar thickness via padded y-range),
   origin summary (only origins with >=8 words; "culturally mixed" caveat), filters that
   STACK (Era, Type), a word search, and a browse grid. Click any word -> card.
5. **Word card** — big word, food/not-food verdict, definition first (or Wikipedia), origin
   & year, the three metrics (question on top, bold answer below), real example sentences
   quietest->fanciest each linking to the actual Michelin restaurant page, a guess box
   ("what do you think the word is?" -> localStorage), and "see where it sits on the map".
6. **Footer** — Yue's first-person essay (amazement -> cultural cue -> Bourdieu -> method ->
   Anglocentric caveat-as-insight -> closing amazement), byline, data facts, repo link,
   and a legal/non-affiliation disclaimer. Pixel two-diners (wine + fork, fish + greens).

## Pixel art
All sprites are drawn in code (no image files): the waiter, the hungry customer, the
service bell, and the two-diners footer scene (the diners are animated — glass and fork bob).

## Word-classification correction lists (client-side in index.html, mirrored in build_data.py's DROP)
Maintained by hand-review, word by word:
- `DROP` — removed entirely (brand names, English words, mislabels, fragments:
  claypot, aubergine, retro, bistronomic, braised, valrhona, ajo, vivre, sik, ...).
- `FOOD_WORDS` — force "food" for dishes mis-tagged as proper nouns (shaomai, niçoise,
  monaka, ...).
- `NOTFOOD_WORDS` — force "not a food" for places / venue types / techniques / concepts
  (terroir, umami, bouchon, périgord, bresse, quercy, nikkei, fjord, café, ikejime, ...).
- `OVERRIDE` — per-word origin fixes + notes (e.g. aji = Japanese fish vs Spanish chili).
- Plus rules: proper nouns, adjectives and verbs default to "not a food"; otherwise a noun
  with a definition that is not a place/venue/technique defaults to "food".

## Copy voice (important)
First-person, natural, humble. NO em-dashes or hyphens as sentence connectors. Avoid
"foreign" as the neutral default (Anglocentric); prefer "words from other languages" /
"kept in its own language". The Guide's text is restaurant **introductions**, not menus.
