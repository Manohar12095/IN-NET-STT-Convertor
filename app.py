"""
IN NET STT Convertor
---------------------
Created by: Manohar
Powered by: IN NET CREATIONS
Contact: innetcreations@gmail.com

A Flask server that converts text to natural-sounding speech using
Microsoft Edge Neural TTS voices.

SETUP (local):
    pip install flask edge-tts

RUN (local dev):
    python app.py
    -- OR double-click run.bat --

Then open http://127.0.0.1:5000 in your browser.

DEPLOY (Vercel):
    vercel deploy
    (uses vercel.json in the project root)

BUILD AS EXE:
    pip install pyinstaller
    pyinstaller --onefile --add-data "templates;templates" --name InNetSTT app.py
"""

import asyncio
import io
import os
import sys
import threading
import uuid
import webbrowser

import edge_tts
from flask import Flask, request, send_file, jsonify, render_template, make_response


def resource_path(relative_path: str) -> str:
    """Get an absolute path to a resource, working both in normal Python
    execution and inside a PyInstaller-built .exe (which unpacks bundled
    files to a temporary folder referenced by sys._MEIPASS)."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


app = Flask(__name__, template_folder=resource_path("templates"))

# Folder where temporary audio clips are written before being streamed back.
# Use a writable location next to the exe (not inside the bundled temp dir).
# If running on Vercel, the file system is read-only except for /tmp.
if os.environ.get("VERCEL"):
    AUDIO_DIR = "/tmp/audio_cache"
else:
    if getattr(sys, "frozen", False):
        APP_DIR = os.path.dirname(sys.executable)
    else:
        APP_DIR = os.path.dirname(os.path.abspath(__file__))
    AUDIO_DIR = os.path.join(APP_DIR, "audio_cache")

os.makedirs(AUDIO_DIR, exist_ok=True)


async def _generate_speech(text: str, voice: str, out_path: str,
                           rate: int = 0, pitch: int = 0):
    """Use edge-tts to synthesize `text` in `voice` and save it as mp3.

    Args:
        text:    The text to speak.
        voice:   The Edge-TTS voice name.
        out_path: Where to write the mp3 file.
        rate:    Speech rate offset in percent (-50 to +100). 0 = normal.
        pitch:   Pitch offset in Hz (-50 to +50). 0 = normal.
    """
    rate_str  = f"+{rate}%" if rate >= 0 else f"{rate}%"
    pitch_str = f"+{pitch}Hz" if pitch >= 0 else f"{pitch}Hz"
    communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
    await communicate.save(out_path)


def _add_cors(response):
    """Add CORS headers so the Vercel-hosted frontend can call the API."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.after_request
def after_request(response):
    return _add_cors(response)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    """Health-check endpoint for Vercel and uptime monitors."""
    return jsonify({"status": "ok", "app": "IN NET STT Convertor",
                    "creator": "Manohar", "powered_by": "IN NET CREATIONS"})


@app.route("/api/voices")
def list_voices():
    """Return the full list of voices so the frontend can build the dropdown."""
    return jsonify(VOICES)


@app.route("/api/tts", methods=["POST", "OPTIONS"])
def tts():
    if request.method == "OPTIONS":
        return make_response('', 204)

    data  = request.get_json(force=True)
    text  = (data.get("text")  or "").strip()
    voice = (data.get("voice") or "").strip()

    try:
        rate  = int(data.get("rate",  0))
        pitch = int(data.get("pitch", 0))
    except (TypeError, ValueError):
        rate, pitch = 0, 0

    # Clamp to safe ranges
    rate  = max(-50, min(100, rate))
    pitch = max(-50, min(50,  pitch))

    if not text:
        return jsonify({"error": "Please enter some text."}), 400
    if not voice:
        return jsonify({"error": "Please choose a voice."}), 400
    if len(text) > 5000:
        return jsonify({"error": "Text is too long (max 5000 characters)."}), 400

    filename = f"{uuid.uuid4().hex}.mp3"
    out_path = os.path.join(AUDIO_DIR, filename)

    try:
        asyncio.run(_generate_speech(text, voice, out_path, rate=rate, pitch=pitch))
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"TTS generation failed: {exc}"}), 500

    return jsonify({
        "success": True,
        "filename": filename,
        "audio_url": f"/api/audio/{filename}",
        "download_url": f"/api/download/{filename}?voice={voice}"
    })


@app.route("/api/audio/<filename>")
def serve_audio(filename):
    """Serve the audio file for inline playback in the browser."""
    safe_path = os.path.join(AUDIO_DIR, os.path.basename(filename))
    if not os.path.exists(safe_path):
        return "Audio not found", 404
    return send_file(safe_path, mimetype="audio/mpeg")


@app.route("/api/download/<filename>")
def download_audio(filename):
    """Trigger a file download dialogue via Content-Disposition: attachment."""
    safe_path = os.path.join(AUDIO_DIR, os.path.basename(filename))
    if not os.path.exists(safe_path):
        return "Audio not found", 404
    
    voice = request.args.get("voice", "Voice")
    # Clean the voice name to make it safe for a filename
    safe_voice = "".join(c for c in voice if c.isalnum() or c in ("-", "_"))
    
    import time
    download_name = f"INNET_STT_{safe_voice}_{int(time.time())}.mp3"
    
    return send_file(
        safe_path,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=download_name
    )


