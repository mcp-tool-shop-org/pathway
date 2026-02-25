<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="logo.png" alt="Pathway logo" width="400">
</p>

<p align="center">
    <em>Append-only journey engine where undo never erases learning.</em>
</p>

<p align="center">
    <a href="https://github.com/mcp-tool-shop-org/pathway/actions/workflows/ci.yml">
        <img src="https://github.com/mcp-tool-shop-org/pathway/actions/workflows/ci.yml/badge.svg" alt="CI">
    </a>
    <a href="https://pypi.org/project/mcpt-pathway/">
        <img src="https://img.shields.io/pypi/v/mcpt-pathway" alt="PyPI version">
    </a>
    <a href="https://opensource.org/licenses/MIT">
        <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
    </a>
    <a href="https://mcp-tool-shop-org.github.io/pathway/">
        <img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page">
    </a>
</p>

**पाथवे कोर एक ऐसा इंजन है जो केवल डेटा जोड़ता है, और इसमें 'अनडू' (पूर्ववत) करने का विकल्प हमेशा सीखने को मिटाता नहीं है।**

'अनडू' का मतलब है नेविगेशन। सीखना जारी रहता है।

## दर्शन

पारंपरिक 'अनडू' इतिहास को बदल देता है। पाथवे ऐसा नहीं करता।

जब आप पाथवे में पीछे जाते हैं, तो आप एक नया इवेंट बनाते हैं जो पीछे की ओर इशारा करता है—मूल पथ बना रहता है। जब आप किसी असफल पथ पर कुछ सीखते हैं, तो वह ज्ञान बना रहता है। आपकी गलतियाँ आपको सिखाती हैं; वे गायब नहीं होतीं।

यह पाथवे को यह दिखाने में मौलिक रूप से ईमानदार बनाता है कि वास्तव में क्या हुआ।

## विशेषताएं

- **केवल डेटा जोड़ने वाला इवेंट लॉग**: इवेंट कभी भी संपादित या हटाए नहीं जाते।
- **'अनडू' = पॉइंटर मूवमेंट**: पीछे हटना एक नया इवेंट बनाता है और 'हेड' को स्थानांतरित करता है।
- **सीखना जारी रहता है**: ज्ञान, पीछे हटने और शाखाओं के बावजूद, बना रहता है।
- **शाखाकरण (ब्रांचिंग) प्राथमिक है**: गिट के समान, नए काम पर निहित विचलन, पीछे हटने के बाद।

## शुरुआत कैसे करें

```bash
# Install
pip install -e ".[dev]"

# Initialize database
python -m pathway.cli init

# Import sample session
python -m pathway.cli import sample_session.jsonl

# View derived state
python -m pathway.cli state sess_001

# Start API server
python -m pathway.cli serve
```

## एपीआई एंडपॉइंट

- `POST /events` - एक इवेंट जोड़ें
- `GET /session/{id}/state` - व्युत्पन्न स्थिति प्राप्त करें (जर्नीव्यू, लर्नडव्यू, आर्टिफैक्टव्यू)
- `GET /session/{id}/events` - कच्चे इवेंट प्राप्त करें
- `GET /sessions` - सभी सत्रों की सूची
- `GET /event/{id}` - एकल इवेंट प्राप्त करें

## इवेंट प्रकार

14 इवेंट प्रकार, जो संपूर्ण यात्रा चक्र को कवर करते हैं:

| Type | उद्देश्य |
| ------ | --------- |
| IntentCreated | उपयोगकर्ता का लक्ष्य और संदर्भ |
| TrailVersionCreated | सीखने का पथ/मानचित्र |
| WaypointEntered | पथ के माध्यम से नेविगेशन |
| ChoiceMade | उपयोगकर्ता एक शाखा निर्णय लेता है |
| StepCompleted | उपयोगकर्ता एक 'वेपॉइंट' पूरा करता है |
| Blocked | उपयोगकर्ता किसी बाधा का सामना करता है |
| Backtracked | उपयोगकर्ता पीछे हटता है ('अनडू') |
| Replanned | पथ को संशोधित किया गया |
| Merged | शाखाएं मिलती हैं |
| ArtifactCreated | उत्पादित आउटपुट |
| ArtifactSuperseded | पुराना आउटपुट बदल दिया गया |
| PreferenceLearned | उपयोगकर्ता किस प्रकार से सीखना पसंद करता है |
| ConceptLearned | उपयोगकर्ता क्या समझता है |
| ConstraintLearned | उपयोगकर्ता के वातावरण के तथ्य |

## व्युत्पन्न दृश्य

सिस्टम इवेंट से तीन दृश्य उत्पन्न करता है:

1. **JourneyView**: वर्तमान स्थिति, शाखाएं, देखे गए 'वेपॉइंट'
2. **LearnedView**: प्राथमिकताएं, अवधारणाएं, बाधाएं, आत्मविश्वास स्कोर के साथ
3. **ArtifactView**: सभी आउटपुट, जिसमें प्रतिस्थापन की जानकारी शामिल है

## सुरक्षा

- **एपीआई कुंजी**: लेखन एंडपॉइंट को सुरक्षित करने के लिए `PATHWAY_API_KEY` पर्यावरण चर सेट करें।
- **पेलोड सीमा**: डिफ़ॉल्ट रूप से 1MB ( `PATHWAY_MAX_PAYLOAD_SIZE` के माध्यम से कॉन्फ़िगर किया जा सकता है)
- **सत्र आईडी सत्यापन**: अल्फ़ान्यूमेरिक + अंडरस्कोर/हाइफ़न, अधिकतम 128 वर्ण

## परीक्षण

```bash
pytest  # 73 tests covering invariants, API, reducers, store
```

## आर्किटेक्चर

```
pathway/
├── models/         # Pydantic models for events and views
├── store/          # SQLite event store + JSONL import/export
├── reducers/       # Compute derived views from events
├── api/            # FastAPI endpoints
└── cli.py          # Command-line tools
```
