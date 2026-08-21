#!/usr/bin/env python3
"""
Multi-Platform Video Downloader -- Plain Script Version
=========================================================

Yeh wahi project hai jo notebook mein tha, bas bina ipywidgets ke -- terminal
se seedha chalta hai. Saara "asli kaam" (detect_platform, detect_video_type,
sanitize_filename, parse_links, download_one, save_summary) bilkul unchanged
hai, kyunki woh functions pehle se hi ipywidgets par depend nahi karte the.
Sirf interface badla hai: buttons/widgets ki jagah ab input() aur print() hai.

Chalane ke do tareeke:
    python script_version.py
        -- sab kuch interactively poochega (folder, phir links file)

    python script_version.py --dest "/home/you/Videos" --links "clips.txt"
        -- seedha chal jaayega, kuch nahi poochega

Is file mein comments jaan-boojh kar THODE ZYAADA detailed hain -- jahan bhi
koi library function ya Python syntax pehli baar dikhta hai, uske baare mein
ek chhoti si explanation saath mein di gayi hai. Agar koi cheez pehle se
familiar lage to comment ko skip karke seedha code par jaao.
"""

# ================= 1. IMPORTS =================
# "import" ka matlab hai -- kisi doosre ne pehle se likha hua, tested code
# apne program mein "udhaar" lena, taaki wahi cheez dobara na likhni pade.
# Neeche har import ke saamne likha hai woh KIS KAAM ke liye hai.

import os
# os = "operating system". Folder banana, file/folder maujood hai ya nahi
# check karna, do path-pieces ko sahi tareeke se jodna -- yeh sab "os"
# module se hota hai. Fayda: Windows ka path "C:\Users\..." aur
# Mac/Linux ka path "/home/..." dikhne mein alag hote hain -- os module
# in farkon ko khud hi sambhal leta hai, hume alag-alag code nahi likhna.

import re
# re = "regular expressions". Text ke andar se koi PATTERN dhoondhna
# (jaise "yahan kahin ek http:// wala link hai") ya kisi pattern ko
# replace karna -- yeh re module ka kaam hai. RegEx patterns poori tarah
# se field guide ke Part 3 mein samjhaye gaye hain.

import sys
# sys = "system". Isse hum program ko beech mein jaan-boojh kar rok sakte
# hain (sys.exit()) -- yahan sirf isi ek kaam ke liye use ho raha hai
# (neeche choose_destination_folder() mein dekho).

import json
# json = ek chhota, insaano ke bhi padhne layak text format, jisme Python
# dictionaries seedhe save ki ja sakti hain. Hum isse DEST_DIR ko "yaad"
# rakhne ke liye use kar rahe hain (downloader_config.json file mein).

import argparse
# argparse = terminal se diye gaye "--dest kuch_path" jaise flags ko
# professionally padhne ka built-in tareeka. Iske bina hume khud hi
# sys.argv (ek plain list of strings) manually check karna padta --
# argparse yeh sab kaam kar deta hai, aur "--help" flag bhi apne aap
# ban jaata hai (terminal mein "python script_version.py --help" try karo).

import traceback
# traceback = jab kisi cheez mein Exception aaye, uska POORA safar
# (kaunsi file, kaunsi line, kaunsa function, kis order mein) text ki
# tarah nikaalne ke liye. Terminal par jo lamba laal error dikhta hai,
# traceback usi ko ek STRING bana kar de deta hai, taaki hum use summary
# file mein save kar sakein aur baad mein padh sakein.

from datetime import datetime
# "from X import Y" -- poore datetime MODULE ko import karne ki jagah,
# sirf usme se "datetime" naam ki ek CLASS le rahe hain. Isse hum "abhi
# kya time hai" pata karte hain, summary file ka naam banane ke liye.

from urllib.parse import urlparse
# Isi tarah, urllib.parse module se sirf "urlparse" function le rahe
# hain -- yeh ek poore URL string ko tukdon mein todta hai (domain,
# path, query, etc.), taaki hum sirf domain dekh kar platform pehchaan
# sakein (neeche detect_platform() mein use hota hai).

import yt_dlp
# yt_dlp -- yeh EK HI third-party library hai (pip se `pip install
# yt-dlp` karke install ki jaati hai), jo poora asli "video dhoondho aur
# download karo" wala kaam karti hai. Baaki upar ke saare imports Python
# ke apne "built-in" modules hain -- unhe alag se install karne ki
# zaroorat nahi padti, Python ke saath hi aate hain. yt_dlp neeche
# download_one() mein use hoti hai: yt_dlp.YoutubeDL(...) ek "session"
# banata hai jisse hum kisi video ke baare mein poochh sakte hain, ya
# use asal mein download kar sakte hain.


# ================= 2. CONFIG =================
# Yeh section notebook ke "2. Imports & configuration" cell jaisa hi hai --
# CONFIG_FILE aur folder-persistence functions bhi hoo-ba-hoo copy hain,
# kyunki inka bhi ipywidgets se koi lena-dena nahi tha.

CONFIG_FILE = "downloader_config.json"
# Yeh ek RELATIVE path hai (poora "C:\..." ya "/home/..." nahi likha
# hai) -- jab bhi is naam se file kholi/likhi jaayegi, Python use "abhi
# is program ka current working folder kya hai" ke hisaab se dhoondhega.
# Zyadatar (jab terminal se seedhe is folder mein jaakar script chalayi
# jaaye), yeh isi folder mein ban jaati hai jahan yeh .py file khud rakhi
# hai -- lekin yeh guarantee nahi hai (agar script kisi doosre folder se
# chalayi jaaye, to config file WAHIN banegi, is folder mein nahi).

