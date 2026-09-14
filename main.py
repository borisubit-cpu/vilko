from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.metrics import dp

from grain_logic import GrainDistillingApp


class MainApp(App):
    title = "Grain Master"

    def build(self):
        self.logic = GrainDistillingApp()
        self.root = TabbedPanel()
        self.root.do_default_tab = False

        tab_recipes = TabbedPanelItem(text='Рецепты')
        tab_recipes.content = self._build_recipes_tab()
        self.root.add_widget(tab_recipes)

        tab_calc = TabbedPanelItem(text='Калькуляторы')
        tab_calc.content = self._build_calc_tab()
        self.root.add_widget(tab_calc)

        tab_log = TabbedPanelItem(text='Журнал')
        tab_log.content = self._build_log_tab()
        self.root.add_widget(tab_log)

        tab_help = TabbedPanelItem(text='Помощь')
        tab_help.content = self._build_help_tab()
        self.root.add_widget(tab_help)

        tab_links = TabbedPanelItem(text='Ссылки')
        tab_links.content = self._build_links_tab()
        self.root.add_widget(tab_links)

        return self.root

    def _build_recipes_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=5)
        scroll = ScrollView()
        self.recipes_layout = GridLayout(cols=1, size_hint_y=None)
        self.recipes_layout.bind(minimum_height=self.recipes_layout.setter('height'))
        scroll.add_widget(self.recipes_layout)
        box.add_widget(scroll)
        self._refresh_recipes()
        return box

    def _refresh_recipes(self):
        self.recipes_layout.clear_widgets()
        all_recipes = []
        for cat, recipes in self.logic.recipes.items():
            for r in recipes:
                all_recipes.append(r)
        for r in self.logic.custom_recipes:
            all_recipes.append(r)
        for i, r in enumerate(all_recipes):
            btn = Button(text=f"{i+1}. {r['название']}", size_hint_y=None, height=dp(50))
            btn.bind(on_press=lambda x, idx=i: self._show_recipe_details(idx))
            self.recipes_layout.add_widget(btn)

    def _show_recipe_details(self, idx):
        all_recipes = []
        for cat, recipes in self.logic.recipes.items():
            for r in recipes:
                all_recipes.append(r)
        for r in self.logic.custom_recipes:
            all_recipes.append(r)
        recipe = all_recipes[idx]
        details = f"Название: {recipe['название']}\n\n"
        details += f"Сложность: {recipe['сложность']}\n"
        details += f"Выход: {recipe['выход']}\n\n"
        details += "Зерно:\n"
        for g, a in recipe['зерно'].items():
            details += f"  - {g}: {a} кг\n"
        details += f"\nГидромодуль: {recipe['гидромодуль']}\n"
        details += f"Дрожжи: {recipe['дрожжи']}\n"
        details += f"Температура: {recipe['температура']}°C\n"
        details += f"Брожение: {recipe['время_брожения']}\n"
        details += f"\n{recipe['описание']}"
        popup = Popup(title=recipe['название'],
                      content=Label(text=details),
                      size_hint=(0.9, 0.8))
        popup.open()

    def _build_calc_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.grain_spinner = Spinner(
            text='Пшеница',
            values=['Пшеница', 'Ячмень', 'Рожь', 'Кукуруза', 'Овёс', 'Гречка'],
            size_hint_y=None, height=dp(50))
        box.add_widget(self.grain_spinner)
        self.amount_input = TextInput(hint_text='Количество (кг)',
                                       multiline=False,
                                       size_hint_y=None, height=dp(50))
        box.add_widget(self.amount_input)
        btn = Button(text='Рассчитать выход', size_hint_y=None, height=dp(50))
        btn.bind(on_press=self._calc_yield)
        box.add_widget(btn)
        self.yield_result = Label(text='', size_hint_y=None, height=dp(50))
        box.add_widget(self.yield_result)
        return box

    def _calc_yield(self, instance):
        try:
            grain_map = {'Пшеница': 'пшеница', 'Ячмень': 'ячмень', 'Рожь': 'рожь',
                         'Кукуруза': 'кукуруза', 'Овёс': 'овёс', 'Гречка': 'гречка'}
            gtype = grain_map[self.grain_spinner.text]
            amount = float(self.amount_input.text)
            result = self.logic.calculate_yield(gtype, amount)
            self.yield_result.text = f"Выход: {result:.2f} л АС"
        except Exception as e:
            self.yield_result.text = f"Ошибка: {e}"

    def _build_log_tab(self):
        box = BoxLayout(orientation='vertical', padding=10)
        scroll = ScrollView()
        self.log_layout = GridLayout(cols=1, size_hint_y=None)
        self.log_layout.bind(minimum_height=self.log_layout.setter('height'))
        scroll.add_widget(self.log_layout)
        box.add_widget(scroll)
        btn = Button(text='Обновить', size_hint_y=None, height=dp(50))
        btn.bind(on_press=lambda x: self._refresh_log())
        box.add_widget(btn)
        self._refresh_log()
        return box

    def _refresh_log(self):
        self.log_layout.clear_widgets()
        for entry in self.logic.brew_log.get_last_entries(20):
            self.log_layout.add_widget(
                Label(text=f"{entry['date']} | {entry['recipe']}",
                      size_hint_y=None, height=dp(40)))

    def _build_help_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.question_input = TextInput(hint_text='Ваш вопрос...',
                                         multiline=False,
                                         size_hint_y=None, height=dp(50))
        box.add_widget(self.question_input)
        btn = Button(text='Спросить', size_hint_y=None, height=dp(50))
        btn.bind(on_press=self._ask_help)
        box.add_widget(btn)
        self.help_result = Label(text='', size_hint_y=None, height=dp(200))
        box.add_widget(self.help_result)
        return box

    def _ask_help(self, instance):
        q = self.question_input.text.strip()
        if q:
            ans = self.logic.assistant.ask(q)
            self.help_result.text = ans if ans else "Не знаю ответа."

    def _build_links_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        links = [
            ("Telegram-канал", "https://t.me/vilko_zerno"),
            ("Форум Самогонщики", "https://forum.homedistiller.ru/"),
            ("Форум АлкоФан", "https://alkofan.com/"),
        ]
        for name, url in links:
            btn = Button(text=name, size_hint_y=None, height=dp(50))
            btn.url = url
            btn.bind(on_press=self._open_link)
            box.add_widget(btn)
        return box

    def _open_link(self, instance):
        import webbrowser
        webbrowser.open(instance.url)


if __name__ == '__main__':
    MainApp().run()