# ---------------------------------------------------------------------------
# Full voice list (name, gender, category, personality) pulled from
# `edge-tts --list-voices`. Used to populate the dropdown on the frontend.
# ---------------------------------------------------------------------------
VOICES = [
    {"name": "af-ZA-AdriNeural", "gender": "Female", "locale": "Afrikaans (South Africa)"},
    {"name": "af-ZA-WillemNeural", "gender": "Male", "locale": "Afrikaans (South Africa)"},
    {"name": "am-ET-AmehaNeural", "gender": "Male", "locale": "Amharic (Ethiopia)"},
    {"name": "am-ET-MekdesNeural", "gender": "Female", "locale": "Amharic (Ethiopia)"},
    {"name": "ar-AE-FatimaNeural", "gender": "Female", "locale": "Arabic (UAE)"},
    {"name": "ar-AE-HamdanNeural", "gender": "Male", "locale": "Arabic (UAE)"},
    {"name": "ar-BH-AliNeural", "gender": "Male", "locale": "Arabic (Bahrain)"},
    {"name": "ar-BH-LailaNeural", "gender": "Female", "locale": "Arabic (Bahrain)"},
    {"name": "ar-DZ-AminaNeural", "gender": "Female", "locale": "Arabic (Algeria)"},
    {"name": "ar-DZ-IsmaelNeural", "gender": "Male", "locale": "Arabic (Algeria)"},
    {"name": "ar-EG-SalmaNeural", "gender": "Female", "locale": "Arabic (Egypt)"},
    {"name": "ar-EG-ShakirNeural", "gender": "Male", "locale": "Arabic (Egypt)"},
    {"name": "ar-IQ-BasselNeural", "gender": "Male", "locale": "Arabic (Iraq)"},
    {"name": "ar-IQ-RanaNeural", "gender": "Female", "locale": "Arabic (Iraq)"},
    {"name": "ar-JO-SanaNeural", "gender": "Female", "locale": "Arabic (Jordan)"},
    {"name": "ar-JO-TaimNeural", "gender": "Male", "locale": "Arabic (Jordan)"},
    {"name": "ar-KW-FahedNeural", "gender": "Male", "locale": "Arabic (Kuwait)"},
    {"name": "ar-KW-NouraNeural", "gender": "Female", "locale": "Arabic (Kuwait)"},
    {"name": "ar-LB-LaylaNeural", "gender": "Female", "locale": "Arabic (Lebanon)"},
    {"name": "ar-LB-RamiNeural", "gender": "Male", "locale": "Arabic (Lebanon)"},
    {"name": "ar-LY-ImanNeural", "gender": "Female", "locale": "Arabic (Libya)"},
    {"name": "ar-LY-OmarNeural", "gender": "Male", "locale": "Arabic (Libya)"},
    {"name": "ar-MA-JamalNeural", "gender": "Male", "locale": "Arabic (Morocco)"},
    {"name": "ar-MA-MounaNeural", "gender": "Female", "locale": "Arabic (Morocco)"},
    {"name": "ar-OM-AbdullahNeural", "gender": "Male", "locale": "Arabic (Oman)"},
    {"name": "ar-OM-AyshaNeural", "gender": "Female", "locale": "Arabic (Oman)"},
    {"name": "ar-QA-AmalNeural", "gender": "Female", "locale": "Arabic (Qatar)"},
    {"name": "ar-QA-MoazNeural", "gender": "Male", "locale": "Arabic (Qatar)"},
    {"name": "ar-SA-HamedNeural", "gender": "Male", "locale": "Arabic (Saudi Arabia)"},
    {"name": "ar-SA-ZariyahNeural", "gender": "Female", "locale": "Arabic (Saudi Arabia)"},
    {"name": "ar-SY-AmanyNeural", "gender": "Female", "locale": "Arabic (Syria)"},
    {"name": "ar-SY-LaithNeural", "gender": "Male", "locale": "Arabic (Syria)"},
    {"name": "ar-TN-HediNeural", "gender": "Male", "locale": "Arabic (Tunisia)"},
    {"name": "ar-TN-ReemNeural", "gender": "Female", "locale": "Arabic (Tunisia)"},
    {"name": "ar-YE-MaryamNeural", "gender": "Female", "locale": "Arabic (Yemen)"},
    {"name": "ar-YE-SalehNeural", "gender": "Male", "locale": "Arabic (Yemen)"},
    {"name": "az-AZ-BabekNeural", "gender": "Male", "locale": "Azerbaijani (Azerbaijan)"},
    {"name": "az-AZ-BanuNeural", "gender": "Female", "locale": "Azerbaijani (Azerbaijan)"},
    {"name": "bg-BG-BorislavNeural", "gender": "Male", "locale": "Bulgarian (Bulgaria)"},
    {"name": "bg-BG-KalinaNeural", "gender": "Female", "locale": "Bulgarian (Bulgaria)"},
    {"name": "bn-BD-NabanitaNeural", "gender": "Female", "locale": "Bengali (Bangladesh)"},
    {"name": "bn-BD-PradeepNeural", "gender": "Male", "locale": "Bengali (Bangladesh)"},
    {"name": "bn-IN-BashkarNeural", "gender": "Male", "locale": "Bengali (India)"},
    {"name": "bn-IN-TanishaaNeural", "gender": "Female", "locale": "Bengali (India)"},
    {"name": "bs-BA-GoranNeural", "gender": "Male", "locale": "Bosnian (Bosnia)"},
    {"name": "bs-BA-VesnaNeural", "gender": "Female", "locale": "Bosnian (Bosnia)"},
    {"name": "ca-ES-EnricNeural", "gender": "Male", "locale": "Catalan (Spain)"},
    {"name": "ca-ES-JoanaNeural", "gender": "Female", "locale": "Catalan (Spain)"},
    {"name": "cs-CZ-AntoninNeural", "gender": "Male", "locale": "Czech (Czechia)"},
    {"name": "cs-CZ-VlastaNeural", "gender": "Female", "locale": "Czech (Czechia)"},
    {"name": "cy-GB-AledNeural", "gender": "Male", "locale": "Welsh (UK)"},
    {"name": "cy-GB-NiaNeural", "gender": "Female", "locale": "Welsh (UK)"},
    {"name": "da-DK-ChristelNeural", "gender": "Female", "locale": "Danish (Denmark)"},
    {"name": "da-DK-JeppeNeural", "gender": "Male", "locale": "Danish (Denmark)"},
    {"name": "de-AT-IngridNeural", "gender": "Female", "locale": "German (Austria)"},
    {"name": "de-AT-JonasNeural", "gender": "Male", "locale": "German (Austria)"},
    {"name": "de-CH-JanNeural", "gender": "Male", "locale": "German (Switzerland)"},
    {"name": "de-CH-LeniNeural", "gender": "Female", "locale": "German (Switzerland)"},
    {"name": "de-DE-AmalaNeural", "gender": "Female", "locale": "German (Germany)"},
    {"name": "de-DE-ConradNeural", "gender": "Male", "locale": "German (Germany)"},
    {"name": "de-DE-FlorianMultilingualNeural", "gender": "Male", "locale": "German (Germany)"},
    {"name": "de-DE-KatjaNeural", "gender": "Female", "locale": "German (Germany)"},
    {"name": "de-DE-KillianNeural", "gender": "Male", "locale": "German (Germany)"},
    {"name": "de-DE-SeraphinaMultilingualNeural", "gender": "Female", "locale": "German (Germany)"},
    {"name": "el-GR-AthinaNeural", "gender": "Female", "locale": "Greek (Greece)"},
    {"name": "el-GR-NestorasNeural", "gender": "Male", "locale": "Greek (Greece)"},
    {"name": "en-AU-NatashaNeural", "gender": "Female", "locale": "English (Australia)"},
    {"name": "en-AU-WilliamMultilingualNeural", "gender": "Male", "locale": "English (Australia)"},
    {"name": "en-CA-ClaraNeural", "gender": "Female", "locale": "English (Canada)"},
    {"name": "en-CA-LiamNeural", "gender": "Male", "locale": "English (Canada)"},
    {"name": "en-GB-LibbyNeural", "gender": "Female", "locale": "English (UK)"},
    {"name": "en-GB-MaisieNeural", "gender": "Female", "locale": "English (UK)"},
    {"name": "en-GB-RyanNeural", "gender": "Male", "locale": "English (UK)"},
    {"name": "en-GB-SoniaNeural", "gender": "Female", "locale": "English (UK)"},
    {"name": "en-GB-ThomasNeural", "gender": "Male", "locale": "English (UK)"},
    {"name": "en-HK-SamNeural", "gender": "Male", "locale": "English (Hong Kong)"},
    {"name": "en-HK-YanNeural", "gender": "Female", "locale": "English (Hong Kong)"},
    {"name": "en-IE-ConnorNeural", "gender": "Male", "locale": "English (Ireland)"},
    {"name": "en-IE-EmilyNeural", "gender": "Female", "locale": "English (Ireland)"},
    {"name": "en-IN-NeerjaExpressiveNeural", "gender": "Female", "locale": "English (India)"},
    {"name": "en-IN-NeerjaNeural", "gender": "Female", "locale": "English (India)"},
    {"name": "en-IN-PrabhatNeural", "gender": "Male", "locale": "English (India)"},
    {"name": "en-KE-AsiliaNeural", "gender": "Female", "locale": "English (Kenya)"},
    {"name": "en-KE-ChilembaNeural", "gender": "Male", "locale": "English (Kenya)"},
    {"name": "en-NG-AbeoNeural", "gender": "Male", "locale": "English (Nigeria)"},
    {"name": "en-NG-EzinneNeural", "gender": "Female", "locale": "English (Nigeria)"},
    {"name": "en-NZ-MitchellNeural", "gender": "Male", "locale": "English (New Zealand)"},
    {"name": "en-NZ-MollyNeural", "gender": "Female", "locale": "English (New Zealand)"},
    {"name": "en-PH-JamesNeural", "gender": "Male", "locale": "English (Philippines)"},
    {"name": "en-PH-RosaNeural", "gender": "Female", "locale": "English (Philippines)"},
    {"name": "en-SG-LunaNeural", "gender": "Female", "locale": "English (Singapore)"},
    {"name": "en-SG-WayneNeural", "gender": "Male", "locale": "English (Singapore)"},
    {"name": "en-TZ-ElimuNeural", "gender": "Male", "locale": "English (Tanzania)"},
    {"name": "en-TZ-ImaniNeural", "gender": "Female", "locale": "English (Tanzania)"},
    {"name": "en-US-AnaNeural", "gender": "Female", "locale": "English (US)"},
    {"name": "en-US-AndrewMultilingualNeural", "gender": "Male", "locale": "English (US)"},
    {"name": "en-US-AndrewNeural", "gender": "Male", "locale": "English (US)"},
    {"name": "en-US-AriaNeural", "gender": "Female", "locale": "English (US)"},
    {"name": "en-US-AvaMultilingualNeural", "gender": "Female", "locale": "English (US)"},
    {"name": "en-US-AvaNeural", "gender": "Female", "locale": "English (US)"},
    {"name": "en-US-BrianMultilingualNeural", "gender": "Male", "locale": "English (US)"},
    {"name": "en-US-BrianNeural", "gender": "Male", "locale": "English (US)"},
    {"name": "en-US-ChristopherNeural", "gender": "Male", "locale": "English (US)"},
    {"name": "en-US-EmmaMultilingualNeural", "gender": "Female", "locale": "English (US)"},
    {"name": "en-US-EmmaNeural", "gender": "Female", "locale": "English (US)"},
    {"name": "en-US-EricNeural", "gender": "Male", "locale": "English (US)"},
    {"name": "en-US-GuyNeural", "gender": "Male", "locale": "English (US)"},
    {"name": "en-US-JennyNeural", "gender": "Female", "locale": "English (US)"},
    {"name": "en-US-MichelleNeural", "gender": "Female", "locale": "English (US)"},
    {"name": "en-US-RogerNeural", "gender": "Male", "locale": "English (US)"},
    {"name": "en-US-SteffanNeural", "gender": "Male", "locale": "English (US)"},
    {"name": "en-ZA-LeahNeural", "gender": "Female", "locale": "English (South Africa)"},
    {"name": "en-ZA-LukeNeural", "gender": "Male", "locale": "English (South Africa)"},
    {"name": "es-AR-ElenaNeural", "gender": "Female", "locale": "Spanish (Argentina)"},
    {"name": "es-AR-TomasNeural", "gender": "Male", "locale": "Spanish (Argentina)"},
    {"name": "es-BO-MarceloNeural", "gender": "Male", "locale": "Spanish (Bolivia)"},
    {"name": "es-BO-SofiaNeural", "gender": "Female", "locale": "Spanish (Bolivia)"},
    {"name": "es-CL-CatalinaNeural", "gender": "Female", "locale": "Spanish (Chile)"},
    {"name": "es-CL-LorenzoNeural", "gender": "Male", "locale": "Spanish (Chile)"},
    {"name": "es-CO-GonzaloNeural", "gender": "Male", "locale": "Spanish (Colombia)"},
    {"name": "es-CO-SalomeNeural", "gender": "Female", "locale": "Spanish (Colombia)"},
    {"name": "es-CR-JuanNeural", "gender": "Male", "locale": "Spanish (Costa Rica)"},
    {"name": "es-CR-MariaNeural", "gender": "Female", "locale": "Spanish (Costa Rica)"},
    {"name": "es-CU-BelkysNeural", "gender": "Female", "locale": "Spanish (Cuba)"},
    {"name": "es-CU-ManuelNeural", "gender": "Male", "locale": "Spanish (Cuba)"},
    {"name": "es-DO-EmilioNeural", "gender": "Male", "locale": "Spanish (Dominican Republic)"},
    {"name": "es-DO-RamonaNeural", "gender": "Female", "locale": "Spanish (Dominican Republic)"},
    {"name": "es-EC-AndreaNeural", "gender": "Female", "locale": "Spanish (Ecuador)"},
    {"name": "es-EC-LuisNeural", "gender": "Male", "locale": "Spanish (Ecuador)"},
    {"name": "es-ES-AlvaroNeural", "gender": "Male", "locale": "Spanish (Spain)"},
    {"name": "es-ES-ElviraNeural", "gender": "Female", "locale": "Spanish (Spain)"},
    {"name": "es-ES-XimenaNeural", "gender": "Female", "locale": "Spanish (Spain)"},
    {"name": "es-GQ-JavierNeural", "gender": "Male", "locale": "Spanish (Equatorial Guinea)"},
    {"name": "es-GQ-TeresaNeural", "gender": "Female", "locale": "Spanish (Equatorial Guinea)"},
    {"name": "es-GT-AndresNeural", "gender": "Male", "locale": "Spanish (Guatemala)"},
    {"name": "es-GT-MartaNeural", "gender": "Female", "locale": "Spanish (Guatemala)"},
    {"name": "es-HN-CarlosNeural", "gender": "Male", "locale": "Spanish (Honduras)"},
    {"name": "es-HN-KarlaNeural", "gender": "Female", "locale": "Spanish (Honduras)"},
    {"name": "es-MX-DaliaNeural", "gender": "Female", "locale": "Spanish (Mexico)"},
    {"name": "es-MX-JorgeNeural", "gender": "Male", "locale": "Spanish (Mexico)"},
    {"name": "es-NI-FedericoNeural", "gender": "Male", "locale": "Spanish (Nicaragua)"},
    {"name": "es-NI-YolandaNeural", "gender": "Female", "locale": "Spanish (Nicaragua)"},
    {"name": "es-PA-MargaritaNeural", "gender": "Female", "locale": "Spanish (Panama)"},
    {"name": "es-PA-RobertoNeural", "gender": "Male", "locale": "Spanish (Panama)"},
    {"name": "es-PE-AlexNeural", "gender": "Male", "locale": "Spanish (Peru)"},
    {"name": "es-PE-CamilaNeural", "gender": "Female", "locale": "Spanish (Peru)"},
    {"name": "es-PR-KarinaNeural", "gender": "Female", "locale": "Spanish (Puerto Rico)"},
    {"name": "es-PR-VictorNeural", "gender": "Male", "locale": "Spanish (Puerto Rico)"},
    {"name": "es-PY-MarioNeural", "gender": "Male", "locale": "Spanish (Paraguay)"},
    {"name": "es-PY-TaniaNeural", "gender": "Female", "locale": "Spanish (Paraguay)"},
    {"name": "es-SV-LorenaNeural", "gender": "Female", "locale": "Spanish (El Salvador)"},
    {"name": "es-SV-RodrigoNeural", "gender": "Male", "locale": "Spanish (El Salvador)"},
    {"name": "es-US-AlonsoNeural", "gender": "Male", "locale": "Spanish (US)"},
    {"name": "es-US-PalomaNeural", "gender": "Female", "locale": "Spanish (US)"},
    {"name": "es-UY-MateoNeural", "gender": "Male", "locale": "Spanish (Uruguay)"},
    {"name": "es-UY-ValentinaNeural", "gender": "Female", "locale": "Spanish (Uruguay)"},
    {"name": "es-VE-PaolaNeural", "gender": "Female", "locale": "Spanish (Venezuela)"},
    {"name": "es-VE-SebastianNeural", "gender": "Male", "locale": "Spanish (Venezuela)"},
    {"name": "et-EE-AnuNeural", "gender": "Female", "locale": "Estonian (Estonia)"},
    {"name": "et-EE-KertNeural", "gender": "Male", "locale": "Estonian (Estonia)"},
    {"name": "fa-IR-DilaraNeural", "gender": "Female", "locale": "Persian (Iran)"},
    {"name": "fa-IR-FaridNeural", "gender": "Male", "locale": "Persian (Iran)"},
    {"name": "fi-FI-HarriNeural", "gender": "Male", "locale": "Finnish (Finland)"},
    {"name": "fi-FI-NooraNeural", "gender": "Female", "locale": "Finnish (Finland)"},
    {"name": "fil-PH-AngeloNeural", "gender": "Male", "locale": "Filipino (Philippines)"},
    {"name": "fil-PH-BlessicaNeural", "gender": "Female", "locale": "Filipino (Philippines)"},
    {"name": "fr-BE-CharlineNeural", "gender": "Female", "locale": "French (Belgium)"},
    {"name": "fr-BE-GerardNeural", "gender": "Male", "locale": "French (Belgium)"},
    {"name": "fr-CA-AntoineNeural", "gender": "Male", "locale": "French (Canada)"},
    {"name": "fr-CA-JeanNeural", "gender": "Male", "locale": "French (Canada)"},
    {"name": "fr-CA-SylvieNeural", "gender": "Female", "locale": "French (Canada)"},
    {"name": "fr-CA-ThierryNeural", "gender": "Male", "locale": "French (Canada)"},
    {"name": "fr-CH-ArianeNeural", "gender": "Female", "locale": "French (Switzerland)"},
    {"name": "fr-CH-FabriceNeural", "gender": "Male", "locale": "French (Switzerland)"},
    {"name": "fr-FR-DeniseNeural", "gender": "Female", "locale": "French (France)"},
    {"name": "fr-FR-EloiseNeural", "gender": "Female", "locale": "French (France)"},
    {"name": "fr-FR-HenriNeural", "gender": "Male", "locale": "French (France)"},
    {"name": "fr-FR-RemyMultilingualNeural", "gender": "Male", "locale": "French (France)"},
    {"name": "fr-FR-VivienneMultilingualNeural", "gender": "Female", "locale": "French (France)"},
    {"name": "ga-IE-ColmNeural", "gender": "Male", "locale": "Irish (Ireland)"},
    {"name": "ga-IE-OrlaNeural", "gender": "Female", "locale": "Irish (Ireland)"},
    {"name": "gl-ES-RoiNeural", "gender": "Male", "locale": "Galician (Spain)"},
    {"name": "gl-ES-SabelaNeural", "gender": "Female", "locale": "Galician (Spain)"},
    {"name": "gu-IN-DhwaniNeural", "gender": "Female", "locale": "Gujarati (India)"},
    {"name": "gu-IN-NiranjanNeural", "gender": "Male", "locale": "Gujarati (India)"},
    {"name": "he-IL-AvriNeural", "gender": "Male", "locale": "Hebrew (Israel)"},
    {"name": "he-IL-HilaNeural", "gender": "Female", "locale": "Hebrew (Israel)"},
    {"name": "hi-IN-MadhurNeural", "gender": "Male", "locale": "Hindi (India)"},
    {"name": "hi-IN-SwaraNeural", "gender": "Female", "locale": "Hindi (India)"},
    {"name": "hr-HR-GabrijelaNeural", "gender": "Female", "locale": "Croatian (Croatia)"},
    {"name": "hr-HR-SreckoNeural", "gender": "Male", "locale": "Croatian (Croatia)"},
    {"name": "hu-HU-NoemiNeural", "gender": "Female", "locale": "Hungarian (Hungary)"},
    {"name": "hu-HU-TamasNeural", "gender": "Male", "locale": "Hungarian (Hungary)"},
    {"name": "id-ID-ArdiNeural", "gender": "Male", "locale": "Indonesian (Indonesia)"},
    {"name": "id-ID-GadisNeural", "gender": "Female", "locale": "Indonesian (Indonesia)"},
    {"name": "is-IS-GudrunNeural", "gender": "Female", "locale": "Icelandic (Iceland)"},
    {"name": "is-IS-GunnarNeural", "gender": "Male", "locale": "Icelandic (Iceland)"},
    {"name": "it-IT-DiegoNeural", "gender": "Male", "locale": "Italian (Italy)"},
    {"name": "it-IT-ElsaNeural", "gender": "Female", "locale": "Italian (Italy)"},
    {"name": "it-IT-GiuseppeMultilingualNeural", "gender": "Male", "locale": "Italian (Italy)"},
    {"name": "it-IT-IsabellaNeural", "gender": "Female", "locale": "Italian (Italy)"},
    {"name": "iu-Cans-CA-SiqiniqNeural", "gender": "Female", "locale": "Inuktitut (Canada)"},
    {"name": "iu-Cans-CA-TaqqiqNeural", "gender": "Male", "locale": "Inuktitut (Canada)"},
    {"name": "iu-Latn-CA-SiqiniqNeural", "gender": "Female", "locale": "Inuktitut Latin (Canada)"},
    {"name": "iu-Latn-CA-TaqqiqNeural", "gender": "Male", "locale": "Inuktitut Latin (Canada)"},
    {"name": "ja-JP-KeitaNeural", "gender": "Male", "locale": "Japanese (Japan)"},
    {"name": "ja-JP-NanamiNeural", "gender": "Female", "locale": "Japanese (Japan)"},
    {"name": "jv-ID-DimasNeural", "gender": "Male", "locale": "Javanese (Indonesia)"},
    {"name": "jv-ID-SitiNeural", "gender": "Female", "locale": "Javanese (Indonesia)"},
    {"name": "ka-GE-EkaNeural", "gender": "Female", "locale": "Georgian (Georgia)"},
    {"name": "ka-GE-GiorgiNeural", "gender": "Male", "locale": "Georgian (Georgia)"},
    {"name": "kk-KZ-AigulNeural", "gender": "Female", "locale": "Kazakh (Kazakhstan)"},
    {"name": "kk-KZ-DauletNeural", "gender": "Male", "locale": "Kazakh (Kazakhstan)"},
    {"name": "km-KH-PisethNeural", "gender": "Male", "locale": "Khmer (Cambodia)"},
    {"name": "km-KH-SreymomNeural", "gender": "Female", "locale": "Khmer (Cambodia)"},
    {"name": "kn-IN-GaganNeural", "gender": "Male", "locale": "Kannada (India)"},
    {"name": "kn-IN-SapnaNeural", "gender": "Female", "locale": "Kannada (India)"},
    {"name": "ko-KR-HyunsuMultilingualNeural", "gender": "Male", "locale": "Korean (Korea)"},
    {"name": "ko-KR-InJoonNeural", "gender": "Male", "locale": "Korean (Korea)"},
    {"name": "ko-KR-SunHiNeural", "gender": "Female", "locale": "Korean (Korea)"},
    {"name": "lo-LA-ChanthavongNeural", "gender": "Male", "locale": "Lao (Laos)"},
    {"name": "lo-LA-KeomanyNeural", "gender": "Female", "locale": "Lao (Laos)"},
    {"name": "lt-LT-LeonasNeural", "gender": "Male", "locale": "Lithuanian (Lithuania)"},
    {"name": "lt-LT-OnaNeural", "gender": "Female", "locale": "Lithuanian (Lithuania)"},
    {"name": "lv-LV-EveritaNeural", "gender": "Female", "locale": "Latvian (Latvia)"},
    {"name": "lv-LV-NilsNeural", "gender": "Male", "locale": "Latvian (Latvia)"},
    {"name": "mk-MK-AleksandarNeural", "gender": "Male", "locale": "Macedonian (North Macedonia)"},
    {"name": "mk-MK-MarijaNeural", "gender": "Female", "locale": "Macedonian (North Macedonia)"},
    {"name": "ml-IN-MidhunNeural", "gender": "Male", "locale": "Malayalam (India)"},
    {"name": "ml-IN-SobhanaNeural", "gender": "Female", "locale": "Malayalam (India)"},
    {"name": "mn-MN-BataaNeural", "gender": "Male", "locale": "Mongolian (Mongolia)"},
    {"name": "mn-MN-YesuiNeural", "gender": "Female", "locale": "Mongolian (Mongolia)"},
    {"name": "mr-IN-AarohiNeural", "gender": "Female", "locale": "Marathi (India)"},
    {"name": "mr-IN-ManoharNeural", "gender": "Male", "locale": "Marathi (India)"},
    {"name": "ms-MY-OsmanNeural", "gender": "Male", "locale": "Malay (Malaysia)"},
    {"name": "ms-MY-YasminNeural", "gender": "Female", "locale": "Malay (Malaysia)"},
    {"name": "mt-MT-GraceNeural", "gender": "Female", "locale": "Maltese (Malta)"},
    {"name": "mt-MT-JosephNeural", "gender": "Male", "locale": "Maltese (Malta)"},
    {"name": "my-MM-NilarNeural", "gender": "Female", "locale": "Burmese (Myanmar)"},
    {"name": "my-MM-ThihaNeural", "gender": "Male", "locale": "Burmese (Myanmar)"},
    {"name": "nb-NO-FinnNeural", "gender": "Male", "locale": "Norwegian (Norway)"},
    {"name": "nb-NO-PernilleNeural", "gender": "Female", "locale": "Norwegian (Norway)"},
    {"name": "ne-NP-HemkalaNeural", "gender": "Female", "locale": "Nepali (Nepal)"},
    {"name": "ne-NP-SagarNeural", "gender": "Male", "locale": "Nepali (Nepal)"},
    {"name": "nl-BE-ArnaudNeural", "gender": "Male", "locale": "Dutch (Belgium)"},
    {"name": "nl-BE-DenaNeural", "gender": "Female", "locale": "Dutch (Belgium)"},
    {"name": "nl-NL-ColetteNeural", "gender": "Female", "locale": "Dutch (Netherlands)"},
    {"name": "nl-NL-FennaNeural", "gender": "Female", "locale": "Dutch (Netherlands)"},
    {"name": "nl-NL-MaartenNeural", "gender": "Male", "locale": "Dutch (Netherlands)"},
    {"name": "pl-PL-MarekNeural", "gender": "Male", "locale": "Polish (Poland)"},
    {"name": "pl-PL-ZofiaNeural", "gender": "Female", "locale": "Polish (Poland)"},
    {"name": "ps-AF-GulNawazNeural", "gender": "Male", "locale": "Pashto (Afghanistan)"},
    {"name": "ps-AF-LatifaNeural", "gender": "Female", "locale": "Pashto (Afghanistan)"},
    {"name": "pt-BR-AntonioNeural", "gender": "Male", "locale": "Portuguese (Brazil)"},
    {"name": "pt-BR-FranciscaNeural", "gender": "Female", "locale": "Portuguese (Brazil)"},
    {"name": "pt-BR-ThalitaMultilingualNeural", "gender": "Female", "locale": "Portuguese (Brazil)"},
    {"name": "pt-PT-DuarteNeural", "gender": "Male", "locale": "Portuguese (Portugal)"},
    {"name": "pt-PT-RaquelNeural", "gender": "Female", "locale": "Portuguese (Portugal)"},
    {"name": "ro-RO-AlinaNeural", "gender": "Female", "locale": "Romanian (Romania)"},
    {"name": "ro-RO-EmilNeural", "gender": "Male", "locale": "Romanian (Romania)"},
    {"name": "ru-RU-DmitryNeural", "gender": "Male", "locale": "Russian (Russia)"},
    {"name": "ru-RU-SvetlanaNeural", "gender": "Female", "locale": "Russian (Russia)"},
    {"name": "si-LK-SameeraNeural", "gender": "Male", "locale": "Sinhala (Sri Lanka)"},
    {"name": "si-LK-ThiliniNeural", "gender": "Female", "locale": "Sinhala (Sri Lanka)"},
    {"name": "sk-SK-LukasNeural", "gender": "Male", "locale": "Slovak (Slovakia)"},
    {"name": "sk-SK-ViktoriaNeural", "gender": "Female", "locale": "Slovak (Slovakia)"},
    {"name": "sl-SI-PetraNeural", "gender": "Female", "locale": "Slovenian (Slovenia)"},
    {"name": "sl-SI-RokNeural", "gender": "Male", "locale": "Slovenian (Slovenia)"},
    {"name": "so-SO-MuuseNeural", "gender": "Male", "locale": "Somali (Somalia)"},
    {"name": "so-SO-UbaxNeural", "gender": "Female", "locale": "Somali (Somalia)"},
    {"name": "sq-AL-AnilaNeural", "gender": "Female", "locale": "Albanian (Albania)"},
    {"name": "sq-AL-IlirNeural", "gender": "Male", "locale": "Albanian (Albania)"},
    {"name": "sr-RS-NicholasNeural", "gender": "Male", "locale": "Serbian (Serbia)"},
    {"name": "sr-RS-SophieNeural", "gender": "Female", "locale": "Serbian (Serbia)"},
    {"name": "su-ID-JajangNeural", "gender": "Male", "locale": "Sundanese (Indonesia)"},
    {"name": "su-ID-TutiNeural", "gender": "Female", "locale": "Sundanese (Indonesia)"},
    {"name": "sv-SE-MattiasNeural", "gender": "Male", "locale": "Swedish (Sweden)"},
    {"name": "sv-SE-SofieNeural", "gender": "Female", "locale": "Swedish (Sweden)"},
    {"name": "sw-KE-RafikiNeural", "gender": "Male", "locale": "Swahili (Kenya)"},
    {"name": "sw-KE-ZuriNeural", "gender": "Female", "locale": "Swahili (Kenya)"},
    {"name": "sw-TZ-DaudiNeural", "gender": "Male", "locale": "Swahili (Tanzania)"},
    {"name": "sw-TZ-RehemaNeural", "gender": "Female", "locale": "Swahili (Tanzania)"},
    {"name": "ta-IN-PallaviNeural", "gender": "Female", "locale": "Tamil (India)"},
    {"name": "ta-IN-ValluvarNeural", "gender": "Male", "locale": "Tamil (India)"},
    {"name": "ta-LK-KumarNeural", "gender": "Male", "locale": "Tamil (Sri Lanka)"},
    {"name": "ta-LK-SaranyaNeural", "gender": "Female", "locale": "Tamil (Sri Lanka)"},
    {"name": "ta-MY-KaniNeural", "gender": "Female", "locale": "Tamil (Malaysia)"},
    {"name": "ta-MY-SuryaNeural", "gender": "Male", "locale": "Tamil (Malaysia)"},
    {"name": "ta-SG-AnbuNeural", "gender": "Male", "locale": "Tamil (Singapore)"},
    {"name": "ta-SG-VenbaNeural", "gender": "Female", "locale": "Tamil (Singapore)"},
    {"name": "te-IN-MohanNeural", "gender": "Male", "locale": "Telugu (India)"},
    {"name": "te-IN-ShrutiNeural", "gender": "Female", "locale": "Telugu (India)"},
    {"name": "th-TH-NiwatNeural", "gender": "Male", "locale": "Thai (Thailand)"},
    {"name": "th-TH-PremwadeeNeural", "gender": "Female", "locale": "Thai (Thailand)"},
    {"name": "tr-TR-AhmetNeural", "gender": "Male", "locale": "Turkish (Turkey)"},
    {"name": "tr-TR-EmelNeural", "gender": "Female", "locale": "Turkish (Turkey)"},
    {"name": "uk-UA-OstapNeural", "gender": "Male", "locale": "Ukrainian (Ukraine)"},
    {"name": "uk-UA-PolinaNeural", "gender": "Female", "locale": "Ukrainian (Ukraine)"},
    {"name": "ur-IN-GulNeural", "gender": "Female", "locale": "Urdu (India)"},
    {"name": "ur-IN-SalmanNeural", "gender": "Male", "locale": "Urdu (India)"},
    {"name": "ur-PK-AsadNeural", "gender": "Male", "locale": "Urdu (Pakistan)"},
    {"name": "ur-PK-UzmaNeural", "gender": "Female", "locale": "Urdu (Pakistan)"},
    {"name": "uz-UZ-MadinaNeural", "gender": "Female", "locale": "Uzbek (Uzbekistan)"},
    {"name": "uz-UZ-SardorNeural", "gender": "Male", "locale": "Uzbek (Uzbekistan)"},
    {"name": "vi-VN-HoaiMyNeural", "gender": "Female", "locale": "Vietnamese (Vietnam)"},
    {"name": "vi-VN-NamMinhNeural", "gender": "Male", "locale": "Vietnamese (Vietnam)"},
    {"name": "zh-CN-XiaoxiaoNeural", "gender": "Female", "locale": "Chinese (Mandarin)"},
    {"name": "zh-CN-XiaoyiNeural", "gender": "Female", "locale": "Chinese (Mandarin)"},
    {"name": "zh-CN-YunjianNeural", "gender": "Male", "locale": "Chinese (Mandarin)"},
    {"name": "zh-CN-YunxiNeural", "gender": "Male", "locale": "Chinese (Mandarin)"},
    {"name": "zh-CN-YunxiaNeural", "gender": "Male", "locale": "Chinese (Mandarin)"},
    {"name": "zh-CN-YunyangNeural", "gender": "Male", "locale": "Chinese (Mandarin)"},
    {"name": "zh-CN-liaoning-XiaobeiNeural", "gender": "Female", "locale": "Chinese (Liaoning dialect)"},
    {"name": "zh-CN-shaanxi-XiaoniNeural", "gender": "Female", "locale": "Chinese (Shaanxi dialect)"},
    {"name": "zh-HK-HiuGaaiNeural", "gender": "Female", "locale": "Chinese (Hong Kong Cantonese)"},
    {"name": "zh-HK-HiuMaanNeural", "gender": "Female", "locale": "Chinese (Hong Kong Cantonese)"},
    {"name": "zh-HK-WanLungNeural", "gender": "Male", "locale": "Chinese (Hong Kong Cantonese)"},
    {"name": "zh-TW-HsiaoChenNeural", "gender": "Female", "locale": "Chinese (Taiwan)"},
    {"name": "zh-TW-HsiaoYuNeural", "gender": "Female", "locale": "Chinese (Taiwan)"},
    {"name": "zh-TW-YunJheNeural", "gender": "Male", "locale": "Chinese (Taiwan)"},
    {"name": "zu-ZA-ThandoNeural", "gender": "Female", "locale": "Zulu (South Africa)"},
    {"name": "zu-ZA-ThembaNeural", "gender": "Male", "locale": "Zulu (South Africa)"},
]