TARGET_SIZE_MB = 10       # ideal / pasandida size
HARD_MAX_SIZE_MB = 25     # absolute ceiling -- isse zyada allowed nahi
TARGET_SIZE_BYTES = TARGET_SIZE_MB * 1024 * 1024
HARD_MAX_SIZE_BYTES = HARD_MAX_SIZE_MB * 1024 * 1024
# Computer hamesha size ko BYTES mein sochta hai, seedhe MB mein nahi.
# 1 MB = 1024 KB, aur 1 KB = 1024 bytes -- isliye MB ko bytes mein
# badalne ke liye 1024 * 1024 (= 1,048,576) se multiply kar rahe hain.
# Yeh do naye variables (TARGET_SIZE_BYTES, HARD_MAX_SIZE_BYTES) neeche
# FORMAT_SELECTOR banane mein use honge.

# yt-dlp format selector: pehle 10MB ke andar fit karne ki koshish, nahi to 25MB,
# warna jo bhi sabse chhota format mile wahi le lo (best effort).
#
# EK video kayi "formats" (quality/size versions) mein available hota hai --
# 144p, 360p, 720p, alag-alag encoding waghera. Har format ke apne do
# size-fields ho sakte hain (yeh yt-dlp khud provide karta hai, hum inhe
# nahi banate):
#   filesize        -- EXACT size, jab platform khud confirm kar deta hai
#   filesize_approx -- ANDAAZA (yt-dlp khud bitrate x duration se
#                       calculate karta hai), jab platform exact size
#                       nahi deta
# (Kaafi videos -- khaaskar YouTube ke -- ek poori file ki tarah nahi,
# balki chhote-chhote chunks mein "stream" hote hain, isliye unka exact
# "filesize" pehle se pata nahi hota. Isi liye neeche dono, filesize aur
# filesize_approx, dono ko har size-tier par try kiya ja raha hai.)
#
# "/" ka matlab yahan yt-dlp ki apni bhasha mein "OR, agar yeh na mile to
# agla try karo" hai -- yt-dlp in options ko UPAR SE NEECHE, ek-ek karke
# check karta hai, aur jo PEHLA match ho jaaye, wahi istemal kar leta hai:
#   1) best jiska EXACT size < 10MB
#   2) best jiska ANDAAZA size < 10MB
#   3) best jiska EXACT size < 25MB
#   4) best jiska ANDAAZA size < 25MB
#   5) upar mein se kuch bhi match na ho to -- "worst" (jo bhi sabse
#      chhota mile, size ki koi guarantee ke bina) -- taaki download
#      kabhi bhi bilkul khaali haath na laute
FORMAT_SELECTOR = (
    f"best[filesize<{TARGET_SIZE_BYTES}]/"
    f"best[filesize_approx<{TARGET_SIZE_BYTES}]/"
    f"best[filesize<{HARD_MAX_SIZE_BYTES}]/"
    f"best[filesize_approx<{HARD_MAX_SIZE_BYTES}]/"
    f"worst"
)
# f"..." ek "f-string" hai (f = "formatted"). {curly braces} ke andar
# koi bhi Python variable ka naam likho, aur uski VALUE seedhe usi jagah
# string ke andar chipak jaati hai. Yahan {TARGET_SIZE_BYTES} ki jagah
# asli number (jaise 10485760) chala jaata hai -- Python yeh khud kar
# deta hai, hume manually str() ya + se jodne ki zaroorat nahi padti.
# Yahan chaar alag f-strings likhe hain jo bracket ke andar apne aap
# ek doosre se "/" ke saath jud kar EK hi lambi string ban jaate hain
# (Python mein paas-paas rakhe gaye string literals khud-ba-khud jud
# jaate hain, "+" likhne ki zaroorat nahi).


def load_saved_folder():
    """Kaam: agar pehle kabhi ek folder 'default' set kiya gaya tha, to woh wapas do.
    Input: kuch nahi
    Output: folder path (string) agar mila, warna None
    """
    if os.path.exists(CONFIG_FILE):
        # os.path.exists(path) -> True ya False deta hai -- yeh sirf
        # itna batata hai ki us naam ki file/folder maujood hai ya nahi,
        # bina use asal mein kholne ki koshish kiye.
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                # "with open(...) as f:" ko "context manager" kehte hain.
                # Iska fayda: jaise hi is indented block ka kaam khatam
                # ho (ya beech mein hi koi error aa jaaye), file KHUD-BA-
                # KHUD band ho jaati hai -- hume alag se f.close() likhna
                # nahi padta, aur file khuli reh jaane ka risk nahi rehta.
                # "r" ka matlab "read mode" hai -- sirf padhne ke liye.
                data = json.load(f)
                # json.load(f) file ke andar likhe JSON text ko padh kar
                # use WAAPAS ek Python dictionary mein badal deta hai --
                # bilkul json.dump() (neeche) ka ulta kaam.
                return data.get("default_folder")
                # dictionary.get("key") -- agar "key" dictionary mein
                # maujood hai to uski value milegi, WARNA seedha None
                # milega. dictionary["key"] seedha likhte to key na hone
                # par program crash ho jaata (KeyError) -- .get() safe hai.
        except Exception:
            return None  # config file corrupt/kharab ho to crash mat karo
    return None  # pehli hi baar chal raha hai -- kuch bhi saved nahi hai abhi


def save_folder_as_default(path: str):
    """Kaam: user ne 'Yes, isse default bana do' chuna -- to yeh path file mein likh do.
    Input: path (string) -- jo folder user ne diya
    Output: kuch return nahi karta -- sirf disk par likhta hai (ek 'side-effect')
    """
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        # "w" = "write mode" -- agar file pehle se hai to uska poora
        # purana content mit jaata hai aur naya likha jaata hai; file na
        # ho to nayi ban jaati hai. (Iske comparison mein "a" = "append
        # mode" hota, jo purane content ke AAGE likhta -- yahan zaroorat
        # nahi, kyunki hume hamesha sirf EK hi latest folder yaad rakhna hai.)
        json.dump({"default_folder": path}, f)
        # json.dump(dictionary, f) -- ek Python dictionary ko JSON text
        # ki tarah seedha file "f" mein likh deta hai.


