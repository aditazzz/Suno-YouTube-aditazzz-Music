"""python3 timing.py -> web/data/timing.json, everything the film is timed to.

Build web/data/timing.json for the whole song from the measurements (clean WAV): tracked beats (105.47 BPM,
HEYs land on beat 3), vocal-stem word onsets / parakeet word times, and the hook template measured in hook 1."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
bt = json.load(open(os.path.join(HERE, "build", "beats.json")))   # the tracked beats (105.47 BPM), measured on the clean WAV
per = 0.56889
while bt[-1] + per < 244.8: bt.append(round(bt[-1] + per, 4))
down = bt[1::4]

def L(text, words, t, end=None): return {"text": text, "words": words, "t": t, "end": end}
heys = [25.199, 27.487, 34.354, 36.641, 70.914, 73.189, 80.051, 82.326, 134.548, 136.812, 143.592, 145.856, 188.906, 191.17, 197.95, 200.202]
S, C, T_, R_ = "Shuffle the deck!", "Cast the cards!", "Turn one over, place your bets", "or reach for"
sw, cw, tw = ["Shuffle", "the", "deck!"], ["Cast", "the", "cards!"], ["Turn", "one", "over,", "place", "your", "bets"]
lines = [
  # ---- intro + hook 1 (the preview, unchanged)
  L("Good news. Bad news.", ["Good", "news.", "Bad", "news."], [9.70, 10.0, 12.87, 13.25], 14.4),
  L("I've seen what's coming.", ["I've", "seen", "what's", "coming."], [18.52, 18.82, 19.08, 19.3], 20.9),
  L("Choose.", ["Choose."], [22.2], 22.95),
  L(S, sw, [23.83, 24.2, 24.35], 25.2), L(S, sw, [26.16, 26.5, 26.7], 27.5),
  L(T_, tw, [28.56, 29.0, 29.5, 30.35, 30.95, 31.4], 32.7),
  L(C, cw, [33.14, 33.5, 33.72], 34.354), L(C, cw, [35.5, 35.8, 36.05], 36.641),
  L(R_, ["or", "reach", "for"], [39.5, 40.12, 40.7], 41.2),
  # ---- verse 1: Twenty Percent
  L("A man with a rocket sits down by the fire", "A man with a rocket sits down by the fire".split(), [42.64, 42.8, 43.04, 43.2, 43.36, 43.76, 44.08, 44.32, 44.48, 44.64], 46.8),
  L("He turns up", ["He", "turns", "up"], [47.2, 47.36, 47.68], 47.92),
  L("the flames climbing higher", ["the", "flames", "climbing", "higher"], [48.4, 48.56, 48.88, 49.36], 51.3),
  L("“Twenty percent,” he says with a grin", ["“Twenty", "percent,”", "he", "says", "with", "a", "grin"], [51.92, 52.48, 52.96, 53.12, 53.44, 53.6, 53.76], 54.1),
  L("The whole hall laughs as the night closes in", "The whole hall laughs as the night closes in".split(), [54.24, 54.4, 54.88, 55.36, 56.08, 56.32, 56.48, 58.08, 58.5], 59.6),
  L("He turns up", ["He", "turns", "up"], [60.72, 61.04, 61.44], 61.62),
  L("a world without need", ["a", "world", "without", "need"], [62.08, 62.16, 62.48, 62.8], 63.02),
  L("The machines make plenty, but who gets to eat?", "The machines make plenty, but who gets to eat?".split(), [63.12, 63.28, 63.76, 64.0, 64.24, 64.48, 64.64, 64.88, 65.07], 65.22),
  L("A feast on one side, the other in flames", "A feast on one side, the other in flames".split(), [65.25, 65.44, 65.92, 66.08, 66.32, 66.72, 66.88, 67.04, 67.2], 67.95),
  L("Two different futures, the very same game", "Two different futures, the very same game".split(), [68.0, 68.24, 68.48, 69.04, 69.2, 69.36, 69.45], 69.6),
  # ---- hook 2
  L(S, sw, [69.63, 70.0, 70.2], heys[4]), L(S, sw, [71.93, 72.34, 72.5], heys[5]),
  L(T_, tw, [74.3, 74.75, 75.25, 76.1, 76.7, 77.15], 78.6),
  L(C, cw, [78.84, 79.18, 79.4], heys[6]), L(C, cw, [81.25, 81.44, 81.68], heys[7]),
  L(R_, ["or", "reach", "for"], [85.22, 85.84, 86.42], 86.92),
  # ---- refrain 1
  L("Singularity", ["Singularity"], [88.72], 90.55), L("Singularity", ["Singularity"], [90.9], 92.45),
  L("Every card a possibility", ["Every", "card", "a", "possibility"], [92.64, 93.04, 93.6, 93.76], 94.15),
  L("None a guarantee", ["None", "a", "guarantee"], [94.29, 94.7, 95.1], 96.7),
  # ---- verse 2: the Robot, the Red Planet, the Gardener (Voluntarily), the Fool
  L("comes up, no more rowing the seas", "comes up, no more rowing the seas".split(), [97.52, 97.84, 98.88, 99.12, 99.36, 99.76, 99.92], 100.5),
  L("Machines take the oars while we sit in the breeze", "Machines take the oars while we sit in the breeze".split(), [100.67, 101.41, 102.16, 102.32, 103.28, 103.6, 103.76, 104.24, 104.4, 104.48], 105.6),
  L("rises, another new shore", ["rises,", "another", "new", "shore"], [107.1, 108.0, 108.72, 109.04], 110.2),
  L("We plant our old flags and go looking for more", "We plant our old flags and go looking for more".split(), [110.4, 110.76, 111.12, 111.28, 111.84, 112.48, 112.72, 113.04, 113.36, 113.6], 114.0),
  L("card, we're finally free", ["card,", "we're", "finally", "free"], [115.8, 117.08, 117.52, 118.0], 119.2),
  L("To grow our tomatoes voluntarily", ["To", "grow", "our", "tomatoes", "voluntarily"], [119.44, 119.76, 120.0, 120.24, 121.52], 123.6),
  L("turns and asks what we're living for", "turns and asks what we're living for".split(), [124.64, 125.28, 125.6, 126.08, 126.24, 126.56, 127.28], 128.4),
  L("When the machines do it all, what are we needed for?", "When the machines do it all, what are we needed for?".split(), [128.64, 128.8, 128.96, 130.0, 130.4, 130.64, 131.12, 131.28, 131.44, 131.52, 132.4], 133.0),
  # ---- hook 3
  L(S, sw, [133.25, 133.76, 133.92], heys[8]), L(S, sw, [135.6, 136.0, 136.16], heys[9]),
  L(T_, tw, [137.92, 138.24, 138.72, 140.08, 140.48, 140.72], 142.2),
  L(C, cw, [142.5, 142.85, 142.97], heys[10]), L(C, cw, [144.76, 145.0, 145.2], heys[11]),
  L(R_, ["or", "reach", "for"], [148.7, 149.32, 149.76], 150.1),
  # ---- bridge: one card per bar
  L("holds the power", ["holds", "the", "power"], [152.56, 152.88, 153.12], 153.85),
  L("holds the cost", ["holds", "the", "cost"], [154.8, 155.2, 155.36], 156.15),
  L("promises plenty", ["promises", "plenty"], [157.04, 157.68], 158.45),
  L("asks what we lost", ["asks", "what", "we", "lost"], [159.2, 159.52, 159.76, 160.0], 160.75),
  L("If it does the thinking", "If it does the thinking".split(), [160.88, 161.04, 161.2, 161.92, 162.16], 162.75),
  L("If it makes the art", "If it makes the art".split(), [162.88, 163.12, 163.36, 164.16, 164.56], 164.9),
  L("Did we lose our purpose", "Did we lose our purpose".split(), [165.04, 165.52, 165.76, 166.32, 166.64], 167.2),
  L("Or were we free from the start?", "Or were we free from the start?".split(), [167.36, 167.56, 167.76, 167.92, 168.48, 168.72, 168.96], 169.5),
  # ---- refrain 2
  L("Singularity", ["Singularity"], [170.16], 172.1), L("Singularity", ["Singularity"], [172.3], 174.0),
  L("Every card a possibility", ["Every", "card", "a", "possibility"], [174.16, 174.72, 175.2, 175.44], 176.2),
  L("None a guarantee", ["None", "a", "guarantee"], [176.4, 177.5, 178.1], 180.5),
  L("Singularity", ["Singularity"], [180.75], 181.95), L("Singularity", ["Singularity"], [182.08], 183.35),
  L("The choice belongs to you and me", "The choice belongs to you and me".split(), [183.52, 183.68, 184.72, 185.84, 186.16, 186.8, 187.04], 187.45),
  # ---- final hook
  L(S, sw, [187.6, 188.08, 188.24], heys[12]), L(S, sw, [189.92, 190.32, 190.56], heys[13]),
  L(T_, tw, [192.24, 192.8, 193.12, 194.4, 194.8, 195.52], 196.5),
  L(C, cw, [196.72, 197.12, 197.28], heys[14]), L(C, cw, [198.96, 199.36, 199.52], heys[15]),
  L(R_, ["or", "reach", "for"], [203.3, 203.66, 204.21], 204.7),
  # ---- outro (the Fool's name is never captioned: the card says it)
  L("One last card.", ["One", "last", "card."], [207.36, 207.76, 208.16], 209.6),
  L("At the edge of the cliff.", "At the edge of the cliff.".split(), [211.68, 211.92, 212.08, 212.32, 212.56, 212.8], 213.5),
  L("Under the stars.", ["Under", "the", "stars."], [213.76, 214.24, 214.48], 215.9),
  L("He told us what the cards might show.", "He told us what the cards might show.".split(), [216.4, 216.64, 216.96, 217.12, 217.36, 217.52, 218.16, 218.8], 220.6),
  L("We asked how soon we could go.", "We asked how soon we could go.".split(), [221.04, 221.2, 221.52, 222.08, 223.28, 223.6, 224.08], 224.5),
  L("How soon.", ["How", "soon."], [226.64, 226.96], 227.85),
]
for l in lines: assert len(l["words"]) == len(l["t"]), l["text"]
cards = [  # the moments a card's own engraved title stands in for the sung name
  {"name": "RAGNARÖK", "t": 37.98}, {"name": "MARS", "t": 41.25},
  {"name": "THE TOWER", "t": 47.84}, {"name": "THE SUN", "t": 61.6},
  {"name": "RAGNARÖK", "t": 83.76}, {"name": "MARS", "t": 86.97},
  {"name": "THE ROBOT", "t": 96.96}, {"name": "THE RED PLANET", "t": 105.84}, {"name": "THE GARDENER", "t": 114.1}, {"name": "THE FOOL", "t": 124.0},
  {"name": "RAGNARÖK", "t": 147.25}, {"name": "MARS", "t": 150.15},
  {"name": "THE MAGICIAN", "t": 151.6}, {"name": "THE TOWER", "t": 154.0}, {"name": "THE STAR", "t": 156.32}, {"name": "THE FOOL", "t": 158.64},
  {"name": "RAGNARÖK", "t": 201.62}, {"name": "MARS", "t": 204.75}, {"name": "THE FOOL", "t": 209.92},
]
stomps = [22.901, 23.185, 23.47, 23.766, 68.621, 68.905, 69.195, 69.486, 186.659, 186.938, 187.217, 187.501]
T = {
  "_about": "Ragnarök or Reach for Mars (clean WAV). Seconds. Beats tracked at 105.47 BPM (every HEY lands on beat 3); downbeats = beats[1::4]. Words from vocal-stem onsets and parakeet word times; hooks from the hook-1 template.",
  "fps": 30, "dur": 244.8, "preview": {"start": 0, "end": 28.45},
  "thunder": [0.48, 1.96, 3.86], "silence": [5.2, 7.45], "drums": 7.45,
  "beats": bt, "downbeats": down, "lines": lines, "cards": cards, "heys": heys, "stomps": stomps,
  "sections": {"intro": [0, 22.6], "hook1": [22.6, 42.34], "v1": [42.34, 69.6], "hook2": [69.6, 88.6], "ref1": [88.6, 96.9], "v2": [96.9, 133.2],
               "hook3": [133.2, 151.5], "bridge": [151.5, 169.5], "ref2": [169.5, 187.5], "final": [187.5, 207.2], "outro": [207.2, 227.9], "coda": [227.9, 241.0], "tail": [241.0, 244.8]},
  "events": {"dropout": [129.8, 133.3], "silence2": [169.5, 170.0], "pause": [224.1, 226.6], "boom": 224.5, "coda": 227.9, "codaEnd": 241.0, "end": 244.8},
  "nextLine": 28.54,
}
out = os.path.join(HERE, "web", "data", "timing.json")
json.dump(T, open(out, "w"), indent=1, ensure_ascii=False)
print("wrote", out, len(lines), "lines,", len(bt), "beats,", len(down), "downbeats; last downbeat", down[-1])
