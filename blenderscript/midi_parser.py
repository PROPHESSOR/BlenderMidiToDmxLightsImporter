from .mido import MidiFile, tick2second, tempo2bpm

FPS = 30

class MidiLightParser:
    filename: str = None
    tempo_ms: int = None
    BPM: int = None
    tracks: list = None
    ticks_per_beat: int = None

    def unload(self):
        self.filename = None
        self.tempo_ms = None
        self.BPM = None
        self.tracks = None
        self.ticks_per_beat = None


    def load(self, filename: str):
        mid = MidiFile(filename, clip=True)

        self.tracks = mid.tracks
        self.ticks_per_beat = mid.ticks_per_beat

        for event in mid.tracks[0]:
            if event.type == 'set_tempo':
                self.tempo_ms = event.tempo
                break

        self.BPM = round(tempo2bpm(self.tempo_ms))

    def getNotesInTrack(self, trackId: int):
        assert(self.tracks and trackId >= 0 and trackId < len(self.tracks))

        track = self.tracks[trackId]

        notes = set()

        for event in track:
            if event.type in ('note_on', 'note_off'):
                notes.add(event.note)

        return sorted(list(notes))

    def parse(self, trackId: int, note: int):
        assert(self.tracks and trackId >= 0 and trackId < len(self.tracks))
        assert(note >= 0 and note < 128)

        time = 0
        track = self.tracks[trackId]

        export = []

        for event in track:
            time += event.time
            if not event.type in ('note_on', 'note_off)'): continue

            if event.note != note: continue

            time_sec = tick2second(time, self.ticks_per_beat, tempo_ms)

            frame = time_sec * FPS

            if event.note == note:
                export.append((round(frame), event.velocity))
                break


# for i, track in enumerate(mid.tracks):
#     print(i, track.name, len(track), 'events')
