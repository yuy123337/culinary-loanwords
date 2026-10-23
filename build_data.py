#!/usr/bin/env python3
"""
build_data.py  —  data builder for the "Is this a food?" bubble site (foreign_words_site/).

Part of Yue Yin's Michelin foreign-words side project. It READS the original project
CSVs (it never writes to them) and produces two derived files in THIS folder:

    michelin_foreign_words.json   (used by index.html; the site inlines a copy)
    michelin_foreign_words.csv    (flat word-level table for reference)

Source files read from the parent michelin folder (unchanged):
    contexts_with_probs_v2.csv      - per-sentence contexts + price_skew + price_level
    word_etymology.csv              - Merriam-Webster definition / etymology / year / origin
    word_etymology_classified.csv   - origin_final / gpt_origin / ud_pos / is_fragment

Run:  python3 build_data.py
"""
import os, re, json, math
import pandas as pd, numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                      # the michelin project folder (read-only here)
MIN_N = 3                                          # keep a word if it appears in >=3 sentences

# ---------------------------------------------------------------- load originals (read only)
ctx = pd.read_csv(os.path.join(BASE, 'contexts_with_probs_v2.csv'))
voc = pd.read_csv(os.path.join(BASE, 'word_etymology.csv'))
cl  = pd.read_csv(os.path.join(BASE, 'word_etymology_classified.csv'))

# ---------------------------------------------------------------- word metadata
cl_small  = cl[['word','origin_final','gpt_origin','ud_pos','is_fragment']].drop_duplicates('word')
voc_small = voc[['word','in_mw','year','origin','pos','etymology','definition']].drop_duplicates('word')
meta = cl_small.merge(voc_small, on='word', how='outer')
meta['origin_best'] = meta['origin_final'].fillna(meta['gpt_origin']).fillna(meta['origin'])

LANGS = ['French','Italian','Spanish','Japanese','German','Chinese','Portuguese','Dutch','Korean',
 'Arabic','Vietnamese','Thai','Hindi','Turkish','Greek','Latin','Indonesian','Malay','Yiddish',
 'Hawaiian','Armenian','Norwegian','Swedish','Danish','Russian','Polish','Hungarian','Persian',
 'Tamil','Catalan','Swiss','Filipino','Peranakan']
NORM = {'Peranakan':'Malay','Tamil':'Indian','Hindi':'Indian','Sanskrit':'Indian','Urdu':'Indian'}
WORD_SPECIAL = {'carpaccio':'Italian','chateaubriand':'French','hunan':'Chinese','gruyere':'Swiss',
 'simmental':'Swiss','kalamata':'Greek','charolais':'French','limousin':'French','ibizan':'Spanish',
 'jollof':'West African','beignet':'French','mojito':'Spanish','poutine':'French','sachertorte':'German',
 'spaetzle':'German','lavash':'Armenian','negroni':'Italian','portobello':'Italian','guanciale':'Italian',
 'vindaloo':'Indian','potsticker':'Chinese','goji':'Chinese','nacho':'Spanish','nachos':'Spanish','sichuan':'Chinese',
 'foie gras':'French','beurre blanc':'French','pata negra':'Spanish','a la carte':'French','prix fixe':'French',
 'sous vide':'French','burrito':'Spanish'}
# count these as one word (plural -> singular)
ALIAS = {'burritos':'burrito'}
# manual definitions for phrases Merriam-Webster didn't give us as a single entry
PHRASE_DEF = {
 'foie gras':'the fattened liver of a duck or goose, a French delicacy',
 'beurre blanc':'a warm French butter sauce',
 'pata negra':'prized Spanish cured ham from black Iberian pigs',
 'burrito':'a flour tortilla rolled or folded around a filling such as meat, beans, and cheese',
}
SKIP = {'cheddar','dungeness','granola','eco','nola','shangri','luma','makis','pavlova','anglo','fledged',
 'morales','lutz','gama','pescatarian','pescetarian','glitz','glitzy'}
