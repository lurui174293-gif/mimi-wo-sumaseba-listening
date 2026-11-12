"""Build the listening data from a locally supplied timed bilingual ASS file.

The reference ASS is deliberately kept out of the repository. The site's
existing data.json supplies clip boundaries and previously reviewed grammar.
"""
from __future__ import annotations

import html
import json
import re
import difflib
from pathlib import Path

from pykakasi import kakasi

ROOT = Path(__file__).parent
SOURCE = ROOT / "reference_subtitles" / "official-bilingual.ass"
if not SOURCE.exists():
    raise SystemExit(f"Missing local reference subtitle: {SOURCE}")


def seconds(value: str) -> float:
    hours, minutes, sec = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(sec)


def clean_ass(value: str) -> str:
    value = re.sub(r"\{[^}]*\}", "", value)
    value = value.replace(r"\N", " ").replace(r"\n", " ").replace(r"\h", " ")
    return re.sub(r"\s+", " ", value).strip()


by_style: dict[str, list[dict]] = {name: [] for name in ("main-cn", "main-jp", "ed-cn", "ed-jp")}
for line in SOURCE.read_text(encoding="utf-8-sig").splitlines():
    if not line.startswith("Dialogue: "):
        continue
    fields = line[len("Dialogue: "):].split(",", 9)
    if len(fields) != 10 or fields[3] not in by_style:
        continue
    by_style[fields[3]].append({"s": seconds(fields[1]), "e": seconds(fields[2]), "text": clean_ass(fields[9])})

assert len(by_style["main-cn"]) == len(by_style["main-jp"]) == 1218
assert all((cn["s"], cn["e"]) == (ja["s"], ja["e"])
           for cn, ja in zip(by_style["main-cn"], by_style["main-jp"]))

old_parts = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
old_cues = [(part["start"] + cue["s"], cue)
            for part in old_parts for cue in part["cues"] if cue["grammar"]]
reader = kakasi()
kanji = re.compile(r"[\u3400-\u9fff々]")
SPECIAL_READINGS = {"月島": "つきしま", "天沢": "あまさわ", "聖司": "せいじ",
                    "雫": "しずく", "夕子": "ゆうこ", "杉村": "すぎむら",
                    "緑柱石": "りょくちゅうせき", "この間": "このあいだ",
                    "行方": "ゆくえ"}
special_pattern = re.compile("|".join(map(re.escape, sorted(SPECIAL_READINGS, key=len, reverse=True))))


def ruby_plain(text: str) -> str:
    result = []
    for token in reader.convert(text):
        original, reading = token["orig"], token["hira"]
        if original == "人":
            reading = "ひと"
        elif original == "小さい":
            reading = "ちいさい"
        elif original == "小さく":
            reading = "ちいさく"
        elif original == "厳しい":
            reading = "きびしい"
        elif original == "日":
            reading = "ひ"
        if not kanji.search(original):
            result.append(html.escape(original))
            continue
        # Leave okurigana beside the ruby, like the user's reference image.
        suffix = ""
        while original and reading and not kanji.search(original[-1]) and original[-1] == reading[-1]:
            suffix = original[-1] + suffix
            original, reading = original[:-1], reading[:-1]
        if original and reading:
            result.append(f"<ruby>{html.escape(original)}<rt>{html.escape(reading)}</rt></ruby>{html.escape(suffix)}")
        else:
            result.append(html.escape(token["orig"]))
    return "".join(result)


def ruby(text: str) -> str:
    result = []
    pos = 0
    for match in special_pattern.finditer(text):
        result.append(ruby_plain(text[pos:match.start()]))
        name = match.group()
        result.append(f"<ruby>{html.escape(name)}<rt>{SPECIAL_READINGS[name]}</rt></ruby>")
        pos = match.end()
    result.append(ruby_plain(text[pos:]))
    return "".join(result)


def reading_key(text: str) -> str:
    return re.sub(r"[^ぁ-んァ-ヶーa-z0-9]", "", "".join(token["hira"] for token in reader.convert(text)).lower())