# ================= 3. HELPER FUNCTIONS =================
# Yeh chaaron function bilkul wahi hain jo notebook mein the -- ek bhi line
# badli nahi hai, kyunki inhe "URL kaisa dikhta hai" aur "text kaisa hai"
# jaanne ke liye sirf built-in Python chahiye, koi UI nahi.

def detect_platform(url: str) -> str:
    """Kaam: URL dekh kar bata do ki yeh YouTube, Instagram ya Facebook hai.
    Input: url (string, zaroori hai) -- jaise "https://youtu.be/xyz123"
    Output: platform ka naam -- "YouTube" / "Instagram" / "Facebook" / "Unknown"
    """
    # "def detect_platform(url: str) -> str:" mein "url: str" ek TYPE HINT
    # hai -- yeh Python ko FORCE nahi karta (Python phir bhi kuch bhi le
    # lega), lekin humein aur code padhne waalon ko batata hai "yahan
    # string aani chahiye". "-> str" batata hai ki yeh function AAKHIR
    # mein ek string RETURN karega.
    try:
        netloc = urlparse(url).netloc.lower()
        # urlparse(url) URL ko tukdon mein todta hai aur ek chhota sa
        # "object" deta hai jiske andar .scheme (jaise "https"), .netloc
        # (jaise "www.youtube.com"), .path (jaise "/watch") waghera hote
        # hain. Hume sirf domain chahiye, isliye seedha .netloc nikaal
        # rahe hain. .lower() ek STRING METHOD hai -- poora text CHHOTE
        # letters mein badal deta hai, taaki "YouTube.com" aur
        # "youtube.com" dono ek hi tarah check ho sakein.
    except Exception:
        return "Unknown"  # URL hi kharab ho to crash mat karo -- seedha "Unknown" bhej do

    if "youtube.com" in netloc or "youtu.be" in netloc:
        # "in" yahan check kar raha hai ki chhota text (jaise "youtube.com")
        # bade text (netloc) ke ANDAR kahin maujood hai ya nahi -- yeh
        # Python ka built-in tareeka hai substring dhoondhne ka, regex
        # ki zaroorat nahi.
        return "YouTube"
    if "instagram.com" in netloc:
        return "Instagram"
    if "facebook.com" in netloc or "fb.watch" in netloc:
        return "Facebook"
    return "Unknown"  # koi jaana-pehchana domain match nahi hua


def detect_video_type(url: str, info: dict) -> str:
    """Kaam: pata karo ki yeh Short/Reel hai ya ek Full video.
    Input: url (string), info (dictionary -- yt-dlp se mila metadata, jaise duration)
    Output: "Short" / "Reel/Short" / "Short/Reel" / "Full video"
    """
    lowered = url.lower()

    if "/shorts/" in lowered:
        return "Short"
    if "/reel/" in lowered or "/reels/" in lowered:
        return "Reel/Short"
    # URL ke text se hi pata chal gaya -- info dictionary ki zaroorat nahi padi

    duration = info.get("duration") if info else None
    # Yeh ek "conditional expression" hai (isse kabhi-kabhi "inline if"
    # bhi kehte hain): "X if CONDITION else Y" -- agar info sach mein
    # maujood hai (khaali dictionary ya None nahi hai) to
    # info.get("duration") value lo, WARNA seedha None. Isse ek poori
    # if/else block likhne se bachte hain jab kaam sirf ek line ka ho.
    if isinstance(duration, (int, float)):
        # isinstance(value, TYPE) check karta hai "kya yeh value is TYPE
        # ki hai?" -- yahan (int, float) ek TUPLE hai do types ka, matlab
        # "duration integer hai YA decimal number hai". Yeh check zaroori
        # hai kyunki duration kabhi-kabhi None bhi ho sakta hai (jab
        # platform duration bataata hi nahi), aur "None <= 60" likhne se
        # Python seedha error de dega (TypeError) -- None aur number ka
        # comparison Python mein allowed nahi hai.
        return "Short/Reel" if duration <= 60 else "Full video"

    return "Full video"  # koi bhi signal na mile to default guess


def sanitize_filename(name: str, max_len: int = 120) -> str:
    """Kaam: title ko ek safe filename mein badlo -- har OS (Windows/Mac/Linux) par chale.
    Input: name (string) -- video ka title; max_len (int) -- kitna lamba naam allowed hai
    Output: ek safe filename (string), kabhi khaali nahi
    """
    # "max_len: int = 120" mein "= 120" ek DEFAULT VALUE hai -- agar is
    # function ko call karte waqt max_len diya hi nahi gaya, to Python
    # khud 120 use kar lega. Isi liye neeche download_one() mein
    # sanitize_filename(title) sirf EK argument ke saath call hota hai
    # (max_len nahi diya), aur phir bhi kaam ho jaata hai.
    if not name:
        name = "untitled_video"  # khaali ya None title aaya to seedha ek default naam de do

    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # re.sub(pattern, replacement, text) -- text ke andar jahan bhi
    # pattern match ho, use replacement se badal deta hai. Yahan pattern
    # [\\/*?:"<>|] ek "character class" hai -- [ ] ke andar likhe kisi
    # bhi EK character se match karta hai (backslash, forward slash,
    # asterisk, question mark, colon, quote, angle brackets, pipe --
    # yeh sab Windows mein filename ke andar allowed nahi hain).
    # replacement yahan "" (khaali string) hai, matlab match hua character
    # seedha DELETE ho jaata hai. r'...' se pehle 'r' ka matlab "raw
    # string" hai -- isse Python backslash ko apna khud ka special
    # meaning dene ki koshish nahi karta, jo yahan zaroori hai.

    name = name.strip().strip(".")
    # .strip() ek STRING METHOD hai -- bina kisi argument ke, yeh sirf
    # aage-peeche ke WHITESPACE (space, tab, newline) hata deta hai.
    # .strip(".") isi method ko EK argument ke saath phir se call kar
    # raha hai -- ab yeh sirf "." (dot) characters hataega, aage-peeche
    # se (Windows mein filename ke end mein dot ya space pasand nahi
    # aata).

    name = re.sub(r"\s+", " ", name)
    # Pattern \s+ ka matlab hai "EK ya ZYADA whitespace characters, jitne
    # bhi paas-paas mile, sabko ek saath". "+" (plus) yahan "1 ya usse
    # zyada baar" batata hai. Poore match ko ek SINGLE space se replace
    # kiya ja raha hai -- taaki "My   Trip   Home" ban jaaye "My Trip Home".

    if len(name) > max_len:
        name = name[:max_len].rstrip()
        # len(name) string ki LAMBAI (kitne characters hain) deta hai.
        # name[:max_len] ek "SLICE" hai -- yeh string ke sirf shuru ke
        # max_len characters uthaata hai (jaise name[:5] pehle 5
        # characters). .rstrip() phir se koi adhoora-kata space hata
        # deta hai end se. Yeh sab isliye zaroori hai kyunki bahut lamba
        # title (Reels ke captions jaise) file path limit (khaaskar
        # Windows par) todkar error de sakta hai.

    return name or "untitled_video"
    # "A or B" yahan ek chhota trick hai: agar name khaali string hai
    # (Python mein khaali string "" ko False maana jaata hai), to poori
    # expression B (yaani "untitled_video") ban jaati hai. Agar name mein
    # kuch bhi hai, to A (yaani name) hi wapas chala jaata hai. Matlab:
    # sab kuch hata dene ke baad agar kuch bacha hi nahi, to default naam.


