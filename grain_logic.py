import json
import os
import copy
from datetime import datetime
from typing import Dict, List

class BrewLog:
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
        total_brews = len(self.entries)
        if total_brews == 0:
            return {"total_brews": 0, "avg_yield": 0, "last_brew": None}
        yields = [e['alcohol_yield_ml'] for e in self.entries if e['alcohol_yield_ml'] is not None]
        avg_yield = sum(yields) / len(yields) if yields else 0
        return {"total_brews": total_brews, "avg_yield": avg_yield, "last_brew": self.entries[-1]['date']}
    
    def get_last_entries(self, count=5):
        return self.entries[-count:][::-1]
    
    def get_recipe_stats(self):
        stats = {}
        for entry in self.entries:
            name = entry['recipe']
            if name not in stats:
                stats[name] = {'count': 0, 'total_rating': 0, 'rating_count': 0}
            stats[name]['count'] += 1
            if entry.get('rating') is not None:
                stats[name]['total_rating'] += entry['rating']
                stats[name]['rating_count'] += 1
        result = []
        for name, data in stats.items():
            avg_rating = data['total_rating'] / data['rating_count'] if data['rating_count'] > 0 else 0
            result.append({'recipe': name, 'count': data['count'], 'avg_rating': avg_rating})
        return result


class VirtualAssistant:
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
            {"ключевые_слова": ["брага", "не бродит"], "ответ": "Проверьте температуру (20-30°C), дрожжи живые, кислотность."},
            {"ключевые_слова": ["головы"], "ответ": "Отбирайте 5-10% от объёма абсолютного спирта, медленно, покапельно."},
            {"ключевые_слова": ["хвосты"], "ответ": "Отсекайте при крепости ниже 40-45% в струе."},
            {"ключевые_слова": ["осахаривание", "ферменты"], "ответ": "Амилосубтилин при 70-80°C, Глюкаваморин при 60-65°C."},
            {"ключевые_слова": ["гидромодуль"], "ответ": "Обычно 1:3 или 1:4 (зерно:вода)."}
        ]
    
    def ask(self, question: str):
        question_lower = question.lower()
        best_match = None
        best_score = 0
        for entry in self.knowledge:
            score = sum(1 for kw in entry["ключевые_слова"] if kw.lower() in question_lower)
            if score > best_score:
                best_score = score
                best_match = entry
        return best_match["ответ"] if best_match else None


class YeastDatabase:
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
            {"название": "SafSpirit USW-6", "тип": "спиртовые", "темп_мин": 12, "темп_макс": 35, "алко_толерантность": 18, "описание": "Универсальные для зерновых", "рекомендации": ["пшеница", "рожь"], "рейтинг": 4.5},
            {"название": "Turbo Yeast 48", "тип": "турбо", "темп_мин": 20, "темп_макс": 35, "алко_толерантность": 20, "описание": "Быстрое брожение", "рекомендации": ["кукуруза"], "рейтинг": 4.0},
            {"название": "Lalvin EC-1118", "тип": "винные", "темп_мин": 10, "темп_макс": 30, "алко_толерантность": 18, "описание": "Для виски", "рекомендации": ["ячмень"], "рейтинг": 4.7}
        ]
    
    def get_all(self):
        return self.yeasts