GRAMMAR_RULES = {
    "～ている": (r"(?<!慌)てる|でる|ている|でいる", "表示动作正在进行或状态持续；口语常省略「い」，说成「てる／でる」。"),
    "～てしまう": (r"ちゃった|じゃった|ちゃう|じゃう|てしま", "口语常缩成「ちゃう／じゃう」；表示动作完成，也可带意外或遗憾的语气。"),
    "～てくれる": (r"てくれ(?:た|る|て|ない|れば)", "别人为自己或己方做某事，带有受益的语感。"),
    "～てもらう": (r"てもら", "请别人为自己做某事，强调受到的帮助。"),
    "～てあげる": (r"てあげ(?:る|て|た)", "为别人做某事，强调给予帮助。"),
    "～ておく": (r"(?:といどく|話しとく|出しといて|ておく)", "提前做好某事；口语里「ておく」常缩成「とく」。"),
    "～てもいい": (r"(?<!と)てもいい|ていい[?？]", "表示请求或给予许可，相当于‘可以……吗／可以……’。"),
    "～なくていい": (r"なくていい", "表示没有必要做某事，相当于‘不用……’。"),
    "～てみる": (r"てみる|てみて|てみた", "试着做某事，强调先尝试看看。"),
    "～ようと思う": (r"ようと思", "表示打算做某事。"),
    "～気がする": (r"気がする", "表示说话人的感觉或不确定的判断，相当于‘总觉得……’。"),
    "～わけじゃない": (r"わけじゃない|わけではない", "表示并非完全如此，相当于‘并不是说……’。"),
    "～ずに": (r"ずに", "表示不做前一动作就做后一动作，相当于‘没……就……’。"),
    "～たり～たり": (r"たり[^。！？?]*たり", "列举几个动作或状态，表示‘又……又……’或‘时而……时而……’。"),
    "～なきゃ": (r"なきゃ|なくちゃ", "「なければならない」的口语说法，表示必须做某事。"),
    "～っぱなし": (r"っぱなし", "做完某动作后保持原状，常带责备语气。"),
}


def grammar_for(start: float, end: float, japanese: str) -> list[dict]:
    notes: list[dict] = []
    names = set()
    for when, old in old_cues:
        if not (start - 2 <= when <= end + 1):
            continue
        source = old.get("raw_ja", old["ja"])
        a = reading_key(source)
        b = reading_key(japanese)
        if len(a) < 4 or not (a in b or b in a or difflib.SequenceMatcher(None, a, b).ratio() >= 0.72):
            continue
        for item in old["grammar"]:
            if item["name"] not in names:
                notes.append(item.copy())
                names.add(item["name"])
    for name, (pattern, body) in GRAMMAR_RULES.items():
        if name not in names and re.search(pattern, japanese):
            if name == "～てしまう" and "～てしまった" in names:
                continue
            notes.append({"name": name, "body": body})
            names.add(name)
    required = {
        "～から": r"から", "～たら": r"たら", "～でしょう": r"でしょ",
        "～たほうがいい": r"(?:方|ほう)がいい", "～てもらう": r"てもら",
        "～てしまった": r"ちゃった|じゃった|てしまった",
        "～なければならない": r"なきゃ|なくちゃ|なければ|ないと",
    }
    return [note for note in notes if note["name"] not in required or re.search(required[note["name"]], japanese)]


pairs = []
last_dialogue_end = max(cue["e"] for cue in by_style["main-jp"])
for cn_style, jp_style in (("main-cn", "main-jp"), ("ed-cn", "ed-jp")):
    for cn, ja in zip(by_style[cn_style], by_style[jp_style]):
        if ja["s"] < 120 or not ja["text"] or not cn["text"]:
            continue
        start = ja["s"]
        if jp_style == "ed-jp":
            if ja["e"] <= last_dialogue_end:
                continue
            start = max(start, last_dialogue_end + 0.02)
        japanese = ja["text"].replace("ちようど", "ちょうど").replace("おぱさん", "おばさん").replace("応援しょう", "応援しよう")
        chinese = cn["text"].replace("滴", "雫")
        pairs.append({"s": start, "e": ja["e"], "ja": japanese, "zh": chinese,
                      "ruby": ruby(japanese), "grammar": grammar_for(start, ja["e"], japanese)})
pairs.sort(key=lambda cue: (cue["s"], cue["e"]))
pairs.insert(0, {"s": 0.0, "e": 120.0, "ja": "オープニング曲", "zh": "片头曲（英语演唱）。点击“跳过片头曲”可从日语对白开始。",
                 "ruby": ruby("オープニング曲"), "grammar": []})

parts = []
for old in old_parts:
    start, duration = old["start"], old["duration"]
    end = start + duration
    cues = [{**cue, "s": round(cue["s"] - start, 2), "e": round(min(cue["e"], end) - start, 2)}
            for cue in pairs if start <= cue["s"] < end]
    parts.append({"file": old["file"], "start": start, "duration": duration, "cues": cues})

blob = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
(ROOT / "data.json").write_text(blob + "\n", encoding="utf-8")
(ROOT / "data.js").write_text("init(" + blob + ");\n", encoding="utf-8")
print("Cues:", [len(part["cues"]) for part in parts])
print("Grammar notes:", sum(bool(cue["grammar"]) for part in parts for cue in part["cues"]))