def parse_links(raw_text: str) -> list:
    """Kaam: messy text ke andar se saare valid links nikaalo, duplicates hata ke.
    Input: raw_text (string) -- poori file content ek hi variable mein
    Output: list of URLs (order same, koi bhi link do baar nahi) -- numbering, bullets,
    extra sentences, ek line mein kayi links -- sab handle ho jaata hai.
    """
    raw_matches = re.findall(r"https?://[^\s]+", raw_text)
    # re.findall(pattern, text) poore text mein DHOONDHTA hai aur SAARE
    # matches ek Python LIST mein deta hai (re.sub() jaisa replace nahi
    # karta, sirf dhoondh kar collect karta hai). Pattern ka matlab:
    # "https" (optional "s") "://" phir jitne bhi non-whitespace
    # characters (yaani asli link ka baaki hissa) milte rahein.

    cleaned = []
    seen = set()
    # [] ek KHAALI LIST hai, set() ek KHAALI SET hai -- dono mein items
    # rakhe ja sakte hain, lekin list mein ORDER yaad rehta hai aur
    # duplicates allowed hain, jabki set mein order yaad NAHI rehta lekin
    # "kya yeh item pehle se hai?" check karna BAHUT fast hota hai. Yahan
    # dono ka istemal ho raha hai -- ek doosre ki kami poori karne ke liye.
    trailing_junk = ".,;:)]}'\""

    for url in raw_matches:
        # "for url in raw_matches:" ek LOOP hai -- yeh raw_matches list ke
        # HAR item par, ek-ek karke, poora indented block chalata hai.
        # Har baar "url" variable us waqt ke item ki value rakhta hai.
        url = url.rstrip(trailing_junk)
        # .rstrip(characters) ek zaroori subtlety hai: yeh EK EXACT SUFFIX
        # nahi hataata, balki trailing_junk string mein diye gaye kisi
        # bhi CHARACTER ko, jitni baar bhi milein, end se hataata rehta
        # hai. Matlab: copy-paste karte waqt link ke peeche jo bhi
        # comma/bracket/quote chipak jaaye, sab saaf ho jaata hai.

        if url and url not in seen:
            # "url" akela likhna Python mein "url khaali string to nahi
            # hai?" check karne jaisa hai (khaali string False maani
            # jaati hai). "url not in seen" set ke andar check karta hai
            # ki yeh URL PEHLE dekha ja chuka hai ya nahi.
            seen.add(url)         # set() add fast hai -- "pehle dekha hai?" turant pata chalta hai
            cleaned.append(url)   # list isliye, kyunki set order yaad nahi rakhta hai

    return cleaned


# ================= 4. CORE DOWNLOADER =================
# Yeh bhi notebook wala hi function hai, bina kisi badlaav ke -- yehi is
# poore project ka core hai, aur is script version mein bhi utna hi zaroori.