# words removed by hand in the site (brand names, English words, mislabels)
DROP = {'claypot','aubergine','retro','bistronomic','braised','valrhona','ajo','vivre','sik','foie','gras'}
BRIT = {'favourite','colourful','flavourful','flavoursome','colour','flavour','savour','savoury',
 'flavoured','coloured','honour','honoured','neighbourhood','speciality','specialities'}

def norm_origin(word, s):
    w = str(word).lower()
    if w in SKIP: return None
    if w in WORD_SPECIAL: return WORD_SPECIAL[w]
    if not isinstance(s, str) or not s.strip(): return None
    for L in LANGS:
        if re.search(r'\b'+L+r'\b', s): return NORM.get(L, L)
    return None
meta['origin_norm'] = [norm_origin(w, o) for w, o in zip(meta['word'], meta['origin_best'])]

def era(y):
    if pd.isna(y): return 'Unknown'
    y = int(y)
    return ('Pre-1900' if y<1900 else '1900–1950' if y<1950 else '1950–1980' if y<1980
            else '1980–2000' if y<2000 else '2000+')
meta['era'] = meta['year'].map(era)

def pos_clean(r):
    p = str(r.get('ud_pos') or '').upper()
    if p == 'PROPN': return 'proper noun'
    if p == 'PHRASE': return 'phrase'
    if p == 'ADJ': return 'adjective'
    if p == 'VERB': return 'verb'
    if p == 'NOUN': return 'noun'
    pp = str(r.get('pos') or '').lower()
    return ('adjective' if 'adj' in pp else 'verb' if 'verb' in pp
            else 'phrase' if ' ' in str(r.get('word','')) else 'noun')
meta['pos_clean'] = meta.apply(pos_clean, axis=1)

def rest_name(url):
    try:
        u = str(url).rstrip('/')
        slug = u.split('/restaurant/')[-1].split('/')[0] if '/restaurant/' in u else u.split('/')[-1]
        return re.sub(r'\s+', ' ', slug.replace('-', ' ')).strip().title()
    except Exception:
        return ''

def clean_ety(s):
    if not s or s == 'None': return None
    s = re.sub(r'\{/?[a-z_|]+\}', '', s)
    s = re.sub(r'\{et_link[^}]*\}', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s or None

# ---------------------------------------------------------------- recover merged phrases the scored
# file dropped (foie gras, sous vide, ...). price_skew is per-sentence, so borrow it from any scored
# row with the same context text.
raw = pd.read_csv(os.path.join(BASE, 'contexts_v2_raw.csv'))
ctx['_ctx'] = ctx['context'].astype(str).str.strip()
skew_by_ctx = (pd.to_numeric(ctx['price_skew'], errors='coerce')
                 .groupby(ctx['_ctx']).mean())
missing = (set(raw['word'].astype(str)) - set(ctx['word'].astype(str)))
rec = raw[raw['word'].astype(str).isin(missing)].copy()
rec['_ctx'] = rec['context'].astype(str).str.strip()
rec['price_skew'] = rec['_ctx'].map(skew_by_ctx)
rec = rec[rec['price_skew'].notna()]
cols = ['word','url','context','price_level','distinction','primary_cuisine','price_skew']
ctx = pd.concat([ctx[[c for c in cols if c in ctx.columns]], rec[cols]], ignore_index=True)

# count plural + singular as one word
ctx['word'] = ctx['word'].astype(str).map(lambda w: ALIAS.get(w.lower(), w))

# ---------------------------------------------------------------- per-word metrics from contexts
c = ctx.copy()
c['price_skew'] = pd.to_numeric(c['price_skew'], errors='coerce')
c = c.dropna(subset=['price_skew'])

rows = []
for w, g in c.groupby('word'):
    n = len(g)
    if n < MIN_N: continue
    m = meta[meta['word'] == w]; mm = m.iloc[0] if len(m) else None
    r = None; gp = g.dropna(subset=['price_level'])
    if len(gp) >= 15 and gp['price_level'].nunique() >= 3:          # price-sensitivity r (Pearson)
        rr, _ = stats.pearsonr(gp['price_level'].astype(float), gp['price_skew'])
        r = round(float(rr), 3) if np.isfinite(rr) else None
    # one example per restaurant (distinct url), spanning quietest -> fanciest, so we never
    # show three near-identical sentences from the same place
    gg = g.drop_duplicates('context').sort_values('price_skew').drop_duplicates('url'); picks = []
    if len(gg) >= 1: picks.append(gg.iloc[0])                       # quietest
    if len(gg) >= 3: picks.append(gg.iloc[len(gg)//2])             # middle
    if len(gg) >= 2: picks.append(gg.iloc[-1])                     # fanciest
    exs = []; seen = set()
    for p in picks:
        t = re.sub(r'\s+', ' ', str(p['context']).strip())
        if len(t) > 240: t = t[:237] + '…'
        if t in seen: continue
        seen.add(t)
        exs.append({'t': t, 'skew': round(float(p['price_skew']), 2),
                    'rest': str(p.get('primary_cuisine') or ''), 'dist': str(p.get('distinction') or ''),
                    'name': rest_name(p.get('url')), 'url': str(p.get('url') or '')})
    rows.append({
        'word': w,
        'origin': ((mm['origin_norm'] if (mm is not None and pd.notna(mm['origin_norm'])) else norm_origin(w, None))),
        'pos': (mm['pos_clean'] if mm is not None else 'noun'),
        'year': (int(mm['year']) if mm is not None and pd.notna(mm['year']) else None),
        'era': (mm['era'] if mm is not None else 'Unknown'),
        'in_mw': bool(mm['in_mw']) if (mm is not None and pd.notna(mm['in_mw'])) else False,
        'definition': (str(mm['definition']) if mm is not None and pd.notna(mm['definition']) else PHRASE_DEF.get(str(w).lower())),
        'etymology': clean_ety(str(mm['etymology'])) if (mm is not None and pd.notna(mm['etymology'])) else None,
        'is_fragment': bool(mm['is_fragment']) if (mm is not None and pd.notna(mm['is_fragment'])) else False,
        'n': int(n),
        'skew': round(float(g['price_skew'].mean()), 3),       # mean "framing" (1 casual .. 4 upscale)
        'sigma': round(float(g['price_skew'].std() if n > 1 else 0), 3),
        'r': r,
        'examples': exs,
    })

W = pd.DataFrame(rows)
keep = W[(~W['word'].str.lower().isin(BRIT)) &
         (~W['word'].str.lower().isin(DROP)) &
         (W['origin'].notna()) &
         (~((W['is_fragment']) & (~W['word'].str.contains(' '))))].copy()
keep = keep.sort_values('n', ascending=False)

# ---------------------------------------------------------------- write JSON (matches the site)
def clean(o):
    if isinstance(o, float): return None if (math.isnan(o) or math.isinf(o)) else (int(o) if o.is_integer() else o)
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    return o
out = {'words': clean(keep.drop(columns=['is_fragment']).to_dict('records')),
       'meta': {'n_words': int(len(keep)), 'n_origins': int(keep['origin'].nunique()),
                'with_def': int(keep['definition'].notna().sum()),
                'origins': keep['origin'].value_counts().index.tolist(),
                'eras': ['Pre-1900','1900–1950','1950–1980','1980–2000','2000+','Unknown'],
                'poss': [p for p in ['noun','phrase','adjective','verb','proper noun'] if p in set(keep['pos'])]}}
with open(os.path.join(HERE, 'michelin_foreign_words.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, allow_nan=False)

# ---------------------------------------------------------------- write flat CSV (no nested examples)
flat = keep.drop(columns=['is_fragment', 'examples']).copy()
flat['n_examples'] = keep['examples'].map(len).values
flat.to_csv(os.path.join(HERE, 'michelin_foreign_words.csv'), index=False)

print(f"words kept: {len(keep)}  | origins: {keep['origin'].nunique()}  | with MW def: {keep['definition'].notna().sum()}  | with r: {keep['r'].notna().sum()}")
print("wrote michelin_foreign_words.json and michelin_foreign_words.csv in", HERE)
