"""
Yoruba-language menu mode.

WHY A MENU INSTEAD OF FREE-FORM YORUBA: testing showed llama3.2:3b cannot
reliably understand or generate Yoruba (it echoed a Yoruba question back
unchanged instead of answering). Rather than risk wrong agricultural
advice from unreliable generation, this mode uses fixed, pre-written
Yoruba answers tied to the same English topics already verified through
the RAG pipeline. This also better fits a real farmer who may prefer
selecting from a list over typing on a small laptop.

IMPORTANT: these translations are a first draft, not verified by a
native Yoruba speaker. Diacritics (tone marks) change meaning in Yoruba,
so this MUST be reviewed before submission, not just polished for tone.
"""

MENU = [
    {
        "label_en": "Maize: Fall armyworm (pest)",
        "label_yo": "Ọkà: Kòkòrò fall armyworm",
        "answer_yo": (
            "Bí o bá rí àmì funfun bí fèrèsé lórí ewé ọ̀dọ́ àti ìgbẹ́ "
            "kòkòrò (frass) nínú àárín ewé, ó ṣe é ṣe kí ó jẹ́ kòkòrò "
            "fall armyworm. Wá àwọn ẹyin funfun lábẹ́ ewé kí o sì yọ wọn "
            "kúrò ní kíákíá. Yàgò fún oògùn kòkòrò tí kò jẹ́ pàtàkì, "
            "kí o lo ọ̀nà àbínibí láti dáàbò bo ọkà rẹ."
        ),
        "source_topic": "fall armyworm",
    },
    {
        "label_en": "Maize: Nitrogen deficiency",
        "label_yo": "Ọkà: Àìní nitrogen",
        "answer_yo": (
            "Bí ewé ọkà àgbà bá ń di yẹlò láti orí wá sí àárín ní àpẹrẹ "
            "lẹ́tà V, èyí lè jẹ́ àmì àìní nitrogen nínú ilẹ̀. Ṣe àyẹ̀wò "
            "ilẹ̀ (soil test) kí o tó fi ajílẹ̀ sí ilẹ̀, nítorí àìní "
            "potassium náà lè fa àmì tí ó jọra."
        ),
        "source_topic": "nitrogen deficiency",
    },
    {
        "label_en": "Cassava: Mosaic disease (CMD)",
        "label_yo": "Ẹ̀gẹ́dẹ̀ (Cassava): Àrùn mosaic",
        "answer_yo": (
            "Bí ewé ẹ̀gẹ́dẹ̀ rẹ bá ní àpẹrẹ aláwọ̀ àdàlú àti tí ó wọ́ "
            "yíká, ó lè jẹ́ àrùn Cassava Mosaic Disease (CMD). Àrùn yìí "
            "ń tàn nípasẹ̀ kòkòrò whitefly àti nípasẹ̀ àwọn èso tí a fi "
            "gbìn tí kò mọ́. Lo èso tí ó mọ́ àti tí kò ní àrùn fún "
            "gbígbìn tuntun, kí o sì yọ àwọn ohun ọ̀gbìn tí àrùn ti pa "
            "run kúrò ní pápá."
        ),
        "source_topic": "cassava mosaic",
    },
    {
        "label_en": "Beans: Anthracnose",
        "label_yo": "Èwà: Àrùn anthracnose",
        "answer_yo": (
            "Bí o bá rí àmì dúdú tí ó hu sí inú lórí èso èwà rẹ, pẹ̀lú "
            "ẹ̀gbẹ́ tí ó pọ́n bí àwọ̀ pupa-dúdú, ó lè jẹ́ àrùn "
            "anthracnose. Àrùn yìí ń tàn nípasẹ̀ irúgbìn tí kò mọ́ àti "
            "omi tí ń ta sí orí ewé. Lo irúgbìn tí a ti dán wò àti tí "
            "kò ní àrùn láti dáàbò bo ọgbà rẹ."
        ),
        "source_topic": "anthracnose",
    },
]


def print_menu():
    print("\n=== Àkójọ Ìbéèrè (Yoruba Menu) ===")
    for i, item in enumerate(MENU, start=1):
        print(f"  {i}. {item['label_yo']}  ({item['label_en']})")
    print("  0. Padà sí Gẹ̀ẹ́sì (Back to English)")


def get_answer(choice_str: str):
    try:
        idx = int(choice_str.strip())
    except ValueError:
        return None
    if idx == 0:
        return "BACK"
    if 1 <= idx <= len(MENU):
        return MENU[idx - 1]["answer_yo"]
    return None