def download_one(url: str, dest_dir: str) -> dict:
    """Kaam: EK link download karo. Kabhi crash mat karo -- sab kuch dictionary mein wapas bhejo.
    Input: url (string), dest_dir (string) -- kahan save karna hai
    Output: ek dictionary -- hamesha, chahe success ho ya failure. Kabhi bhi Exception
    upar tak nahi phenkta, isliye ek kharaab link poore batch ko rokta nahi.
    """
    result = {
        "url": url,
        "platform": detect_platform(url),
        "type": "Unknown",
        "status": "failed",
        "title": None,
        "path": None,
        "size_mb": None,
        "error": None,
        "error_detail": None,  # poora traceback -- debugging ke liye
    }
    # Yeh ek DICTIONARY hai -- { } ke andar "key": value jode hote hain.
    # Ek dictionary ko ek "form" ki tarah socho jisme har cheez ka apna
    # naam-diya-hua khaana hai (jaise "status", "title"), aur baad mein
    # hum result["status"] likh kar seedha us khaane tak pahunch sakte
    # hain -- list ki tarah number se dhoondhna nahi padta. Result pehle
    # hi "failed" maan ke bana lo -- jaise-jaise kaam hoga, values update
    # karte jaayenge.

    probe_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    # Yeh bhi ek dictionary hai, lekin is baar yt_dlp ko SETTINGS batane
    # ke liye -- keys "quiet", "no_warnings", "skip_download" yt_dlp KHUD
    # define karta hai (yeh hamari apni banayi hui nahi hain), aur unki
    # values True/False (Python ke BOOLEAN data type) hain.

    try:
        # ---- Pehla pass: sirf metadata maango, download nahi ----
        with yt_dlp.YoutubeDL(probe_opts) as ydl:
            # yt_dlp.YoutubeDL(options_dict) ek "session" object banata
            # hai jisse hum video platform se baat kar sakte hain. Phir
            # se "with ... as" wala context-manager pattern -- is block
            # ke khatam hote hi yeh session apne aap saaf-suthre tarike
            # se band ho jaata hai.
            info = ydl.extract_info(url, download=False)
            # .extract_info() ek METHOD hai (yaani ek function jo kisi
            # object -- yahan ydl -- ke andar rehta hai). download=False
            # yahan ek "keyword argument" hai -- hum saaf-saaf bata rahe
            # hain ki iski value False honi chahiye, sirf order se guess
            # karwaane ki jagah. Yeh call video ke baare mein JAANKARI
            # (title, duration, available formats waghera) le aati hai,
            # bina ek bhi video byte download kiye.

        if info is None:
            raise ValueError("No metadata returned (private/unavailable video?)")
            # "raise" jaan-boojh kar ek Exception PAIDA karta hai. Yahan
            # hum khud decide kar rahe hain ki "info None hona" ek
            # error-jaisi situation hai, taaki neeche wala except block
            # ise pakad le aur sabko ek jaisi tarah handle kare.

        result["type"] = detect_video_type(url, info)
        title = sanitize_filename(info.get("title", "untitled_video"))
        # info.get("title", "untitled_video") .get() ka DO-ARGUMENT wala
        # roop hai -- pehla argument key hai, DOOSRA argument ek default
        # value hai jo tabhi use hoti hai jab key maujood na ho. Yeh
        # load_saved_folder() wale .get() se thoda alag hai (jahan sirf
        # ek argument tha, aur default apne aap None ban jaata tha).
        result["title"] = title

        out_template = os.path.join(dest_dir, f"{title}.%(ext)s")
        # os.path.join(a, b) do path-pieces ko OS ke hisaab se sahi
        # slash/backslash se jodta hai -- khud "+" se jodne se yeh behtar
        # hai, kyunki Windows aur Mac/Linux alag separator use karte hain.
        # "%(ext)s" yeh Python ka syntax NAHI hai -- yeh yt_dlp ka apna
        # TEMPLATE syntax hai, jise yt_dlp khud, download ke baad, asli
        # extension (jaise "mp4") se replace karega.

        # ---- Doosra pass: ab asli download ----
        download_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": FORMAT_SELECTOR,          # size-based fallback chain (CONFIG mein)
            "outtmpl": out_template,
            "noplaylist": True,                 # zaroori! ek link = ek video, poori playlist nahi
            "merge_output_format": "mp4",       # yeh "hamesha MP4" wala promise poora karta hai
        }

        with yt_dlp.YoutubeDL(download_opts) as ydl:
            info_dl = ydl.extract_info(url, download=True)
            final_path = ydl.prepare_filename(info_dl)
            # .prepare_filename() yt_dlp ka apna method hai jo batata hai
            # ki asal mein FILE KAHAN SAVE HUI -- outtmpl ke andar likha
            # "%(ext)s" template ab poori tarah se resolve ho chuka hota
            # hai (jaise "My Trip.mp4").

        if not os.path.exists(final_path):
            guess = os.path.splitext(final_path)[0] + ".mp4"
            # os.path.splitext(path) path ko DO hisson mein todta hai --
            # ek TUPLE deta hai: (naam-bina-extension, extension). Yahan
            # [0] se sirf pehla hissa (bina extension wala naam) uthaya
            # ja raha hai, phir ".mp4" khud jod diya ja raha hai.
            if os.path.exists(guess):
                final_path = guess
            # kabhi-kabhi asli extension .mp4 hi hota hai lekin prepare_filename() ka
            # andaza thoda alag nikal jaata hai -- yeh ek fallback check hai

        if os.path.exists(final_path):
            size_mb = os.path.getsize(final_path) / (1024 * 1024)
            # os.path.getsize(path) file ka size BYTES mein deta hai --
            # isi liye 1024*1024 se divide karke MB mein badal rahe hain
            # (bilkul CONFIG section mein MB-se-bytes conversion ka ulta).
            result["status"] = "success" if size_mb <= HARD_MAX_SIZE_MB else "success_over_limit"
            result["path"] = final_path
            result["size_mb"] = round(size_mb, 2)
            # round(number, 2) number ko sirf 2 decimal places tak
            # round kar deta hai (jaise 4.837291 -> 4.84), taaki report
            # mein saaf, chhota number dikhe.
        else:
            raise FileNotFoundError("Download finished but output file was not found")

    except Exception as e:
        # "except Exception as e:" try block ke andar aayi KISI BHI
        # exception ko pakad leta hai, aur use "e" naam ke variable mein
        # rakh deta hai, taaki hum uske baare mein jaankari nikaal sakein.
        result["status"] = "failed"
        result["error"] = f"{type(e).__name__}: {e}"
        # type(e) exception ka "class" deta hai (jaise ValueError,
        # FileNotFoundError); .__name__ us class ka NAAM string ki tarah
        # deta hai. f"{e}" khud exception ka message deta hai. Dono jodkar
        # ek chhota, saaf error message ban jaata hai.
        result["error_detail"] = traceback.format_exc()
        # traceback.format_exc() poora traceback (kaunsi file, kaunsi
        # line, kya hua) EK LAMBI STRING ki tarah deta hai -- terminal
        # par PRINT nahi karta, sirf STRING RETURN karta hai, taaki hum
        # use aage save_summary() mein file mein likh sakein.
        # Yahan pakad lo -- result "failed" rahega, poora program nahi girega

    return result  # HAMESHA ek dictionary -- kabhi bhi Exception nahi phenkta


