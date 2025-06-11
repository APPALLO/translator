import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from deep_translator import GoogleTranslator, single_detection
import traceback
import requests
import time
import re
import json
import os
import threading
from tkinter import font
from PIL import Image, ImageTk, ImageDraw
from io import BytesIO

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gelişmiş Türkçe-İngilizce Çeviri Uygulaması")
        self.root.geometry("950x600")  # Daha büyük pencere
        self.root.resizable(True, True)
        
        # Varsayılan fontlar
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Segoe UI", size=10)
        self.header_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.button_font = font.Font(family="Segoe UI", size=10)
        self.logo_font = font.Font(family="Segoe UI", size=16, weight="bold")
        
        # Modern renk şeması
        self.colors = {
            "light": {
                "bg": "#f8f9fa",
                "text_bg": "white",
                "button": "#7952b3",  # Bootstrap mor
                "button_hover": "#614092",
                "button_text": "white",
                "label": "#343a40",
                "border": "#dee2e6",
                "accent": "#17a2b8"  # Vurgu rengi
            },
            "dark": {
                "bg": "#212529",
                "text_bg": "#343a40",
                "button": "#7952b3",
                "button_hover": "#614092",
                "button_text": "white",
                "label": "#f8f9fa",
                "border": "#495057",
                "accent": "#17a2b8"
            }
        }
        
        self.current_theme = "light"
        
        # Çeviri geçmişi
        self.history = []
        self.history_file = "translation_history.json"
        self.load_history()
        
        # Çeviri önbelleği
        self.translation_cache = {}
        
        # Desteklenen diller
        self.supported_languages = {
            "Türkçe": "tr",
            "İngilizce": "en",
            "Almanca": "de",
            "Fransızca": "fr",
            "İspanyolca": "es",
            "İtalyanca": "it",
            "Rusça": "ru",
            "Çince": "zh-CN",
            "Japonca": "ja",
            "Korece": "ko",
            "Arapça": "ar"
        }
        
        # Ana çerçeve
        self.root.configure(bg=self.colors[self.current_theme]["bg"])
        self.setup_ui()
        self.create_custom_styles()

    # Metin logo oluşturma
    def create_text_logo(self, size=(50, 50)):
        logo_frame = tk.Frame(
            width=size[0],
            height=size[1],
            bg=self.colors[self.current_theme]["accent"],
            highlightthickness=0
        )
        logo_frame.pack_propagate(False)  # Boyutları sabit tut
        
        # Logo metni
        logo_text = tk.Label(
            logo_frame,
            text="Ç",
            font=self.logo_font,
            bg=self.colors[self.current_theme]["accent"],
            fg="white"
        )
        logo_text.pack(expand=True)
        
        return logo_frame

    def create_custom_styles(self):
        """Özel ttk stilleri oluştur"""
        style = ttk.Style()
        
        # Combobox stili
        style.configure("TCombobox", 
                      fieldbackground=self.colors[self.current_theme]["text_bg"],
                      background=self.colors[self.current_theme]["text_bg"])

        # Scrollbar stili
        style.configure("TScrollbar", 
                      background=self.colors[self.current_theme]["button"],
                      troughcolor=self.colors[self.current_theme]["bg"],
                      borderwidth=0,
                      arrowsize=13)
                      
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana çerçeve
        main_frame = tk.Frame(self.root, bg=self.colors[self.current_theme]["bg"])
        main_frame.pack(pady=15, padx=15, fill="both", expand=True)
        
        # Başlık ve logo çerçevesi
        header_frame = tk.Frame(main_frame, bg=self.colors[self.current_theme]["bg"])
        header_frame.pack(fill="x", pady=(0, 15))
        
        # Logo oluştur
        self.logo_frame = self.create_text_logo()
        self.logo_frame.pack(side="left", padx=(0, 10))
        
        title_label = tk.Label(header_frame, 
                              text="Gelişmiş Çeviri Uygulaması", 
                              font=("Segoe UI", 16, "bold"),
                              bg=self.colors[self.current_theme]["bg"],
                              fg=self.colors[self.current_theme]["accent"])
        title_label.pack(side="left")
        
        # Üst kontrol paneli - Yeniden düzenlenmiş
        control_frame = tk.Frame(main_frame, bg=self.colors[self.current_theme]["bg"], 
                               pady=10, padx=5)
        control_frame.pack(fill="x")
        
        # Kaynak ve hedef dil seçimi için konteyner
        lang_container = tk.Frame(control_frame, bg=self.colors[self.current_theme]["bg"])
        lang_container.pack(fill="x")
        
        # Kaynak dil frame
        src_lang_frame = tk.Frame(lang_container, bg=self.colors[self.current_theme]["bg"], 
                                padx=10, pady=5)
        src_lang_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(src_lang_frame, text="Kaynak Dil:", 
                bg=self.colors[self.current_theme]["bg"], 
                fg=self.colors[self.current_theme]["label"], 
                font=self.header_font).pack(side="top", anchor="w", pady=(0, 5))
        
        src_select_frame = tk.Frame(src_lang_frame, bg=self.colors[self.current_theme]["bg"])
        src_select_frame.pack(side="top", fill="x")
        
        self.src_lang_var = tk.StringVar()
        self.src_lang_combobox = ttk.Combobox(src_select_frame, textvariable=self.src_lang_var, 
                                             values=list(self.supported_languages.keys()), 
                                             state="readonly", width=15)
        self.src_lang_combobox.current(0)
        self.src_lang_combobox.pack(side="left", pady=5)
        
        # Otomatik algılama butonu
        self.auto_detect_button = tk.Button(src_select_frame, text="Otomatik Algıla", 
                                          command=self.auto_detect_language,
                                          bg=self.colors[self.current_theme]["accent"], 
                                          fg=self.colors[self.current_theme]["button_text"],
                                          font=self.button_font,
                                          relief=tk.FLAT, padx=10)
        self.auto_detect_button.pack(side="left", padx=10)
        self.auto_detect_button.bind("<Enter>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["button_hover"]))
        self.auto_detect_button.bind("<Leave>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["accent"]))
        
        # Dil değiştirme butonu
        swap_button = tk.Button(lang_container, text="🔄", 
                              command=self.swap_languages, 
                              bg=self.colors[self.current_theme]["button"], 
                              fg=self.colors[self.current_theme]["button_text"],
                              font=("Segoe UI", 12),
                              relief=tk.FLAT,
                              width=3, height=1)
        swap_button.pack(side="left", padx=20)
        swap_button.bind("<Enter>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["button_hover"]))
        swap_button.bind("<Leave>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["button"]))
        
        # Hedef dil frame
        dest_lang_frame = tk.Frame(lang_container, bg=self.colors[self.current_theme]["bg"], 
                                 padx=10, pady=5)
        dest_lang_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(dest_lang_frame, text="Hedef Dil:", 
                bg=self.colors[self.current_theme]["bg"], 
                fg=self.colors[self.current_theme]["label"], 
                font=self.header_font).pack(side="top", anchor="w", pady=(0, 5))
        
        self.dest_lang_var = tk.StringVar()
        self.dest_lang_combobox = ttk.Combobox(dest_lang_frame, textvariable=self.dest_lang_var, 
                                              values=list(self.supported_languages.keys()), 
                                              state="readonly", width=15)
        self.dest_lang_combobox.current(1)
        self.dest_lang_combobox.pack(side="left", pady=5)
        
        # Tema değiştirme butonu ve arayüzü
        theme_frame = tk.Frame(control_frame, bg=self.colors[self.current_theme]["bg"])
        theme_frame.pack(side="right", padx=10)
        
        self.theme_button = tk.Button(theme_frame, text="🌙" if self.current_theme == "light" else "☀️", 
                                     command=self.toggle_theme,
                                     bg=self.colors[self.current_theme]["bg"], 
                                     fg=self.colors[self.current_theme]["label"],
                                     font=("Segoe UI", 14),
                                     relief=tk.FLAT,
                                     width=2, height=1,
                                     borderwidth=0)
        self.theme_button.pack(side="right")
        
        # Tema etiketi
        self.theme_label = tk.Label(theme_frame, 
                                  text="Koyu Temaya Geç" if self.current_theme == "light" else "Açık Temaya Geç", 
                                  bg=self.colors[self.current_theme]["bg"], 
                                  fg=self.colors[self.current_theme]["label"],
                                  font=("Segoe UI", 9))
        self.theme_label.pack(side="right", padx=(0, 5))
        
        # Separator
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)
        
        # Metin alanları
        text_frame = tk.Frame(main_frame, bg=self.colors[self.current_theme]["bg"])
        text_frame.pack(fill="both", expand=True, pady=5)
        
        # Kaynak metin
        src_frame = tk.Frame(text_frame, bg=self.colors[self.current_theme]["bg"], 
                           highlightbackground=self.colors[self.current_theme]["border"],
                           highlightthickness=1)
        src_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        src_label_frame = tk.Frame(src_frame, bg=self.colors[self.current_theme]["bg"])
        src_label_frame.pack(fill="x", pady=5, padx=5)
        
        tk.Label(src_label_frame, text="Kaynak Metin", 
                bg=self.colors[self.current_theme]["bg"],
                fg=self.colors[self.current_theme]["label"], 
                font=self.header_font).pack(side="left", anchor="w")
        
        # Kaynak metin butonları
        src_buttons_frame = tk.Frame(src_label_frame, bg=self.colors[self.current_theme]["bg"])
        src_buttons_frame.pack(side="right")
        
        clear_button = tk.Button(src_buttons_frame, text="Temizle", command=self.clear_source,
                               bg=self.colors[self.current_theme]["bg"], 
                               fg=self.colors[self.current_theme]["label"],
                               font=self.button_font,
                               relief=tk.FLAT,
                               padx=8, pady=2)
        clear_button.pack(side="left", padx=5)
        clear_button.bind("<Enter>", lambda e: e.widget.config(bg="#e6e6e6" if self.current_theme == "light" else "#3a3a3a"))
        clear_button.bind("<Leave>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["bg"]))
        
        load_button = tk.Button(src_buttons_frame, text="Dosyadan Yükle", 
                              command=self.load_from_file,
                              bg=self.colors[self.current_theme]["accent"], 
                              fg=self.colors[self.current_theme]["button_text"],
                              font=self.button_font,
                              relief=tk.FLAT,
                              padx=8, pady=2)
        load_button.pack(side="left", padx=5)
        load_button.bind("<Enter>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["button_hover"]))
        load_button.bind("<Leave>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["accent"]))
        
        # Kaynak metin alanı
        self.src_text = scrolledtext.ScrolledText(src_frame, height=10, width=30, 
                                                font=("Segoe UI", 11), 
                                                bg=self.colors[self.current_theme]["text_bg"],
                                                wrap=tk.WORD,
                                                padx=10, pady=10,
                                                relief=tk.FLAT)
        self.src_text.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Hedef metin
        dest_frame = tk.Frame(text_frame, bg=self.colors[self.current_theme]["bg"],
                            highlightbackground=self.colors[self.current_theme]["border"],
                            highlightthickness=1)
        dest_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        dest_label_frame = tk.Frame(dest_frame, bg=self.colors[self.current_theme]["bg"])
        dest_label_frame.pack(fill="x", pady=5, padx=5)
        
        tk.Label(dest_label_frame, text="Çeviri", 
                bg=self.colors[self.current_theme]["bg"],
                fg=self.colors[self.current_theme]["label"], 
                font=self.header_font).pack(side="left", anchor="w")
        
        # Hedef metin butonları
        dest_buttons_frame = tk.Frame(dest_label_frame, bg=self.colors[self.current_theme]["bg"])
        dest_buttons_frame.pack(side="right")
        
        copy_button = tk.Button(dest_buttons_frame, text="Kopyala", 
                              command=self.copy_translation,
                              bg=self.colors[self.current_theme]["accent"], 
                              fg=self.colors[self.current_theme]["button_text"],
                              font=self.button_font,
                              relief=tk.FLAT,
                              padx=8, pady=2)
        copy_button.pack(side="left", padx=5)
        copy_button.bind("<Enter>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["button_hover"]))
        copy_button.bind("<Leave>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["accent"]))
        
        # Hedef metin alanı
        self.dest_text = scrolledtext.ScrolledText(dest_frame, height=10, width=30, 
                                                font=("Segoe UI", 11), 
                                                bg=self.colors[self.current_theme]["text_bg"],
                                                wrap=tk.WORD,
                                                padx=10, pady=10,
                                                relief=tk.FLAT)
        self.dest_text.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Alt panel
        bottom_frame = tk.Frame(main_frame, bg=self.colors[self.current_theme]["bg"])
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        # Çeviri butonu
        self.translate_button = tk.Button(bottom_frame, text="ÇEVİR", 
                                        command=self.start_translation,
                                        bg=self.colors[self.current_theme]["button"], 
                                        fg=self.colors[self.current_theme]["button_text"], 
                                        font=("Segoe UI", 12, "bold"),
                                        relief=tk.FLAT, 
                                        padx=25, pady=8)
        self.translate_button.pack(side="left", padx=(0, 15))
        self.translate_button.bind("<Enter>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["button_hover"]))
        self.translate_button.bind("<Leave>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["button"]))
        
        # Geçmiş butonu
        self.history_button = tk.Button(bottom_frame, text="Geçmiş", 
                                      command=self.show_history,
                                      bg=self.colors[self.current_theme]["bg"], 
                                      fg=self.colors[self.current_theme]["label"],
                                      font=self.button_font,
                                      relief=tk.FLAT, 
                                      padx=10, pady=5,
                                      borderwidth=1)
        self.history_button.pack(side="left")
        self.history_button.bind("<Enter>", lambda e: e.widget.config(bg="#e6e6e6" if self.current_theme == "light" else "#3a3a3a"))
        self.history_button.bind("<Leave>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["bg"]))
        
        # Durum çubuğu
        status_frame = tk.Frame(main_frame, bg=self.colors[self.current_theme]["bg"])
        status_frame.pack(fill="x", pady=(10, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")
        self.status_bar = tk.Label(status_frame, textvariable=self.status_var, 
                                  bg=self.colors[self.current_theme]["bg"], 
                                  fg=self.colors[self.current_theme]["accent"],
                                  font=("Segoe UI", 9), anchor="w")
        self.status_bar.pack(side="left", fill="x")
        
        # Basit çeviri sözlüğü (çevrimdışı çalışması için)
        self.basic_dictionary = {
            # Türkçe-İngilizce
            "merhaba": "hello", "selam": "hi", "nasılsın": "how are you", 
            "teşekkürler": "thank you", "evet": "yes", "hayır": "no",
            "ve": "and", "veya": "or", "ama": "but", "eğer": "if",
            "ben": "I", "sen": "you", "o": "he/she/it", "biz": "we", 
            "siz": "you", "onlar": "they", "bu": "this", "şu": "that",
            
            # İngilizce-Türkçe
            "hello": "merhaba", "hi": "selam", "how are you": "nasılsın",
            "thank you": "teşekkürler", "yes": "evet", "no": "hayır",
            "and": "ve", "or": "veya", "but": "ama", "if": "eğer",
            "i": "ben", "you": "sen", "he": "o", "she": "o", "it": "o",
            "we": "biz", "they": "onlar", "this": "bu", "that": "şu"
        }
    
    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.theme_button.config(text="☀️")
            self.theme_label.config(text="Açık Temaya Geç")
        else:
            self.current_theme = "light"
            self.theme_button.config(text="🌙")
            self.theme_label.config(text="Koyu Temaya Geç")
        
        # Tüm bileşenlerin temasını güncelle
        self.root.configure(bg=self.colors[self.current_theme]["bg"])
        self.update_all_widget_colors()
        
    def update_all_widget_colors(self):
        """Tüm widget'ları mevcut temaya göre güncelle"""
        for widget in self.root.winfo_children():
            self.update_widget_colors(widget)
        
        # Logo rengini tema değişimine göre güncelle
        if hasattr(self, 'logo_frame'):
            self.logo_frame.configure(bg=self.colors[self.current_theme]["accent"])
            for child in self.logo_frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=self.colors[self.current_theme]["accent"], fg="white")
            
        # ttk stillerini güncelle
        self.create_custom_styles()
    
    def update_widget_colors(self, widget):
        try:
            if isinstance(widget, tk.Frame) or isinstance(widget, tk.Label):
                widget.configure(bg=self.colors[self.current_theme]["bg"])
                if isinstance(widget, tk.Label):
                    widget.configure(fg=self.colors[self.current_theme]["label"])
            
            elif isinstance(widget, scrolledtext.ScrolledText) or isinstance(widget, tk.Text):
                widget.configure(bg=self.colors[self.current_theme]["text_bg"])
            
            elif isinstance(widget, tk.Button):
                if widget == self.translate_button:
                    widget.configure(bg=self.colors[self.current_theme]["button"], 
                                   fg=self.colors[self.current_theme]["button_text"])
                elif widget in [self.auto_detect_button] or "Kopyala" in str(widget['text']) or "Dosyadan Yükle" in str(widget['text']):
                    widget.configure(bg=self.colors[self.current_theme]["accent"],
                                   fg=self.colors[self.current_theme]["button_text"])
                else:
                    widget.configure(bg=self.colors[self.current_theme]["bg"],
                                   fg=self.colors[self.current_theme]["label"])
            
            # Alt bileşenleri kontrol et
            for child in widget.winfo_children():
                self.update_widget_colors(child)
                
            # Çerçeve sınırlarını güncelle
            if isinstance(widget, tk.Frame) and 'highlightbackground' in widget.keys():
                widget.configure(highlightbackground=self.colors[self.current_theme]["border"])
                
        except:
            pass  # Bazı bileşenler bu özellikleri desteklemeyebilir
    
    def clear_source(self):
        self.src_text.delete("1.0", "end")
        self.status_var.set("Kaynak metin temizlendi")
    
    def copy_translation(self):
        translation = self.dest_text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(translation)
        self.status_var.set("Çeviri panoya kopyalandı")
    
    def load_from_file(self):
        try:
            file_path = filedialog.askopenfilename(
                title="Metin Dosyası Seç",
                filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
            )
            
            if file_path:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.src_text.delete("1.0", "end")
                    self.src_text.insert("1.0", content)
                self.status_var.set(f"Dosya yüklendi: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Dosya Okuma Hatası", f"Dosya okunamadı: {str(e)}")
    
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as file:
                    self.history = json.load(file)
        except Exception as e:
            print(f"Geçmiş yüklenirken hata: {str(e)}")
            self.history = []
    
    def save_history(self):
        try:
            # En son 20 çeviri kaydedilsin
            if len(self.history) > 20:
                self.history = self.history[-20:]
                
            with open(self.history_file, "w", encoding="utf-8") as file:
                json.dump(self.history, file, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Geçmiş kaydedilirken hata: {str(e)}")
    
    def add_to_history(self, source_text, translated_text, source_lang, target_lang):
        # Çok uzun metinlerde ilk 100 karakter kaydedilsin
        if len(source_text) > 100:
            display_source = source_text[:100] + "..."
        else:
            display_source = source_text
            
        self.history.append({
            "source": display_source,
            "full_source": source_text,
            "translation": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        self.save_history()
    
    def show_history(self):
        if not self.history:
            messagebox.showinfo("Geçmiş", "Henüz çeviri geçmişi bulunmuyor.")
            return
            
        # Geçmiş penceresi
        history_window = tk.Toplevel(self.root)
        history_window.title("Çeviri Geçmişi")
        history_window.geometry("680x450")
        history_window.transient(self.root)
        history_window.grab_set()
        history_window.configure(bg=self.colors[self.current_theme]["bg"])
        
        # Başlık
        title_frame = tk.Frame(history_window, bg=self.colors[self.current_theme]["bg"])
        title_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(title_frame, text="Çeviri Geçmişi", 
                font=("Segoe UI", 14, "bold"), 
                bg=self.colors[self.current_theme]["bg"],
                fg=self.colors[self.current_theme]["accent"]).pack(side="left")
        
        # Liste çerçevesi
        list_frame = tk.Frame(history_window, bg=self.colors[self.current_theme]["bg"],
                            padx=15, pady=10)  # Tuple formatı yerine tek sayı kullanıyorum
        list_frame.pack(side="left", fill="both", expand=True)
        
        # Listbox çerçevesi (sınır eklemek için)
        listbox_frame = tk.Frame(list_frame, 
                               bg=self.colors[self.current_theme]["bg"],
                               highlightbackground=self.colors[self.current_theme]["border"],
                               highlightthickness=1)
        listbox_frame.pack(fill="both", expand=True)
        
        # Geçmiş listesi
        history_listbox = tk.Listbox(listbox_frame, 
                                   font=("Segoe UI", 10),
                                   bg=self.colors[self.current_theme]["text_bg"],
                                   fg=self.colors[self.current_theme]["label"],
                                   selectbackground=self.colors[self.current_theme]["button"],
                                   selectforeground="white",
                                   borderwidth=0,
                                   highlightthickness=0)
        history_listbox.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Kaydırma çubuğu
        scrollbar = ttk.Scrollbar(listbox_frame, command=history_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        history_listbox.config(yscrollcommand=scrollbar.set)
        
        # Listbox'a geçmiş öğeleri ekle (ters sırayla - en yeni üstte)
        for i, item in enumerate(reversed(self.history)):
            date_time = item['timestamp']
            text_preview = item['source']
            history_listbox.insert(tk.END, f"{date_time} - {text_preview}")
            
            # Alternatif satırlara arka plan rengi ekle
            if i % 2 == 1:
                history_listbox.itemconfig(i, bg="#f5f5f5" if self.current_theme == "light" else "#3a3a3a")
        
        # Butonlar
        button_frame = tk.Frame(history_window, bg=self.colors[self.current_theme]["bg"], padx=15)
        button_frame.pack(side="right", fill="y", pady=10)
        
        # Çeviriyi yükle butonu
        load_button = tk.Button(button_frame, text="Çeviriyi Yükle", 
                              command=lambda: self.load_from_history(history_listbox.curselection()),
                              bg=self.colors[self.current_theme]["button"], 
                              fg=self.colors[self.current_theme]["button_text"],
                              font=self.button_font,
                              width=15,
                              relief=tk.FLAT, padx=10, pady=5)
        load_button.pack(fill="x", pady=5)
        load_button.bind("<Enter>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["button_hover"]))
        load_button.bind("<Leave>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["button"]))
        
        # Kapat butonu
        close_button = tk.Button(button_frame, text="Kapat", 
                               command=history_window.destroy,
                               bg=self.colors[self.current_theme]["bg"], 
                               fg=self.colors[self.current_theme]["label"],
                               font=self.button_font,
                               width=15, 
                               relief=tk.FLAT, padx=10, pady=5,
                               highlightbackground=self.colors[self.current_theme]["border"],
                               highlightthickness=1)
        close_button.pack(fill="x", pady=5)
        close_button.bind("<Enter>", lambda e: e.widget.config(bg="#e6e6e6" if self.current_theme == "light" else "#3a3a3a"))
        close_button.bind("<Leave>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["bg"]))
        
        # Çeviri detayları çerçevesi
        details_frame = tk.Frame(list_frame, bg=self.colors[self.current_theme]["bg"])
        details_frame.pack(fill="x", pady=10)
        
        # Çift tıklama ile çeviriyi yükleme
        history_listbox.bind("<Double-Button-1>", lambda e: self.load_from_history(history_listbox.curselection()))
        
        # Seçili öğenin detaylarını göstermek için fonksiyon
        def show_details(event=None):
            selection = history_listbox.curselection()
            if selection:
                index = len(self.history) - 1 - selection[0]
                item = self.history[index]
                messagebox.showinfo("Çeviri Detayları", 
                                  f"Tarih: {item['timestamp']}\n\n"
                                  f"Kaynak Dil: {list(self.supported_languages.keys())[list(self.supported_languages.values()).index(item['source_lang'])]}\n"
                                  f"Hedef Dil: {list(self.supported_languages.keys())[list(self.supported_languages.values()).index(item['target_lang'])]}\n\n"
                                  f"Kaynak Metin: {item['full_source'][:150]}{'...' if len(item['full_source']) > 150 else ''}\n\n"
                                  f"Çeviri: {item['translation'][:150]}{'...' if len(item['translation']) > 150 else ''}")
        
        # Detay butonu
        details_button = tk.Button(button_frame, text="Detayları Göster", 
                                 command=show_details,
                                 bg=self.colors[self.current_theme]["bg"], 
                                 fg=self.colors[self.current_theme]["label"],
                                 font=self.button_font,
                                 width=15,
                                 relief=tk.FLAT, padx=10, pady=5,
                                 highlightbackground=self.colors[self.current_theme]["border"],
                                 highlightthickness=1)
        details_button.pack(fill="x", pady=5)
        details_button.bind("<Enter>", lambda e: e.widget.config(bg="#e6e6e6" if self.current_theme == "light" else "#3a3a3a"))
        details_button.bind("<Leave>", lambda e: e.widget.config(bg=self.colors[self.current_theme]["bg"]))
    
    def load_from_history(self, selection):
        if not selection:
            messagebox.showinfo("Seçim", "Lütfen bir çeviri seçin.")
            return
            
        # Seçilen öğeyi al (listbox ters sıralı olduğu için indeksi düzelt)
        index = len(self.history) - 1 - selection[0]
        item = self.history[index]
        
        # Kaynak metni ve dilleri yükle
        self.src_text.delete("1.0", "end")
        self.src_text.insert("1.0", item["full_source"])
        
        # Dilleri ayarla
        for i, lang in enumerate(self.supported_languages.keys()):
            if self.supported_languages[lang] == item["source_lang"]:
                self.src_lang_combobox.current(i)
            if self.supported_languages[lang] == item["target_lang"]:
                self.dest_lang_combobox.current(i)
    
    def auto_detect_language(self):
        text = self.src_text.get("1.0", "end-1c")
        
        if not text.strip():
            messagebox.showinfo("Uyarı", "Lütfen dil algılaması için bir metin girin.")
            return
            
        self.status_var.set("Dil algılanıyor...")
        self.root.update()
        
        try:
            # Kısa bir metin parçası al (algılama için yeterlidir)
            sample = text[:100] if len(text) > 100 else text
            
            # GoogleTranslator ile dil algılama denemeleri
            try:
                translator = GoogleTranslator(source='auto', target='en')
                detected_lang = translator.detect(sample)
            except:
                # Basit dil algılama mantığı
                detected_lang = self.simple_detect_language(sample)
            
            # Algılanan dile göre combobox'ı ayarla
            found = False
            for i, lang_name in enumerate(self.supported_languages.keys()):
                if self.supported_languages[lang_name] == detected_lang:
                    self.src_lang_combobox.current(i)
                    found = True
                    break
            
            if found:
                self.status_var.set(f"Dil algılandı: {list(self.supported_languages.keys())[list(self.supported_languages.values()).index(detected_lang)]}")
            else:
                # Varsayılan olarak İngilizce veya Türkçe
                if detected_lang == "en":
                    self.src_lang_combobox.current(1)  # İngilizce
                    self.status_var.set(f"Dil algılandı: İngilizce")
                else:
                    self.src_lang_combobox.current(0)  # Türkçe
                    self.status_var.set(f"Dil algılandı: Türkçe")
        
        except Exception as e:
            print(f"Dil algılama hatası: {str(e)}")
            # Hata durumunda varsayılan olarak Türkçe seç
            self.src_lang_combobox.current(0)  # Türkçe
            self.status_var.set("Dil algılanamadı, varsayılan olarak Türkçe seçildi")
    
    # Basit dil algılama - en yaygın dilleri tespit eden basit bir algoritma
    def simple_detect_language(self, text):
        text = text.lower()
        
        # Türkçe'ye özgü karakterler
        tr_chars = {'ç', 'ğ', 'ı', 'ö', 'ş', 'ü'}
        # İngilizce'ye özgü karakter grupları
        en_patterns = ['th', 'wh', 'ph']
        
        # Türkçe karakterlerin sayısını say
        tr_count = sum(1 for c in text if c in tr_chars)
        
        # İngilizce pattern sayısını say
        en_count = sum(1 for p in en_patterns if p in text)
        
        # Eğer Türkçe karakterler varsa muhtemelen Türkçe
        if tr_count > 0:
            return "tr"
        # Eğer İngilizce patternler varsa muhtemelen İngilizce
        elif en_count > 0:
            return "en"
        # Sonuç belirsizse karakter frekans analizi yap
        else:
            # İngilizce'de sık kullanılan kelimeleri say
            en_words = ['the', 'a', 'an', 'and', 'or', 'but', 'i', 'you', 'he', 'she', 'it', 'we', 'they']
            tr_words = ['ve', 'veya', 'ama', 'ben', 'sen', 'o', 'biz', 'siz', 'onlar', 'bu', 'şu', 'için']
            
            words = text.split()
            en_word_count = sum(1 for w in words if w in en_words)
            tr_word_count = sum(1 for w in words if w in tr_words)
            
            return "en" if en_word_count > tr_word_count else "tr"
    
    def swap_languages(self):
        src_index = self.src_lang_combobox.current()
        dest_index = self.dest_lang_combobox.current()
        
        self.src_lang_combobox.current(dest_index)
        self.dest_lang_combobox.current(src_index)
        
        # Metin alanlarını da değiştir
        src_text = self.src_text.get("1.0", "end-1c")
        dest_text = self.dest_text.get("1.0", "end-1c")
        
        self.src_text.delete("1.0", "end")
        self.dest_text.delete("1.0", "end")
        
        if dest_text:
            self.src_text.insert("1.0", dest_text)
    
    # Metni parçalara ayırma (maksimum uzunluk sınırı için)
    def split_text(self, text, max_length=4500):
        # Boş metin kontrolü
        if not text:
            return []
            
        # Metin yeterince kısa ise, doğrudan döndür
        if len(text) <= max_length:
            return [text]
            
        chunks = []
        
        # Metin çok uzunsa, cümlelere ayırıyoruz
        sentences = re.split(r'(?<=[.!?])\s+', text)
        current_chunk = ""
        
        for sentence in sentences:
            # Tek bir cümle çok uzunsa, kelimelere ayırıyoruz
            if len(sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                words = sentence.split()
                word_chunk = ""
                
                for word in words:
                    if len(word_chunk) + len(word) + 1 <= max_length:
                        word_chunk += word + " "
                    else:
                        chunks.append(word_chunk.strip())
                        word_chunk = word + " "
                
                if word_chunk:
                    current_chunk = word_chunk
            else:
                # Cümle eklendiğinde chunk fazla uzun olmayacaksa ekle
                if len(current_chunk) + len(sentence) + 1 <= max_length:
                    current_chunk += sentence + " "
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence + " "
        
        # Son chunk'ı da ekliyoruz
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    # Alternatif çeviri yöntemi: LibreTranslate
    def translate_with_libre(self, text, source, target):
        try:
            # LibreTranslate API'si ile çeviri (API anahtarı gerektirmez)
            url = "https://translate.argosopentech.com/translate"
            data = {
                "q": text,
                "source": source,
                "target": target
            }
            response = requests.post(url, json=data, timeout=5)  # 5 saniye timeout eklendi
            response.raise_for_status()  # HTTP hataları için
            return response.json()["translatedText"]
        except Exception as e:
            print(f"LibreTranslate hatası: {str(e)}")
            raise e
             
    # Basit çevrimdışı çeviri
    def offline_translate(self, text, src_lang, dest_lang):
        # Küçük harfe çeviriyoruz
        text_lower = text.lower()
        
        # Eğer tam bir eşleşme varsa doğrudan döndür
        if text_lower in self.basic_dictionary:
            return self.basic_dictionary[text_lower]
             
        # Kelime kelime çeviri yapalım
        words = text_lower.split()
        translated_words = []
        
        for word in words:
            # Noktalama işaretlerini temizle
            clean_word = re.sub(r'[^\w\s]', '', word)
            
            if clean_word in self.basic_dictionary:
                # Eğer kelime sözlükte varsa, çevirisini ekle
                translated_word = self.basic_dictionary[clean_word]
                
                # Orijinal kelimede büyük harf varsa, çeviride de uygula
                if word[0].isupper():
                    translated_word = translated_word[0].upper() + translated_word[1:]
                    
                translated_words.append(translated_word)
            else:
                # Kelime sözlükte yoksa, olduğu gibi bırak
                translated_words.append(word)
                
        return " ".join(translated_words)
    
    def start_translation(self):
        # Çeviriyi ayrı bir thread'de başlat
        translation_thread = threading.Thread(target=self.translate_text)
        translation_thread.daemon = True
        translation_thread.start()

    def translate_text(self):
        # Çeviri düğmesini devre dışı bırak
        self.translate_button.config(state="disabled")
        
        text_to_translate = self.src_text.get("1.0", "end-1c")
        
        if not text_to_translate.strip():
            messagebox.showinfo("Uyarı", "Lütfen çevrilecek bir metin girin.")
            self.translate_button.config(state="normal")
            return
        
        self.status_var.set("Çeviriliyor...")
        self.root.update()
        
        try:
            src_lang_name = self.src_lang_var.get()
            dest_lang_name = self.dest_lang_var.get()
            
            src_lang = self.supported_languages[src_lang_name]
            dest_lang = self.supported_languages[dest_lang_name]
            
            # Önbellekte var mı kontrol et
            cache_key = f"{src_lang}:{dest_lang}:{text_to_translate}"
            if cache_key in self.translation_cache:
                full_translation = self.translation_cache[cache_key]
                self.status_var.set("Çeviri önbellekten alındı")
            else:
                # Metni parçalara ayır (uzunluk sınırı için)
                text_chunks = self.split_text(text_to_translate)
                translated_chunks = []
                
                # Her parçayı çevir
                for i, chunk in enumerate(text_chunks):
                    if len(text_chunks) > 1:
                        self.status_var.set(f"Çeviriliyor... ({i+1}/{len(text_chunks)})")
                        self.root.update()
                    
                    try:
                        # İlk yöntem: GoogleTranslator
                        try:
                            translator = GoogleTranslator(source=src_lang, target=dest_lang)
                            translated_chunk = translator.translate(chunk)
                            
                            if not translated_chunk:
                                raise Exception("Çeviri sonucu boş")
                                
                        except Exception as e:
                            print(f"GoogleTranslator hatası: {str(e)}")
                            
                            # İkinci yöntem: LibreTranslate
                            try:
                                translated_chunk = self.translate_with_libre(chunk, src_lang, dest_lang)
                            except Exception as libre_error:
                                print(f"LibreTranslate hatası: {str(libre_error)}")
                                
                                # Son çare: Basit çevrimdışı çeviri
                                translated_chunk = self.offline_translate(chunk, src_lang, dest_lang)
                                self.status_var.set("Çevrimdışı çeviri kullanılıyor (sınırlı)")
                        
                        translated_chunks.append(translated_chunk)
                        
                        # API limitlerini aşmamak için kısa bir bekleme
                        if len(text_chunks) > 1 and i < len(text_chunks) - 1:
                            time.sleep(0.5)
                    
                    except Exception as chunk_error:
                        print(f"Chunk {i+1} çeviri hatası: {str(chunk_error)}")
                        # Hata durumunda da çevrilmemiş metni ekle
                        translated_chunks.append(f"[Çeviri hatası: {chunk}]")
                
                # Tüm çevrilmiş parçaları birleştir
                full_translation = " ".join(translated_chunks)
                
                # Önbelleğe ekle
                self.translation_cache[cache_key] = full_translation
            
            self.dest_text.delete("1.0", "end")
            self.dest_text.insert("1.0", full_translation)
            
            # Geçmişe ekle
            self.add_to_history(text_to_translate, full_translation, src_lang, dest_lang)
            
            self.status_var.set("Çeviri tamamlandı")
            
        except Exception as e:
            error_msg = str(e)
            traceback_msg = traceback.format_exc()
            print(f"Çeviri hatası: {error_msg}")
            print(traceback_msg)
            
            self.status_var.set("Çeviri başarısız")
            messagebox.showerror("Hata", f"Çeviri yapılırken bir hata oluştu:\n{error_msg}")
        
        finally:
            # Çeviri düğmesini tekrar etkinleştir
            self.translate_button.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop() 