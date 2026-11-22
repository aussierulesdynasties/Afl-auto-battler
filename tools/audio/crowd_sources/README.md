# Crowd takes

ElevenLabs Sound Effects (v3, prompt influence 30%) on the director's account, 2026-11-21. Each prompt gave four takes; the one kept is named here. `tools/audio/build_crowd.py` trims and levels them into `assets/audio/crowd/`.

| File | Take | Prompt |
|---|---|---|
| `bed.mp3` | 30 s, loop on | Steady ambience of a big Australian football stadium crowd of 50,000 during general play: a constant wash of thousands of voices murmuring and chatting, occasional distant individual shouts of encouragement, a few claps, a low rumble of anticipation. Even level throughout, no big cheers. Recorded from high in the grandstand, open-air stadium reverb. No music, no commentary, no announcer. |
| `goal.mp3` | 6 s | A packed Australian football stadium of 80,000 people erupting the instant a goal is kicked: a sudden huge roar of cheering, whistling and clapping from all around the ground, peaking after a second, then slowly settling back to excited chatter. Recorded from high in the grandstand, big open-air stadium reverb. No music, no commentary, no announcer. |
| `behind.mp3` | 6 s | A big Australian football stadium crowd of 50,000 reacting to a shot at goal that just misses for a behind: a rising hopeful 'ohhh' that turns into a loud collective groan, mixed with scattered polite applause from the other supporters, then back to chatter. Recorded from the grandstand, open-air stadium reverb. No music, no commentary. |
| `ball.mp3` | 6 s | Australian football stadium crowd of 50,000 screaming 'BALL!' together as a player is tackled holding the ball: hundreds of loud angry voices bellowing one sharp 'BAAALL!', a few voices continuing 'baaall!', then excited buzzing chatter. Recorded from the grandstand, open-air stadium reverb. No music, no commentary. |
| `siren_swell.mp3` | 6 s | The end of a quarter at a packed Australian football stadium of 80,000: the crowd goes from tense murmur to a big rolling roar of cheering, clapping and whistling that swells for three seconds and slowly fades into loud chatter as the players leave the ground. Recorded from the grandstand, huge open-air stadium reverb. No siren, no horn, no music, no commentary. |

Each take was chosen without playing it aloud: by its loudness over time and a speech-recognition pass (the "BALL!" take reads as "All!", the behind as "Oh!", the goal and the swell as "Yeah!").

ElevenLabs was also asked for the siren itself. All four takes were a single note near 208 Hz with its overtones, not the AFL siren's two notes, so the siren is synthesised from measurements instead (see `assets/audio/crowd/README.md`).