if __name__ == "__main__":
    import time

    PORT = int(os.environ.get("PORT", 5000))

    # ── Try to launch as a native desktop window via pywebview ──────────────
    # pywebview uses Windows WebView2 (built into Win10/11) — no browser tab.
    # Falls back to the regular browser if pywebview is not installed.
    _use_webview = not os.environ.get("INNET_NO_BROWSER") and not os.environ.get("INNET_BROWSER_MODE")
    try:
        import webview as _webview
    except ImportError:
        _webview = None
        _use_webview = False

    if _webview and _use_webview:
        # Flask must run in a background daemon thread so pywebview can own
        # the main thread (required by Windows GUI APIs).
        def _run_flask():
            app.run(debug=False, use_reloader=False, port=PORT, host="127.0.0.1")

        flask_thread = threading.Thread(target=_run_flask, daemon=True)
        flask_thread.start()

        # Give Flask a moment to bind the port before opening the window.
        time.sleep(1.2)

        print("\n[IN NET STT Convertor]")
        print("   Powered by IN NET CREATIONS")
        print("   Created by Manohar | innetcreations@gmail.com")
        print("   Launching desktop window…\n")

        # Resolve the icon path (works both frozen exe and normal Python).
        _icon_path = os.path.join(
            getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))),
            "Assets", "logo.ico"
        )
        _icon_arg = _icon_path if os.path.isfile(_icon_path) else None

        window = _webview.create_window(
            title="IN NET STT Convertor — IN NET CREATIONS",
            url=f"http://127.0.0.1:{PORT}",
            width=1200,
            height=840,
            min_size=(860, 640),
            resizable=True,
            text_select=True,
        )

        # icon kwarg supported on Windows in pywebview ≥ 4.3
        try:
            _webview.start(icon=_icon_arg, debug=False)
        except TypeError:
            # Older pywebview without icon param
            _webview.start(debug=False)

    else:
        # ── Fallback: open in the default browser ────────────────────────────
        if not os.environ.get("INNET_NO_BROWSER"):
            threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()

        print("\n[IN NET STT Convertor]")
        print("   Powered by IN NET CREATIONS")
        print("   Created by Manohar | innetcreations@gmail.com")
        print(f"   Running at: http://127.0.0.1:{PORT}\n")

        # debug=False and use_reloader=False are required for PyInstaller exes.
        app.run(debug=False, use_reloader=False, port=PORT, host="0.0.0.0")