class GrainDistillingApp:
    def __init__(self):
        self.grain_base = self._default_grain_data()
        self.recipes = self._default_recipes()
        self.custom_recipes = []
        self.brew_log = BrewLog()
        self.yeast_db = YeastDatabase()
        self.assistant = VirtualAssistant()
    
    def _default_grain_data(self):
        return {
            "пшеница": {"выход_спирта": 0.44, "вкус": "Мягкий, хлебный"},
            "ячмень": {"выход_спирта": 0.40, "вкус": "Сладковатый, виски"},
            "рожь": {"выход_спирта": 0.37, "вкус": "Пряный, острый"},
            "кукуруза": {"выход_спирта": 0.47, "вкус": "Сладкий, бурбон"},
            "овёс": {"выход_спирта": 0.34, "вкус": "Мягкий, ореховый"},
            "гречка": {"выход_спирта": 0.37, "вкус": "Ореховый"}
        }
    
    def _default_recipes(self):
        return {
            "classic": [
                {"название": "Пшеничная водка", "зерно": {"пшеница": 25}, "гидромодуль": "1:4", "дрожжи": "спиртовые", "температура": 25, "время_брожения": "5-7 дней", "описание": "Классическая пшеничная водка", "сложность": "средняя", "выход": "11 л АС"},
                {"название": "Ржаная водка", "зерно": {"рожь": 22}, "гидромодуль": "1:4.5", "дрожжи": "спиртовые", "температура": 25, "время_брожения": "6-8 дней", "описание": "Традиционная ржаная водка", "сложность": "высокая", "выход": "8 л АС"},
                {"название": "Рисовая водка", "зерно": {"рис": 28}, "гидромодуль": "1:3.6", "дрожжи": "винные", "температура": 22, "время_брожения": "10-12 дней", "описание": "Лёгкий дистиллят в стиле саке", "сложность": "высокая", "выход": "12 л АС"},
                {"название": "Овсяная водка", "зерно": {"овёс": 20}, "гидромодуль": "1:5", "дрожжи": "спиртовые", "температура": 24, "время_брожения": "7 дней", "описание": "Мягкая водка с кремовой текстурой", "сложность": "средняя", "выход": "7 л АС"}
            ],
            "whiskey": [
                {"название": "Односолодовый виски", "зерно": {"ячменный_солод": 30}, "гидромодуль": "1:3.3", "дрожжи": "винные", "температура": 20, "время_брожения": "7-10 дней", "описание": "Классический солодовый виски", "сложность": "высокая", "выход": "12 л АС"},
                {"название": "Бурбон классический", "зерно": {"кукуруза": 28, "ячменный_солод": 7}, "гидромодуль": "1:2.9", "дрожжи": "спиртовые", "температура": 28, "время_брожения": "5 дней", "описание": "Американский бурбон", "сложность": "средняя", "выход": "16 л АС"},
                {"название": "Ржаной виски", "зерно": {"рожь": 25, "пшеница": 5}, "гидромодуль": "1:3.3", "дрожжи": "спиртовые", "температура": 25, "время_брожения": "7 дней", "описание": "Острый, пряный виски", "сложность": "высокая", "выход": "11 л АС"},
                {"название": "Пшеничный виски", "зерно": {"пшеница": 22, "ячменный_солод": 5, "овёс": 3}, "гидромодуль": "1:3.3", "дрожжи": "пивные", "температура": 22, "время_брожения": "8 дней", "описание": "Мягкий виски", "сложность": "средняя", "выход": "13 л АС"}
            ],
            "gourmet": [
                {"название": "Кукурузно-рисовый бурбон", "зерно": {"кукуруза": 20, "рис": 10}, "гидромодуль": "1:3.3", "дрожжи": "спиртовые", "температура": 27, "время_брожения": "5-6 дней", "описание": "Экзотический гибрид", "сложность": "высокая", "выход": "14 л АС"},
                {"название": "Полбяной дистиллят", "зерно": {"полба": 25}, "гидромодуль": "1:4", "дрожжи": "винные", "температура": 22, "время_брожения": "7-8 дней", "описание": "Ореховый, дикий аромат", "сложность": "средняя", "выход": "10 л АС"},
                {"название": "Гречишный виски", "зерно": {"гречка": 22, "ячмень": 5}, "гидромодуль": "1:3.7", "дрожжи": "спиртовые", "температура": 26, "время_брожения": "6 дней", "описание": "Травянистый, терпкий", "сложность": "высокая", "выход": "10 л АС"}
            ]
        }
    
    def calculate_yield(self, grain_type, amount_kg):
        if grain_type in self.grain_base:
            return self.grain_base[grain_type]["выход_спирта"] * amount_kg
        return 0
