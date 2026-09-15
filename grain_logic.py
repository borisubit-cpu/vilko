import json
import os
import copy
import time
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class BrewLog:
    """Журнал варок"""
    def __init__(self, filename="brew_log.json"):
        self.filename = filename
        self.entries = self._load()

    def _load(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def add_entry(self, recipe_name, grain_bill, og=None, fg=None, yield_ml=None, notes=""):
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "recipe": recipe_name,
            "grain_bill": grain_bill,
            "original_gravity": og,
            "final_gravity": fg,
            "alcohol_yield_ml": yield_ml,
            "notes": notes,
            "rating": None,
            "fermentation_start": None,
            "fermentation_end": None
        }
        self.entries.append(entry)
        self._save()
        return len(self.entries) - 1

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)

    def get_statistics(self):
        total = len(self.entries)
        if total == 0:
            return {"total_brews": 0, "avg_yield": 0, "last_brew": None}
        yields = [e['alcohol_yield_ml'] for e in self.entries if e['alcohol_yield_ml'] is not None]
        avg = sum(yields) / len(yields) if yields else 0
        return {"total_brews": total, "avg_yield": avg, "last_brew": self.entries[-1]['date']}

    def search_by_recipe(self, recipe_name):
        return [e for e in self.entries if recipe_name.lower() in e['recipe'].lower()]

    def get_last_entries(self, count=5):
        return self.entries[-count:][::-1]

    def get_entry(self, index):
        if 0 <= index < len(self.entries):
            return self.entries[index]
        return None

    def update_entry(self, index, field, value):
        if 0 <= index < len(self.entries):
            self.entries[index][field] = value
            self.entries[index]['modified'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._save()
            return True
        return False

    def add_notes(self, index, notes):
        return self.update_entry(index, 'notes', notes)

    def set_rating(self, index, rating):
        if 1 <= rating <= 5:
            return self.update_entry(index, 'rating', rating)
        return False

    def set_fermentation_start(self, index, dt):
        return self.update_entry(index, 'fermentation_start', dt)

    def set_fermentation_end(self, index, dt):
        return self.update_entry(index, 'fermentation_end', dt)

    def delete_entry(self, index):
        if 0 <= index < len(self.entries):
            del self.entries[index]
            self._save()
            return True
        return False

    def clear_entries(self):
        self.entries = []
        self._save()

    def get_recipe_stats(self):
        stats = {}
        for e in self.entries:
            name = e['recipe']
            if name not in stats:
                stats[name] = {'count': 0, 'total_yield': 0, 'total_rating': 0, 'rating_count': 0}
            stats[name]['count'] += 1
            if e.get('alcohol_yield_ml') is not None:
                stats[name]['total_yield'] += e['alcohol_yield_ml']
            if e.get('rating') is not None:
                stats[name]['total_rating'] += e['rating']
                stats[name]['rating_count'] += 1
        result = []
        for name, d in stats.items():
            result.append({
                'recipe': name,
                'count': d['count'],
                'avg_yield': d['total_yield'] / d['count'] if d['count'] > 0 else 0,
                'avg_rating': d['total_rating'] / d['rating_count'] if d['rating_count'] > 0 else 0
            })
        return result

    def get_rating_distribution(self):
        dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for e in self.entries:
            if e.get('rating') is not None:
                dist[e['rating']] = dist.get(e['rating'], 0) + 1
        return dist

    def get_monthly_stats(self):
        months = {}
        for e in self.entries:
            m = e['date'][:7]
            months[m] = months.get(m, 0) + 1
        return months

    def check_fermentation_notifications(self):
        notes = []
        now = datetime.now()
        for idx, e in enumerate(self.entries):
            s = e.get('fermentation_end')
            if s:
                try:
                    t = datetime.strptime(s, "%Y-%m-%d %H:%M")
                    if t <= now:
                        notes.append((idx, e['recipe'], s))
                except ValueError:
                    pass
        return notes


class VirtualAssistant:
    """Локальный виртуальный помощник"""
    def __init__(self, filename="assistant_knowledge.json"):
        self.filename = filename
        self.knowledge = self._load()
        if not self.knowledge:
            self.knowledge = self._default_knowledge()
            self._save()

    def _load(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, ensure_ascii=False, indent=2)

    def _default_knowledge(self):
        return [
            {"ключевые_слова": ["брага", "не бродит", "не забродила"],
             "ответ": "Если брага не бродит:\n1. Проверьте температуру (20-30°C).\n2. Убедитесь, что дрожжи живые.\n3. Возможно, сусло слишком кислое.\n4. Проверьте герметичность гидрозатвора."},
            {"ключевые_слова": ["головы", "отбор голов", "первак"],
             "ответ": "Головы отбираются при второй перегонке — 5-10% от абсолютного спирта. Медленно, 2-3 капли в секунду."},
            {"ключевые_слова": ["хвосты", "отбор хвостов"],
             "ответ": "Хвосты отбирают, когда крепость в струе падает ниже 40-45%. Их можно добавлять в следующую первую перегонку."},
            {"ключевые_слова": ["осахаривание", "ферменты", "амилосубтилин", "глюкаваморин"],
             "ответ": "Амилосубтилин — при 70-80°C, Глюкаваморин — при 60-65°C. Постоянно перемешивайте."},
            {"ключевые_слова": ["гидромодуль", "сколько воды"],
             "ответ": "Гидромодуль 1:3 или 1:4. Больше воды — легче брага, но ниже выход за перегон."},
            {"ключевые_слова": ["дрожжи", "какие дрожжи"],
             "ответ": "Спиртовые или винные дрожжи. Норма 0,4-0,6 г на 1 л затора."},
            {"ключевые_слова": ["температура", "оптимальная температура"],
             "ответ": "Спиртовые: 20-30°C. Винные: 15-25°C. Турбо: 20-35°C."}
        ]

    def ask(self, question: str):
        q = question.lower()
        best, score_best = None, 0
        for entry in self.knowledge:
            score = sum(1 for kw in entry["ключевые_слова"] if kw.lower() in q)
            if score > score_best:
                score_best, best = score, entry
        return best["ответ"] if best else None


class YeastDatabase:
    """База дрожжей"""
    def __init__(self, filename="yeast_database.json"):
        self.filename = filename
        self.yeasts = self._load()
        if not self.yeasts:
            self.yeasts = self._default_yeasts()
            self._save()

    def _load(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.yeasts, f, ensure_ascii=False, indent=2)

    def _default_yeasts(self):
        return [
            {"название": "SafSpirit USW-6", "тип": "спиртовые", "темп_мин": 12, "темп_макс": 35,
             "алко_толерантность": 18, "описание": "Универсальные для зерновых.",
             "рекомендации": ["пшеница", "рожь", "кукуруза"], "рейтинг": 4.5},
            {"название": "Turbo Yeast 48", "тип": "турбо", "темп_мин": 20, "темп_макс": 35,
             "алко_толерантность": 20, "описание": "Быстрое брожение.",
             "рекомендации": ["кукуруза", "пшеница"], "рейтинг": 4.0},
            {"название": "Lalvin EC-1118", "тип": "винные", "темп_мин": 10, "темп_макс": 30,
             "алко_толерантность": 18, "описание": "Для виски и фруктовых браг.",
             "рекомендации": ["ячмень", "солод"], "рейтинг": 4.7},
            {"название": "SafSpirit M-1", "тип": "виски", "темп_мин": 15, "темп_макс": 30,
             "алко_толерантность": 15, "описание": "Специализированные для виски.",
             "рекомендации": ["ячмень", "рожь", "пшеница"], "рейтинг": 4.8},
            {"название": "Safale S-04", "тип": "пивные", "темп_мин": 15, "темп_макс": 24,
             "алко_толерантность": 10, "описание": "Английские элевые.",
             "рекомендации": ["пшеница", "ячмень"], "рейтинг": 4.2}
        ]

    def search(self, query):
        q = query.lower()
        return [y for y in self.yeasts if q in y['название'].lower() or q in y['тип'].lower()
                or any(q in r.lower() for r in y.get('рекомендации', []))]

    def get_all(self):
        return self.yeasts


class GrainDistillingApp:
    """Справочник по зерновому самогоноварению"""

    def __init__(self):
        self.grain_base = self._load_json_or_default('grains.json', self._default_grain_data)
        self.recipes = self._load_json_or_default('recipes.json', self._default_recipes)
        self.custom_recipes = self._load_custom_recipes()
        self.brew_log = BrewLog()
        self.yeast_db = YeastDatabase()
        self.assistant = VirtualAssistant()
        self.current_plan = []

    def _default_grain_data(self):
        return {
            "пшеница": {"крахмал": 65, "выход_спирта": 0.44, "вкус": "Мягкий, хлебный",
                        "особенности": "Классика для водки", "совместимость": ["ячмень", "рожь", "кукуруза"]},
            "ячмень": {"крахмал": 60, "выход_спирта": 0.40, "вкус": "Сладковатый, виски",
                       "особенности": "Основа для виски", "совместимость": ["пшеница", "рожь", "овёс"]},
            "рожь": {"крахмал": 55, "выход_спирта": 0.37, "вкус": "Пряный, острый",
                     "особенности": "Ржаной аромат", "совместимость": ["пшеница", "ячмень"]},
            "кукуруза": {"крахмал": 70, "выход_спирта": 0.47, "вкус": "Сладкий, бурбон",
                         "особенности": "Высокий выход", "совместимость": ["ячмень", "рожь", "пшеница"]},
            "овёс": {"крахмал": 50, "выход_спирта": 0.34, "вкус": "Мягкий, ореховый",
                     "особенности": "Добавляет мягкость", "совместимость": ["ячмень", "пшеница"]},
            "гречка": {"крахмал": 55, "выход_спирта": 0.37, "вкус": "Ореховый",
                       "особенности": "Экзотика", "совместимость": ["пшеница"]}
        }

        def _default_recipes(self):
        return {
            "classic": [
                {
                    "название": "Пшеничная водка (мягкая)",
                    "зерно": {"пшеница": 25},
                    "гидромодуль": "1:4",
                    "дрожжи": "спиртовые",
                    "температура": 25,
                    "время_брожения": "5-7 дней",
                    "описание": "Классическая пшеничная водка с мягким хлебным вкусом.",
                    "сложность": "средняя",
                    "выход": "11 л АС",
                    "ферменты": {"Амилосубтилин": 25, "Глюкаваморин": 35, "Протосубтилин": 10},
                    "паузы": [
                        "Залить зерно кипятком, довести до 80°C, внести Амилосубтилин, выдержать 1 час.",
                        "Охладить до 65°C, внести Глюкаваморин и Протосубтилин, пауза 2 часа."
                    ],
                    "перегон": "Двойной. Первый до 0% в струе, второй дробный.",
                    "настаивание": "Отдых 2-3 недели в стекле.",
                    "примечания": "Щепа не нужна."
                },
                {
                    "название": "Ржаная водка (Полугар)",
                    "зерно": {"рожь": 22},
                    "гидромодуль": "1:4.5",
                    "дрожжи": "спиртовые",
                    "температура": 25,
                    "время_брожения": "6-8 дней",
                    "описание": "Традиционная ржаная водка с ярким хлебным ароматом.",
                    "сложность": "высокая",
                    "выход": "8.1 л АС",
                    "ферменты": {"Амилосубтилин": 30, "Глюкаваморин": 40, "Протосубтилин": 15},
                    "паузы": ["80°C -> Амилосубтилин, 1 час.", "63°C -> Глюкаваморин и Протосубтилин, 2.5 часа."],
                    "перегон": "Тройной или тщательный двойной дробный.",
                    "настаивание": "Разбавить до 45%, добавить корочку ржаного хлеба на 3 дня.",
                    "примечания": "Пеногаситель обязателен."
                },
                {
                    "название": "Рисовая водка (лёгкая)",
                    "зерно": {"рис": 28},
                    "гидромодуль": "1:3.6",
                    "дрожжи": "винные",
                    "температура": 22,
                    "время_брожения": "10-12 дней",
                    "описание": "Лёгкий дистиллят в стиле саке.",
                    "сложность": "высокая",
                    "выход": "12.6 л АС",
                    "ферменты": {"Амилосубтилин": 35, "Глюкаваморин": 45, "Протосубтилин": 15},
                    "паузы": ["Залить кипятком (90°C), внести Амилосубтилин, 1.5 часа.", "Охладить до 62°C, внести Глюкаваморин и Протосубтилин, 3 часа."],
                    "перегон": "Двойной.",
                    "настаивание": "Фильтрация через кокосовый уголь, отдых 2 недели.",
                    "примечания": "Рис сильно густеет."
                },
                {
                    "название": "Овсяная водка (кремовая)",
                    "зерно": {"овёс": 20},
                    "гидромодуль": "1:5",
                    "дрожжи": "спиртовые",
                    "температура": 24,
                    "время_брожения": "7 дней",
                    "описание": "Мягкая водка с кремовой текстурой.",
                    "сложность": "средняя",
                    "выход": "6.8 л АС",
                    "ферменты": {"Амилосубтилин": 25, "Глюкаваморин": 30, "Протосубтилин": 20},
                    "паузы": ["80°C -> Амилосубтилин, 1 час.", "65°C -> Глюкаваморин и Протосубтилин, 3 часа."],
                    "перегон": "Двойной на пару.",
                    "настаивание": "Без щепы, отдых 3 недели.",
                    "примечания": "Овёс пригорает."
                }
            ],
            "whiskey": [
                {
                    "название": "Односолодовый виски (Single Malt)",
                    "зерно": {"ячменный_солод": 30},
                    "гидромодуль": "1:3.3",
                    "дрожжи": "винные",
                    "температура": 20,
                    "время_брожения": "7-10 дней",
                    "описание": "Классический солодовый виски.",
                    "сложность": "высокая",
                    "выход": "12 л АС",
                    "ферменты": {"Амилосубтилин": 20, "Глюкаваморин": 30, "Протосубтилин": 10},
                    "паузы": ["Нагреть до 65-67°C, внести все ферменты, 2-3 часа."],
                    "перегон": "Двойной, отбор сердца до 65-70%.",
                    "настаивание": "Дубовая щепа среднего обжига 2-3 г/л, 4-6 мес.",
                    "примечания": "Дрожжи SafSpirit M-1."
                },
                {
                    "название": "Бурбон классический",
                    "зерно": {"кукуруза": 28, "ячменный_солод": 7},
                    "гидромодуль": "1:2.9",
                    "дрожжи": "спиртовые (для бурбона)",
                    "температура": 28,
                    "время_брожения": "5 дней",
                    "описание": "Американский бурбон с кукурузной сладостью.",
                    "сложность": "средняя",
                    "выход": "15.9 л АС",
                    "ферменты": {"Амилосубтилин": 35, "Глюкаваморин": 45, "Протосубтилин": 20},
                    "паузы": ["Кукуруза в кипяток (100°C), Амилосубтилин, 1-2 часа.", "Охладить до 65°C, солод + Г, П, 2 часа."],
                    "перегон": "Двойной.",
                    "настаивание": "Американский дуб сильного обжига 3-4 г/л, 3 мес.",
                    "примечания": "Дрожжи turbo whisky."
                },
                {
                    "название": "Ржаной виски (Spicy Rye)",
                    "зерно": {"рожь": 25, "пшеница": 5},
                    "гидромодуль": "1:3.3",
                    "дрожжи": "спиртовые",
                    "температура": 25,
                    "время_брожения": "7 дней",
                    "описание": "Острый, пряный виски.",
                    "сложность": "высокая",
                    "выход": "11.45 л АС",
                    "ферменты": {"Амилосубтилин": 30, "Глюкаваморин": 40, "Протосубтилин": 15},
                    "паузы": ["80°C -> Амилосубтилин, 1 час.", "64°C -> Глюкаваморин и Протосубтилин, 2.5 часа."],
                    "перегон": "Двойной, куб на 70%.",
                    "настаивание": "Дуб сильного/среднего обжига 2 г/л, от 5 мес.",
                    "примечания": "Пеногаситель обязателен."
                },
                {
                    "название": "Пшеничный виски (Wheated)",
                    "зерно": {"пшеница": 22, "ячменный_солод": 5, "овёс": 3},
                    "гидромодуль": "1:3.3",
                    "дрожжи": "пивные (Safale S-04)",
                    "температура": 22,
                    "время_брожения": "8 дней",
                    "описание": "Мягкий, сладковатый виски.",
                    "сложность": "средняя",
                    "выход": "12.7 л АС",
                    "ферменты": {"Амилосубтилин": 25, "Глюкаваморин": 35, "Протосубтилин": 10},
                    "паузы": ["78°C -> Амилосубтилин, 1 час.", "64°C -> Глюкаваморин и Протосубтилин, 2.5 часа."],
                    "перегон": "Двойной.",
                    "настаивание": "Карамелизированная щепа 2 г/л, 4 мес.",
                    "примечания": "Пивные элевые дрожжи."
                },
                {
                    "название": "Белый дог (White Dog)",
                    "зерно": {"кукуруза": 28, "ячменный_солод": 7},
                    "гидромодуль": "1:2.9",
                    "дрожжи": "спиртовые (для бурбона)",
                    "температура": 28,
                    "время_брожения": "5 дней",
                    "описание": "Невыдержанный бурбон.",
                    "сложность": "средняя",
                    "выход": "15.9 л АС",
                    "ферменты": {"Амилосубтилин": 35, "Глюкаваморин": 45, "Протосубтилин": 20},
                    "паузы": ["Кукуруза + Амилосубтилин, 1-2 часа.", "65°C + солод + Г, П, 2 часа."],
                    "перегон": "Двойной.",
                    "настаивание": "Разбавить до 45%, отдых 2 недели.",
                    "примечания": "Без щепы."
                },
                {
                    "название": "Виски из пивного сусла (экспресс)",
                    "зерно": {"концентрат_сусла": 16, "декстроза": 10},
                    "гидромодуль": "1:0",
                    "дрожжи": "SafSpirit M-1",
                    "температура": 25,
                    "время_брожения": "3-4 дня",
                    "описание": "Быстрый вариант пивного виски.",
                    "сложность": "лёгкая",
                    "выход": "10 л АС",
                    "ферменты": {"Глюкаваморин": 30},
                    "паузы": ["Растворить в 100 л воды, 30°C.", "Внести Глюкаваморин."],
                    "перегон": "Двойной.",
                    "настаивание": "Дубовая щепа 2 г/л, 3 мес.",
                    "примечания": "Быстро, но менее глубокий вкус."
                }
            ],
            "gourmet": [
                {
                    "название": "Кукурузно-рисовый бурбон «Азиатский мотив»",
                    "зерно": {"кукуруза": 20, "рис": 10},
                    "гидромодуль": "1:3.3",
                    "дрожжи": "спиртовые",
                    "температура": 27,
                    "время_брожения": "5-6 дней",
                    "описание": "Экзотический гибрид.",
                    "сложность": "высокая",
                    "выход": "13.9 л АС",
                    "ферменты": {"Амилосубтилин": 35, "Глюкаваморин": 50, "Протосубтилин": 20},
                    "паузы": ["Кукуруза + Амилосубтилин, 100°C, 1.5 часа.", "65°C + рис + Г, П, 2 часа."],
                    "перегон": "Двойной.",
                    "настаивание": "Дуб сильный + стружка кокоса (1:1), 3 г/л, 4 мес.",
                    "примечания": "Рис даёт гладкость."
                },
                {
                    "название": "Полбяной дистиллят (спельта)",
                    "зерно": {"полба": 25},
                    "гидромодуль": "1:4",
                    "дрожжи": "винные (совиньон)",
                    "температура": 22,
                    "время_брожения": "7-8 дней",
                    "описание": "Ореховый, дикий, сложный аромат.",
                    "сложность": "средняя",
                    "выход": "10 л АС",
                    "ферменты": {"Амилосубтилин": 25, "Глюкаваморин": 35, "Протосубтилин": 10},
                    "паузы": ["75°C -> Амилосубтилин, 1 час.", "63°C -> Глюкаваморин и Протосубтилин, 3 часа."],
                    "перегон": "Двойной.",
                    "настаивание": "Дуб слабого обжига 1.5 г/л, 3 мес.",
                    "примечания": "Полба близка к пшенице."
                },
                {
                    "название": "Гречишный виски",
                    "зерно": {"гречка_зелёная": 22, "ячмень": 5},
                    "гидромодуль": "1:3.7",
                    "дрожжи": "спиртовые",
                    "температура": 26,
                    "время_брожения": "6 дней",
                    "описание": "Травянистый, терпкий.",
                    "сложность": "высокая",
                    "выход": "10.1 л АС",
                    "ферменты": {"Амилосубтилин": 30, "Глюкаваморин": 40, "Протосубтилин": 20},
                    "паузы": ["80°C -> Амилосубтилин, 1 час.", "64°C -> Глюкаваморин и Протосубтилин, 2 часа."],
                    "перегон": "Двойной, медленный нагрев.",
                    "настаивание": "Дуб средний 3 г/л, 5 мес.",
                    "примечания": "Обязателен пеногаситель."
                },
                {
                    "название": "Солодовый виски с хересными нотами",
                    "зерно": {"солод_торфяной": 10, "солод_пшеничный": 20},
                    "гидромодуль": "1:3.3",
                    "дрожжи": "SafSpirit M-1",
                    "температура": 22,
                    "время_брожения": "5-7 дней",
                    "описание": "Сложный аромат с хересом.",
                    "сложность": "высокая",
                    "выход": "12 л АС",
                    "ферменты": {"Амилосубтилин": 20, "Глюкаваморин": 30},
                    "паузы": ["Осахаривание 65°C, 2-3 часа."],
                    "перегон": "Двойной.",
                    "настаивание": "Щепу 2 г/л вымочить в хересе 3 дня, добавить. 6-8 мес.",
                    "примечания": "Торфяной солод для дымка."
                },
                {
                    "название": "Амарантовый дистиллят (безглютеновый)",
                    "зерно": {"амарант": 15, "кукуруза": 15},
                    "гидромодуль": "1:3.3",
                    "дрожжи": "спиртовые",
                    "температура": 25,
                    "время_брожения": "6 дней",
                    "описание": "Землянистый вкус, без глютена.",
                    "сложность": "высокая",
                    "выход": "13.1 л АС",
                    "ферменты": {"Амилосубтилин": 30, "Глюкаваморин": 40, "Протосубтилин": 20},
                    "паузы": ["Кукуруза + Амилосубтилин, 100°C, 1 час.", "65°C + амарант + Г, П, 2.5 часа."],
                    "перегон": "Двойной.",
                    "настаивание": "Дуб слабый 1.5 г/л.",
                    "примечания": "Пенится, нужен пеногаситель."
                }
            ],
            "malt": [
                {
                    "название": "Классический зерновой на солоде (пшеница)",
                    "зерно": {"пшеница": 20, "ячменный_солод": 5},
                    "гидромодуль": "1:4",
                    "дрожжи": "спиртовые",
                    "температура": 24,
                    "время_брожения": "5-7 дней",
                    "описание": "Самый душистый хлебный дистиллят.",
                    "сложность": "высокая",
                    "выход": "10.8 л АС",
                    "ферменты": None,
                    "паузы": ["Пшеница 70-72°C, 30 мин.", "63-65°C + солод, 2 часа.", "72°C, 30 мин (йодная проба)."],
                    "перегон": "Двойной.",
                    "настаивание": "Отдых 2-3 недели.",
                    "примечания": "Солод — источник ферментов."
                },
                {
                    "название": "Ржаная на красном солоде («Бородинский»)",
                    "зерно": {"рожь": 18, "солод_ржаной_красный": 8},
                    "гидромодуль": "1:3.8",
                    "дрожжи": "спиртовые",
                    "температура": 25,
                    "время_брожения": "6 дней",
                    "описание": "Мощный аромат бородинского хлеба.",
                    "сложность": "высокая",
                    "выход": "9.9 л АС",
                    "ферменты": None,
                    "паузы": ["Смешать, 63°C, 2 часа.", "70°C, 1 час."],
                    "перегон": "Двойной, куб на 70%.",
                    "настаивание": "Дуб средний 2 г/л, 6 мес.",
                    "примечания": "Ферментированный красный солод."
                },
                {
                    "название": "Виски шотландский (торфяной)",
                    "зерно": {"солод_торфяной": 27},
                    "гидромодуль": "1:3.7",
                    "дрожжи": "SafSpirit M-1",
                    "температура": 20,
                    "время_брожения": "3-5 дней",
                    "описание": "Дымный аромат Шотландии.",
                    "сложность": "высокая",
                    "выход": "10.8 л АС",
                    "ферменты": None,
                    "паузы": ["64°C - 1 час, 72°C - 30 мин."],
                    "перегон": "Двойной.",
                    "настаивание": "Дуб средний 2 г/л, от 8 мес.",
                    "примечания": "Только торфяной солод."
                },
                {
                    "название": "Виски ирландский (тройная перегонка)",
                    "зерно": {"ячмень": 15, "ячменный_солод": 15},
                    "гидромодуль": "1:3.3",
                    "дрожжи": "пивные (элевые)",
                    "температура": 22,
                    "время_брожения": "5 дней",
                    "описание": "Супергладкий виски.",
                    "сложность": "высокая",
                    "выход": "12 л АС",
                    "ферменты": None,
                    "паузы": ["Осахаривание 65°C, 2 часа."],
                    "перегон": "Тройной. Сердце 60-65%.",
                    "настаивание": "Щепа из-под бурбона 2 г/л, 6 мес.",
                    "примечания": "Непросоложенный ячмень."
                },
                {
                    "название": "«Гурман-солод» (пять злаков)",
                    "зерно": {"кукуруза": 15, "пшеница": 5, "рожь": 5, "овёс": 3, "ячменный_солод": 7},
                    "гидромодуль": "1:2.9",
                    "дрожжи": "спиртовые",
                    "температура": 25,
                    "время_брожения": "6 дней",
                    "описание": "Сложный букет из пяти злаков.",
                    "сложность": "высокая",
                    "выход": "16.1 л АС",
                    "ферменты": None,
                    "паузы": ["Кукуруза отдельно, 100°C, + 15 г А.", "Смешать при 65°C.", "Солод + 2 часа."],
                    "перегон": "Двойной.",
                    "настаивание": "1 г/л дуба + 1 г/л бурбонового дуба, 5 мес.",
                    "примечания": "Идеален для экспериментов."
                }
            ]
        }

    def _load_json_or_default(self, filename, default_func):
        path = os.path.join(os.getcwd(), filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        data = default_func()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
        return data

    def _load_custom_recipes(self):
        path = os.path.join(os.getcwd(), 'custom_recipes.json')
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def _save_custom_recipes(self):
        with open('custom_recipes.json', 'w', encoding='utf-8') as f:
            json.dump(self.custom_recipes, f, ensure_ascii=False, indent=2)

    def calculate_water_volume(self, recipe):
        try:
            total = sum(recipe['зерно'].values())
            ratio = float(recipe['гидромодуль'].split(':')[1])
            return total * ratio
        except:
            return 0.0

    def calculate_enzymes(self, grain_bill):
        norms = {'Амилосубтилин': 0.5, 'Глюкаваморин': 1.0, 'Протосубтилин': 0.2}
        total = sum(grain_bill.values())
        return {n: round(v * total, 1) for n, v in norms.items()}

    def calculate_yeast(self, water_volume, yeast_type):
        norms = {'спиртовые': 0.4, 'турбо': 0.6, 'винные': 0.5, 'пивные': 0.5,
                 'SafSpirit M-1': 0.5, 'SafSpirit USW-6': 0.5, 'пивные (Safale S-04)': 0.5,
                 'спиртовые (для бурбона)': 0.5, 'винные (совиньон)': 0.5, 'винные (красные)': 0.5}
        return round(water_volume * norms.get(yeast_type, 0.5), 1)

    def calculate_yield(self, grain_type, amount_kg):
        if grain_type in self.grain_base:
            return self.grain_base[grain_type]["выход_спирта"] * amount_kg
        return 0

    def calculate_hydromodule(self, grain_amount, ratio="1:4"):
        return grain_amount * float(ratio.split(":")[1])

    def calculate_dilution(self, current_abv, target_abv, volume):
        return max(0, (volume * current_abv / target_abv) - volume)

        # ==================== МЕТОДЫ ПРОСМОТРА ====================
    def show_recipes(self):
        print("\n📋 РЕЦЕПТЫ")
        print("-"*40)
        titles = {"classic": "🏛 КЛАССИЧЕСКИЕ ЗЕРНОВЫЕ", "whiskey": "🥃 ВИСКИ И БУРБОНЫ",
                  "gourmet": "🌍 ЗЕРНОВОЙ ГУРМАН", "malt": "🌾 СОЛОДОВЫЕ", "custom": "👤 ПОЛЬЗОВАТЕЛЬСКИЕ"}
        all_r = []
        for cat, recipes in self.recipes.items():
            for r in recipes:
                all_r.append((cat, r))
        for r in self.custom_recipes:
            all_r.append(("custom", r))
        for i, (cat, r) in enumerate(all_r, 1):
            print(f"{i:2d}. {r['название']}  [{titles.get(cat, cat)}]")
        print("\nВведите номер рецепта или 'д' для добавления своего, Enter — назад")
        choice = input("Выбор: ").strip()
        if choice.lower() == 'д':
            self.add_custom_recipe()
        elif choice:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(all_r):
                    self.show_recipe_details(all_r[idx][1])
                else:
                    print("❌ Неверный номер")
            except ValueError:
                print("❌ Введите число")

    def show_recipe_details(self, recipe):
        print("\n" + "="*60)
        print(f"📜 {recipe['название']}")
        print("="*60)
        print(f"Описание: {recipe['описание']}")
        print(f"Сложность: {recipe['сложность']}")
        print(f"Выход: {recipe['выход']}")
        print(f"\nЗерновой состав:")
        for g, a in recipe['зерно'].items():
            print(f"  - {g}: {a} кг")
        print(f"Гидромодуль: {recipe['гидромодуль']}")
        print(f"Дрожжи: {recipe['дрожжи']}")
        print(f"Температура: {recipe['температура']}°C")
        print(f"Время брожения: {recipe['время_брожения']}")
        if recipe.get('ферменты'):
            print("\nФерменты:")
            for e, a in recipe['ферменты'].items():
                print(f"  - {e}: {a} г")
        if recipe.get('паузы'):
            print("\nПаузы:")
            for i, p in enumerate(recipe['паузы'], 1):
                print(f"  {i}. {p}")
        if recipe.get('перегон'):
            print(f"\nПерегон: {recipe['перегон']}")
        if recipe.get('настаивание'):
            print(f"Настаивание: {recipe['настаивание']}")
        if recipe.get('примечания'):
            print(f"Примечания: {recipe['примечания']}")

    def show_plan(self):
        print("\n🔧 ГЕНЕРАТОР ПЛАНА")
        all_r = []
        for cat in self.recipes.values():
            all_r.extend(cat)
        all_r.extend(self.custom_recipes)
        for i, r in enumerate(all_r, 1):
            print(f"{i}. {r['название']}")
        try:
            idx = int(input("\nВыберите рецепт: ")) - 1
            if not (0 <= idx < len(all_r)):
                print("❌ Неверный номер")
                return
            recipe = copy.deepcopy(all_r[idx])
            if input("Внести изменения? (да/нет): ").lower() == "да":
                recipe = self.edit_recipe_interactive(recipe)
            plan = self.generate_plan(recipe)
            print(f"\n📅 ПЛАН: {recipe['название']}")
            print("="*60)
            for s in plan:
                print(f"\nДень {s['день']} | {s['этап']}")
                print(f"⏰ {s['действие']}")
            if input("\nСохранить в файл? (да/нет): ").lower() == "да":
                fmt = input("Формат (json/html): ").lower()
                if fmt == "html":
                    fn = self.export_plan_to_html(plan, recipe['название'])
                    print(f"✅ Сохранено: {fn}")
                else:
                    with open(f"план_{recipe['название'].replace(' ', '_')}.json", "w", encoding="utf-8") as f:
                        json.dump(plan, f, ensure_ascii=False, indent=2)
                    print("✅ Сохранено в JSON")
            entry_idx = self.brew_log.add_entry(recipe['название'], recipe['зерно'].copy())
            print(f"\n📓 Запись #{entry_idx+1} создана в журнале")
            if input("Добавить заметку/рейтинг сейчас? (да/нет): ").lower() == "да":
                notes = input("Заметки: ").strip()
                if notes:
                    self.brew_log.add_notes(entry_idx, notes)
                r = input("Рейтинг 1-5 (Enter — пропустить): ").strip()
                if r:
                    try:
                        self.brew_log.set_rating(entry_idx, int(r))
                        print("✅ Рейтинг сохранён")
                    except ValueError:
                        print("Некорректный рейтинг")
        except ValueError:
            print("❌ Введите число")

    def show_calculators(self):
        print("\n🧮 КАЛЬКУЛЯТОРЫ")
        print("1. Выход спирта")
        print("2. Вода для затора")
        print("3. Разбавление")
        print("4. Отбор голов")
        ch = input("Выбор: ").strip()
        if ch == "1":
            for g, p in self.grain_base.items():
                print(f"  {g}: {p['выход_спирта']} л/кг")
            g = input("Зерно: ").lower()
            a = float(input("Кг: "))
            r = self.calculate_yield(g, a)
            print(f"\n✅ Выход: {r:.2f} л АС ({r*2.5:.2f} л 40%)" if r else "❌ Неизвестное зерно")
        elif ch == "2":
            a = float(input("Кг зерна: "))
            ratio = input("Гидромодуль (1:4): ")
            print(f"\n✅ Воды: {self.calculate_hydromodule(a, ratio):.1f} л")
        elif ch == "3":
            cur = float(input("Текущая крепость %: "))
            tgt = float(input("Желаемая %: "))
            vol = float(input("Объём л: "))
            w = self.calculate_dilution(cur, tgt, vol)
            print(f"\n✅ Добавить воды: {w:.2f} л (итого {vol+w:.2f} л)")
        elif ch == "4":
            self.calculate_heads()

    def calculate_heads(self):
        print("\n🍶 РАСЧЁТ ГОЛОВ")
        print("1. По АС\n2. По объёму и крепости")
        m = input("Выбор: ").strip()
        try:
            if m == "1":
                ac = float(input("АС (мл): "))
                p = float(input("% голов (10): ") or 10)
                print(f"\n✅ Голов: {ac*p/100:.0f} мл")
            elif m == "2":
                v = float(input("Объём (мл): "))
                s = float(input("Крепость %: "))
                p = float(input("% голов (10): ") or 10)
                ac = v*s/100
                print(f"\n✅ АС: {ac:.0f} мл, голов: {ac*p/100:.0f} мл")
        except ValueError:
            print("❌ Неверные числа")

    def start_timer(self):
        print("\n⏱ ТАЙМЕР")
        try:
            h = int(input("Часы: ") or 0)
            m = int(input("Минуты: ") or 0)
            s = int(input("Секунды: ") or 0)
            total = h*3600 + m*60 + s
            if total <= 0:
                print("❌ Нулевое время")
                return
            print(f"Таймер: {h}ч {m}м {s}с. Ctrl+C для отмены.")
            for rem in range(total, 0, -1):
                hh, r = divmod(rem, 3600)
                mm, ss = divmod(r, 60)
                print(f"\r⏳ {hh:02d}:{mm:02d}:{ss:02d}", end="", flush=True)
                time.sleep(1)
            print("\n" + "="*40)
            print("🔔 ВРЕМЯ ВЫШЛО! 🔔")
            print("="*40)
            print("\a")
        except ValueError:
            print("❌ Целые числа")
        except KeyboardInterrupt:
            print("\n⚠️ Отменено")

    def edit_recipe_interactive(self, recipe):
        print("\n✏️ РЕДАКТИРОВАНИЕ (Enter — оставить)")
        for g, a in recipe['зерно'].items():
            print(f"  {g}: {a} кг")
        if input("Изменить зерно? (да/нет): ").lower() == "да":
            ng = {}
            while True:
                g = input("Тип (готово — завершить): ").strip().lower()
                if g == "готово":
                    break
                if g:
                    ng[g] = float(input(f"Кг {g}: "))
            if ng:
                recipe['зерно'] = ng
                print(f"Воды: {self.calculate_water_volume(recipe)} л")
        h = input(f"Гидромодуль ({recipe['гидромодуль']}): ").strip()
        if h:
            recipe['гидромодуль'] = h
            print(f"Воды: {self.calculate_water_volume(recipe):.1f} л")
        y = input(f"Дрожжи ({recipe['дрожжи']}): ").strip()
        if y:
            recipe['дрожжи'] = y
        t = input(f"Температура ({recipe['температура']}): ").strip()
        if t:
            try:
                recipe['температура'] = float(t)
            except ValueError:
                pass
        tm = input(f"Время ({recipe['время_брожения']}): ").strip()
        if tm:
            recipe['время_брожения'] = tm
        wv = self.calculate_water_volume(recipe)
        if recipe.get('ферменты'):
            ez = self.calculate_enzymes(recipe['зерно'])
            print(f"\n🔬 Ферменты на {sum(recipe['зерно'].values())} кг:")
            for e, a in ez.items():
                print(f"  {e}: {a} г")
            if input("Применить? (да/нет): ").lower() == "да":
                recipe['ферменты'] = ez
        ya = self.calculate_yeast(wv, recipe['дрожжи'])
        print(f"🔬 Дрожжи: {ya} г на {wv:.1f} л")
        recipe['количество_дрожжей_г'] = ya
        return recipe

    def add_custom_recipe(self):
        print("\n➕ НОВЫЙ РЕЦЕПТ")
        r = {"название": input("Название: ").strip(), "зерно": {}}
        if not r['название']:
            print("❌ Название обязательно")
            return
        while True:
            g = input("Зерно (тип, Enter — завершить): ").strip().lower()
            if not g:
                break
            try:
                r['зерно'][g] = float(input(f"Кг {g}: "))
            except ValueError:
                pass
        if not r['зерно']:
            print("❌ Зерно обязательно")
            return
        r['гидромодуль'] = input("Гидромодуль (1:4): ").strip() or "1:4"
        r['дрожжи'] = input("Дрожжи: ").strip() or "спиртовые"
        try:
            r['температура'] = float(input("Температура (25): ") or 25)
        except ValueError:
            r['температура'] = 25
        r['время_брожения'] = input("Время (5-7 дней): ").strip() or "5-7 дней"
        r['описание'] = input("Описание: ").strip()
        r['сложность'] = input("Сложность: ").strip() or "средняя"
        r['выход'] = input("Выход: ").strip() or "неизвестно"
        if input("Использовать ферменты? (да/нет): ").lower() == "нет":
            r['ферменты'] = None
        else:
            r['ферменты'] = self.calculate_enzymes(r['зерно'])
        r['паузы'] = []
        r['перегон'] = ""
        r['настаивание'] = ""
        r['примечания'] = ""
        self.custom_recipes.append(r)
        self._save_custom_recipes()
        print(f"✅ Рецепт «{r['название']}» сохранён")

    def generate_plan(self, recipe):
        plan = []
        day = 1
        gs = ', '.join(f'{v} кг {k}' for k, v in recipe['зерно'].items())
        plan.append({"день": day, "этап": "Подготовка", "действие": f"Сырьё: {gs}", "время": "30 мин"})
        plan.append({"день": day, "этап": "Подготовка", "действие": "Промыть, замочить", "время": "4-6 ч"})
        plan.append({"день": day, "этап": "Подготовка", "действие": "Измельчить", "время": "1 ч"})
        wv = self.calculate_water_volume(recipe) or 100
        plan.append({"день": day+1, "этап": "Затирание", "действие": f"Нагреть {wv:.1f} л воды", "время": "30-40 мин"})
        plan.append({"день": day+1, "этап": "Затирание", "действие": "Внести зерно", "время": "15 мин"})
        for p in recipe.get("паузы", []):
            plan.append({"день": day+1, "этап": "Осахаривание", "действие": p, "время": "см. паузу"})
        try:
            df = int(recipe["время_брожения"].split("-")[-1].split()[0])
        except:
            df = 7
        ya = recipe.get('количество_дрожжей_г') or self.calculate_yeast(wv, recipe['дрожжи'])
        plan.append({"день": day+2, "этап": "Брожение", "действие": f"Охладить до {recipe['температура']}°C", "время": "1-2 ч"})
        plan.append({"день": day+2, "этап": "Брожение", "действие": f"Дрожжи: {recipe['дрожжи']} ({ya} г), гидрозатвор", "время": "30 мин"})
        plan.append({"день": f"{day+2}–{day+2+df}", "этап": "Брожение", "действие": f"При {recipe['температура']}°C", "время": recipe["время_брожения"]})
        plan.append({"день": day+2+df, "этап": "1-я перегонка", "действие": "До 0° в струе", "время": "3-4 ч"})
        plan.append({"день": day+3+df, "этап": "2-я перегонка", "действие": "Дробная, отбор голов 5-10%", "время": "4-5 ч"})
        plan.append({"день": day+4+df, "этап": "Финализация", "действие": "Разбавить, щепа, отдых", "время": "по рецепту"})
        self.current_plan = plan
        return plan

    def export_plan_to_html(self, plan, name):
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{name}</title>
<style>body{{font-family:Arial;margin:30px}}h1{{color:#2c3e50}}.s{{margin-bottom:15px;padding:10px;border-left:4px solid #3498db}}.d{{font-weight:bold;color:#e67e22}}</style>
</head><body><h1>План: {name}</h1>"""
        for s in plan:
            html += f'<div class="s"><div class="d">День {s["день"]} | {s["этап"]}</div><div>{s["действие"]}</div><div>⏰ {s["время"]}</div></div>'
        html += "</body></html>"
        fn = f"план_{name.replace(' ', '_')}.html"
        with open(fn, 'w', encoding='utf-8') as f:
            f.write(html)
        return fn

    def export_instruction_to_html(self):
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Инструкция</title></head>
<body><h1>Зерновой Мастер — инструкция</h1>{self.get_instruction_text()}</body></html>"""
        with open("инструкция.html", 'w', encoding='utf-8') as f:
            f.write(html)
        return "инструкция.html"

    def get_instruction_text(self):
        return """<h2>Разделы</h2>
<ul>
<li><b>Рецепты</b> — 20 встроенных + свои</li>
<li><b>Генератор плана</b> — пошаговый план с изменениями</li>
<li><b>Калькуляторы</b> — выход, вода, разбавление, головы</li>
<li><b>Журнал варок</b> — статистика, рейтинг, заметки</li>
<li><b>Таймеры</b> — с часами и минутами</li>
<li><b>База дрожжей</b> — характеристики</li>
<li><b>Виртуальная помощь</b> — вопросы/ответы</li>
<li><b>Ссылки</b> — форумы и Telegram</li>
</ul>
<p>⚠️ Соблюдайте законодательство вашей страны.</p>"""

    # ==================== БАЗА ДРОЖЖЕЙ ====================
    def show_yeast_database(self):
        while True:
            print("\n🍺 БАЗА ДРОЖЖЕЙ")
            print("1. Все\n2. Поиск\n0. Назад")
            c = input("Выбор: ")
            if c == "1":
                for y in self.yeast_db.get_all():
                    self._show_yeast(y)
                input("\nEnter...")
            elif c == "2":
                q = input("Поиск: ")
                res = self.yeast_db.search(q)
                if res:
                    for y in res:
                        self._show_yeast(y)
                else:
                    print("Ничего не найдено")
                input("\nEnter...")
            elif c == "0":
                break

    def _show_yeast(self, y):
        print(f"\n{y['название']} ({y['тип']})")
        print(f"  Темп: {y['темп_мин']}-{y['темп_макс']}°C")
        print(f"  Алкоголь: до {y['алко_толерантность']}%")
        print(f"  Рейтинг: {'⭐'*int(y.get('рейтинг', 0))} ({y.get('рейтинг', 0)})")
        print(f"  {y['описание']}")
        print(f"  Подходит: {', '.join(y['рекомендации'])}")

    # ==================== ПОМОЩНИК ====================
    def show_virtual_assistant(self):
        print("\n🤖 ВИРТУАЛЬНАЯ ПОМОЩЬ (выход — выход)")
        while True:
            q = input("\nВопрос: ").strip()
            if q.lower() in ['выход', 'exit', 'quit']:
                break
            if not q:
                continue
            ans = self.assistant.ask(q)
            print(f"\n💡 {ans}" if ans else "\n❓ Не знаю. Спросите про: брагу, головы, хвосты, осахаривание, гидромодуль, дрожжи, температуру.")

    def show_instruction(self):
        print("\n📘 ИНСТРУКЦИЯ")
        print(self.get_instruction_text())
        if input("\nСохранить в HTML? (да/нет): ").lower() == "да":
            print(f"✅ {self.export_instruction_to_html()}")

    def show_useful_links(self):
        links = [
            ("Мой Telegram-канал", "https://t.me/vilko_zerno"),
            ("Форум Самогонщики", "https://forum.homedistiller.ru/"),
            ("Форум АлкоФан", "https://alkofan.com/"),
            ("Форум Гоним с нами", "https://gonim-s-nami.ru/"),
            ("Самогонный аппарат", "https://samogonnyj-apparat.ru/forum/")
        ]
        while True:
            print("\n🔗 ПОЛЕЗНЫЕ ССЫЛКИ")
            for i, (n, u) in enumerate(links, 1):
                print(f"{i}. {n}")
            print("0. Назад")
            c = input("Выбор: ")
            if c == "0":
                break
            try:
                i = int(c) - 1
                if 0 <= i < len(links):
                    print(f"\nОткрываю: {links[i][1]}")
                    webbrowser.open(links[i][1])
                else:
                    print("❌ Неверный номер")
            except ValueError:
                print("❌ Введите число")

    # ==================== ЖУРНАЛ ====================
    def show_brew_menu(self):
        print("\n📓 ЖУРНАЛ ВАРОК")
        print("1. Добавить вручную\n2. Статистика\n3. Поиск\n4. Последние 5")
        print("5. Редактировать\n6. Расширенная статистика\n7. Удалить")
        print("8. Очистить всё\n9. Даты брожения\n10. Проверить брожение\n0. Назад")
        return input("Выбор: ")

    def log_brew_manually(self):
        print("\n📓 НОВАЯ ЗАПИСЬ")
        name = input("Рецепт: ")
        og = float(input("OG (Enter — пропустить): ") or 0) or None
        fg = float(input("FG: ") or 0) or None
        ym = float(input("Выход АС (мл): ") or 0) or None
        notes = input("Заметки: ")
        gb = {}
        while True:
            g = input("Зерно (тип, Enter — конец): ").strip().lower()
            if not g:
                break
            try:
                gb[g] = float(input(f"Кг {g}: "))
            except ValueError:
                pass
        idx = self.brew_log.add_entry(name, gb, og, fg, ym, notes)
        print(f"✅ Запись #{idx+1} добавлена")

    def show_brew_statistics(self):
        s = self.brew_log.get_statistics()
        print(f"\n📊 Всего варок: {s['total_brews']}")
        if s['total_brews'] > 0:
            print(f"Средний выход: {s['avg_yield']:.0f} мл")
            print(f"Последняя: {s['last_brew']}")

    def show_advanced_statistics(self):
        if not self.brew_log.entries:
            print("Журнал пуст")
            return
        print("\n📈 РАСШИРЕННАЯ СТАТИСТИКА")
        for s in self.brew_log.get_recipe_stats():
            print(f"\n{s['recipe']}: {s['count']} варок, ср.выход {s['avg_yield']:.0f} мл, ⭐ {s['avg_rating']:.1f}")
        print("\nРаспределение рейтингов:")
        for r, c in self.brew_log.get_rating_distribution().items():
            if c:
                print(f"  {r}★: {c}")
        print("\nПо месяцам:")
        for m, c in sorted(self.brew_log.get_monthly_stats().items()):
            print(f"  {m}: {c}")

    def search_brew_log(self):
        q = input("Поиск: ")
        res = self.brew_log.search_by_recipe(q)
        if res:
            for i, e in enumerate(res, 1):
                print(f"{i}. {e['date']} | {e['recipe']} | {e['alcohol_yield_ml']} мл")
                if e.get('notes'):
                    print(f"   📝 {e['notes']}")
                if e.get('rating'):
                    print(f"   {'⭐'*e['rating']}")
        else:
            print("❌ Не найдено")

    def show_last_brews(self):
        for i, e in enumerate(self.brew_log.get_last_entries(5), 1):
            print(f"{i}. {e['date']} | {e['recipe']} | {e['alcohol_yield_ml']} мл")
            if e.get('rating'):
                print(f"   {'⭐'*e['rating']}")

    def edit_brew_entry(self):
        if not self.brew_log.entries:
            print("Журнал пуст")
            return
        for i, e in enumerate(self.brew_log.entries, 1):
            print(f"{i}. {e['date']} | {e['recipe']}")
        try:
            idx = int(input("Номер: ")) - 1
            if not (0 <= idx < len(self.brew_log.entries)):
                print("❌ Неверный номер")
                return
            print("1. Заметки\n2. Рейтинг\n3. OG\n4. FG\n5. Выход\n6. Название\n7. Зерно")
            c = input("Что: ")
            if c == "1":
                self.brew_log.add_notes(idx, input("Новые заметки: "))
            elif c == "2":
                self.brew_log.set_rating(idx, int(input("Рейтинг 1-5: ")))
            elif c == "3":
                self.brew_log.update_entry(idx, 'original_gravity', float(input("OG: ")))
            elif c == "4":
                self.brew_log.update_entry(idx, 'final_gravity', float(input("FG: ")))
            elif c == "5":
                self.brew_log.update_entry(idx, 'alcohol_yield_ml', float(input("Выход: ")))
            elif c == "6":
                self.brew_log.update_entry(idx, 'recipe', input("Название: "))
            elif c == "7":
                ng = {}
                while True:
                    g = input("Тип (Enter — конец): ").strip().lower()
                    if not g:
                        break
                    ng[g] = float(input(f"Кг {g}: "))
                if ng:
                    self.brew_log.update_entry(idx, 'grain_bill', ng)
            print("✅ Обновлено")
        except ValueError:
            print("❌ Ошибка ввода")

    def delete_brew_entry(self):
        if not self.brew_log.entries:
            print("Журнал пуст")
            return
        for i, e in enumerate(self.brew_log.entries, 1):
            print(f"{i}. {e['date']} | {e['recipe']}")
        try:
            idx = int(input("Номер для удаления: ")) - 1
            if 0 <= idx < len(self.brew_log.entries):
                if input(f"Удалить «{self.brew_log.entries[idx]['recipe']}»? (да/нет): ").lower() == "да":
                    self.brew_log.delete_entry(idx)
                    print("✅ Удалено")
        except ValueError:
            print("❌ Ошибка")

    def clear_brew_log(self):
        if not self.brew_log.entries:
            print("Журнал пуст")
            return
        if input(f"Удалить все {len(self.brew_log.entries)} записей? (да/нет): ").lower() == "да":
            self.brew_log.clear_entries()
            print("✅ Журнал очищен")

    def set_fermentation_dates(self):
        if not self.brew_log.entries:
            print("Журнал пуст")
            return
        for i, e in enumerate(self.brew_log.entries, 1):
            print(f"{i}. {e['date']} | {e['recipe']}")
        try:
            idx = int(input("Номер: ")) - 1
            if 0 <= idx < len(self.brew_log.entries):
                s = input("Старт (ГГГГ-ММ-ДД ЧЧ:ММ, Enter — пропустить): ").strip()
                if s:
                    self.brew_log.set_fermentation_start(idx, s)
                e = input("Конец (ГГГГ-ММ-ДД ЧЧ:ММ): ").strip()
                if e:
                    self.brew_log.set_fermentation_end(idx, e)
                print("✅ Установлено")
        except ValueError:
            print("❌ Ошибка")

    def check_fermentation(self):
        ns = self.brew_log.check_fermentation_notifications()
        if ns:
            print("\n🔔 Завершено брожение:")
            for idx, name, dt in ns:
                print(f"  #{idx+1}: {name} ({dt})")
        else:
            print("\n✅ Нет завершённых")

    # ==================== ГЛАВНОЕ МЕНЮ ====================
    def show_menu(self):
        print("\n" + "="*60)
        print("🌾 ЗЕРНОВОЙ МАСТЕР")
        print("="*60)
        print("1. 📋 Рецепты")
        print("2. 🔧 Генератор плана")
        print("3. 🧮 Калькуляторы")
        print("4. 📓 Журнал варок")
        print("5. ⏱ Таймеры")
        print("6. 🍺 База дрожжей")
        print("7. 🤖 Виртуальная помощь")
        print("8. 📘 Инструкция")
        print("9. 🔗 Полезные ссылки")
        print("0. Выход")
        return input("\nРаздел: ")

    def run(self):
        print("Добро пожаловать!")
        print("⚠️ Соблюдайте законодательство вашей страны!\n")
        while True:
            c = self.show_menu()
            if c == "1":
                self.show_recipes()
            elif c == "2":
                self.show_plan()
            elif c == "3":
                self.show_calculators()
            elif c == "4":
                while True:
                    sc = self.show_brew_menu()
                    if sc == "1":
                        self.log_brew_manually()
                    elif sc == "2":
                        self.show_brew_statistics()
                    elif sc == "3":
                        self.search_brew_log()
                    elif sc == "4":
                        self.show_last_brews()
                    elif sc == "5":
                        self.edit_brew_entry()
                    elif sc == "6":
                        self.show_advanced_statistics()
                    elif sc == "7":
                        self.delete_brew_entry()
                    elif sc == "8":
                        self.clear_brew_log()
                    elif sc == "9":
                        self.set_fermentation_dates()
                    elif sc == "10":
                        self.check_fermentation()
                    elif sc == "0":
                        break
                    input("\nEnter...")
            elif c == "5":
                self.start_timer()
            elif c == "6":
                self.show_yeast_database()
            elif c == "7":
                self.show_virtual_assistant()
            elif c == "8":
                self.show_instruction()
            elif c == "9":
                self.show_useful_links()
            elif c == "0":
                print("\n🥃 Удачи!")
                break
            if c not in ["4", "5", "6", "7", "8", "9"]:
                input("\nEnter...")


if __name__ == "__main__":
    app = GrainDistillingApp()
    app.run()
