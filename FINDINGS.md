# What 2,500 Years of Indian Philosophy Taught Me About Asking AI the Right Question

Here's something worth knowing if you ever use AI to compare two sides of an argument, ask it to explain a disagreement, or just get a balanced view on something contested: the way you frame the question can quietly tilt the answer, even when the AI is doing everything "right."

I found this out by accident while building a small experiment on top of a dataset of Indian philosophical texts, and I think the result is useful for anyone who relies on AI for things like research summaries, debate prep, comparing philosophies or religions, or even just settling an argument with a friend.

## The setup, explained simply

I built a tool where two AI agents argue opposite sides of a philosophical question, drawing only from a large collection of real passages from Hindu, Buddhist, and Jain texts that I'd organized into a searchable database. To keep them honest, I gave each agent a rule: they can only make a claim if they can point to a real quote from a real ancient text. No making things up. If an agent has no evidence for a point, it has to say so out loud, instead of bluffing.

The two sides were Buddhism and Advaita Vedanta (a major school of Hindu philosophy), arguing about one of the oldest disagreements in religious thought: does a permanent self exist?

Advaita Vedanta says yes. There is an eternal, unchanging self (called atman) underneath everything.

Buddhism says no. What we call "self" is just a temporary, changing bundle of experiences. The Buddhist term for this is anatta, meaning "no fixed self."

## What happened when I asked the question three different ways

I ran the same debate three times, changing only one thing each time: which word I used to frame the question.

**Round 1: I asked both sides to debate "atman."**

This seems neutral. It's just the word for "self," right? But atman is a Hindu term. Buddhism doesn't have a positive doctrine built around that word, because Buddhism's whole point is that the word describes something that doesn't exist. So the Buddhist AI kept getting stuck. It could only find quotes where Buddhist texts mention atman in passing, usually just to wave it away. It never got to make its actual case. The debate felt one sided and confusing, even though both AIs were technically being honest.

**Round 2: I asked about "dukkha" (suffering), a topic central to Buddhism.**

Here the opposite problem showed up. The Buddhist side had tons of strong, specific quotes about suffering. The Hindu side, by contrast, kept saying things like "we don't have a specific enough quote to back this up." This wasn't because Advaita Vedanta has nothing to say about suffering. It clearly does. The real reason was that my underlying source material (a database of tagged philosophical quotes) happened to have much richer, more specific coverage of this topic on the Buddhist side. The debate ended up looking like Buddhism "won," but really it just had a deeper well of well organized evidence to draw from.

**Round 3: I let each side argue using its own home term. Buddhism argued for anatta. Hinduism argued for atman.**

This is when the debate actually came alive. Both sides had strong, specific things to say, in their own words, on their own terms. The Buddhist AI built up a real argument step by step: there's no fixed self, everything is impermanent, even the comforting idea of a "soul" is something we cling to out of fear, and that clinging itself is a source of suffering. The Hindu AI held firm on its own ground too: there is something unchanging beneath the impermanence, and that's what truly defines us. Neither side caved. It read like an actual disagreement between two real, coherent worldviews. That's because, for the first time, neither side was forced to fight on the other's home turf.

## Why this matters beyond philosophy nerds

If you've ever asked an AI to "compare X and Y" or "explain both sides of," the framing of your question is doing more work than you might think.

Forcing two different perspectives to use the exact same vocabulary can quietly favor whichever side that vocabulary originally belongs to. It's a bit like asking a tea drinker and a coffee drinker to debate "is tea good?" The coffee drinker never even gets to make their real case, because the question was never on their terms to begin with.

A more honest way to compare two viewpoints is often to let each one make its strongest case in its own language first, and then look at where they actually clash, rather than forcing them into a single shared frame from the start.

This also applies outside of religion or philosophy. Think about workplace disagreements, political debates, or even comparing two product strategies. If you frame a comparison using only one side's terminology or metrics, you can end up with a debate that looks balanced but secretly isn't.

## A second, smaller lesson: sometimes "winning" just means having better notes

In the suffering debate, the Buddhist side looked stronger mostly because it had richer, more detailed source material to draw from, not because its philosophical position was actually stronger. This is an easy trap to fall into with any AI comparison tool. If one side's information happens to be more complete or better organized than the other's, the AI can end up looking more convincing on that side, even when the underlying ideas are equally rich. It's worth asking, when an AI tells you one argument "has stronger support," whether that's really about the strength of the idea, or just about how well documented it happened to be in whatever the AI was trained or fed on.

## The honest part I actually liked best

The most reassuring thing in this whole experiment wasn't the debate itself. It was watching the AI say "I don't have evidence for that" instead of making something up to sound convincing. When the Buddhist AI had nothing to cite, it didn't pretend. It said so plainly. That's a small thing, but it's the difference between an AI tool you can actually trust to show its work, and one that just sounds confident.

If you're using AI for anything where accuracy matters, that's the behavior worth looking for: not whether it always has an answer, but whether it's willing to tell you when it doesn't.

## The takeaway

Next time you ask an AI to compare two sides of something, try asking it twice: once using neutral or shared terms, and once letting each side describe itself in its own words. You might be surprised how different the two answers look, and which one actually helps you understand the disagreement better.

---

*The philosophical text database behind this experiment is [darshana-graph](https://github.com/joyboseroy/darshana-graph), an open dataset of Hindu, Buddhist, and Jain texts organized for exactly this kind of comparison. The debate tool itself is [vada-simulator](https://github.com/joyboseroy/vada-simulator), also open source if you want to try it yourself or run your own three-round experiment on a different question.*

## A follow-up: "real citation" doesn't always mean "accurate claim"

After publishing the first version of this piece, someone who actually knows Advaita Vedanta well read one of the transcripts and pointed out a real error. The AI had written that "the self is distinct from karma, or actions, and their consequences, as it is not affected by them." That sounds reasonable, but it's not quite right. Advaita Vedanta's actual position is that there is no karma, no action, and no consequence that exists separately from the self at all. There is only the self. Saying the self is "distinct from" karma quietly assumes karma is a real, separate thing sitting next to the self, which is exactly what this school of thought denies.

I checked where that claim came from. The AI had a real quote to back it up, an old text saying the self "shakes off both virtue and vice." That's a real, defensible idea: the self isn't touched by the consequences of past actions. But "shakes off" and "is unaffected by" are not the same claim as "is a separate thing from." The AI took a quote about being untouched by something and turned it into a quote about being a separate entity from something. That's a small shift in wording with a big shift in meaning, and it happened even though the citation itself was completely real and properly sourced.

This matters more than it might first seem. Having a real source for a claim is reassuring, but it isn't the same as the claim being an accurate summary of that source. A citation tells you "this comes from somewhere real." It doesn't tell you "this is a faithful description of what that source actually says." Those are two different kinds of trust, and it's easy to only check for the first one.

If you use AI tools that show their sources, it's worth occasionally clicking through to the actual source, not just checking that a source exists. The presence of a citation is a good sign. It is not, by itself, proof that the AI read the source correctly.

