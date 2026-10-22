## Data and Method

### Michelin Guide Data

I compiled a list of 18,812 Michelin Guide restaurant URLs and scraped their public detail pages using Python, `requests`, and BeautifulSoup. For each restaurant, I collected its name, address, cuisine categories, Michelin distinction, editorial description, website, and displayed price category.

I converted Michelin’s currency-symbol categories into four numerical price tiers by counting the displayed currency symbols. The resulting dataset contains 18,800 restaurant descriptions and 18,065 restaurants with usable price-tier information.

### Identifying Foreign-Origin Culinary Terms

I tokenized and lemmatized the Michelin descriptions using spaCy. I retained alphabetic lemmas longer than two characters that did not appear in a combined English reference vocabulary constructed from the NLTK Words corpus and Brown Corpus.

To reduce accidental tokens, typographical errors, restaurant names, and personal names, I retained only candidate lemmas appearing at least three times across the corpus. This threshold is a practical screening rule rather than a statistically optimized cutoff.

I queried the Merriam-Webster Collegiate Dictionary API for each candidate’s definition, part of speech, etymology, and first recorded use in English. Terms with a documented non-English origin were classified as borrowed terms. Candidates absent from Merriam-Webster were treated as potentially foreign and reviewed further.

Because dictionary entries can be ambiguous in culinary contexts, I used GPT-4o-mini as a secondary review step for unmatched terms, geographical and biographical names, and entries whose dictionary classification did not fit their use in restaurant descriptions. Therefore, the resulting vocabulary represents foreign-origin culinary terms identified through corpus screening, dictionary evidence, and contextual review; it should not be interpreted as an exhaustive inventory of all non-English words.

### Context Extraction

For each identified term, I extracted the complete sentence in which it appeared rather than using a fixed-width character window. Sentence boundaries were detected with a rule-based splitter that preserved common abbreviations, and terms were matched case-insensitively using word boundaries.

Multi-word culinary expressions were identified through exact phrase matching. Individual components should be merged into a phrase only when the complete phrase appears in that same sentence. Standalone uses of a component remain separate observations. Duplicate term–restaurant–sentence records are removed after phrase resolution.

### Contextual Price Register

I encoded both complete Michelin descriptions and term-containing sentences using the 384-dimensional `all-MiniLM-L6-v2` sentence-embedding model.

I trained a multinomial logistic-regression classifier on restaurant-description embeddings labeled with Michelin’s four price tiers. When applied to a sentence, the classifier returns four probabilities indicating how closely the sentence resembles the language associated with each price tier.

I summarize these probabilities as a contextual price-register score:

`Price-register score = Σ P(tier k) × k`, for `k = 1, 2, 3, 4`.

A higher value indicates stronger similarity to language associated with higher-priced restaurants. It is not an estimate of the restaurant’s actual price.

### 3D Visualization

For each term with at least ten price-labeled sentence contexts, I calculate:

- **Mean price-register score:** the term’s average association with casual- or luxury-oriented language.
- **Price responsiveness:** the Pearson correlation between the restaurant’s actual price tier and the sentence-level price-register score.
- **Contextual variability:** the standard deviation of the term’s price-register scores across sentences.



### Limitations

This is an exploratory analysis of linguistic associations. It does not establish that particular words cause higher prices or predict a restaurant’s actual price. The vocabulary-selection threshold is heuristic, dictionary coverage is incomplete, and language origin can be ambiguous. Cuisine, geography, Michelin distinction, and restaurant style may also influence both vocabulary and price-related language.
