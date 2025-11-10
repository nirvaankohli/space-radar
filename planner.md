# Idea

A multi-agent system that scrapes or gets major space/astronomy news sources, clusters duplicate stories, summarizes them, and ranks what matter most. 

## Ranking

If you do not want to read the following in depth description of how ranking is calculated, remember one line:
 
**Ranking = Deterministic Score per Clustered Story; Then these story is are reranked by a diversity-aware thingy.**

That being said, the following steps are the ones that happen when ranking stories:

### 1. Base Score Per Story
> Each story(represented by `s`) has a item: (title, text, source, ts). It also has a Topic Set(represented by `T`)
>
> #### Components
> (These are clamped/within 0 & 1)
>  * `R` - The Recency: `R = exp(-hours_since(ts)/24` - Recency Decay(clamped to [0, 1])
>  * `C` - The Credibility: from a lookup by domain; Default - .6.
>  * `N` - The Novelty: Measures how new or different a story is compared to what was recently seen.
>           - If two headlines are near duplicates the `N` will be very high, and this ensures that only one instance is ranked.
>           - Calculated by `1 - max_cosine(emb(s), emb(top_k_recent))`. If no history, `N=1`. (emb() refers to the embedded vector of story(ies) title + summary)
>  * `D` - The Diversity/Topic balance: Measures how overrepresented a topic is. It works by counting how many stories already selected share each topic, and computing a small penalty based on that count. Calculated by `D = 1 - min(0.6, 0.15*count_overrepresented(T))`
>
> #### Score
> ```
> S0 = 0.35(R) + 0.25(C) + 0.25(N) + 0.15(D) # Prone to change
>```
> #### Final Base:
> ```
> S = clamp(S0 + B - penalties, 0, 1)
>```

### 2. Diversity-aware re-rank (MMR-style)

> Objective: select top `K` stories that are high-score and non-redundant.
> The following algo is to be iterated until `K` is eventually picked:
> ```
> pick argmax of: λ*S(s) - (1-λ)*max_sim(emb(s), emb(picked))
> ```
> Key/Legend
> * λ = 0.7
> * sim = cosine between story embeddings
> * Enforce topic quotas: at most q_topic per day (e.g., <40% “launch”, <40% “jwst”).*