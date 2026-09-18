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
from kivy.lang import Builder
from kivy.graphics import Rectangle, Color as GColor
from kivy.core.image import Image as CoreImage
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

# ==================== СТИЛЬ ====================

Builder.load_string('''
<Button>:
    background_normal: ''
    background_down: ''
    background_color: 0.18, 0.30, 0.24, 1
    color: 0.96, 0.90, 0.78, 1
    font_size: '15sp'

<Label>:
    color: 0.20, 0.14, 0.08, 1

<TextInput>:
    background_color: 0.97, 0.92, 0.82, 1
    foreground_color: 0.18, 0.12, 0.06, 1

<TabbedPanelItem>:
    background_color: 0.18, 0.30, 0.24, 1
    color: 0.96, 0.90, 0.78, 1
''')


class BackgroundTabbedPanel(TabbedPanel):
    """TabbedPanel с фоновым изображением под всеми вкладками."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            bg = CoreImage('bg.png').texture
        except Exception:
            bg = None
        with self.canvas.before:
            GColor(1, 1, 1, 1)
            self._bg_rect = Rectangle(texture=bg, pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
class TimersTab(BoxLayout):
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
        for w in (self.name_input, self.h_input, self.m_input, self.s_input, add_btn):
            form.add_widget(w)
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
        pause_btn = Button(text='Пауза', size_hint_x=None, width=dp(90))
        del_btn = Button(text='X', size_hint_x=None, width=dp(50))
        timer = {'name': name, 'remaining': total, 'running': True, 'label': label, 'row': row}

        def toggle(inst, t=timer):
            t['running'] = not t['running']
            inst.text = 'Пуск' if not t['running'] else 'Пауза'

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
        popup = Popup(title='Время вышло!',
                       content=Label(text=f"Таймер «{name}» завершён"),
                       size_hint=(0.75, 0.3))
        popup.open()


class MainApp(App):
    title = "Зерновой Мастер"

    def build(self):
        self.logic = GrainDistillingApp(data_dir=self.user_data_dir)
        self.root = BackgroundTabbedPanel()
        self.root.do_default_tab = False

        tabs = [
            ('Рецепты', self._build_recipes_tab),
            ('Калькуляторы', self._build_calc_tab),
            ('План варки', self._build_plan_tab),
            ('Журнал', self._build_log_tab),
            ('Статистика', self._build_stats_tab),
            ('Дрожжи', self._build_yeast_tab),
            ('Помощь', self._build_help_tab),
            ('Инструкция', self._build_instruction_tab),
            ('Ссылки', self._build_links_tab),
        ]
        for title, builder in tabs:
            tab = TabbedPanelItem(text=title)
            tab.content = builder()
            self.root.add_widget(tab)

        tab_timers = TabbedPanelItem(text='Таймеры')
        tab_timers.content = TimersTab()
        self.root.add_widget(tab_timers)

        Clock.schedule_once(lambda dt: self._check_fermentation_notifications(), 2)
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
                del_btn = Button(text='X', size_hint_x=None, width=dp(45))
                ci = i - n_builtin
                del_btn.bind(on_press=lambda x, c=ci: self._delete_custom_recipe(c))
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
        hydro_in = TextInput(text='1:4', hint_text='Гидромодуль', multiline=False, size_hint_y=None, height=dp(45))
        yeast_in = TextInput(text='спиртовые', hint_text='Тип дрожжей', multiline=False, size_hint_y=None, height=dp(45))
        temp_in = TextInput(text='25', hint_text='Температура брожения (°C)', multiline=False, size_hint_y=None, height=dp(45))
        time_in = TextInput(text='5-7 дней', hint_text='Время брожения', multiline=False, size_hint_y=None, height=dp(45))
        desc_in = TextInput(hint_text='Описание', multiline=True, size_hint_y=None, height=dp(70))
        for w in (name_in, grain_spinner, amount_in, hydro_in, yeast_in, temp_in, time_in, desc_in):
            box.add_widget(w)
        save_btn = Button(text='Сохранить рецепт', size_hint_y=None, height=dp(50))
        box.add_widget(save_btn)
        popup = Popup(title='Новый рецепт', content=box, size_hint=(0.9, 0.9))

    def save(instance):
            name = name_in.text.strip()
            if not name:
                info_popup('Ошибка', 'Введите название')
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
            grain_bill = {GRAIN_KEY_MAP[grain_spinner.text]: amount}
            recipe = {
                'название': name, 'зерно': grain_bill,
                'гидромодуль': hydro_in.text.strip() or '1:4',
                'дрожжи': yeast_in.text.strip() or 'спиртовые',
                'температура': temp,
                'время_брожения': time_in.text.strip() or '5-7 дней',
                'описание': desc_in.text.strip(),
                'сложность': 'средняя', 'выход': 'неизвестно',
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
        gs = Spinner(text='Пшеница', values=GRAIN_DISPLAY_NAMES, size_hint_y=None, height=dp(50))
        ai = TextInput(hint_text='Количество (кг)', multiline=False, size_hint_y=None, height=dp(50))
        res = Label(text='', size_hint_y=None, height=dp(60))

        def calc(inst):
            try:
                v = self.logic.calculate_yield(GRAIN_KEY_MAP[gs.text], float(ai.text))
                res.text = f"Ожидаемый выход: {v:.2f} л АС"
            except Exception as e:
                res.text = f"Ошибка: {e}"

        b = Button(text='Рассчитать выход', size_hint_y=None, height=dp(50))
        b.bind(on_press=calc)
        for w in (gs, ai, b, res):
            box.add_widget(w)
        item.content = box
        return item

    def _make_calc_water_tab(self):
        item = TabbedPanelItem(text='Вода')
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        gs = Spinner(text='Пшеница', values=GRAIN_DISPLAY_NAMES, size_hint_y=None, height=dp(50))
        ai = TextInput(hint_text='Количество зерна (кг)', multiline=False, size_hint_y=None, height=dp(50))
        hi = TextInput(text='1:4', hint_text='Гидромодуль', multiline=False, size_hint_y=None, height=dp(50))
        res = Label(text='', size_hint_y=None, height=dp(60))

        def calc(inst):
            try:
                fake = {'зерно': {GRAIN_KEY_MAP[gs.text]: float(ai.text)},
                        'гидромодуль': hi.text.strip() or '1:4'}
                res.text = f"Требуется воды: {self.logic.calculate_water_volume(fake):.1f} л"
            except Exception as e:
                res.text = f"Ошибка: {e}"

        b = Button(text='Рассчитать объём воды', size_hint_y=None, height=dp(50))
        b.bind(on_press=calc)
        for w in (gs, ai, hi, b, res):
            box.add_widget(w)
        item.content = box
        return item

    def _make_calc_enzymes_tab(self):
        item = TabbedPanelItem(text='Ферменты')
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        gs = Spinner(text='Пшеница', values=GRAIN_DISPLAY_NAMES, size_hint_y=None, height=dp(50))
        ai = TextInput(hint_text='Количество зерна (кг)', multiline=False, size_hint_y=None, height=dp(50))
        res = Label(text='', size_hint_y=None, height=dp(120))

        def calc(inst):
            try:
                enz = self.logic.calculate_enzymes({GRAIN_KEY_MAP[gs.text]: float(ai.text)})
                res.text = "\n".join(f"{n}: {v} г" for n, v in enz.items())
            except Exception as e:
                res.text = f"Ошибка: {e}"

        b = Button(text='Рассчитать ферменты', size_hint_y=None, height=dp(50))
        b.bind(on_press=calc)
        for w in (gs, ai, b, res):
            box.add_widget(w)
        item.content = box
        return item

    def _make_calc_yeast_tab(self):
        item = TabbedPanelItem(text='Дрожжи')
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        wi = TextInput(hint_text='Объём затора (л)', multiline=False, size_hint_y=None, height=dp(50))
        yi = TextInput(text='спиртовые', hint_text='Тип дрожжей', multiline=False, size_hint_y=None, height=dp(50))
        res = Label(text='', size_hint_y=None, height=dp(60))

        def calc(inst):
            try:
                res.text = f"Требуется дрожжей: {self.logic.calculate_yeast(float(wi.text), yi.text.strip())} г"
            except Exception as e:
                res.text = f"Ошибка: {e}"

        b = Button(text='Рассчитать дрожжи', size_hint_y=None, height=dp(50))
        b.bind(on_press=calc)
        for w in (wi, yi, b, res):
            box.add_widget(w)
        item.content = box
        return item

    def _make_calc_heads_tab(self):
        item = TabbedPanelItem(text='Головы')
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        vi = TextInput(hint_text='Объём спирта-сырца (мл)', multiline=False, size_hint_y=None, height=dp(50))
        si = TextInput(hint_text='Крепость спирта-сырца (%)', multiline=False, size_hint_y=None, height=dp(50))
        pi = TextInput(text='10', hint_text='Процент отбора голов (%)', multiline=False, size_hint_y=None, height=dp(50))
        res = Label(text='', size_hint_y=None, height=dp(100))

        def calc(inst):
            try:
                ac = float(vi.text) * float(si.text) / 100
                heads = ac * float(pi.text or 10) / 100
                res.text = f"Абсолютный спирт: {ac:.0f} мл\nОбъём голов: {heads:.0f} мл"
            except Exception as e:
                res.text = f"Ошибка: {e}"

        b = Button(text='Рассчитать головы', size_hint_y=None, height=dp(50))
        b.bind(on_press=calc)
        for w in (vi, si, pi, b, res):
            box.add_widget(w)
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

        self.plan_save_btn = Button(text='Сохранить план в HTML',
                                     size_hint_y=None, height=dp(50), disabled=True)
        self.plan_save_btn.bind(on_press=self._save_plan_html)
        box.add_widget(self.plan_save_btn)

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
        all_recipes = self.logic.get_all_recipes()
        recipe = next((r for r in all_recipes if r['название'] == self.plan_spinner.text), None)
        if not recipe:
            return
        self._open_edit_recipe_dialog(recipe)

    def _open_edit_recipe_dialog(self, recipe):
        box = BoxLayout(orientation='vertical', padding=10, spacing=6)

        source_text = "Исходный состав: " + ", ".join(
            f"{g} {a} кг" for g, a in recipe['зерно'].items())
        box.add_widget(Label(text=source_text, size_hint_y=None, height=dp(40)))

        total_grain_original = sum(recipe['зерно'].values())
        box.add_widget(Label(text='Общее количество зерна (кг):', size_hint_y=None, height=dp(25)))
        grain_in = TextInput(text=str(total_grain_original), multiline=False,
                              input_filter='float', size_hint_y=None, height=dp(45))
        box.add_widget(grain_in)

        box.add_widget(Label(text='Гидромодуль (например 1:4):', size_hint_y=None, height=dp(25)))
        hydro_in = TextInput(text=recipe['гидромодуль'], multiline=False,
                              size_hint_y=None, height=dp(45))
        box.add_widget(hydro_in)

        calc_label = Label(text='', size_hint_y=None, height=dp(130),
                            halign='left', valign='top')
        calc_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], val[1])))
        box.add_widget(calc_label)

        def recalc(*args):
            try:
                total_grain = float(grain_in.text)
                ratio_str = hydro_in.text.strip()
                ratio = float(ratio_str.split(':')[1])
                water = total_grain * ratio
                scale = total_grain / total_grain_original if total_grain_original > 0 else 0
                scaled = {g: round(a * scale, 2) for g, a in recipe['зерно'].items()}
                enzymes = self.logic.calculate_enzymes(scaled)
                ac = sum(self.logic.grain_base.get(g, {}).get('выход_спирта', 0) * a
                          for g, a in scaled.items())
                lines = [f"Воды: {water:.1f} л"]
                for name, val in enzymes.items():
                    lines.append(f"{name}: {val} г")
                lines.append(f"Ожидаемый выход АС: {ac:.2f} л")
                calc_label.text = "\n".join(lines)
            except Exception:
                calc_label.text = "Введите корректные числа"

        grain_in.bind(text=recalc)
        hydro_in.bind(text=recalc)
        recalc()

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=6)
        ok_btn = Button(text='Сгенерировать план')
        cancel_btn = Button(text='Отмена')
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        box.add_widget(btn_row)

        popup = Popup(title='Параметры варки', content=box, size_hint=(0.92, 0.92))

        def on_ok(inst):
            try:
                total_grain = float(grain_in.text)
                ratio = float(hydro_in.text.strip().split(':')[1])
            except Exception:
                info_popup('Ошибка', 'Проверьте числа')
                return
            scale = total_grain / total_grain_original if total_grain_original > 0 else 0
            scaled = {g: round(a * scale, 2) for g, a in recipe['зерно'].items()}
            modified = dict(recipe)
            modified['зерно'] = scaled
            modified['гидромодуль'] = f"1:{ratio}"
            popup.dismiss()
            self._build_and_show_plan(modified)

        def on_cancel(inst):
            popup.dismiss()

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=on_cancel)
        popup.open()

    def _build_and_show_plan(self, recipe):
        self.plan_layout.clear_widgets()

        water = self.logic.calculate_water_volume(recipe)
        enzymes = self.logic.calculate_enzymes(recipe['зерно'])
        ac_yield = sum(self.logic.grain_base.get(g, {}).get('выход_спирта', 0) * a
                        for g, a in recipe['зерно'].items())

        summary_lines = [
            f"Зерно: {sum(recipe['зерно'].values()):.1f} кг",
            f"Вода: {water:.1f} л",
            "Ферменты: " + ", ".join(f"{n} {v} г" for n, v in enzymes.items()),
            f"Ожидаемый выход: {ac_yield:.2f} л АС",
        ]
        summary = Label(text="\n".join(summary_lines),
                         size_hint_y=None, height=dp(110),
                         halign='left', valign='top',
                         color=(0.1, 0.4, 0.8, 1))
        summary.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], val[1])))
        self.plan_layout.add_widget(summary)

        try:
            plan = self.logic.generate_plan(recipe)
        except Exception as e:
            self.plan_layout.add_widget(Label(text=f"Ошибка плана: {e}",
                                                size_hint_y=None, height=dp(60)))
            return

        self._last_plan = plan
        self._last_plan_recipe_name = recipe['название']
        self.plan_save_btn.disabled = False

        try:
            self.logic.brew_log.add_entry(
                recipe_name=recipe['название'],
                grain_bill=recipe['зерно'].copy(),
                og=None, fg=None, yield_ml=None,
                notes=f"Запланировано: {recipe['название']}")
            try:
                self._refresh_log()
            except Exception:
                pass
            note = Label(text="Запись добавлена в журнал",
                          size_hint_y=None, height=dp(30),
                          color=(0.2, 0.7, 0.2, 1))
            self.plan_layout.add_widget(note)
        except Exception as e:
            print(f"Не удалось записать в журнал: {e}")

        for step in plan:
            text = f"День {step['день']} | {step['этап']}\n{step['действие']}\nВремя: {step['время']}"
            lbl = Label(text=text, size_hint_y=None, halign='left', valign='top')
            lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(10)))
            lbl.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
            self.plan_layout.add_widget(lbl)

    def _save_plan_html(self, instance):
        plan = getattr(self, '_last_plan', None)
        name = getattr(self, '_last_plan_recipe_name', None)
        if not plan or not name:
            info_popup('Нечего сохранять', 'Сначала сгенерируйте план.')
            return
        try:
            path = self.logic.export_plan_to_html(plan, name)
            info_popup('План сохранён', f"Файл: {path}")
        except Exception as e:
            info_popup('Ошибка', str(e))

    def _check_fermentation_notifications(self):
        try:
            notifications = self.logic.brew_log.check_fermentation_notifications()
        except Exception as e:
            print(f"Ошибка проверки брожения: {e}")
            return
        pending = []
        for idx, name, dt_str in notifications:
            entry = self.logic.brew_log.get_entry(idx)
            if entry and not entry.get('notified'):
                pending.append((idx, name, dt_str))
        if not pending:
            return
        lines = [f"• {name}  (окончание: {dt_str})" for _, name, dt_str in pending]
        text = "Брожение завершено. Пора проверять брагу:\n\n" + "\n".join(lines)
        for idx, _, _ in pending:
            self.logic.brew_log.update_entry(idx, 'notified', True)
        popup = Popup(title='Брожение завершено',
                       content=Label(text=text, halign='left', valign='top'),
                       size_hint=(0.85, 0.5))
        popup.open()

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
            rating = entry.get('rating')
            rating_str = f" [{rating}/5]" if rating else ""
            label_text = f"{entry['date']} | {entry['recipe']}{rating_str}"
            btn = Button(text=label_text)
            btn.bind(on_press=lambda x, idx=real_index: self._show_log_entry(idx))
            row.add_widget(btn)
            del_btn = Button(text='X', size_hint_x=None, width=dp(45))
            del_btn.bind(on_press=lambda x, idx=real_index: self._delete_log_entry(idx))
            row.add_widget(del_btn)
            self.log_layout.add_widget(row)

    def _show_log_entry(self, index):
        entry = self.logic.brew_log.get_entry(index)
        if not entry:
            return
        box = BoxLayout(orientation='vertical', padding=12, spacing=8)
        info = Label(
            text=(f"Рецепт: {entry['recipe']}\n"
                  f"Дата: {entry['date']}\n"
                  f"OG: {entry.get('original_gravity')}  |  FG: {entry.get('final_gravity')}\n"
                  f"Выход: {entry.get('alcohol_yield_ml')} мл"),
            size_hint_y=None, height=dp(90), halign='left', valign='top')
        info.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], val[1])))
        box.add_widget(info)
        box.add_widget(Label(text='Заметки:', size_hint_y=None, height=dp(25)))
        notes_in = TextInput(text=entry.get('notes') or '', multiline=True,
                             size_hint_y=None, height=dp(90))
        box.add_widget(notes_in)
        box.add_widget(Label(text='Оценка (1-5):', size_hint_y=None, height=dp(25)))
        stars_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=4)
        current = {'rating': entry.get('rating') or 0}
        btns = []

        def refresh_buttons():
            for i, b in enumerate(btns, 1):
                b.background_color = (0.2, 0.7, 0.2, 1) if i == current['rating'] else (0.5, 0.5, 0.5, 1)

        def handler(v):
            def h(inst):
                current['rating'] = v
                refresh_buttons()
            return h

        for i in range(1, 6):
            b = Button(text=str(i), size_hint_x=None, width=dp(60))
            b.bind(on_press=handler(i))
            btns.append(b)
            stars_row.add_widget(b)
        refresh_buttons()
        box.add_widget(stars_row)
        box.add_widget(Label(text='Начало брожения (ГГГГ-ММ-ДД ЧЧ:ММ):', size_hint_y=None, height=dp(25)))
        start_in = TextInput(text=entry.get('fermentation_start') or '',
                              multiline=False, size_hint_y=None, height=dp(45))
        box.add_widget(start_in)
        box.add_widget(Label(text='Окончание брожения:', size_hint_y=None, height=dp(25)))
        end_in = TextInput(text=entry.get('fermentation_end') or '',
                            multiline=False, size_hint_y=None, height=dp(45))
        box.add_widget(end_in)
        save_btn = Button(text='Сохранить изменения', size_hint_y=None, height=dp(50))
        box.add_widget(save_btn)
        popup = Popup(title=f"Запись: {entry['recipe']}", content=box, size_hint=(0.92, 0.92))

        def save(inst):
            self.logic.brew_log.add_notes(index, notes_in.text.strip())
            if current['rating'] >= 1:
                self.logic.brew_log.set_rating(index, current['rating'])
            if start_in.text.strip():
                self.logic.brew_log.set_fermentation_start(index, start_in.text.strip())
            if end_in.text.strip():
                self.logic.brew_log.set_fermentation_end(index, end_in.text.strip())
            popup.dismiss()
            self._refresh_log()
            info_popup('Сохранено', f"Запись обновлена")

        save_btn.bind(on_press=save)
        popup.open()

    def _delete_log_entry(self, index):
        self.logic.brew_log.delete_entry(index)
        self._refresh_log()

    def _open_add_log_form(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=6)
        names = [r['название'] for r in self.logic.get_all_recipes()]
        sp = Spinner(text=names[0] if names else '', values=names, size_hint_y=None, height=dp(45))
        og_in = TextInput(hint_text='Начальная плотность (OG)', multiline=False, size_hint_y=None, height=dp(45))
        fg_in = TextInput(hint_text='Конечная плотность (FG)', multiline=False, size_hint_y=None, height=dp(45))
        y_in = TextInput(hint_text='Выход, мл', multiline=False, size_hint_y=None, height=dp(45))
        n_in = TextInput(hint_text='Заметки', multiline=True, size_hint_y=None, height=dp(80))
        for w in (sp, og_in, fg_in, y_in, n_in):
            box.add_widget(w)
        save_btn = Button(text='Сохранить', size_hint_y=None, height=dp(50))
        box.add_widget(save_btn)
        popup = Popup(title='Новая запись', content=box, size_hint=(0.9, 0.85))

        def tf(t):
            t = t.strip()
            if not t:
                return None
            try:
                return float(t)
            except ValueError:
                return None

        def save(inst):
            rname = sp.text
            rec = next((r for r in self.logic.get_all_recipes() if r['название'] == rname), None)
            gb = rec['зерно'] if rec else {}
            self.logic.brew_log.add_entry(rname, gb, tf(og_in.text), tf(fg_in.text),
                                            tf(y_in.text), n_in.text.strip())
            popup.dismiss()
            self._refresh_log()

        save_btn.bind(on_press=save)
        popup.open()

    # ==================== СТАТИСТИКА ====================
    def _build_stats_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        refresh_btn = Button(text='Обновить статистику', size_hint_y=None, height=dp(50))
        refresh_btn.bind(on_press=lambda x: self._refresh_stats())
        box.add_widget(refresh_btn)
        scroll = ScrollView()
        self.stats_label = Label(text='', size_hint_y=None, halign='left', valign='top')
        self.stats_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        self.stats_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        scroll.add_widget(self.stats_label)
        box.add_widget(scroll)
        self._refresh_stats()
        return box

    def _refresh_stats(self):
        entries = self.logic.brew_log.entries
        if not entries:
            self.stats_label.text = "Журнал пуст — статистики нет."
            return
        lines = []
        s = self.logic.brew_log.get_statistics()
        lines.append("=== Общая статистика ===")
        lines.append(f"Всего варок: {s['total_brews']}")
        lines.append(f"Средний выход: {s['avg_yield']:.0f} мл")
        lines.append(f"Последняя: {s['last_brew']}\n")
        lines.append("=== По рецептам ===")
        for r in self.logic.brew_log.get_recipe_stats():
            ar = f"{r['avg_rating']:.1f}" if r['avg_rating'] else "нет"
            lines.append(f"{r['recipe']}: варок {r['count']}, ср.выход {r['avg_yield']:.0f} мл, оценка {ar}")
        lines.append("\n=== Распределение оценок ===")
        d = self.logic.brew_log.get_rating_distribution()
        any_r = False
        for rating in [5, 4, 3, 2, 1]:
            c = d.get(rating, 0)
            if c > 0:
                lines.append(f"{rating}/5: {c}")
                any_r = True
        if not any_r:
            lines.append("Оценок пока нет")
        lines.append("\n=== По месяцам ===")
        for m, c in sorted(self.logic.brew_log.get_monthly_stats().items(), reverse=True):
            lines.append(f"{m}: {c}")
        self.stats_label.text = "\n".join(lines)

    # ==================== ДРОЖЖИ ====================
    def _build_yeast_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=6)
        sr = BoxLayout(size_hint_y=None, height=dp(50), spacing=6)
        self.yeast_search_input = TextInput(hint_text='Поиск', multiline=False)
        sb = Button(text='Искать', size_hint_x=None, width=dp(90))
        sb.bind(on_press=lambda x: self._search_yeasts())
        cb = Button(text='Сброс', size_hint_x=None, width=dp(90))
        cb.bind(on_press=lambda x: self._refresh_yeasts())
        sr.add_widget(self.yeast_search_input)
        sr.add_widget(sb)
        sr.add_widget(cb)
        box.add_widget(sr)
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
        q = self.yeast_search_input.text.strip()
        if not q:
            self._refresh_yeasts()
            return
        self._render_yeasts(self.logic.yeast_db.search(q))

    def _render_yeasts(self, yeasts):
        self.yeast_layout.clear_widgets()
        if not yeasts:
            self.yeast_layout.add_widget(Label(text='Ничего не найдено', size_hint_y=None, height=dp(40)))
            return
        for y in yeasts:
            text = (f"{y['название']} ({y['тип']})\n"
                    f"Темп: {y['темп_мин']}-{y['темп_макс']}°C | Толерантность: {y['алко_толерантность']}%\n"
                    f"{y['описание']}\nРекомендации: {', '.join(y.get('рекомендации', []))}")
            lbl = Label(text=text, size_hint_y=None, halign='left', valign='top')
            lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(10)))
            lbl.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
            self.yeast_layout.add_widget(lbl)

    # ==================== ПОМОЩЬ ====================
    def _build_help_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.question_input = TextInput(hint_text='Ваш вопрос...', multiline=False,
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
        save_btn = Button(text='Сохранить инструкцию в HTML', size_hint_y=None, height=dp(50))
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
            "• [b]План варки[/b] — пошаговый план с редактированием параметров\n"
            "• [b]Журнал[/b] — заметки, оценки, даты брожения\n"
            "• [b]Статистика[/b] — сводка по рецептам, оценкам, месяцам\n"
            "• [b]Таймеры[/b] — несколько параллельных таймеров\n"
            "• [b]Дрожжи[/b] — база с характеристиками\n"
            "• [b]Помощь[/b] — быстрые ответы\n"
            "• [b]Ссылки[/b] — Telegram и форумы\n\n"

            "[b][size=16]Генерация плана варки (важно!)[/size][/b]\n"
            "1. Откройте «План варки», выберите рецепт\n"
            "2. Нажмите «Сгенерировать план» — откроется окно «Параметры варки»\n"
            "3. Измените количество зерна и/или гидромодуль под свои условия\n"
            "4. Программа [b]мгновенно пересчитает[/b]:\n"
            "    - объём воды\n"
            "    - количество ферментов\n"
            "    - ожидаемый выход абсолютного спирта\n"
            "5. Нажмите «Сгенерировать план» — план появится с расчётными данными\n"
            "6. Запись автоматически попадёт в Журнал\n"
            "7. Кнопкой «Сохранить план в HTML» можно выгрузить план в файл\n\n"

            "[b][size=16]Журнал и уведомления[/size][/b]\n"
            "• Нажмите на запись — откроется редактор (заметки, оценка, даты)\n"
            "• Укажите дату окончания брожения в формате ГГГГ-ММ-ДД ЧЧ:ММ\n"
            "• При следующем запуске приложение напомнит о завершённом брожении\n\n"

            "[b][size=16]Советы[/size][/b]\n"
            "• Используйте Таймеры для контроля пауз осахаривания\n"
            "• Дрожжи выбирайте по температуре и типу зерна\n"
            "• Статистика покажет, какие рецепты у вас в почёте\n\n"

            "[color=#b8860b][b]Внимание:[/b] Соблюдайте законодательство вашей страны "
            "в отношении производства алкогольных напитков.[/color]"
        )

    def _save_instruction_html(self, instance):
        try:
            path = self.logic.export_instruction_to_html()
            info_popup('Инструкция сохранена', f"Файл: {path}")
        except Exception as e:
            info_popup('Ошибка', str(e))

    # ==================== ССЫЛКИ ====================
    def _build_links_tab(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        links = [
            ("Мой Telegram-канал", "https://t.me/vilko_zerno"),
            ("Форум «Самогонщики»", "https://forum.homedistiller.ru/"),
            ("Форум «АлкоФан»", "https://alkofan.com/"),
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
