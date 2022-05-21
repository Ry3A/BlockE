from tkinter import *
import tkinter.ttk as ttk
from tkinter.ttk import Notebook, Frame, Combobox, Checkbutton, Radiobutton
import xml.dom.minidom
import urllib.request
import matplotlib
import matplotlib.pyplot as plt
import random
import datetime
import re
from calendar import monthrange

RUBLE_SLUG = 'Российский рубль'
CBR_URL = 'http://www.cbr.ru/scripts/XML_daily.asp'
SORT_CURRENCY_LIST = False
NUMBER_OF_PERIODS = 4
QUARTERS_SLUGS = ['I квартал', 'II квартал', 'III квартал', 'IV квартал']
IGNORE_NON_COMING_DAYS = False
MONTHS_SLUGS = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь',
                'Декабрь']
RANDOM_CURRENCY = True
NUMBER_OF_POINTS_IN_INDICATOR = 5
LOADER_PIXEL = 5


def convert_currency_input_to_btn() -> None:
    try:
        value = float(enter.get().replace(',', '.'))  # тут куда мы пишем
        label1.configure(fg='black')  # тут куда получаем
        currency_from = combobox1.get()  # валюта из
        currency_to = combobox2.get()  # валюта в
        if currency_from and currency_to:
            label1.configure(  # туда куда получаем
                text=(1 / get_current_exchange_rate(currency_from)) * get_current_exchange_rate(currency_to) * value)
            # print(currency_from, '->', currency_to)
            # print((1 / get_current_exchange_rate(currency_from)) * get_current_exchange_rate(currency_to))
            # print('======')
        else:
            label1.configure(fg='red')
            label1.configure(text="Не выбрана валюта")
    except ValueError:
        label1.configure(fg='red')
        label1.configure(text="Не является числом")


# тут список денег
def get_currency_list(with_ruble: bool = True) -> list:
    currency_list = [RUBLE_SLUG] if with_ruble else []
    response = urllib.request.urlopen(CBR_URL)
    dom = xml.dom.minidom.parse(response)  # Получение DOM структуры файла
    dom.normalize()
    node_array = dom.getElementsByTagName("ValCurs")  # Получение элементов с тегом
    for currency in node_array:  # Перебираем по валютам
        for data in currency.childNodes:
            currency_list.append(data.childNodes[3].childNodes[0].nodeValue)
    return sorted(currency_list) if SORT_CURRENCY_LIST else currency_list


# тут курс обмена валют
def get_current_exchange_rate(currency: str = None, date: datetime.datetime = None, num_code: int = None) -> float:
    if currency == RUBLE_SLUG:
        return 1.0
    response = urllib.request.urlopen(CBR_URL + (f'?date_req={str(date.strftime("%d/%m/%Y"))}' if date else ''))
    # print(f'?date_req={str(date.strftime("%d/%m/%Y"))}' if date else '')
    dom = xml.dom.minidom.parse(response)  # Получение DOM структуры айла
    dom.normalize()
    node_array = dom.getElementsByTagName("ValCurs")  # Получили список объектов валют
    for currency_data in node_array:  # Перебираем по валютам
        for data in currency_data.childNodes:
            if data.childNodes[3].childNodes[0].nodeValue == currency or \
                    int(data.childNodes[0].childNodes[0].nodeValue) == num_code:
                # print(float(data.childNodes[4].childNodes[0].nodeValue.replace(',', '.')) / float(
                #     data.childNodes[2].childNodes[0].nodeValue.replace(',', '.')))
                return float(data.childNodes[4].childNodes[0].nodeValue.replace(',', '.')) / float(
                    data.childNodes[2].childNodes[0].nodeValue.replace(',', '.'))


def get_currency_num_code(currency: str) -> int:
    if currency == RUBLE_SLUG:
        return 1
    response = urllib.request.urlopen(CBR_URL)
    dom = xml.dom.minidom.parse(response)  # Получение DOM структуры айла
    dom.normalize()
    node_array = dom.getElementsByTagName("ValCurs")  # Получили список объектов валют
    for currency_data in node_array:  # Перебираем по валютам
        for data in currency_data.childNodes:
            if data.childNodes[3].childNodes[0].nodeValue == currency:
                return int(data.childNodes[0].childNodes[0].nodeValue)


