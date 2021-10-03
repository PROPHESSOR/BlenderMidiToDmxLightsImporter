import csv
from mido import MidiFile, tick2second, tempo2bpm

FILENAME = "In The End5.mid"
FPS = 30

mid = MidiFile(FILENAME)

for i, track in enumerate(mid.tracks):
    print(i, track.name, len(track), 'events')

track = int(input('>>> '))
assert(track >= 0 and track < len(mid.tracks))

tempo_ms = None

for event in mid.tracks[0]:
    if event.type == 'set_tempo':
        tempo_ms = event.tempo
        break

print('BPM:', round(tempo2bpm(tempo_ms)))

export = []

time = 0
prevvelocity = None

for event in mid.tracks[track]:
    time += event.time
    if not event.type in ('note_on', 'note_off)'): continue

    if prevvelocity == event.velocity: continue
    prevvelocity = event.velocity

    time_sec = tick2second(time, mid.ticks_per_beat, tempo_ms)

    frame = time_sec * FPS

    export.append((round(frame), event.velocity))

with open(f'{FILENAME}_{track}.csv', 'w') as _out:
    writer = csv.writer(_out)

    for row in export:
        writer.writerow(row)
