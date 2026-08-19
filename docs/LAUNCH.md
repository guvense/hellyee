# Getting hellyee heard

Ordered by leverage. Do the prerequisites first — every later step points
people at the repo, and the repo has one chance to look finished.

## 0. Prerequisites (before any announcement)

- [ ] **Record the GIFs** (`docs/RECORDING.md`). The install GIF and the
      arrangement GIF matter most. Nobody reads before they watch.
- [ ] **CI green on all three OSes** — the badge is social proof.
- [ ] **Repo settings on GitHub:**
  - Description: `Make music in Ableton Live by talking to Claude — mixes and masters by actually reading the meters`
  - Topics: `ableton` `ableton-live` `mcp` `mcp-server` `claude` `ai` `music-production` `midi` `osc` `music`
  - Social preview image (Settings → General): screenshot of the arrangement
    Claude built, or the architecture SVG on a dark background.
- [ ] Pin a short demo video or GIF at the top of the README.

## 1. MCP directories (free, lasting traffic)

These are where people actually search for MCP servers:

| Directory | How |
|---|---|
| [PulseMCP](https://www.pulsemcp.com) | Submit form on site ("Add a server") |
| [Glama](https://glama.ai/mcp/servers) | Indexes GitHub automatically once topics are set; can also claim the listing |
| [mcpservers.org](https://mcpservers.org) | PR to their GitHub repo |
| [mcp.directory](https://mcp.directory) | Submission form |
| [LobeHub MCP](https://lobehub.com/mcp) | Submission form |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | PR adding hellyee to the community servers list — the highest-traffic single link |

## 2. Community posts

One post per community, written for that community, honest about limits.
Never post the same text twice; each community smells cross-posting.

### Show HN (news.ycombinator.com)

> **Title:** Show HN: Hellyee – Claude makes music in Ableton, mixing by
> actually reading the meters
>
> **Text:** I built an MCP server that lets Claude drive Ableton Live
> end-to-end. The part I haven't seen elsewhere: it closes the loop —
> when you say "balance the mix", it plays the drop, reads every track's
> output meter, adjusts faders, and measures again until it converges.
> Same for mastering: it drives the limiter by measured headroom, and
> checks that the breakdown-to-drop dynamic survived.
>
> It also ships a "skill" — a document teaching the model how to produce:
> which Live behaviours fail silently, why a bass filtered at 400 Hz
> disappears, why a drop only lands if the section before it is thinner.
>
> Honest limits: Claude can't hear, so tonal judgement is convention +
> measurement, not taste. Third-party VSTs expose one parameter until you
> Configure them by hand. Audio-to-MIDI is monophonic.
>
> Install: uvx hellyee setup. Python package, MIT, built on AbletonOSC.

Post on a weekday morning US time. Reply to every comment fast — HN rewards
present authors.

### r/ableton and r/edmproduction

Both ban low-effort self-promo; both allow "I built a thing" posts with
substance. Lead with the *result*, not the tool: post the arrangement
screenshot or GIF ("I had Claude build and master a full trance track in
Ableton — here's how the levels converged") and put the repo link in a
comment. Show the meter-convergence table — producers respect numbers.

### r/ClaudeAI and r/mcp

More tolerant of tool posts. Focus on the MCP angle: the skill layer, the
closed measurement loop, what the tool descriptions alone couldn't teach.

### X / Bluesky

30-second screen recording: type one sentence, watch tracks appear, devices
load, the timeline fill. Caption: "Claude just arranged, mixed and mastered
this. It read the meters itself. `uvx hellyee setup`" — tag @AnthropicAI.

## 3. Slower burns

- **Anthropic's MCP Discord / community showcase** — post in show-and-tell.
- **Ableton forum** (forum.ableton.com, Max/Remote Scripts section) — the
  AbletonOSC-patch angle interests that crowd; frame as "extending
  AbletonOSC with browser/master/automation handlers".
- **A 3-5 minute YouTube walkthrough** — "AI produces a track in Ableton,
  start to finish" is a searchable phrase with real volume. Screen + voice,
  no editing needed.
- **Write up the build story** (blog/dev.to): "What breaks when an AI
  produces music" — the back_to_arranger trap, the muffled-filter bug, the
  silent-track fader disaster. Failure stories travel further than feature
  lists.

## What not to do

- Don't submit to directories before the GIFs exist.
- Don't astroturf (fake accounts, engagement pods) — small communities
  notice, and the repo is the proof anyway.
- Don't oversell the AI: "Claude can't hear" stated plainly builds more
  trust than any claim. It's also the interesting part.
