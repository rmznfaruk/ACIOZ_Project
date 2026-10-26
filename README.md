# ACIÖZ

Yerel Ollama, Vosk, OpenCV ve PySide6 kullanan masaüstü asistanı. Metin,
mikrofon ve kamera verileri yapılandırılmış bir bulut servisine gönderilmez.

## Kurulum

Python 3.10+ ve Ollama'yı kur. Proje kökünde PowerShell ile:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Ollama modellerini ayrıca indir:

```powershell
ollama pull qwen3:4b
ollama pull qwen2.5vl:3b
```

Türkçe Vosk modeli `models\vosk-model-small-tr-0.3` altında bulunmalıdır.
Modeli indirmek için Vosk'un `vosk-model-small-tr-0.3` arşivini açıp bu dizine
yerleştir. `.gitignore` nedeniyle model ağırlıkları Git'e eklenmez.

## Çalıştırma

```powershell
python main.py
```

Pencere içinde metinle komut gönderebilir veya mikrofon izni verip
"Hey ACIÖZ" diyerek uyandırabilirsin. Görüntü analizi yalnızca kamera sorusu
geldiğinde çalışır.

## Güvenlik ve sınırlar

- Ollama bağlantısı `127.0.0.1` üzerindedir; istemci uzak servis kullanmaz.
- Araçlar dizin listeleme, var olan yolu açma, HTTP(S) adresi açma ve üç
  izinli Windows uygulamasını başlatmayla sınırlıdır.
- Serbest terminal komutu ve dosya silme araçları bilerek sunulmaz.
- Kamera otomatik kaydetmez; yalnızca açıkça görüntü sorulduğunda tek kare alır.
- `ACIOZ_CHAT_MODEL`, `ACIOZ_VISION_MODEL` ve `ACIOZ_VOSK_MODEL` ortam
  değişkenleriyle yerel yapılandırma değiştirilebilir.
