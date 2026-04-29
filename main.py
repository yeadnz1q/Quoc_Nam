import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.error
import json
import os
from datetime import datetime

class CurrencyConverterApp:
    # Публичный API ExchangeRate (не требует ключа для базового использования)
    API_BASE_URL = "https://api.exchangerate-api.com/v4/latest/"
    
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter — Конвертер валют")
        self.root.geometry("800x650")
        self.root.minsize(700, 550)
        
        self.history_file = "conversion_history.json"
        self.exchange_rates = {}
        self.base_currency = "USD"
        self.currencies = []
        self.history = []
        
        self.load_history()
        self.setup_ui()
        self.load_exchange_rates()

    def setup_ui(self):
        # === Верхняя панель: выбор валют и сумма ===
        input_frame = tk.LabelFrame(self.root, text="Параметры конвертации", 
                                    padx=15, pady=12, font=("Arial", 10, "bold"))
        input_frame.pack(fill="x", padx=12, pady=10)

        # Сумма
        tk.Label(input_frame, text="Сумма:").grid(row=0, column=0, sticky="w", pady=5)
        self.amount_var = tk.StringVar(value="1")
        self.amount_entry = tk.Entry(
            input_frame, textvariable=self.amount_var, 
            width=15, font=("Arial", 11), justify="right"
        )
        self.amount_entry.grid(row=0, column=1, padx=8, pady=5)
        self.amount_entry.bind("<Return>", lambda e: self.convert_currency())

        # Валюта "ИЗ"
        tk.Label(input_frame, text="Из:").grid(row=0, column=2, sticky="w", padx=(20, 5))
        self.from_currency_var = tk.StringVar(value="USD")
        self.from_currency_combo = ttk.Combobox(
            input_frame, textvariable=self.from_currency_var,
            state="readonly", width=10, font=("Arial", 10)
        )
        self.from_currency_combo.grid(row=0, column=3, padx=5, pady=5)

        # Валюта "В"
        tk.Label(input_frame, text="В:").grid(row=0, column=4, sticky="w", padx=(20, 5))
        self.to_currency_var = tk.StringVar(value="EUR")
        self.to_currency_combo = ttk.Combobox(
            input_frame, textvariable=self.to_currency_var,
            state="readonly", width=10, font=("Arial", 10)
        )
        self.to_currency_combo.grid(row=0, column=5, padx=5, pady=5)

        # Кнопка конвертации
        convert_btn = tk.Button(
            input_frame, text="Конвертировать", command=self.convert_currency,
            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=15
        )
        convert_btn.grid(row=0, column=6, padx=20, pady=5)

        # Результат
        self.result_var = tk.StringVar(value="Введите сумму и нажмите «Конвертировать»")
        result_label = tk.Label(
            input_frame, textvariable=self.result_var,
            font=("Arial", 13, "bold"), fg="#1976D2", anchor="center", relief="sunken", bd=1
        )
        result_label.grid(row=1, column=0, columnspan=7, pady=12, sticky="ew")

        input_frame.columnconfigure(1, weight=1)

        # === Блок управления ===
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill="x", padx=12, pady=5)

        tk.Button(
            control_frame, text="Обновить курсы", command=self.load_exchange_rates,
            bg="#2196F3", fg="white"
        ).pack(side="left", padx=5)
        
        tk.Button(
            control_frame, text="Очистить историю", command=self.clear_history,
            bg="#f44336", fg="white"
        ).pack(side="right", padx=5)

        # === Таблица истории ===
        history_frame = tk.LabelFrame(self.root, text="История конвертаций", 
                                      padx=10, pady=10)
        history_frame.pack(fill="both", expand=True, padx=12, pady=10)

        columns = ("time", "from_curr", "to_curr", "amount", "result", "rate")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings")

        # Заголовки
        self.tree.heading("time", text="Время")
        self.tree.heading("from_curr", text="Из")
        self.tree.heading("to_curr", text="В")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("result", text="Результат")
        self.tree.heading("rate", text="Курс")

        # Ширина колонок
        self.tree.column("time", width=140, anchor="center")
        self.tree.column("from_curr", width=70, anchor="center")
        self.tree.column("to_curr", width=70, anchor="center")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("result", width=120, anchor="e")
        self.tree.column("rate", width=110, anchor="e")

        # Прокрутка
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var, bd=1, 
            relief="sunken", anchor="w", padx=10, pady=3, fg="#555"
        )
        status_bar.pack(side="bottom", fill="x")

        self.update_history_view()

    def load_exchange_rates(self):
        """Загружает актуальные курсы валют из API."""
        self.status_var.set("Загрузка курсов валют...")
        self.root.update()
        
        try:
            url = self.API_BASE_URL + self.base_currency
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            self.exchange_rates = data.get("rates", {})
            self.currencies = sorted(self.exchange_rates.keys())
            
            # Обновляем списки валют
            self.from_currency_combo["values"] = self.currencies
            self.to_currency_combo["values"] = self.currencies
            
            # Устанавливаем значения по умолчанию
            if "USD" in self.currencies:
                self.from_currency_var.set("USD")
            if "EUR" in self.currencies:
                self.to_currency_var.set("EUR")
                
            self.status_var.set(f"Загружено {len(self.currencies)} валют")
            messagebox.showinfo("Успех", "Курсы валют успешно обновлены!")
            
        except urllib.error.HTTPError as e:
            if e.code == 429:
                self.status_var.set("Превышен лимит запросов API")
                messagebox.showwarning("Лимит API", "Превышено количество запросов. Попробуйте позже.")
            else:
                self.status_var.set(f"Ошибка API: {e.code}")
                messagebox.showerror("Ошибка", f"Ошибка сервера: {e.code}")
                
        except urllib.error.URLError:
            self.status_var.set("Нет подключения к интернету")
            messagebox.showerror("Ошибка сети", "Проверьте подключение к интернету")
            
        except Exception as e:
            self.status_var.set(f"Ошибка: {type(e).__name__}")
            messagebox.showerror("Ошибка", f"Неожиданная ошибка: {e}")

    def convert_currency(self):
        """Выполняет конвертацию валют."""
        # === Валидация суммы ===
        try:
            amount = float(self.amount_var.get().strip())
            if amount <= 0:
                raise ValueError("Отрицательное число")
        except ValueError:
            messagebox.showwarning("Ошибка ввода", 
                "Сумма должна быть положительным числом!\nПример: 100 или 15.5")
            self.amount_entry.focus()
            return

        from_curr = self.from_currency_var.get().strip()
        to_curr = self.to_currency_var.get().strip()
        
        if not from_curr or not to_curr:
            messagebox.showwarning("Выбор валют", "Выберите валюты для конвертации!")
            return

        if not self.exchange_rates:
            messagebox.showwarning("Нет курсов", "Сначала загрузите курсы валют!")
            return

        try:
            # === Расчёт конвертации ===
            if from_curr == to_curr:
                result = amount
                rate = 1.0
            else:
                # Конвертация через базовую валюту (USD)
                amount_in_base = amount / self.exchange_rates[from_curr]
                result = amount_in_base * self.exchange_rates[to_curr]
                rate = self.exchange_rates[to_curr] / self.exchange_rates[from_curr]

            result_rounded = round(result, 2)
            rate_rounded = round(rate, 6)
            
            # Форматирование результата
            result_text = f"{amount:,.2f} {from_curr} = {result_rounded:,.2f} {to_curr}"
            self.result_var.set(result_text)
            
            # === Запись в историю ===
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "from_currency": from_curr,
                "to_currency": to_curr,
                "amount": amount,
                "result": result_rounded,
                "exchange_rate": rate_rounded
            }
            self.history.insert(0, entry)  # Новые записи сверху
            
            # Ограничиваем историю 100 записями
            if len(self.history) > 100:
                self.history = self.history[:100]
                
            self.save_history()
            self.update_history_view()
            
            self.status_var.set(f"Конвертация выполнена: {result_text}")
            
        except KeyError as e:
            messagebox.showerror("Ошибка", f"Валюта не найдена: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка конвертации: {e}")

    def update_history_view(self):
        """Обновляет отображение таблицы истории."""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Заполнение данными
        for item in self.history:
            self.tree.insert("", "end", values=(
                item["timestamp"],
                item["from_currency"],
                item["to_currency"],
                f"{item['amount']:,.2f}",
                f"{item['result']:,.2f}",
                f"{item['exchange_rate']:.6f}"
            ))

    def save_history(self):
        """Сохраняет историю в JSON файл."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except IOError as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить историю:\n{e}")

    def load_history(self):
        """Загружает историю из JSON файла."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except json.JSONDecodeError:
                messagebox.showwarning("Ошибка", "Файл истории повреждён. Создан новый.")
                self.history = []
            except IOError:
                self.history = []

    def clear_history(self):
        """Очищает историю с подтверждением."""
        if not self.history:
            messagebox.showinfo("Информация", "История уже пуста.")
            return
            
        if messagebox.askyesno("Подтверждение", 
            "Вы действительно хотите очистить всю историю конвертаций?\nЭто действие нельзя отменить."):
            self.history = []
            self.save_history()
            self.update_history_view()
            self.status_var.set("История очищена")

    def on_closing(self):
        """Обработчик закрытия окна."""
        self.save_history()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    
    # Настройка современной темы
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    
    app = CurrencyConverterApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
