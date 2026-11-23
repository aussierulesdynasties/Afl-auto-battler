# Crowd sounds and the ground siren

Built by `tools/audio/build_crowd.py`; don't edit the WAVs, change the script or its takes and re-run it:

```bash
python tools/audio/build_crowd.py      # needs numpy, scipy, pyloudnorm and ffmpeg
```

| File | Length | What it is | Where it comes from |
|---|---|---|---|
| `crowd_bed.wav` | 30 s, seamless loop | The crowd during general play | ElevenLabs take |
| `crowd_goal.wav` | 5.5 s | The roar for a goal, and for your side running through the banner | ElevenLabs take |
| `crowd_behind.wav` | 4 s | "Ohhh" into a groan, for a behind | ElevenLabs take |
| `crowd_ball.wav` | 3.5 s | "BALL!" at a tackle paid as holding the ball | ElevenLabs take |
| `crowd_siren.wav` | 7.2 s | The siren in the stadium, the crowd coming up under it 0.8 s later | Siren synthesised; crowd an ElevenLabs take |

44100 Hz, mono, 16-bit, every peak under -3 dBFS. `scripts/ui/match/CrowdSound.gd` sets the level of each sound as it plays (louder through a run of goals, quieter for the away side); with the file levels a home goal roars about 14 dB over the murmur and the siren sits about 12 dB over it.

## The siren

Every AFL ground we measured sounds the same siren: the MCG (2021 and 2022 clips, the 2026 Grand Final from the stands, the 2023 Grand Final broadcast), Optus Stadium, and a country ground in South Australia. It is two notes at once, about 329 Hz and 441 Hz (E4 and A4), each with its own row of overtones. The two rows meet near 1317 and 1323 Hz, and those partials beat about six times a second: that is its waver. It comes on in about 40 ms with no wind-up, and the timekeeper held it about four seconds at the 2026 Grand Final.

The script builds those two notes with the overtone levels averaged from the three MCG recordings, drives them through one soft-clipped horn (which adds the faint in-between partials the recordings have), and puts it in a stadium: a 2.2 s reverb that loses its top first, and the echo back off the far stand about half a second later.

Measured against the four real grounds (1/24-octave spectrum, 250 Hz to 5 kHz, correlation), the siren over the crowd scores 0.75; the real grounds score 0.68 to 0.80 against each other. The old two-sine siren scored 0.22.

The recordings were only measured. None of them is in the game or in this repository.

## The crowd takes

Made with ElevenLabs Sound Effects (model v3) on the director's own paid account, which licenses them for use in the game. The takes and their prompts are in `tools/audio/crowd_sources/`.
