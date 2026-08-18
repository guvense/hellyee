# Recording the demo GIFs

The README references three GIFs that need to be recorded by hand — they show
Live's UI reacting in real time, which cannot be generated from code.

Record with [Kap](https://getkap.co) (free, macOS) or ScreenStudio, export as
GIF at **900 px wide**, **12–15 fps**, and keep each one **under 8 MB** so
GitHub renders it inline. Save them to `docs/`.

### 1. `docs/demo-build.gif` — the headline demo (~25 s)

Split screen: Claude on the left, Live's Session View on the right.

1. Start from an empty Live set.
2. Type: `make a 4-bar house beat at 124 BPM in F minor, then add a bassline`
3. Let it run. The GIF should capture tracks appearing, devices loading, and
   MIDI notes materialising in the clips.
4. End on the clips playing.

### 2. `docs/demo-sound-design.gif` — parameter control (~15 s)

Live's Device View, showing a Wavetable instrument.

1. Type: `make this lead softer — round off the highs and slow the attack`
2. Capture the knobs physically moving as parameters are set.

### 3. `docs/demo-arrangement.gif` — the full song (~20 s)

Live's Arrangement View, zoomed to fit.

1. Type: `arrange this into a full track — intro, build, drop, breakdown, drop, outro`
2. Capture clips filling the timeline section by section.
3. End on the full arrangement in view.

### 4. `docs/demo-install.gif` — the installer (~10 s)

A terminal, nothing else. Shows how little there is to it.

1. Type `uvx hellyee setup` and let it run to completion.
2. Capture the download, patch and config lines, ending on the manual-step
   instructions.

This one matters more than it looks — "is this hard to install?" is the first
question anyone asks.

### Tips

- Hide your track list / personal projects; use a clean set.
- Increase Live's zoom so clips read clearly at 900 px.
- Trim dead time — nobody wants to watch a VST load for 4 seconds.
