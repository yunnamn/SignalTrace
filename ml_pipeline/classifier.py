import re
import os
import io
import tempfile
import yt_dlp
import whisper
import cv2
import requests
from PIL import Image
from transformers import pipeline, CLIPProcessor, CLIPModel
import torch

MAX_VIDEO_BYTES = int(os.getenv("MAX_VIDEO_BYTES", str(100 * 1024 * 1024)))
MAX_VIDEO_DURATION_SECONDS = int(os.getenv("MAX_VIDEO_DURATION_SECONDS", "900"))

class MLPipeline:
    def __init__(self):
        self.text_classifier = None
        self.clip_model = None
        self.clip_processor = None
        self.whisper_model = None
        self.is_loaded = False
        
        self.text_classes = {
            "casino": [
                "занос на слотах сегодня",
                "крути слоты со мной",
                "зашёл в плюс в авиаторе",
                "бонус на первый депозит казино",
                "выиграл джекпот в онлайн казино",
                "ставки на спорт сегодня",
                "лучшие слоты для заноса",
                "регистрируйся и получи фриспины",
                "авиатор стратегия выигрыша",
                "букмекер лучшие коэффициенты",
                "слот занёс с первого спина",
                "онлайн казино без проверки",
                "игровые автоматы с выводом денег",
                "топовые слоты для заноса 2026",
                "выиграл на спортивных ставках сегодня",
                "краш-игра авиатор тактика",
                "рокет стратегия выигрыша работает",
                "выиграл миллион в казино честно",
                "слот х1000 занос случился реально",
                "депозит в казино вернулся с плюсом",
                "покер онлайн с реальными деньгами",
                "фриспины без депозита бери сейчас",
                "лучшая стратегия игры в авиатор",
                "казино платит без задержек быстро",
                "зашёл в казино вышел с деньгами",
                "рулетка онлайн выигрышная стратегия",
                "ставки на футбол сегодня капперы",
                "занос дня на любимом слоте",
                "промокод казино бонус только сегодня",
                "честный букмекер с быстрым выводом",
                "краш-игра как не крашнуться совет",
                "топ слоты которые реально заносят",
                "мой первый занос на миллион",
                "авиатор успел выйти вовремя вот",
                "игровые автоматы секрет выигрыша открываю",
                "казино дало бонус за регистрацию",
                "ставка зашла как я и говорил",
                "крашнул но поднялся в следующей игре",
                "бонус на депозит удвоил мой счёт",
                "ставлю каждый день стабильно в плюс",
            ],
            "pyramid": [
                "строим команду вместе зарабатываем",
                "пассивный доход с первого дня",
                "моя структура уже пятьсот человек",
                "наставник поможет тебе стартовать",
                "заходи в мой бизнес зарабатывай",
                "партнёрская программа высокий доход",
                "реферальный доход каждый день",
                "уровни партнёрства растёт доход",
                "обучение системе за символическую сумму",
                "закрытый клуб успешных людей",
                "сетевой бизнес который реально работает",
                "приглашай друзей получай свой процент",
                "бизнес-система которая работает за тебя",
                "команда три тысячи человек пассивный доход",
                "вступай в сеть начни зарабатывать",
                "два реферала и ты в плюсе",
                "мой наставник вывел меня в лидеры",
                "платформа платит всем участникам сети",
                "дупликация системы на автопилоте работает",
                "открой своё дело через нашу систему",
                "лидерский бонус за развитие команды",
                "заработок без продаж через партнёров",
                "сетевой маркетинг без порога входа",
                "матрица заполняется деньги капают",
                "бинарная система доход с двух веток",
                "регистрируйся под меня получи бонус",
                "структура работает пока ты спишь",
                "три партнёра и система закрутилась",
                "млм бизнес который не требует опыта",
                "вступительный взнос окупается за неделю",
                "приглашай людей уровень растёт доход",
                "онлайн бизнес с командой по всему миру",
                "стань лидером своей сети сегодня",
                "система приносит доход от чужих продаж",
                "квалификация выполнена бонус начислен",
                "закрытый чат только для партнёров сети",
                "твой первый реферал уже в системе",
                "автоматический заработок через структуру",
                "обучение бесплатно при регистрации в сеть",
                "наша система работает во всех странах",
            ],
            "guaranteed_income": [
                "поднял двести тысяч за неделю",
                "зарабатываю лёжа на диване",
                "покажу схему без вложений",
                "гарантированно пятьдесят тысяч в месяц",
                "сто тысяч за первый месяц легко",
                "без опыта без вложений с нуля",
                "работая из дома по два часа",
                "мой метод приносит стабильно всегда",
                "скриншоты выплат сегодня утром",
                "схема которая реально работает",
                "пассивный доход без усилий ежедневно",
                "пятьсот долларов в день это реально",
                "заработок без обмана проверено лично",
                "покажу как зарабатывать от тысячи в день",
                "вышел на доход без вложений быстро",
                "стабильный заработок из любой точки мира",
                "каждый может заработать по этой схеме",
                "результат с первого дня гарантирован",
                "показываю реальный доход в сторис",
                "зарабатываю больше чем на основной работе",
                "пять минут в день и деньги идут",
                "схема работает автоматически без участия",
                "покажу как выйти на сто тысяч в месяц",
                "система даёт стабильный результат всегда",
                "деньги поступают каждый день на счёт",
                "проверенный способ заработка без риска",
                "вложи десять получи сто гарантированно",
                "без образования без навыков зарабатываю",
                "мой доход вырос за месяц в пять раз",
                "покажу как зарабатывать пока спишь",
                "новичок с нуля вышел на восемьдесят тысяч",
                "стабильный пассивный доход с гарантией",
                "работаю час в день имею всё",
                "схема проверена тысячами людей работает",
                "реальные выплаты скриншоты в профиле",
                "заработал первые пятьдесят тысяч уже завтра",
                "обучу методу который приносит всегда",
                "без рисков без потерь только плюс",
                "делюсь схемой которую скрывают богатые",
                "деньги идут даже когда отдыхаешь",
            ],
            "referral": [
                "ссылка в шапке профиля жми",
                "переходи по моей ссылке сегодня",
                "регистрируйся через меня получи бонус",
                "промокод на депозит в описании",
                "жми на ссылку ниже не теряй время",
                "пиши слово СТАРТ в директ",
                "подпишись и получи инструкцию бесплатно",
                "мой промокод даёт плюс пятьдесят процентов",
                "телеграм канал в шапке профиля заходи",
                "первый шаг регистрация по моей ссылке",
                "переходи в телеграм всё объясню там",
                "кидай плюс получи мою схему",
                "ссылка внизу видео жми сейчас",
                "зарегистрируйся получи приветственный бонус",
                "по моей ссылке бонус в два раза больше",
                "пиши ХОЧУ в директ отвечу лично",
                "открой описание там главная ссылка",
                "заходи в закрытый чат по ссылке",
                "мой реферальный код введи при регистрации",
                "первые сто мест со скидкой по ссылке",
                "перейди по ссылке зарегистрируйся бесплатно",
                "телеграм ссылка в закрепе канала",
                "жми кнопку ниже заполни форму",
                "напиши в директ слово ДЕНЬГИ",
                "ссылка на регистрацию в шапке профиля",
                "мой промокод действует только сегодня",
                "переходи за бонусом по реферальной ссылке",
                "пиши мне получишь доступ к закрытому материалу",
                "все детали в телеграм канале ссылка ниже",
                "зарегистрируйся по коду получи кэшбэк",
                "напиши плюс в комменты дам ссылку",
                "подписка через мою ссылку даёт бонус",
                "регистрация по ссылке даёт двойной бонус",
                "скидка только через мой реферальный код",
                "пиши ИНФО получи доступ прямо сейчас",
                "переходи получи первый урок бесплатно",
                "жми на аватар там ссылка на регистрацию",
                "пиши в личку дам рабочую схему",
                "первый бесплатно потом решишь сам",
                "ссылка на вход в систему в сторис",
            ],
            "investment_scam": [
                "токен взлетит в сто иксов",
                "купи сейчас завтра будет поздно",
                "инсайд от команды проекта есть",
                "успей зайти до листинга монеты",
                "крипта даст иксы уже скоро",
                "раскрутка счёта от моего трейдера",
                "форекс сигналы плюс каждый день",
                "вложи в проект выйди на иксы",
                "доверительное управление стабильный доход",
                "памп начался успей купить сейчас",
                "новый токен проекта заходи быстрее",
                "нфт проект который изменит рынок",
                "к луне этот альткоин уже летит",
                "закрытый пул инвестиций только своим",
                "HYIP проект платит уже третий месяц",
                "трейдер слил сигнал покупай сейчас",
                "биткоин вырастет до конца недели",
                "зашёл по сигналу вышел в плюс",
                "токен листится на бирже покупай",
                "форекс советник торгует без потерь",
                "инвестиции в проект от топ команды",
                "крипто фонд с гарантированным доходом",
                "монета уйдёт в иксы через сутки",
                "доверь капитал профессиональному трейдеру",
                "вход в пул только до полуночи",
                "команда проекта уже на связи",
                "мой трейдер сделал иксы за неделю",
                "форекс стратегия без потерь проверено",
                "успей до памп-зоны войти сейчас",
                "ICO открытое участвуй получи иксы",
                "альткоин перед листингом последний шанс",
                "крипта против доллара растёт вкладывай",
                "гарантирую рост твоего депозита в месяц",
                "сигналы которые всегда в плюсе",
                "передай деньги в управление получи доход",
                "стартап на блокчейне ищет первых инвесторов",
                "токен с реальной ценностью покупай пока дёшево",
                "получи иксы вложив тысячу тенге",
                "проект платит с первого дня вклада",
                "войди в крипту до большого роста",
            ]
        }
        
        self.image_classes = {
            "casino": [
                "online casino app interface",
                "slot machine game screen",
                "sports betting odds screen",
            ],
            "investment_scam": [
                "cryptocurrency trading chart with profit claims",
                "luxury money investment advertisement",
                "forex trading signal screenshot",
            ],
            "pyramid": [
                "multi level marketing pyramid diagram",
                "referral earnings dashboard",
            ]
        }
        self.neutral_image_classes = [
            "ordinary person talking to camera",
            "financial education slide",
            "news article screenshot",
            "family photo",
            "landscape photo",
            "product review video frame",
            "plain text document",
        ]
        self.text_category_labels = {
            "casino": "online gambling promotion, casino bonuses, slots, sports betting, aviator crash game",
            "pyramid": "financial pyramid or MLM recruitment requiring referrals, team structure, entry fee, passive income from recruits",
            "guaranteed_income": "unrealistic guaranteed income scheme, risk free fast money, effortless earnings promises",
            "referral": "aggressive referral link promotion, promo code, direct message call to join a money scheme",
            "investment_scam": "investment scam, crypto pump, forex signal, guaranteed investment returns, trust management",
        }
        self.neutral_text_labels = [
            "legitimate financial education about budgeting, saving, debt, investing, and risk management",
            "neutral personal finance news or market commentary without guaranteed returns",
            "ordinary unrelated social media content",
            "consumer advice warning people about scams",
        ]

    def load_models(self):
        if self.is_loaded:
            return
            
        print("Loading Scam/Gambling Detection ML models. This may take a while...")
        device = 0 if torch.cuda.is_available() else -1
        
        # 1. Zero-shot Multilingual Text Classification
        self.text_classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli", device=device)
        
        # 2. Whisper for Audio Transcription (tiny to save memory)
        whisper_device = "cuda" if torch.cuda.is_available() else "cpu"
        self.whisper_model = whisper.load_model("tiny", device=whisper_device)
        
        # 3. Zero-shot CLIP for video frames
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        if device == 0:
            self.clip_model = self.clip_model.to("cuda")
            
        self.is_loaded = True
        print("Scam Detection Models loaded successfully.")

    def download_video(self, url, output_path):
        def reject_oversized_or_long(info, *, incomplete):
            filesize = info.get("filesize") or info.get("filesize_approx")
            duration = info.get("duration")
            if filesize and filesize > MAX_VIDEO_BYTES:
                return f"Video is larger than {MAX_VIDEO_BYTES} bytes"
            if duration and duration > MAX_VIDEO_DURATION_SECONDS:
                return f"Video is longer than {MAX_VIDEO_DURATION_SECONDS} seconds"
            return None

        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'max_filesize': MAX_VIDEO_BYTES,
            'match_filter': reject_oversized_or_long,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def download_image(self, url, max_bytes=5 * 1024 * 1024):
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, stream=True)
        response.raise_for_status()
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > max_bytes:
                raise ValueError("Image URL is too large")
        return Image.open(io.BytesIO(content)).convert("RGB")

    def extract_frames(self, video_path, num_frames=3):
        frames = []
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > 0:
            step = max(total_frames // num_frames, 1)
            for i in range(num_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i * step)
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(Image.fromarray(frame_rgb))
        cap.release()
        return frames

    def transcribe_audio(self, video_path):
        try:
            result = self.whisper_model.transcribe(video_path)
            return result["text"]
        except Exception as e:
            print(f"Error transcribing: {e}")
            return ""

    def _lexical_evidence(self, text: str) -> dict:
        text_l = text.lower()
        patterns = {
            "casino": [
                r"\bcasino\b", r"\bказино\b", r"\bказиноға\b", r"\bслот", r"\bslots?\b",
                r"\baviator\b", r"\bавиатор\b", r"\bфриспин", r"\bставк", r"\bбукмекер",
            ],
            "pyramid": [
                r"\bпирами", r"\bmlm\b", r"\bмлм\b", r"\bреферал", r"\bструктур",
                r"\bкоманд[ау]", r"\bнаставник", r"\bвступительн", r"\bжелілік маркетинг",
            ],
            "guaranteed_income": [
                r"\bгарантир", r"\bкепіл", r"\bбез риск", r"\brisk[- ]?free\b", r"\bпассивн",
                r"\bтабыс\b", r"\bдоход\b", r"\bақша таб", r"\bза неделю\b", r"\bза день\b",
            ],
            "referral": [
                r"\bссылка\b", r"\blink\b", r"\bпромокод\b", r"\bpromo\b", r"\bдирект\b",
                r"\bжми\b", r"\bпиши\b", r"\bтіркел", r"\bregister\b",
            ],
            "investment_scam": [
                r"\bкрипт", r"\bcrypto\b", r"\bforex\b", r"\bфорекс\b", r"\bпамп\b",
                r"\bсигнал", r"\bикс", r"\bx100\b", r"\bлистинг", r"\bинвестици",
            ],
        }
        evidence = {}
        for category, regexes in patterns.items():
            hits = sum(1 for pattern in regexes if re.search(pattern, text_l))
            evidence[category] = min(0.20, hits * 0.05)
        return evidence

    def _classify_text_scores(self, text: str) -> dict:
        labels = list(self.text_category_labels.values()) + self.neutral_text_labels
        result = self.text_classifier(text, labels, multi_label=False)
        label_scores = {label: float(score) for label, score in zip(result["labels"], result["scores"])}
        neutral_score = max(label_scores.get(label, 0.0) for label in self.neutral_text_labels)
        lexical = self._lexical_evidence(text)

        scores = {}
        for category, label in self.text_category_labels.items():
            model_score = label_scores.get(label, 0.0)
            dampened = model_score * max(0.0, 1.0 - (neutral_score * 0.85))
            scores[category] = max(0.0, min(1.0, dampened + lexical.get(category, 0.0)))
        return scores

    def classify_content(self, text=None, image=None, url=None) -> dict:
        if not self.is_loaded:
            self.load_models()
            
        scores = {
            "casino": 0.0,
            "pyramid": 0.0,
            "guaranteed_income": 0.0,
            "referral": 0.0,
            "investment_scam": 0.0
        }
        
        transcription = ""
        frames = []
        
        if url:
            try:
                if re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", url, re.IGNORECASE):
                    frames = [self.download_image(url)]
                else:
                    # Download and extract
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
                        video_path = tmp_file.name
                    self.download_video(url, video_path)
                    transcription = self.transcribe_audio(video_path)
                    frames = self.extract_frames(video_path)
                    os.remove(video_path)
                    text = transcription if not text else text + "\n" + transcription
            except Exception as e:
                print(f"Failed to process URL: {e}")
                
        if image and not frames:
            frames = [image]
            
        # Analyze Text
        if text and text.strip():
            text_scores = self._classify_text_scores(text)
            for category, score in text_scores.items():
                scores[category] = max(scores[category], score)
                
        # Analyze Frames
        if frames:
            all_image_phrases = []
            image_phrase_to_category = {}
            for category, phrases in self.image_classes.items():
                for phrase in phrases:
                    if phrase not in image_phrase_to_category:
                        all_image_phrases.append(phrase)
                        image_phrase_to_category[phrase] = category
            all_image_phrases.extend(self.neutral_image_classes)

            inputs = self.clip_processor(
                text=all_image_phrases,
                images=frames,
                return_tensors="pt",
                padding=True
            )
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            outputs = self.clip_model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1).cpu().detach().numpy()
            max_probs = probs.max(axis=0)
            neutral_start = len(image_phrase_to_category)
            neutral_score = float(max(max_probs[neutral_start:])) if len(max_probs) > neutral_start else 0.0

            for i, phrase in enumerate(all_image_phrases):
                if phrase not in image_phrase_to_category:
                    continue
                category = image_phrase_to_category[phrase]
                scam_score = float(max_probs[i]) * max(0.0, 1.0 - (neutral_score * 0.75))
                scores[category] = max(scores[category], scam_score)
            
        return {
            "scores": scores,
            "transcription": transcription
        }
