"""Narração do vídeo: gera voz_<id>.wav (44,1 kHz, mono) na pasta do roteiro, uma por cena.

Uso: python -I voz.py windows <roteiro.json> [--voz "Microsoft Maria Desktop"] [--rate 2]
     python -I voz.py eleven  <roteiro.json> --voice-id <id> [--model eleven_v4]
     python -I voz.py texto   <roteiro.json> <falas.md>          (falas numeradas para gerar à mão)
     python -I voz.py mp3     <roteiro.json> <pasta>             (converte <pasta>/<id>.mp3 gerados à mão)

A chave do ElevenLabs vem de ELEVENLABS_API_KEY (ambiente ou, no Windows, o registro do usuário,
onde o `setx` grava) e nunca é impressa. O ffmpeg vem do imageio-ffmpeg ou do PATH.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roteiro  # noqa: E402

PS_TTS = r"""
param([string]$Entrada, [string]$Voz, [int]$Rate)
Add-Type -AssemblyName System.Speech
$itens = Get-Content -Raw -Encoding UTF8 $Entrada | ConvertFrom-Json
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(44100, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
foreach ($i in $itens) {
    $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $s.SelectVoice($Voz)
    $s.Rate = $Rate
    $s.SetOutputToWaveFile($i.saida, $fmt)
    $s.Speak($i.fala)
    $s.Dispose()
}
"""


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        exe = shutil.which("ffmpeg")
        if not exe:
            sys.exit("ffmpeg não encontrado: pip install imageio-ffmpeg")
        return exe


def para_wav(origem, destino):
    subprocess.run([ffmpeg(), "-loglevel", "error", "-y", "-i", origem, "-ac", "1", "-ar", "44100", "-sample_fmt", "s16", destino],
                   check=True)


def opcao(args, nome, padrao=None):
    return args[args.index(nome) + 1] if nome in args else padrao


def chave_eleven():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k and os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as reg:
                k = winreg.QueryValueEx(reg, "ELEVENLABS_API_KEY")[0]
        except OSError:
            k = None
    if not k:
        sys.exit("defina ELEVENLABS_API_KEY (o usuário roda: setx ELEVENLABS_API_KEY \"...\")")
    return k.strip()


def windows(r, pasta, voz, rate):
    itens = [{"fala": c["fala"], "saida": os.path.join(pasta, f"voz_{c['id']}.wav")} for c in r["cenas"]]
    with tempfile.TemporaryDirectory() as tmp:
        entrada, script = os.path.join(tmp, "itens.json"), os.path.join(tmp, "tts.ps1")
        with open(entrada, "w", encoding="utf-8") as f:
            json.dump(itens, f, ensure_ascii=False)
        with open(script, "w", encoding="utf-8-sig") as f:
            f.write(PS_TTS)
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script,
                        "-Entrada", entrada, "-Voz", voz, "-Rate", str(rate)], check=True)


def eleven(r, pasta, voice_id, modelo):
    k = chave_eleven()
    for c in r["cenas"]:
        corpo = json.dumps({"text": c["fala"], "model_id": modelo, "language_code": "pt"}).encode()
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
                                     data=corpo, method="POST", headers={"xi-api-key": k, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                audio = resp.read()
        except urllib.error.HTTPError as e:
            detalhe = e.read()[:300].decode(errors="replace")
            dica = " (plano gratuito não usa vozes da biblioteca pela API: gere à mão com 'texto' + 'mp3')" if e.code == 402 else ""
            sys.exit(f"ElevenLabs HTTP {e.code} na cena {c['id']}: {detalhe}{dica}")
        mp3 = os.path.join(pasta, f"{c['id']}.mp3")
        with open(mp3, "wb") as f:
            f.write(audio)
        para_wav(mp3, os.path.join(pasta, f"voz_{c['id']}.wav"))
        print("ok", c["id"])


def texto(r, saida):
    with open(saida, "w", encoding="utf-8") as f:
        f.write("# Falas do vídeo\n\nGere cada fala na ferramenta de voz, baixe o MP3 e salve com o nome indicado numa pasta só.\n\n")
        for i, c in enumerate(r["cenas"], 1):
            f.write(f"## {i:02d}. Salvar como: {c['id']}.mp3\n\n{c['fala']}\n\n")


def mp3(r, pasta, origem):
    faltam = [c["id"] for c in r["cenas"] if not os.path.exists(os.path.join(origem, f"{c['id']}.mp3"))]
    if faltam:
        sys.exit("faltam os MP3: " + ", ".join(faltam))
    for c in r["cenas"]:
        para_wav(os.path.join(origem, f"{c['id']}.mp3"), os.path.join(pasta, f"voz_{c['id']}.wav"))
    print(f"ok: {len(r['cenas'])} falas convertidas")


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ("windows", "eleven", "texto", "mp3"):
        sys.exit(__doc__)
    caminho = a[1]
    r = roteiro.carregar(caminho)
    erros = roteiro.validar(r)
    if erros:
        sys.exit("\n".join(erros))
    pasta = os.path.dirname(os.path.abspath(caminho))
    if a[0] == "windows":
        windows(r, pasta, opcao(a, "--voz", "Microsoft Maria Desktop"), int(opcao(a, "--rate", "2")))
    elif a[0] == "eleven":
        voice = opcao(a, "--voice-id")
        if not voice:
            sys.exit("informe --voice-id")
        eleven(r, pasta, voice, opcao(a, "--model", "eleven_v4"))
    elif a[0] == "texto":
        texto(r, a[2])
    else:
        mp3(r, pasta, a[2])
    if a[0] != "texto":
        total = roteiro.linha_do_tempo(r, roteiro.duracoes_da_pasta(r, pasta))
        print(f"narração total {total:.1f}s")


if __name__ == "__main__":
    main()
