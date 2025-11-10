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
>  * `N`:
>  * `D`: