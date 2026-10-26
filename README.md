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

Ollama kurulduktan sonra modelleri bir kez indir:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\setup-models.ps1
```

Türkçe Vosk modeli `models\vosk-model-small-tr-0.3` altında bulunmalıdır.
Modeli indirmek için Vosk'un `vosk-model-small-tr-0.3` arşivini açıp bu dizine
yerleştir. `.gitignore` nedeniyle model ağırlıkları Git'e eklenmez.

## Çalıştırma

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\run.ps1
```

Pencere içinde metinle komut gönderebilir veya mikrofon izni verip
"Hey ACIÖZ" diyerek uyandırabilirsin. Görüntü analizi yalnızca kamera sorusu
geldiğinde çalışır.

## Testler

```powershell
python -m unittest discover -s tests -v
```

## Güvenlik ve sınırlar

- Ollama bağlantısı `127.0.0.1` üzerindedir; istemci uzak servis kullanmaz.
- Araçlar dizin listeleme, var olan yolu açma, HTTP(S) adresi açma ve izinli
  uygulamaları (tarayıcı, not defteri, hesap makinesi, dosya gezgini) başlatmayla sınırlıdır.
- Serbest terminal komutu ve dosya silme araçları bilerek sunulmaz.
- Kamera otomatik kaydetmez; yalnızca açıkça görüntü sorulduğunda tek kare alır.
- `ACIOZ_CHAT_MODEL`, `ACIOZ_VISION_MODEL` ve `ACIOZ_VOSK_MODEL` ortam
  değişkenleriyle yerel yapılandırma değiştirilebilir.
