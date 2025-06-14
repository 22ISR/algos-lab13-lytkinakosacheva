import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from PIL import Image, ImageTk
from io import BytesIO
from datetime import datetime
import json

class SpotifyViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Просмотр треков Spotify")
        self.root.geometry("1200x700")

        self.all_songs = []
        self.filtered_songs = []
        self.current_image = None

        self.search_var = tk.StringVar(value="")
        self.sort_var = tk.StringVar(value="added_at")
        self.hide_explicit_var = tk.BooleanVar(value=False)

        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_frame, text="Поиск:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))
        self.search_var.trace('w', self.on_search_change)

        ttk.Label(top_frame, text="Сортировка:").pack(side=tk.LEFT, padx=(0, 5))
        sort_combo = ttk.Combobox(top_frame, textvariable=self.sort_var,
                                  values=["added_at", "duration_ms", "popularity"],
                                  state="readonly", width=15)
        sort_combo.pack(side=tk.LEFT, padx=(0, 20))
        sort_combo.bind('<<ComboboxSelected>>', self.on_sort_change)

        explicit_check = ttk.Checkbutton(top_frame, text="Скрыть explicit треки",
                                         variable=self.hide_explicit_var,
                                         command=self.on_filter_change)
        explicit_check.pack(side=tk.LEFT)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        columns = ('name', 'artist', 'duration', 'album')
        self.tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=20)

        self.tree.heading('name', text='Название песни')
        self.tree.heading('artist', text='Исполнитель')
        self.tree.heading('duration', text='Длительность')
        self.tree.heading('album', text='Альбом')

        self.tree.column('name', width=300)
        self.tree.column('artist', width=200)
        self.tree.column('duration', width=100, anchor=tk.CENTER)
        self.tree.column('album', width=250)

        tree_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)

        right_frame = ttk.Frame(content_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)

        self.image_label = ttk.Label(right_frame, text="Обложка альбома",
                                     background="black", foreground="white",
                                     anchor=tk.CENTER)
        self.image_label.pack(pady=10, padx=10, fill=tk.X)

        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.X, padx=10)

        self.track_info = ttk.Label(info_frame, text="", justify=tk.LEFT,
                                    wraplength=280, background="white")
        self.track_info.pack(fill=tk.X)

    def load_data(self):
        def fetch_data():
            try:
                response = requests.get("https://kitek.ktkv.dev/songs.json", timeout=10)
                if response.status_code == 200:
                    self.all_songs = response.json()
                    print(json.dumps(self.all_songs[0], indent=2, ensure_ascii=False)) 
                    print(f"Загружено песен: {len(self.all_songs)}")
                    self.root.after(0, self.update_display)
                else:
                    self.root.after(0, lambda: messagebox.showerror("Ошибка",
                               f"Не удалось загрузить данные. Код ошибки: {response.status_code}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка",
                               f"Ошибка при загрузке данных: {str(e)}"))
        threading.Thread(target=fetch_data, daemon=True).start()

    def update_display(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.apply_filters()
        self.sort_data()
        print(f"Отображаем {len(self.filtered_songs)} треков")
        for song in self.filtered_songs:
            track = song.get('track', {})
            name = track.get('name', '')
            artist = ', '.join([a['name'] for a in track.get('artists', [])])
            duration = self.format_duration(track.get('duration_ms', 0))
            album = track.get('album', {}).get('name', '')
            self.tree.insert('', tk.END, values=(name, artist, duration, album))
        print(f"Элементов в таблице после вставки: {len(self.tree.get_children())}")

    def apply_filters(self):
        search_text = self.search_var.get().lower().strip()
        hide_explicit = self.hide_explicit_var.get()
        self.filtered_songs = []
        for song in self.all_songs:
            track = song.get('track', {})
            if hide_explicit and track.get('explicit', False):
                continue
            if search_text:
                name = track.get('name', '').lower()
                artist_names = ' '.join([artist['name'].lower() for artist in track.get('artists', [])])
                album_name = track.get('album', {}).get('name', '').lower()
                if search_text not in name and search_text not in artist_names and search_text not in album_name:
                    continue
            self.filtered_songs.append(song)

    def sort_data(self):
        sort_by = self.sort_var.get()
        def get_track_field(song, field, default=''):
            return song.get('track', {}).get(field, default)
        if sort_by == "added_at":
            self.filtered_songs.sort(key=lambda x: x.get('added_at', ''), reverse=True)
        elif sort_by == "duration_ms":
            self.filtered_songs.sort(key=lambda x: get_track_field(x, 'duration_ms', 0), reverse=True)
        elif sort_by == "popularity":
            self.filtered_songs.sort(key=lambda x: get_track_field(x, 'popularity', 0), reverse=True)

    def format_duration(self, ms):
        if not ms:
            return "0:00"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def on_search_change(self, *args):
        self.update_display()

    def on_sort_change(self, event):
        self.update_display()

    def on_filter_change(self):
        self.update_display()

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        item = selected_items[0]
        values = self.tree.item(item, 'values')
        if not values:
            return
        song_name = values[0]
        for song in self.filtered_songs:
            track = song.get('track', {})
            if track.get('name') == song_name:
                self.show_track_info(song)
                break

    def show_track_info(self, song):
        track = song.get('track', {})
        name = track.get('name', 'Неизвестно')
        artists = ', '.join([a['name'] for a in track.get('artists', [])])
        album = track.get('album', {}).get('name', 'Неизвестно')
        duration = self.format_duration(track.get('duration_ms', 0))
        popularity = track.get('popularity', 0)
        explicit = "Да" if track.get('explicit', False) else "Нет"
        added_at = song.get('added_at', '')
        if added_at:
            try:
                date_obj = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
                added_at = date_obj.strftime('%Y-%m-%d')
            except:
                pass
        info_text = f"""Название: {name}

Исполнитель: {artists}

Альбом: {album}

Длительность: {duration}

Популярность: {popularity}

Explicit: {explicit}

Дата добавления: {added_at}"""
        self.track_info.config(text=info_text)

        album_images = track.get('album', {}).get('images', [])
        if album_images:
            image_url = album_images[1]['url'] if len(album_images) > 1 else album_images[0]['url']
            self.load_album_cover(image_url)
        else:
            self.image_label.config(image='', text='Обложка альбома')
            self.current_image = None

    def load_album_cover(self, url):
        def download_image():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    image = image.resize((250, 250), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    self.root.after(0, lambda: self.update_album_cover(photo))
            except Exception as e:
                print(f"Ошибка загрузки обложки: {e}")
        threading.Thread(target=download_image, daemon=True).start()

    def update_album_cover(self, photo):
        self.image_label.config(image=photo, text="")
        self.current_image = photo 

if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyViewer(root)
    root.mainloop()