def draw_currency_graph() -> None:
    # Очищаем и подготавливаем график
    plt.close()
    fig = plt.figure()
    canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(fig, master=tab2)
    plot_widget = canvas.get_tk_widget()
    canvas.get_tk_widget()
    fig.clear()

    # Включаем индикатор
    start_load_indicator()

    # Получаем данные для построения
    now = datetime.datetime.now()
    pr = radio_period_state.get()
    num_of_period = combobox4.current()
    delta = datetime.timedelta(days=1)
    currency_num_code = get_currency_num_code(combobox3.get())
    now_day = now.day
    num_of_points: int = 0
    labels: [str] = []
    x: [float] = []
    y: [float] = []
    if pr == 1:
        now -= (num_of_period + 1) * 7 * delta - delta
        num_of_points = 7
        for i in range(num_of_points):
            x.append(i)
            y.append(get_current_exchange_rate(date=now, num_code=currency_num_code))
            labels.append(str(now.strftime('%d.%m.%Y')) if not i % 2 else '')
            now += delta
            next_load_indicator()
    elif pr == 2:
        num_of_points = get_number_of_days_in_month(now)
        now -= (now.day - 1) * delta
        for i in range(num_of_period):
            now -= delta
            num_of_points = get_number_of_days_in_month(now)
            now -= (num_of_points - 1) * delta
            now_day = num_of_points
        for i in range(num_of_points):
            if i < now_day or IGNORE_NON_COMING_DAYS:
                x.append(i)
                y.append(get_current_exchange_rate(date=now, num_code=currency_num_code))
            labels.append(str(now.day) if i < 9 or not i % 2 else '')
            now += delta
            next_load_indicator()
    elif pr == 3:
        now -= num_of_period * 3 * 30 * delta  # Попадаем в нужный квартал
        now = get_first_day_of_quarter(now)
        num_of_points_l_t = 0
        for j in range(3):
            num_of_points_t = get_number_of_days_in_month(now)
            for i in range(num_of_points_t):
                if not i % 4:
                    num_of_points += 1
                    x.append(i // 4 + num_of_points_l_t)
                    y.append(get_current_exchange_rate(date=now, num_code=currency_num_code))  # Курс
                    labels.append(
                        get_month_slug(now)[:3] if i == 0 else (str(now.day) if 5 < i < 28 and not i % 2 else ''))
                    next_load_indicator()
                now += delta
            num_of_points_l_t = num_of_points  # Для подcчета последующих координат
    elif pr == 4:
        now -= num_of_period * 365 * delta  # Попадаем в нужный год
        num_of_points = 24
        for i in range(num_of_points):
            date = datetime.datetime(year=now.year, month=(i // 2 + 1), day=(1 if not i % 2 else 15))
            x.append(i)
            y.append(get_current_exchange_rate(
                date=date,
                num_code=currency_num_code))  # Курс
            labels.append(get_month_slug(date)[:3] if not i % 2 else '')
            next_load_indicator()

    plt.plot(x, y)
    plt.xticks(range(num_of_points), labels)
    plt.grid()
    plot_widget.grid(column=4, row=6)
    end_load_indicator()


# Возвращает название месяца
def get_month_slug(date: datetime.datetime) -> str:
    return MONTHS_SLUGS[date.month % 12 - 1]


# Возвращает количество дней в месяце
def get_number_of_days_in_month(date: datetime.datetime) -> int:
    return monthrange(date.year, month=date.month)[1]


def change_selection_period() -> None:
    now = datetime.datetime.now()
    pr = radio_period_state.get()
    delta = datetime.timedelta(days=1)
    data = []

    if pr == 1:
        now -= 6 * delta
        for i in range(NUMBER_OF_PERIODS):
            data.append(str(now.strftime('%d.%m.%Y') + '-' + (now + 6 * delta).strftime('%d.%m.%Y')))
            now -= 7 * delta
    elif pr == 2:
        for i in range(NUMBER_OF_PERIODS):
            data.append(get_month_slug(now) + ' ' + str(now.year))
            now -= 30 * delta
    elif pr == 3:
        for i in range(NUMBER_OF_PERIODS):
            data.append(QUARTERS_SLUGS[get_current_quarter(now)] + ' ' + str(now.year))
            now -= 3 * 30 * delta
    elif pr == 4:
        for i in range(NUMBER_OF_PERIODS):
            data.append(str(now.year))
            now -= 365 * delta
    combobox4['values'] = data
    combobox4.current(0)


# Возвращает номер квартала (0-3)
def get_current_quarter(date: datetime.datetime) -> int:
    return (date.month - 1) // 3


# Возвращает первый день квартала
def get_first_day_of_quarter(date: datetime.datetime) -> datetime.datetime:
    delta = datetime.timedelta(days=1)  # Дельта
    nq = cq = get_current_quarter(date)  # Получаем номер текущего квартала
    while nq == cq:
        date -= delta
        nq = get_current_quarter(date)
    return date + delta


# Переводит индикатор в следующую позицию
def next_load_indicator() -> None:
    global loader_state
    loader_canvas.itemconfigure(loader_data[loader_state], fill='orange')
    loader_canvas.itemconfigure(loader_data[loader_state], outline='orange')
    loader_state = (loader_state + 1) % NUMBER_OF_POINTS_IN_INDICATOR
    loader_canvas.itemconfigure(loader_data[loader_state], fill='blue')
    loader_canvas.itemconfigure(loader_data[loader_state], outline='blue')
    tab2.update()


def end_load_indicator() -> None:
    for i in range(NUMBER_OF_POINTS_IN_INDICATOR):
        loader_canvas.itemconfigure(loader_data[i], fill='lightgreen')
        loader_canvas.itemconfigure(loader_data[i], outline='lightgreen')
    tab2.update()


def start_load_indicator() -> None:
    global loader_data, loader_state
    if not len(loader_data):
        d = LOADER_PIXEL
        for i in range(NUMBER_OF_POINTS_IN_INDICATOR):
            loader_data.append(
                loader_canvas.create_rectangle(d + 6 * d * i, d, 6 * d * i + 5 * d, 5 * d, fill="orange",
                                               outline='orange'))
    else:
        for i in range(NUMBER_OF_POINTS_IN_INDICATOR):
            loader_canvas.itemconfigure(loader_data[i], fill='orange')
            loader_canvas.itemconfigure(loader_data[i], outline='orange')
        loader_state = 0
    loader_canvas.itemconfigure(loader_data[0], fill='blue')
    loader_canvas.itemconfigure(loader_data[0], outline='blue')
    loader_canvas.grid(column=4, row=4)
    tab2.update()


if __name__ == '__main__':
    window = Tk()  # создается базовое окно приложения
    window.title("Конвертатор")
    window.geometry("600x200")

    tab_control = Notebook(window)  # виджет для управления вкладками
    # Вкладка 1
    tab1 = Frame(tab_control)  # виджет рамки(вкладка)
    tab_control.add(tab1, text="Калькулятор валют")
    combobox1 = Combobox(tab1)  # штука где буду выбирать денюжки
    combobox1["values"] = get_currency_list()  # сюда вероятно надо вкинуть массив
    combobox1.current(21 if SORT_CURRENCY_LIST else 0)
    combobox1.grid(column=0, row=0, padx=10, pady=15)
    combobox2 = Combobox(tab1)
    combobox2["values"] = get_currency_list()  # тут должны быть денюжки
    combobox2.current(0)
    combobox2.grid(column=0, row=1, padx=10, pady=15)
    label1 = Label(tab1, text="")
    label1.grid(column=1, row=1, padx=10, pady=15)
    btn1 = Button(tab1, text="Конвертировать", command=convert_currency_input_to_btn)
    btn1.grid(column=2, row=0, padx=10, pady=15)
    enter = Entry(tab1)  # текстовое поле
    enter.grid(column=1, row=0, padx=10, pady=15)

    # Вкладка 2
    tab2 = Frame(tab_control)
    tab_control.add(tab2, text="Динамика курса")
    combobox3 = Combobox(tab2)
    combobox3["values"] = get_currency_list()  # тут должны быть денюжки
    combobox3.current(
        random.randint(0, len(combobox2['values']) - 2) if RANDOM_CURRENCY else 0)
    # combobox3.grid(column=0, row=1, padx=10, pady=15)
    combobox3.grid(column=0, row=1, padx=10)
    label2 = Label(tab2, text="Валюта")
    # label2.grid(column=0, row=0, padx=10, pady=15)
    label2.grid(column=0, row=0)
    label3 = Label(tab2, text="Период")
    label3.grid(column=10, row=0, padx=10, pady=15)
    combobox4 = ttk.Combobox(tab2)
    # combobox4["values"] = (1)  # тут должны быть периоды денюжек
    # combobox4.current(0)
    # combobox4.grid(column=0, row=1, padx=10, pady=15)
    combobox4.grid(column=20, row=1, padx=10)
    radio_period_state = IntVar()
    radio_period_state.set(1)
    change_selection_period()

    rad1 = Radiobutton(tab2, text='Неделя', value=1, variable=radio_period_state,
                       command=change_selection_period)
    rad2 = Radiobutton(tab2, text='Месяц', value=2, variable=radio_period_state,
                       command=change_selection_period)
    rad3 = Radiobutton(tab2, text='Квартал', value=3, variable=radio_period_state,
                       command=change_selection_period)
    rad4 = Radiobutton(tab2, text='Год', value=4, variable=radio_period_state,
                       command=change_selection_period)
    rad1.grid(column=10, row=1)
    rad2.grid(column=10, row=2)
    rad3.grid(column=10, row=3)
    rad4.grid(column=10, row=4)
    label4 = Label(tab2, text="Выбор периода")
    label4.grid(column=20, row=0, padx=10, pady=15)

    btn2 = Button(tab2, text="Построить график", command=draw_currency_graph)
    btn2.grid(column=0, row=4)

    # Настраиваем способ отрисовки графика
    matplotlib.use('TkAgg')

    # Переменные для индикатора загрузки
    loader_canvas = Canvas(tab2, width=150, height=30)
    loader_data = []
    loader_state = 0

    tab_control.pack(expand=True, fill=BOTH)  # открытие вкладок
    window.mainloop()  # запуск главного цикла
    print("Приветик, а ты чего тут?")