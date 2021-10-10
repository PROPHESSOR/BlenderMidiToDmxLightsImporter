import json
import sys
from mido import MidiFile, tick2second, tempo2bpm

if len(sys.argv) < 2:
    print('Usage: <path/to/file.mid>')
    exit()

FILENAME = sys.argv[1]
FPS = 30

mid = MidiFile(FILENAME, clip=True)

for i, track in enumerate(mid.tracks):
    print(i, track.name, len(track), 'events')

track = int(input('Track number >>> '))
assert(track >= 0 and track < len(mid.tracks))

note = int(input('Channel 1 note (36=C2) >>> '))
assert(note >= 0 and note < 128)

channelsno = int(input('Channels >>> '))
assert(channelsno > 0)

tempo_ms = None

for event in mid.tracks[0]:
    if event.type == 'set_tempo':
        tempo_ms = event.tempo
        break

print('BPM:', round(tempo2bpm(tempo_ms)))

export = [[] for _ in range(channelsno)]

time = 0
prevvelocity = None

for event in mid.tracks[track]:
    time += event.time
    if not event.type in ('note_on', 'note_off)'): continue

    if event.note != note: continue

    time_sec = tick2second(time, mid.ticks_per_beat, tempo_ms)

    frame = time_sec * FPS

    for i in range(channelsno):
        if event.note == note + i:
            export[i].append((round(frame), event.velocity))
            break

    #if prevvelocity == event.velocity: continue
    #prevvelocity = event.velocity



with open(f'{FILENAME}_{track}_{note}x{channelsno}.json', 'w') as _out:
    json.dump(export, _out)
