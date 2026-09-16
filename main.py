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
from kivy.clock import Clock

from grain_logic import GrainDistillingApp

GRAIN_DISPLAY_NAMES = ['Пшеница', 'Ячмень', 'Рожь', 'Кукуруза', 'Овёс', 'Гречка']
GRAIN_KEY_MAP = {'Пшеница': 'пшеница', 'Ячмень': 'ячмень', 'Рожь': 'рожь',
                  'Кукуруза': 'кукуруза', 'Овёс': 'овёс', 'Гречка': 'гречка'}


def info_popup(title, message):
    popup = Popup(title=title,
                   content=Label(text=message, halign='left', valign='top'),
                   size_hint=(0.85, 0.6))
    popup.open()
    return popup


class TimersTab(BoxLayout):
    """Вкладка с несколькими таймерами."""

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=8, **kwargs)
        self.timers = []

        form = BoxLayout(size_hint_y=None, height=dp(45), spacing=6)
        self.name_input = TextInput(hint_text='Название', multiline=False, size_hint_x=0.45)
        self.h_input = TextInput(hint_text='ч', multiline=False, input_filter='int', size_hint_x=0.15)
        self.m_input = TextInput(hint_text='мин', multiline=False, input_filter='int', size_hint_x=0.15)
        self.s_input = TextInput(hint_text='сек', multiline=False, input_filter='int', size_hint_x=0.15)
        add_btn = Button(text='+', size_hint_x=None, width=dp(50))
        add_btn.bind(on_press=self.add_timer)
        form.add_widget(self.name_input)
        form.add_widget(self.h_input)
        form.add_widget(self.m_input)
        form.add_widget(self.s_input)
        form.add_widget(add_btn)
        self.add_widget(form)

        scroll = ScrollView()
        self.list_layout = GridLayout(cols=1, size_hint_y=None, spacing=4)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        scroll.add_widget(self.list_layout)
        self.add_widget(scroll)

        Clock.schedule_interval(self._tick, 1)

    def add_timer(self, instance):
        name = self.name_input.text.strip() or 'Таймер'
        try:
            h = int(self.h_input.text or 0)
            m = int(self.m_input.text or 0)
            s = int(self.s_input.text or 0)
        except ValueError:
            return
        total = h * 3600 + m * 60 + s
        if total <= 0:
            return

        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=4)
        label = Label(text=f"{name}: {self._fmt(total)}", halign='left', valign='middle')
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], val[1])))
        pause_btn = Button(text='⏸', size_hint_x=None, width=dp(55))
        del_btn = Button(text='✕', size_hint_x=None, width=dp(55))

        timer = {'name': name, 'remaining': total, 'running': True,
                 'label': label, 'row': row}

        def toggle(inst, t=timer):
            t['running'] = not t['running']
            inst.text = '▶' if not t['running'] else '⏸'

        def remove(inst, t=timer):
            if t in self.timers:
                self.timers.remove(t)
            if t['row'] in self.list_layout.children:
                self.list_layout.remove_widget(t['row'])

        pause_btn.bind(on_press=toggle)
        del_btn.bind(on_press=remove)

        row.add_widget(label)
        row.add_widget(pause_btn)
        row.add_widget(del_btn)
        self.list_layout.add_widget(row)
        self.timers.append(timer)

        self.name_input.text = ''
        self.h_input.text = ''
        self.m_input.text = ''
        self.s_input.text = ''

    def _tick(self, dt):
        for t in list(self.timers):
            if t['running'] and t['remaining'] > 0:
                t['remaining'] -= 1
                t['label'].text = f"{t['name']}: {self._fmt(t['remaining'])}"
                if t['remaining'] == 0:
                    t['running'] = False
                    self._notify(t['name'])

    def _fmt(self, seconds):
        h, r = divmod(seconds, 3600)
        m, s = divmod(r, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _notify(self, name):
        popup = Popup(title='⏰ Время вышло!',
                       content=Label(text=f"Таймер «{name}» завершён"),
                       size_hint=(0.75, 0.3))
        popup.open()


class MainApp(App):
    title = "Grain Master"

    def build(self):
        self.logic = GrainDistillingApp(data_dir=self.user_data_dir)
        self.root = TabbedPanel()
        self.root.do_default_tab = False

        tab_recipes = TabbedPanelItem(text='Рецепты')
        tab_recipes.content = self._build_recipes_tab()
        self.root.add_widget(tab_recipes)

        tab_calc = TabbedPanelItem(text='Калькуляторы')
        tab_calc.content = self._build_calc_tab()
        self.root.add_widget(tab_calc)

        tab_plan = TabbedPanelItem(text='План варки')
        tab_plan.content = self._build_plan_tab()
        self.root.add_widget(tab_plan)

        tab_log = TabbedPanelItem(text='Журнал')
        tab_log.content = self._build_log_tab()
        self.root.add_widget(tab_log)

        tab_timers = TabbedPanelItem(text='Таймеры')
        tab_timers.content = TimersTab()
        self.root.add_widget(tab_timers)

        tab_yeast = TabbedPanelItem(text='Дрожжи')
        tab_yeast.content = self._build_yeast_tab()
        self.root.add_widget(tab_yeast)

        tab_help = TabbedPanelItem(text='Помощь')
        tab_help.content = self._build_help_tab()
        self.root.add_widget(tab_help)

        tab_instr = TabbedPanelItem(text='Инструкция')
        tab_instr.content = self._build_instruction_tab()
        self.root.add_widget(tab_instr)

        tab_links = TabbedPanelItem(text='Ссылки')
        tab_links.content = self._build_links_tab()
        self.root.add_widget(tab_links)

        return self.root

    # ==================== РЕЦЕПТЫ ====================
    def _build_recipes_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=5)
        add_btn = Button(text='+ Добавить свой рецепт', size_hint_y=None, height=dp(45))
        add_btn.bind(on_press=lambda x: self._open_add_recipe_form())
        box.add_widget(add_btn)

        scroll = ScrollView()
        self.recipes_layout = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.recipes_layout.bind(minimum_height=self.recipes_layout.setter('height'))
        scroll.add_widget(self.recipes_layout)
        box.add_widget(scroll)
        self._refresh_recipes()
        return box

    def _refresh_recipes(self):
        self.recipes_layout.clear_widgets()
        all_recipes = self.logic.get_all_recipes()
        n_builtin = len(all_recipes) - len(self.logic.custom_recipes)
        for i, r in enumerate(all_recipes):
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=4)
            btn = Button(text=f"{i+1}. {r['название']}")
            btn.bind(on_press=lambda x, idx=i: self._show_recipe_details(idx))
            row.add_widget(btn)
            if i >= n_builtin:
                del_btn = Button(text='✕', size_hint_x=None, width=dp(45))
                custom_idx = i - n_builtin
                del_btn.bind(on_press=lambda x, ci=custom_idx: self._delete_custom_recipe(ci))
                row.add_widget(del_btn)
            self.recipes_layout.add_widget(row)

    def _delete_custom_recipe(self, custom_idx):
        self.logic.delete_custom_recipe(custom_idx)
        self._refresh_recipes()
        self._refresh_plan_spinner()

    def _show_recipe_details(self, idx):
        recipe = self.logic.get_all_recipes()[idx]
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
        details += f"\n{recipe.get('описание', '')}"
        popup = Popup(title=recipe['название'], content=ScrollView(size_hint=(1, 1)))
        lbl = Label(text=details, size_hint_y=None, halign='left', valign='top')
        lbl.bind(texture_size=lambda inst, val: setattr(lbl, 'height', val[1]))
        lbl.bind(width=lambda inst, val: setattr(lbl, 'text_size', (val, None)))
        popup.content.add_widget(lbl)
        popup.size_hint = (0.9, 0.85)
        popup.open()

    def _open_add_recipe_form(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=6)
        name_in = TextInput(hint_text='Название рецепта', multiline=False, size_hint_y=None, height=dp(45))
        grain_spinner = Spinner(text='Пшеница', values=GRAIN_DISPLAY_NAMES, size_hint_y=None, height=dp(45))
        amount_in = TextInput(hint_text='Количество зерна (кг)', multiline=False, size_hint_y=None, height=dp(45))
        hydro_in = TextInput(text='1:4', hint_text='Гидромодуль (например 1:4)', multiline=False, size_hint_y=None, height=dp(45))
        yeast_in = TextInput(text='спиртовые', hint_text='Тип дрожжей', multiline=False, size_hint_y=None, height=dp(45))
        temp_in = TextInput(text='25', hint_text='Температура брожения (°C)', multiline=False, size_hint_y=None, height=dp(45))
        ferment_time_in = TextInput(text='5-7 дней', hint_text='Время брожения', multiline=False, size_hint_y=None, height=dp(45))
        desc_in = TextInput(hint_text='Описание', multiline=True, size_hint_y=None, height=dp(70))

        for w in (name_in, grain_spinner, amount_in, hydro_in, yeast_in, temp_in, ferment_time_in, desc_in):
            box.add_widget(w)

        save_btn = Button(text='Сохранить рецепт', size_hint_y=None, height=dp(50))
        box.add_widget(save_btn)
        popup = Popup(title='Новый рецепт', content=box, size_hint=(0.9, 0.9))

        def save(instance):
            name = name_in.text.strip()
            if not name:
                info_popup('Ошибка', 'Введите название рецепта')
                return
            try:
                amount = float(amount_in.text)
            except ValueError:
                info_popup('Ошибка', 'Некорректное количество зерна')
                return
            try:
                temp = float(temp_in.text)
            except ValueError:
                temp = 25
            grain_key = GRAIN_KEY_MAP[grain_spinner.text]
            grain_bill = {grain_key: amount}
            recipe = {
                'название': name,
                'зерно': grain_bill,
                'гидромодуль': hydro_in.text.strip() or '1:4',
                'дрожжи': yeast_in.text.strip() or 'спиртовые',
                'температура': temp,
                'время_брожения': ferment_time_in.text.strip() or '5-7 дней',
                'описание': desc_in.text.strip(),
                'сложность': 'средняя',
                'выход': 'неизвестно',
                'ферменты': self.logic.calculate_enzymes(grain_bill),
            }
            self.logic.add_custom_recipe_data(recipe)
            popup.dismiss()
            self._refresh_recipes()
            self._refresh_plan_spinner()

        save_btn.bind(on_press=save)
        popup.open()

    # ==================== КАЛЬКУЛЯТОРЫ ====================
    def _build_calc_tab(self):
        outer = TabbedPanel(do_default_tab=False)
        outer.add_widget(self._make_calc_yield_tab())
        outer.add_widget(self._make_calc_water_tab())
        outer.add_widget(self._make_calc_enzymes_tab())
        outer.add_widget(self._make_calc_yeast_tab())
        outer.add_widget(self._make_calc_heads_tab())
        return outer

    def _make_calc_yield_tab(self):
        item = TabbedPanelItem(text='Выход спирта')
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        grain_spinner = Spinner(text='Пшеница', values=GRAIN_DISPLAY_NAMES, size_hint_y=None, height=dp(50))
        amount_input = TextInput(hint_text='Количество (кг)', multiline=False, size_hint_y=None, height=dp(50))
        result = Label(text='', size_hint_y=None, height=dp(60))

        def calc(instance):
            try:
                grain_key = GRAIN_KEY_MAP[grain_spinner.text]
                amount = float(amount_input.text)
                value = self.logic.calculate_yield(grain_key, amount)
                result.text = f"Ожидаемый выход: {value:.2f} л АС"
            except Exception as e:
                result.text = f"Ошибка: {e}"

        btn = Button(text='Рассчитать выход', size_hint_y=None, height=dp(50))
        btn.bind(on_press=calc)
        box.add_widget(grain_spinner)
        box.add_widget(amount_input)
        box.add_widget(btn)
        box.add_widget(result)
        item.content = box
        return item

    def _make_calc_water_tab(self):
        item = TabbedPanelItem(text='Вода')
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        grain_spinner = Spinner(text='Пшеница', values=GRAIN_DISPLAY_NAMES, size_hint_y=None, height=dp(50))
        amount_input = TextInput(hint_text='Количество зерна (кг)', multiline=False, size_hint_y=None, height=dp(50))
        hydro_input = TextInput(text='1:4', hint_text='Гидромодуль (например 1:4)', multiline=False, size_hint_y=None, height=dp(50))
        result = Label(text='', size_hint_y=None, height=dp(60))

        def calc(instance):
            try:
                grain_key = GRAIN_KEY_MAP[grain_spinner.text]
                amount = float(amount_input.text)
                fake_recipe = {'зерно': {grain_key: amount}, 'гидромодуль': hydro_input.text.strip() or '1:4'}
                water = self.logic.calculate_water_volume(fake_recipe)
                result.text = f"Требуется воды: {water:.1f} л"
            except Exception as e:
                result.text = f"Ошибка: {e}"

        btn = Button(text='Рассчитать объём воды', size_hint_y=None, height=dp(50))
        btn.bind(on_press=calc)
        box.add_widget(grain_spinner)
        box.add_widget(amount_input)
        box.add_widget(hydro_input)
        box.add_widget(btn)
        box.add_widget(result)
        item.content = box
        return item

    def _make_calc_enzymes_tab(self):
        item = TabbedPanelItem(text='Ферменты')
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        grain_spinner = Spinner(text='Пшеница', values=GRAIN_DISPLAY_NAMES, size_hint_y=None, height=dp(50))
        amount_input = TextInput(hint_text='Количество зерна (кг)', multiline=False, size_hint_y=None, height=dp(50))
        result = Label(text='', size_hint_y=None, height=dp(120))

        def calc(instance):
            try:
                grain_key = GRAIN_KEY_MAP[grain_spinner.text]
                amount = float(amount_input.text)
                enzymes = self.logic.calculate_enzymes({grain_key: amount})
                lines = [f"{name}: {val} г" for name, val in enzymes.items()]
                result.text = "\n".join(lines)
            except Exception as e:
                result.text = f"Ошибка: {e}"

        btn = Button(text='Рассчитать ферменты', size_hint_y=None, height=dp(50))
        btn.bind(on_press=calc)
        box.add_widget(grain_spinner)
        box.add_widget(amount_input)
        box.add_widget(btn)
        box.add_widget(result)
        item.content = box
        return item

    def _make_calc_yeast_tab(self):
        item = TabbedPanelItem(text='Дрожжи')
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        water_input = TextInput(hint_text='Объём затора (л)', multiline=False, size_hint_y=None, height=dp(50))
        yeast_input = TextInput(text='спиртовые', hint_text='Тип дрожжей', multiline=False, size_hint_y=None, height=dp(50))
        result = Label(text='', size_hint_y=None, height=dp(60))

        def calc(instance):
            try:
                water = float(water_input.text)
                amount = self.logic.calculate_yeast(water, yeast_input.text.strip())
                result.text = f"Требуется дрожжей: {amount} г"
            except Exception as e:
                result.text = f"Ошибка: {e}"

        btn = Button(text='Рассчитать дрожжи', size_hint_y=None, height=dp(50))
        btn.bind(on_press=calc)
        box.add_widget(water_input)
        box.add_widget(yeast_input)
        box.add_widget(btn)
        box.add_widget(result)
        item.content = box
        return item

    def _make_calc_heads_tab(self):
        item = TabbedPanelItem(text='Головы')
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        ac_input = TextInput(hint_text='Количество абсолютного спирта (мл)', multiline=False, size_hint_y=None, height=dp(50))
        percent_input = TextInput(text='10', hint_text='Процент отбора голов (%)', multiline=False, size_hint_y=None, height=dp(50))
        result = Label(text='', size_hint_y=None, height=dp(60))

        def calc(instance):
            try:
                ac_ml = float(ac_input.text)
                percent = float(percent_input.text or 10)
                heads_ml = ac_ml * percent / 100
                result.text = f"Объём голов: {heads_ml:.0f} мл ({percent:.0f}% от {ac_ml:.0f} мл АС)"
            except Exception as e:
                result.text = f"Ошибка: {e}"

        btn = Button(text='Рассчитать головы', size_hint_y=None, height=dp(50))
        btn.bind(on_press=calc)
        box.add_widget(ac_input)
        box.add_widget(percent_input)
        box.add_widget(btn)
        box.add_widget(result)
        item.content = box
        return item

    # ==================== ПЛАН ВАРКИ ====================
    def _build_plan_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.plan_spinner = Spinner(size_hint_y=None, height=dp(50))
        self._refresh_plan_spinner()
        box.add_widget(self.plan_spinner)

        gen_btn = Button(text='Сгенерировать план', size_hint_y=None, height=dp(50))
        gen_btn.bind(on_press=self._generate_plan)
        box.add_widget(gen_btn)

        scroll = ScrollView()
        self.plan_layout = GridLayout(cols=1, size_hint_y=None, spacing=6)
        self.plan_layout.bind(minimum_height=self.plan_layout.setter('height'))
        scroll.add_widget(self.plan_layout)
        box.add_widget(scroll)
        return box

    def _refresh_plan_spinner(self):
        names = [r['название'] for r in self.logic.get_all_recipes()]
        self.plan_spinner.values = names
        if names and self.plan_spinner.text not in names:
            self.plan_spinner.text = names[0]

    def _generate_plan(self, instance):
        self.plan_layout.clear_widgets()
        all_recipes = self.logic.get_all_recipes()
        recipe = next((r for r in all_recipes if r['название'] == self.plan_spinner.text), None)
        if not recipe:
            return
        try:
            plan = self.logic.generate_plan(recipe)
        except Exception as e:
            self.plan_layout.add_widget(Label(text=f"Ошибка построения плана: {e}",
                                               size_hint_y=None, height=dp(60)))
            return

        # ===== Автоматически добавляем запись в журнал =====
        try:
            self.logic.brew_log.add_entry(
                recipe_name=recipe['название'],
                grain_bill=recipe['зерно'].copy(),
                og=None, fg=None, yield_ml=None,
                notes=f"Запланировано: {recipe['название']}",
            )
            try:
                self._refresh_log()
            except Exception:
                pass

            note = Label(
                text=f"✅ Запись «{recipe['название']}» добавлена в журнал",
                size_hint_y=None, height=dp(30), color=(0.2, 0.7, 0.2, 1)
            )
            self.plan_layout.add_widget(note)
        except Exception as e:
            print(f"Не удалось записать в журнал: {e}")
        # ===================================================

        for step in plan:
            text = f"День {step['день']} | {step['этап']}\n{step['действие']}\n⏰ {step['время']}"
            lbl = Label(text=text, size_hint_y=None, halign='left', valign='top')
            lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(10)))
            lbl.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
            self.plan_layout.add_widget(lbl)

    # ==================== ЖУРНАЛ ====================
    def _build_log_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=6)
        self.log_stats_label = Label(text='', size_hint_y=None, height=dp(40))
        box.add_widget(self.log_stats_label)

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=6)
        add_btn = Button(text='+ Записать варку')
        add_btn.bind(on_press=lambda x: self._open_add_log_form())
        refresh_btn = Button(text='Обновить')
        refresh_btn.bind(on_press=lambda x: self._refresh_log())
        btn_row.add_widget(add_btn)
        btn_row.add_widget(refresh_btn)
        box.add_widget(btn_row)

        scroll = ScrollView()
        self.log_layout = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.log_layout.bind(minimum_height=self.log_layout.setter('height'))
        scroll.add_widget(self.log_layout)
        box.add_widget(scroll)
        self._refresh_log()
        return box

    def _refresh_log(self):
        self.log_layout.clear_widgets()
        stats = self.logic.brew_log.get_statistics()
        if stats['total_brews']:
            self.log_stats_label.text = (f"Всего варок: {stats['total_brews']} | "
                                          f"Средний выход: {stats['avg_yield']:.0f} мл | "
                                          f"Последняя: {stats['last_brew']}")
        else:
            self.log_stats_label.text = "Записей пока нет"

        entries = self.logic.brew_log.get_last_entries(20)
        total = len(self.logic.brew_log.entries)
        for pos, entry in enumerate(entries):
            real_index = total - 1 - pos
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=4)
            rating_stars = '★' * (entry.get('rating') or 0)
            label_text = f"{entry['date']} | {entry['recipe']} {rating_stars}""
            btn = Button(text=label_text)
            btn.bind(on_press=lambda x, idx=real_index: self._show_log_entry(idx))
            row.add_widget(btn)
            del_btn = Button(text='✕', size_hint_x=None, width=dp(45))
            del_btn.bind(on_press=lambda x, idx=real_index: self._delete_log_entry(idx))
            row.add_widget(del_btn)
            self.log_layout.add_widget(row)

        def _show_log_entry(self, index):
        entry = self.logic.brew_log.get_entry(index)
        if not entry:
            return

        box = BoxLayout(orientation='vertical', padding=12, spacing=8)

        # --- Информация (только для чтения) ---
        info = Label(
            text=(f"Рецепт: {entry['recipe']}\n"
                  f"Дата создания: {entry['date']}\n"
                  f"OG: {entry.get('original_gravity')}  |  FG: {entry.get('final_gravity')}\n"
                  f"Выход: {entry.get('alcohol_yield_ml')} мл"),
            size_hint_y=None, height=dp(90), halign='left', valign='top')
        info.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], val[1])))
        box.add_widget(info)

        # --- Заметки ---
        box.add_widget(Label(text='Заметки:', size_hint_y=None, height=dp(25)))
        notes_in = TextInput(text=entry.get('notes') or '', multiline=True,
                             size_hint_y=None, height=dp(90))
        box.add_widget(notes_in)

        # --- Рейтинг звёздочками ---
        box.add_widget(Label(text='Оценка рецепта:', size_hint_y=None, height=dp(25)))
        stars_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=4)

        # Храним текущий рейтинг в изменяемом контейнере (closure)
        current = {'rating': entry.get('rating') or 0}
        star_buttons = []

        def refresh_stars():
            for i, b in enumerate(star_buttons, 1):
                b.text = '★' if i <= current['rating'] else '☆'

        def make_star_handler(value):
            def handler(inst):
                current['rating'] = value
                refresh_stars()
            return handler

        for i in range(1, 6):
            b = Button(text='☆', size_hint_x=None, width=dp(55))
            b.bind(on_press=make_star_handler(i))
            star_buttons.append(b)
            stars_row.add_widget(b)
        refresh_stars()
        box.add_widget(stars_row)

        # --- Даты брожения ---
        box.add_widget(Label(text='Начало брожения (ГГГГ-ММ-ДД ЧЧ:ММ):',
                             size_hint_y=None, height=dp(25)))
        start_in = TextInput(text=entry.get('fermentation_start') or '',
                             hint_text='например 2025-10-15 18:30',
                             multiline=False, size_hint_y=None, height=dp(45))
        box.add_widget(start_in)

        box.add_widget(Label(text='Окончание брожения (ГГГГ-ММ-ДД ЧЧ:ММ):',
                             size_hint_y=None, height=dp(25)))
        end_in = TextInput(text=entry.get('fermentation_end') or '',
                           hint_text='например 2025-10-22 12:00',
                           multiline=False, size_hint_y=None, height=dp(45))
        box.add_widget(end_in)

        # --- Кнопка сохранения ---
        save_btn = Button(text='💾 Сохранить изменения', size_hint_y=None, height=dp(50))
        box.add_widget(save_btn)

        popup = Popup(title=f"Запись: {entry['recipe']}",
                       content=box, size_hint=(0.92, 0.92))

        def save(instance):
            notes_val = notes_in.text.strip()
            self.logic.brew_log.add_notes(index, notes_val)

            if current['rating'] >= 1:
                self.logic.brew_log.set_rating(index, current['rating'])

            s = start_in.text.strip()
            if s:
                self.logic.brew_log.set_fermentation_start(index, s)

            e = end_in.text.strip()
            if e:
                self.logic.brew_log.set_fermentation_end(index, e)

            popup.dismiss()
            self._refresh_log()
            info_popup('Сохранено', f"Запись «{entry['recipe']}» обновлена")

        save_btn.bind(on_press=save)
        popup.open()

    def _delete_log_entry(self, index):
        self.logic.brew_log.delete_entry(index)
        self._refresh_log()

    def _open_add_log_form(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=6)
        names = [r['название'] for r in self.logic.get_all_recipes()]
        recipe_spinner = Spinner(text=names[0] if names else '', values=names, size_hint_y=None, height=dp(45))
        og_in = TextInput(hint_text='Начальная плотность (необязательно)', multiline=False, size_hint_y=None, height=dp(45))
        fg_in = TextInput(hint_text='Конечная плотность (необязательно)', multiline=False, size_hint_y=None, height=dp(45))
        yield_in = TextInput(hint_text='Выход, мл (необязательно)', multiline=False, size_hint_y=None, height=dp(45))
        notes_in = TextInput(hint_text='Заметки', multiline=True, size_hint_y=None, height=dp(80))

        for w in (recipe_spinner, og_in, fg_in, yield_in, notes_in):
            box.add_widget(w)

        save_btn = Button(text='Сохранить запись', size_hint_y=None, height=dp(50))
        box.add_widget(save_btn)
        popup = Popup(title='Новая запись в журнале', content=box, size_hint=(0.9, 0.85))

        def to_float(text):
            text = text.strip()
            if not text:
                return None
            try:
                return float(text)
            except ValueError:
                return None

        def save(instance):
            recipe_name = recipe_spinner.text
            all_recipes = self.logic.get_all_recipes()
            recipe = next((r for r in all_recipes if r['название'] == recipe_name), None)
            grain_bill = recipe['зерно'] if recipe else {}
            self.logic.brew_log.add_entry(
                recipe_name=recipe_name,
                grain_bill=grain_bill,
                og=to_float(og_in.text),
                fg=to_float(fg_in.text),
                yield_ml=to_float(yield_in.text),
                notes=notes_in.text.strip(),
            )
            popup.dismiss()
            self._refresh_log()

        save_btn.bind(on_press=save)
        popup.open()

    # ==================== ДРОЖЖИ ====================
    def _build_yeast_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=6)
        search_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=6)
        self.yeast_search_input = TextInput(hint_text='Поиск (название, тип, зерно)', multiline=False)
        search_btn = Button(text='Искать', size_hint_x=None, width=dp(90))
        search_btn.bind(on_press=lambda x: self._search_yeasts())
        clear_btn = Button(text='Сброс', size_hint_x=None, width=dp(90))
        clear_btn.bind(on_press=lambda x: self._refresh_yeasts())
        search_row.add_widget(self.yeast_search_input)
        search_row.add_widget(search_btn)
        search_row.add_widget(clear_btn)
        box.add_widget(search_row)

        scroll = ScrollView()
        self.yeast_layout = GridLayout(cols=1, size_hint_y=None, spacing=4)
        self.yeast_layout.bind(minimum_height=self.yeast_layout.setter('height'))
        scroll.add_widget(self.yeast_layout)
        box.add_widget(scroll)
        self._refresh_yeasts()
        return box

    def _refresh_yeasts(self):
        self._render_yeasts(self.logic.yeast_db.get_all())

    def _search_yeasts(self):
        query = self.yeast_search_input.text.strip()
        if not query:
            self._refresh_yeasts()
            return
        self._render_yeasts(self.logic.yeast_db.search(query))

    def _render_yeasts(self, yeasts):
        self.yeast_layout.clear_widgets()
        if not yeasts:
            self.yeast_layout.add_widget(Label(text='Ничего не найдено', size_hint_y=None, height=dp(40)))
            return
        for yeast in yeasts:
            text = (f"{yeast['название']} ({yeast['тип']})\n"
                    f"Темп: {yeast['темп_мин']}-{yeast['темп_макс']}°C | "
                    f"Толерантность: {yeast['алко_толерантность']}% | "
                    f"Рейтинг: {yeast.get('рейтинг', '-')}\n"
                    f"{yeast['описание']}\n"
                    f"Рекомендации: {', '.join(yeast.get('рекомендации', []))}")
            lbl = Label(text=text, size_hint_y=None, halign='left', valign='top')
            lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(10)))
            lbl.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
            self.yeast_layout.add_widget(lbl)

    # ==================== ПОМОЩЬ ====================
    def _build_help_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.question_input = TextInput(hint_text='Ваш вопрос...',
                                         multiline=False,
                                         size_hint_y=None, height=dp(50))
        box.add_widget(self.question_input)
        btn = Button(text='Спросить', size_hint_y=None, height=dp(50))
        btn.bind(on_press=self._ask_help)
        box.add_widget(btn)
        scroll = ScrollView()
        self.help_result = Label(text='', size_hint_y=None, halign='left', valign='top')
        self.help_result.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        self.help_result.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        scroll.add_widget(self.help_result)
        box.add_widget(scroll)
        return box

    def _ask_help(self, instance):
        q = self.question_input.text.strip()
        if q:
            ans = self.logic.assistant.ask(q)
            self.help_result.text = ans if ans else ("Не знаю ответа. Попробуйте спросить про: "
                                                       "брагу, головы, хвосты, осахаривание, "
                                                       "гидромодуль, дрожжи, температуру.")

    # ==================== ИНСТРУКЦИЯ ====================
    def _build_instruction_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)

        save_btn = Button(text='💾 Сохранить инструкцию в HTML', size_hint_y=None, height=dp(50))
        save_btn.bind(on_press=self._save_instruction_html)
        box.add_widget(save_btn)

        scroll = ScrollView()
        label = Label(text=self._instruction_text(), size_hint_y=None,
                      halign='left', valign='top', markup=True)
        label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        scroll.add_widget(label)
        box.add_widget(scroll)
        return box

    def _instruction_text(self):
        return (
            "[b][size=20]Зерновой Мастер — инструкция[/size][/b]\n\n"

            "[b][size=16]Разделы приложения[/size][/b]\n"
            "• [b]Рецепты[/b] — 20 встроенных рецептов + добавление своих\n"
            "• [b]Калькуляторы[/b] — выход спирта, вода, ферменты, дрожжи, головы\n"
            "• [b]План варки[/b] — пошаговый план по выбранному рецепту\n"
            "• [b]Журнал[/b] — статистика, оценки, заметки по каждой варке\n"
            "• [b]Таймеры[/b] — несколько параллельных таймеров с уведомлением\n"
            "• [b]Дрожжи[/b] — база с характеристиками и рекомендациями\n"
            "• [b]Помощь[/b] — быстрые ответы на частые вопросы\n"
            "• [b]Ссылки[/b] — Telegram-канал и форумы\n\n"

            "[b][size=16]Как начать[/size][/b]\n"
            "1. Выберите рецепт в разделе «Рецепты» или добавьте свой\n"
            "2. Откройте «План варки», выберите рецепт — получите пошаговую инструкцию\n"
            "3. Отмечайте процесс в «Журнале»: заметки, оценки, даты брожения\n"
            "4. Используйте «Таймеры» для контроля пауз и брожения\n\n"

            "[b][size=16]Полезные особенности[/size][/b]\n"
            "• Все данные хранятся в JSON-файлах на устройстве\n"
            "• Пользовательские рецепты сохраняются отдельно\n"
            "• Журнал можно редактировать и очищать\n"
            "• При изменении записи фиксируется дата и время\n\n"

            "[color=#b8860b][b]⚠ Внимание:[/b] Соблюдайте законодательство вашей страны "
            "в отношении производства алкогольных напитков.[/color]"
        )

    def _save_instruction_html(self, instance):
        try:
            path = self.logic.export_instruction_to_html()
            info_popup('Инструкция сохранена',
                       f"Файл: {path}\n\n(в папке с данными приложения)")
        except Exception as e:
            info_popup('Ошибка', str(e))

    # ==================== ССЫЛКИ ====================
    def _build_links_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        links = [
            ("Мой Telegram-канал", "https://t.me/vilko_zerno"),
            ("Форум «Самогонщики»", "https://forum.homedistiller.ru/"),
            ("Форум «АлкоФан»", "https://alkofan.com/"),
            ("Форум «Гоним с нами»", "https://gonim-s-nami.ru/"),
            ("Форум «Самогонный аппарат»", "https://samogonnyj-apparat.ru/forum/"),
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