# ================= 5. REPORTING =================
# Notebook mein yeh kaam render_results_table() (HTML) karta tha. Terminal mein
# HTML table nahi chalti, isliye iski jagah seedha print() use ho raha hai --
# lekin JAANKARI bilkul wahi hai, bas dikhne ka tareeka badla hai.

STATUS_ICON = {"success": "[OK]", "success_over_limit": "[!!]", "failed": "[XX]"}
# Ek aur dictionary -- is baar "lookup table" ki tarah use ho raha hai:
# "status" ki value do, aur badle mein turant uska icon mil jaata hai,
# ek lambi if/elif/else chain likhne ki zaroorat nahi.


def print_result_line(result: dict):
    """Kaam: ek result ko ek chhoti, saaf line mein terminal par dikhao."""
    icon = STATUS_ICON.get(result["status"], "[??]")
    # Yahan bhi .get() ka DO-ARGUMENT roop -- agar status kisi wajah se
    # in teeno mein se koi na ho (aisa normally nahi hona chahiye), to
    # crash hone ki jagah "[??]" dikha do.
    if result["status"] == "failed":
        detail = result["error"] or "Unknown error"
    else:
        size = f"{result['size_mb']} MB" if result["size_mb"] is not None else "? MB"
        detail = f"{result['title']}  ({size})"
    print(f"    {icon} [{result['platform']}] [{result['type']}] {detail}")


def save_summary(results: list, dest_dir: str) -> str:
    """Kaam: poore batch ka ek timestamped .txt report likh do -- notebook wala
    save_summary() bhi hoo-ba-hoo yehi karta hai, sirf ek line extra hai
    (destination folder bhi likh di gayi hai, taaki report khud-mukhtaar rahe).
    """
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # datetime.now() "abhi" ka poora date+time ek object ki tarah deta
    # hai. .strftime(format_string) us object ko EK STRING mein badalta
    # hai, jaisa format_string mein bataya gaya ho: %Y = 4-digit saal,
    # %m = mahina, %d = din, %H = ghanta (24-hour), %M = minute, %S =
    # second. Isse ek aisa naam banta hai jo har run mein UNIQUE hoga,
    # aur purani summary files kabhi overwrite nahi hongi.
    summary_path = os.path.join(dest_dir, f"download_summary_{ts}.txt")

    success = [r for r in results if r["status"] in ("success", "success_over_limit")]
    failed = [r for r in results if r["status"] == "failed"]
    # Yeh dono ek "LIST COMPREHENSION" hain -- ek poori for-loop likhne
    # ka CHHOTA tareeka. "[r for r in results if CONDITION]" ka matlab:
    # "results list ke har item 'r' ko dekho, aur sirf unhi 'r' ko nayi
    # list mein daalo jinke liye CONDITION sach ho." Yeh bilkul yeh
    # likhne jaisa hi hai:
    #     success = []
    #     for r in results:
    #         if r["status"] in ("success", "success_over_limit"):
    #             success.append(r)
    # bas ek hi line mein. "in (A, B)" yahan check karta hai ki value
    # in do options mein se KISI EK ke barabar hai ya nahi.

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"Run: {ts}\n")
        f.write(f"Destination folder: {dest_dir}\n")
        f.write(f"Total links: {len(results)}\n")
        f.write(f"Downloaded OK: {len(success)}\n")
        f.write(f"Failed: {len(failed)}\n\n")
        # f.write(string) file mein us STRING ko seedha likh deta hai --
        # print() ki tarah khud se ek naya newline NAHI jodta, isliye
        # hume "\n" khud likhna padta hai jahan bhi line-break chahiye.

        f.write("--- Successful downloads ---\n")
        for r in success:
            f.write(f"[{r['platform']}] [{r['type']}] {r['size_mb']} MB -> {r['path']}\n")

        f.write("\n--- Failed downloads ---\n")
        for r in failed:
            f.write(f"[{r['platform']}] {r['url']}  ({r['error']})\n")
            if r.get("error_detail"):
                f.write(f"    {r['error_detail'].strip().replace(chr(10), chr(10) + '    ')}\n")
                # Yeh line thodi ghani hai, isliye piece-by-piece:
                #   r['error_detail'].strip()   -- traceback ke aage-peeche
                #                                   ka extra whitespace hataya
                #   .replace(chr(10), chr(10) + '    ')
                #       -- chr(10) Python mein NEWLINE character (\n) ka
                #          hi doosra tareeka likhne ka hai. Yeh line har
                #          newline ko DHOONDH kar, uski jagah "newline +
                #          4 spaces" laga deti hai -- matlab traceback ki
                #          HAR line thodi indent ho jaati hai, taaki
                #          summary file mein woh saaf se "andar" dikhe,
                #          bahar wale text se alag.

    return summary_path


# ================= 6. CLI / INTERFACE LAYER =================
# Yeh poora section NAYA hai -- notebook mein iski jagah widgets (Text box,
# Checkbox, FileUpload, Button) the. Yahan unki jagah input() prompts hain,
# lekin IDEA bilkul wahi hai jo notebook ke Section 3 aur Section 6 mein tha.

