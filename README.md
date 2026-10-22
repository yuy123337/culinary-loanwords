# culinary-loanwords
An interactive 3D exploration of how non-English culinary words, their etymologies, and their sentence contexts relate to restaurant price tiers.
# Etymology 3D

An interactive 3D exploration of how non-English culinary words, their etymologies, and their sentence contexts relate to restaurant price tiers.

## Overview

Etymology 3D examines how non-English culinary terms are used in Michelin Guide restaurant descriptions. I trace each word’s linguistic origin, analyze the sentence in which it appears, and visualize how its framing relates to casual and luxury dining language.

## Method

I first identify non-English culinary terms and collect information about their linguistic origins. For every occurrence of a term, I extract the full sentence surrounding it.

I encode these sentence contexts using the `all-MiniLM-L6-v2` sentence-embedding model. I then apply a multinomial logistic-regression classifier trained on Michelin restaurant descriptions labeled with four price tiers.

For each sentence, the classifier estimates how closely its language resembles the language associated with each price tier. I summarize these probabilities as a **contextual price-register score**, ranging from casual-associated to luxury-associated language.

## 3D Visualization

Each word is positioned using three dimensions:

- **Luxury-language association:** How strongly the word’s contexts resemble language used for higher-priced restaurants.
- **Price responsiveness:** How much the word’s framing changes across actual restaurant price tiers.
- **Contextual variability:** How differently the word is framed across sentences.

Point color represents the word’s linguistic origin, while point size represents the number of sentence contexts in which the word appears.

## Interpretation

The visualization shows how the same culinary term can take on different meanings or signals depending on its surrounding language. A word may consistently appear in luxury-associated language, shift its framing across price tiers, or vary substantially from one context to another.

## Important Note

This project does **not** predict a restaurant’s actual price. It measures associations between sentence-level language and the linguistic styles found across Michelin price tiers. The results are correlational and should not be interpreted as causal.