def choose_destination_folder(cli_dest=None) -> str:
    """Kaam: pata karo videos kahan save karni hain -- command-line se, saved
    default se, ya seedha user se pooch kar. Notebook ke folder_input +
    save_default_checkbox + confirm_folder_button, teeno ka kaam yahan
    ek hi function mein ho raha hai.
    Input: cli_dest (string ya None) -- agar --dest flag diya gaya tha
    Output: ek valid, already-created folder ka path (string)
    """
    # "cli_dest=None" bhi ek DEFAULT VALUE hai, jaisa sanitize_filename()
    # mein tha -- isse hum is function ko bina kuch diye bhi call kar
    # sakte hain (choose_destination_folder()), aur cli_dest apne aap
    # None ban jaata hai.
    saved = load_saved_folder()

    if cli_dest:
        # cli_dest ek KHAALI string bhi ho sakti hai (agar --dest "" diya
        # gaya ho) -- "if cli_dest:" khaali string ko False maanta hai,
        # isliye yeh sirf tabhi True hoga jab cli_dest mein SACH MEIN
        # kuch likha ho.
        path = cli_dest.strip().strip('"')
        # .strip() aage-peeche ka whitespace hataata hai; .strip('"')
        # phir se, is baar sirf quote-marks hataata hai -- kabhi-kabhi
        # log copy-paste karte waqt poora path galti se quotes ke saath
        # paste kar dete hain (jaise "C:\Videos"), yeh unhe saaf kar deta hai.
        print(f"Command-line se folder mila: {path}")
    else:
        if saved:
            prompt = f"Kis folder mein save karna hai? [Enter dabao '{saved}' use karne ke liye]: "
        else:
            prompt = "Kis folder mein videos save karni hain? "
        path = input(prompt).strip().strip('"')
        # input(prompt) terminal par "prompt" text dikhata hai, phir
        # RUK JAATA hai jab tak user kuch type karke Enter na dabaye.
        # Jo bhi user ne type kiya, woh HAMESHA ek STRING ki tarah wapas
        # milta hai (chahe user ne number hi kyun na likha ho).
        if not path and saved:
            path = saved  # user ne khaali Enter dabaya -- saved default use karo

    while not path:
        # "while" bhi ek LOOP hai, lekin "for" se alag -- yeh utni baar
        # chalta hai jitni baar CONDITION sach rahe (yahan tak ki koi
        # fixed count nahi hai). Jab tak path khaali hai, baar-baar
        # poochta rahega -- khaali Enter allow nahi.
        path = input("Khaali nahi chalega -- ek folder path likho: ").strip().strip('"')

    try:
        os.makedirs(path, exist_ok=True)
        # os.makedirs(path) EK folder ke bajaye, POORA NESTED path bana
        # deta hai agar zaroorat ho (jaise "a/b/c" -- teeno folders ek
        # saath ban jaate hain, agar pehle se na hon). exist_ok=True na
        # likhte to, agar folder pehle se maujood hota, Python EK ERROR
        # de deta -- exist_ok=True is error ko chup kara deta hai, kyunki
        # humein bas itna chahiye ki folder KISI BHI tarah maujood ho.
    except Exception as e:
        print(f"Yeh folder nahi ban paaya: {e}")
        sys.exit(1)
        # sys.exit(1) poora PROGRAM turant ROK deta hai. Number 1 yahan
        # "exit code" hai -- convention ke hisaab se 0 ka matlab "sab
        # theek se khatam hua", aur koi bhi non-zero number (jaise 1) ka
        # matlab "kuch galat hua" -- yeh baad mein automation scripts ke
        # liye kaam aata hai jo check karte hain script safal hui ya nahi.

    if not cli_dest and path != saved:
        # Agar user ne command-line se folder diya (cli_dest), to phir
        # se "save as default?" poochna zaroori nahi -- woh already ek
        # explicit choice hai. Aur agar user ne wahi purana saved folder
        # chuna hai, to use dobara "save karna hai?" poochna bekaar hai.
        choice = input("Isse agli baar ke liye default bana dein? (y/n): ").strip().lower()
        if choice.startswith("y"):
            # .startswith("y") sirf "y" se check nahi karta -- "yes",
            # "Y", "Yeah" jaisa kuch bhi likhein jo "y"/"Y" se shuru ho,
            # accept ho jaayega (chhote/bade letters .lower() ne pehle
            # hi barabar kar diye the).
            save_folder_as_default(path)
            print(f"Default save ho gaya: {path}")

    print(f"Destination folder taiyaar: {path}\n")
    return path


def choose_links_file(cli_links=None) -> list:
    """Kaam: .txt file ka path lo, padho, aur parse_links() se URLs nikaalo.
    Notebook ke uploader widget + _on_upload_change() ka kaam yahan
    ek hi function mein ho raha hai -- bas file 'upload' hone ki jagah
    seedha disk se 'read' hoti hai.
    Input: cli_links (string ya None) -- agar --links flag diya gaya tha
    Output: URLs ki list (empty ho sakti hai agar kuch match na ho)
    """
    if cli_links:
        txt_path = cli_links.strip().strip('"')
    else:
        txt_path = input("Links wali .txt file ka path: ").strip().strip('"')

    while not os.path.isfile(txt_path):
        # os.path.isfile(path) sirf True deta hai agar us naam ki cheez
        # maujood HO AUR woh ek FILE ho (folder nahi). Isse os.path.exists()
        # se ek kadam aage ka, zyada precise check milta hai.
        print(f"Yeh file nahi mili: {txt_path}")
        txt_path = input("Dobara sahi path likho: ").strip().strip('"')

    with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
        # encoding="utf-8" batata hai file kis "character set" mein
        # likhi maani jaaye (aajkal ka sabse common standard).
        # errors="replace" batata hai ki agar koi character utf-8 mein
        # decode na ho paaye (kabhi purani/alag encoding wali files mein
        # hota hai), to CRASH hone ki jagah bas woh character "?" jaisa
        # kuch dikha do -- poori file padhna abhi bhi safal rahega.
        raw_text = f.read()
        # .read() poori file ka content EK HI STRING ki tarah le aata
        # hai (chhote-chhote pieces mein nahi) -- parse_links() ko poore
        # text mein ek saath dhoondhna hota hai, isliye yeh sahi hai.

    urls = parse_links(raw_text)
    print(f"{len(urls)} link(s) mile '{txt_path}' mein.\n")
    return urls


def run_batch(urls: list, dest_dir: str) -> list:
    """Kaam: Orchestrator -- notebook ke on_start_clicked() jaisa hi hai.
    Har link par loop karo, download_one() call karo, aur turant result
    print karo (yehi is script ka "live results table" hai).
    Input: urls (list of strings), dest_dir (string)
    Output: results (list of dictionaries) -- ek entry har link ke liye
    """
    total = len(urls)
    results = []

    for idx, url in enumerate(urls, start=1):
        # enumerate(list, start=1) ek normal for-loop se EXTRA cheez
        # deta hai: har item ke saath uska POSITION (index) bhi. Bina
        # enumerate() ke hume khud ek counter variable banakar, har baar
        # loop ke andar +1 karna padta. start=1 batata hai ki counting 0
        # se nahi, 1 se shuru ho (kyunki "link 1 of 5" insaano ko zyada
        # natural lagta hai "link 0 of 5" se). Har baar idx aur url, dono
        # variables ek saath mil jaate hain.
        print(f"[{idx}/{total}] {url[:70]}")
        # url[:70] bhi ek SLICE hai -- URL ke sirf shuru ke 70 characters
        # dikha rahe hain, taaki bahut lambe links terminal ki line ko
        # todh na dein.
        try:
            result = download_one(url, dest_dir)
        except Exception as e:
            # Doosra safety net -- download_one khud kabhi raise nahi karta,
            # yeh jaan-boojh kar rakhi gayi redundancy hai
            result = {
                "url": url, "platform": detect_platform(url), "type": "Unknown",
                "status": "failed", "title": None, "path": None,
                "size_mb": None, "error": f"Unexpected: {e}",
                "error_detail": traceback.format_exc(),
            }
        results.append(result)
        # .append(item) list ke SABSE AAKHIR mein ek naya item jod deta
        # hai -- list ka size ek se badh jaata hai.
        print_result_line(result)

    return results


def main():
    """Kaam: poore script ka entry point -- yahan se sab kuch shuru hota hai."""
    parser = argparse.ArgumentParser(
        description="Multi-Platform Video Downloader (YouTube/Instagram/Facebook) -- plain script version"
    )
    # ArgumentParser() ek "parser" object banata hai jo terminal se aaye
    # text ko samajhne ka kaam karega. description yahan sirf --help
    # dikhaate waqt upar ek line mein context dene ke liye hai.
    parser.add_argument("--dest", help="Destination folder (nahi diya to poocha jaayega)")
    parser.add_argument("--links", help="Links wali .txt file ka path (nahi diya to poocha jaayega)")
    # .add_argument("--dest", ...) parser ko batata hai "is naam ka ek
    # OPTIONAL flag accept karo". Do dashes (--) convention hai OPTIONAL
    # arguments ke liye (jinke bina bhi chal jaaye) -- agar single dash
    # hota (jaise "-d"), woh short-form alias hota. help=... yahan --help
    # dikhaane par is flag ke saamne dikhne wala text hai.
    args = parser.parse_args()
    # .parse_args() asal mein terminal se diye gaye arguments ko padhta
    # hai aur ek chhota "Namespace" object deta hai -- iske andar
    # args.dest aur args.links naam se seedha values milengi (jo diya
    # nahi gaya uski value apne aap None hogi, kyunki humne default nahi
    # diya).
    # argparse: agar terminal se --dest ya --links diya gaya, wahi use hoga;
    # nahi to args.dest / args.links dono None honge, aur aage input() poochega

    print("=" * 60)
    # "=" * 60 STRING ko 60 baar REPEAT karta hai -- "="*60 ek lambi
    # seedhi line ban jaati hai, print() ke bina loop likhe.
    print("Multi-Platform Video Downloader -- Script Version")
    print("=" * 60)

    dest_dir = choose_destination_folder(args.dest)
    uploaded_urls = choose_links_file(args.links)
    # naam jaan-boojh kar 'uploaded_urls' rakha hai -- notebook ke us hi
    # naam waale global variable jaisa role nibhata hai

    if not uploaded_urls:
        # Khaali list ([]) bhi Python mein False maani jaati hai, isliye
        # "if not uploaded_urls:" ka matlab hai "agar list mein kuch bhi
        # nahi hai".
        print("Koi valid link nahi mila -- ruk rahe hain.")
        return
        # "return" (bina kisi value ke) function ko YAHIN par ROK deta
        # hai -- neeche ka baaki code (download loop, summary) bilkul
        # nahi chalega.

    print(f"{len(uploaded_urls)} link(s) download honge -> {dest_dir}\n")
    results = run_batch(uploaded_urls, dest_dir)

    summary_path = save_summary(results, dest_dir)
    success_count = len([r for r in results if r["status"] in ("success", "success_over_limit")])
    failed_count = len([r for r in results if r["status"] == "failed"])
    # Yahan list comprehension ke bahar seedha len() laga diya gaya hai --
    # poori chhoti list banti hai, aur turant uski LAMBAI le li jaati hai,
    # kyunki humein actual items nahi, sirf GINTI chahiye.

    print("\n" + "=" * 60)
    print(f"Khatam. {success_count} safal, {failed_count} fail.")
    print(f"Summary yahan save hui: {summary_path}")
    print("=" * 60)


if __name__ == "__main__":
    # Har Python file ke andar ek chhoti si built-in variable hoti hai
    # jiska naam __name__ hai. Jab is FILE ko SEEDHA chalaya jaaye
    # (jaise "python script_version.py"), Python khud __name__ ki value
    # "__main__" set kar deta hai. Lekin agar koi is file ko kisi DOOSRI
    # file mein "import script_version" likh kar use kare, tab __name__
    # "__main__" NAHI hoga -- ismport hone par yeh check False ho jaayega.
    main()
    # Yeh line isliye zaroori hai: agar koi is file ko "import" kare kisi doosri
    # file mein, to main() apne aap nahi chalega -- sirf seedha run karne par chalega.
