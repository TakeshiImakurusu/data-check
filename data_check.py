import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import threading
import os
import sys
import json
import datetime

# 各シリーズのチェックロジックをインポート
# これらのモジュールは、main_checker_app.py と同じディレクトリに配置されている必要があります。
try:
    import dekispart
    import innosite
    import dekispart_school
    import cloud
except ImportError as e:
    messagebox.showerror("モジュールエラー", f"必要なシリーズチェックモジュールが見つかりません。以下のファイルが同じディレクトリにあるか確認してください。\n{e}\n\nアプリケーションを終了します。")
    sys.exit(1)

class DataCheckerApp:
    def __init__(self, master):
        self.master = master
        master.title("基幹データチェックプログラム")
        master.geometry("1000x700") # ウィンドウサイズを調整

        # アプリケーション情報
        self.APP_VERSION = "1.0.1" # バージョン更新 (ユーザIDカラム名修正)
        self.APP_AUTHOR = "情報システム部 / 今久留主"
        self.APP_DATE = "2025-06-19"

        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.aux_file_paths = {}
        self.settings_file = "app_settings.json"
        self.check_definitions_file = "check_definitions.json" # チェック定義ファイル名
        self.check_definitions = {} # チェック定義を格納する辞書

        # メニューオブジェクトへの参照を保持するための変数を初期化
        self.settings_menu = None
        self.help_menu = None

        self.load_settings() 
        self.load_check_definitions() # チェック定義を読み込む

        # シリーズリストを動的に取得
        self.all_series = self._get_all_series_names()

        self._create_menu_bar()
        self._create_widgets() # ウィジェット作成を別のメソッドに分離

        # 初期ステータス
        self.status_label.config(text="準備完了")

    def _get_all_series_names(self):
        """利用可能なすべてのシリーズ名を取得する"""
        series_set = set()
        for def_id, definition in self.check_definitions.items():
            if "series" in definition:
                series_set.add(definition["series"])
        
        # アルファベット順にソートして返す
        return list(series_set)

    def _create_menu_bar(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        # ファイルメニュー (念のため追加)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="設定を保存", command=self.save_settings)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.master.quit)

        # 設定メニュー
        # self.settings_menu をインスタンス変数として保持
        self.settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="設定", menu=self.settings_menu)
        self.settings_menu.add_command(label="補助ファイル設定", command=self.open_file_settings)
        self.settings_menu.add_command(label="チェック内容編集", command=self.open_check_definition_editor) # 新しいメニュー項目

        # ヘルプメニュー
        # self.help_menu をインスタンス変数として保持
        self.help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=self.help_menu)
        self.help_menu.add_command(label="使い方", command=self.show_usage_info)
        self.help_menu.add_command(label="バージョン情報", command=self.show_version_info)
        self.help_menu.add_command(label="チェック内容一覧", command=self.show_check_definition_viewer) # 新しいメニュー項目


    def _create_widgets(self):
        # メインフレーム (左右分割用)
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1) # 左ペインを伸縮可能に
        main_frame.grid_columnconfigure(1, weight=3) # 右ペインをより大きく伸縮可能に

        # ---------- 左ペイン ----------
        left_pane = ttk.Frame(main_frame, width=250) # 幅を固定気味に
        left_pane.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_pane.grid_rowconfigure(0, weight=1) # データチェック実行フレームが伸縮するように
        left_pane.grid_columnconfigure(0, weight=1)

        # データチェックの実行フレーム
        check_execution_frame = ttk.LabelFrame(left_pane, text="データチェックの実行")
        check_execution_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew") # nsewで伸縮
        check_execution_frame.grid_columnconfigure(0, weight=1)

        # check_definitions.jsonから取得したシリーズ名をボタンに反映
        self.buttons = {}
        for series_name in self.all_series:
            # モジュールが存在しないシリーズのボタンは作らない、または無効にするなどのロジックを追加しても良い
            btn = ttk.Button(
                check_execution_frame,
                text=f"{series_name} のチェックを実行",
                command=lambda s=series_name: self.run_single_series_check(s)
            )
            btn.pack(padx=10, pady=5, fill="x")
            self.buttons[series_name] = btn
        
        # 補助ファイル設定ボタン
        self.file_setting_button = ttk.Button(check_execution_frame, text="補助ファイル設定", command=self.open_file_settings)
        self.file_setting_button.pack(padx=10, pady=10, fill="x")

        # ---------- 右ペイン ----------
        right_pane = ttk.Frame(main_frame)
        right_pane.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_pane.grid_rowconfigure(0, weight=0) # フィルタリングソート
        right_pane.grid_rowconfigure(1, weight=3) # 結果一覧 (伸縮)
        right_pane.grid_rowconfigure(2, weight=1) # サマリーレポート (伸縮)
        right_pane.grid_rowconfigure(3, weight=0) # ボタン類
        right_pane.grid_columnconfigure(0, weight=1)

        # フィルタリングとソートフレーム
        filter_sort_frame = ttk.LabelFrame(right_pane, text="フィルタリングとソート")
        filter_sort_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        filter_sort_frame.grid_columnconfigure(1, weight=1) # Entry/Combobox を伸縮可能に

        ttk.Label(filter_sort_frame, text="シリーズでフィルタ:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.filter_series_var = tk.StringVar(self.master)
        self.filter_series_var.set("全て")
        self.filter_series_dropdown = ttk.Combobox(filter_sort_frame, textvariable=self.filter_series_var, values=["全て"] + self.all_series, state="readonly")
        self.filter_series_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.filter_series_dropdown.bind("<<ComboboxSelected>>", self.apply_filters_and_sort)

        ttk.Label(filter_sort_frame, text="エラー内容/IDで検索:").grid(row=1, column=0, padx=5, pady=2, sticky="w") # 検索対象をエラー内容/IDに変更
        self.search_error_var = tk.StringVar()
        self.search_error_entry = ttk.Entry(filter_sort_frame, textvariable=self.search_error_var)
        self.search_error_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.search_error_entry.bind("<KeyRelease>", self.apply_filters_and_sort)

        ttk.Label(filter_sort_frame, text="ソート基準:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.sort_by_var = tk.StringVar(self.master)
        self.sort_by_var.set("シリーズ")
        # ソート基準の選択肢を修正: 保守整理番号を追加
        self.sort_by_dropdown = ttk.Combobox(filter_sort_frame, textvariable=self.sort_by_var, values=["シリーズ", "ユーザID", "保守整理番号", "チェックID", "エラー内容"], state="readonly") 
        self.sort_by_dropdown.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        self.sort_by_dropdown.bind("<<ComboboxSelected>>", self.apply_filters_and_sort)

        ttk.Label(filter_sort_frame, text="ソート順:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.sort_order_var = tk.StringVar(self.master)
        self.sort_order_var.set("昇順")
        self.sort_order_dropdown = ttk.Combobox(filter_sort_frame, textvariable=self.sort_order_var, values=["昇順", "降順"], state="readonly")
        self.sort_order_dropdown.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        self.sort_order_dropdown.bind("<<ComboboxSelected>>", self.apply_filters_and_sort)


        # 結果表示フレーム
        self.results_frame = ttk.LabelFrame(right_pane, text="チェック結果一覧")
        self.results_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew") # 伸縮するように
        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)

        # Treeviewのカラムを修正: 保守整理番号カラムを追加
        self.tree = ttk.Treeview(self.results_frame, columns=("シリーズ", "ユーザID", "保守整理番号", "チェックID", "エラー内容"), show="headings")
        self.tree.heading("シリーズ", text="シリーズ")
        self.tree.heading("ユーザID", text="ユーザID")
        self.tree.heading("保守整理番号", text="保守整理番号") # 新規追加
        self.tree.heading("チェックID", text="チェックID")
        self.tree.heading("エラー内容", text="エラー内容")
        self.tree.column("シリーズ", width=80, anchor="center")
        self.tree.column("ユーザID", width=80, anchor="center")
        self.tree.column("保守整理番号", width=100, anchor="center") # 新規追加
        self.tree.column("チェックID", width=100, anchor="center")
        self.tree.column("エラー内容", width=300, anchor="w") # 幅を調整

        vsb = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # サマリーレポートフレーム
        summary_frame = ttk.LabelFrame(right_pane, text="サマリーレポート")
        summary_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew") # 伸縮するように
        summary_frame.grid_rowconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(0, weight=1)

        self.summary_text = tk.Text(summary_frame, wrap="word", height=5, state="disabled")
        self.summary_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        summary_vsb = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_vsb.set)
        summary_vsb.grid(row=0, column=1, sticky="ns")

        # 下部のボタンフレーム
        bottom_buttons_frame = ttk.Frame(right_pane)
        bottom_buttons_frame.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        bottom_buttons_frame.grid_columnconfigure(0, weight=1)
        bottom_buttons_frame.grid_columnconfigure(1, weight=1)

        self.clear_button = ttk.Button(bottom_buttons_frame, text="結果をクリア", command=self.clear_results)
        self.clear_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.download_button = ttk.Button(bottom_buttons_frame, text="チェック結果をダウンロード (CSV/Excel)", command=self.download_results)
        self.download_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.download_button.config(state="disabled")

        # all_results_dfのカラムを修正: 保守整理番号カラムを追加
        self.all_results_df = pd.DataFrame(columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"]) 
        self.filtered_results_df = pd.DataFrame(columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"]) 

        # ステータスバー
        self.status_frame = ttk.Frame(self.master, relief=tk.SUNKEN, borderwidth=1)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.status_label = ttk.Label(self.status_frame, text="準備完了", anchor="w")
        self.status_label.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.progress_bar = ttk.Progressbar(self.status_frame, orient="horizontal", mode="indeterminate", length=200)

    def load_settings(self):
        """設定ファイルから補助ファイルのパスを読み込む"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                try:
                    settings = json.load(f)
                    self.aux_file_paths = settings.get("aux_file_paths", {})
                except json.JSONDecodeError:
                    messagebox.showwarning("設定エラー", "設定ファイルの読み込みに失敗しました。ファイルが破損している可能性があります。")
                    self.aux_file_paths = {}
        else:
            self.aux_file_paths = {}

    def save_settings(self):
        """補助ファイルのパスを設定ファイルに保存する"""
        settings = {
            "aux_file_paths": self.aux_file_paths,
        }
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("設定保存", "補助ファイルのパス設定を保存しました。")

    def load_check_definitions(self):
        """チェック定義ファイルを読み込む。存在しない場合はデフォルトを作成。"""
        if os.path.exists(self.check_definitions_file):
            try:
                with open(self.check_definitions_file, 'r', encoding='utf-8') as f:
                    self.check_definitions = json.load(f)
            except json.JSONDecodeError:
                messagebox.showwarning("設定エラー", "チェック定義ファイルの読み込みに失敗しました。ファイルが破損している可能性があります。デフォルト設定を再生成します。")
                self._create_default_check_definitions()
            except Exception as e:
                messagebox.showwarning("設定エラー", f"チェック定義ファイルの読み込み中に予期せぬエラーが発生しました: {e}。デフォルト設定を再生成します。")
                self._create_default_check_definitions()
        else:
            self._create_default_check_definitions()

    def _create_default_check_definitions(self):
        """デフォルトのチェック定義を作成し、ファイルに保存する"""
        default_defs = {
            "DEKISPART_E001": {
                "series": "DEKISPART",
                "name": "個人名未登録チェック",
                "default_message": "登録されていない個人名です。個人名リストを確認してください。",
                "user_message": "",
                "severity": "エラー",
                "description": "DEKISPARTデータに含まれる個人名が、指定された個人名リストに存在するかどうかを確認します。未登録の場合は、リストへの追加またはデータ修正を検討してください。"
            },
            "CHK_0058": {
                "series": "DEKISPART",
                "name": "stdNsyu「121」とstdKbiko「更新案内不要」の組み合わせチェック",
                "default_message": "stdNsyu(入金経路)が121でstdKbiko(備考（更新・一斉）)に「更新案内不要」を含む場合NG",
                "user_message": "",
                "severity": "エラー",
                "description": "stdNsyu（入金経路）が「121」であり、かつstdKbiko（備考）に「更新案内不要」という文字列が含まれている場合に検出されます。入金経路と備考内容の矛盾を確認します。"
            }
        }
        self.check_definitions = default_defs
        self.save_check_definitions()
        messagebox.showinfo("チェック定義", "デフォルトのチェック定義ファイルが作成されました。")
        # デフォルト定義を再生成した場合は、シリーズリストも更新が必要
        self.all_series = self._get_all_series_names() 

    def save_check_definitions(self):
        """チェック定義をファイルに保存する"""
        try:
            with open(self.check_definitions_file, 'w', encoding='utf-8') as f:
                json.dump(self.check_definitions, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("保存エラー", f"チェック定義ファイルの保存中にエラーが発生しました。\n詳細: {e}")

    def get_error_message_by_check_id(self, check_id):
        """チェックIDに基づいてエラーメッセージを取得する。
           ユーザー定義メッセージがあればそれを使用し、なければデフォルトを使用する。
        """
        definition = self.check_definitions.get(check_id)
        if definition:
            user_msg = definition.get("user_message")
            if user_msg:
                return user_msg
            else:
                return definition.get("default_message", "エラー内容が定義されていません。")
        return f"不明なチェックID: {check_id}"


    def open_file_settings(self):
        """補助ファイル設定ダイアログを開く"""
        settings_window = tk.Toplevel(self.master)
        settings_window.title("補助ファイル設定")
        settings_window.geometry("600x500") 
        settings_window.transient(self.master)
        settings_window.grab_set()

        labels = {
            "individual_list_path": "個人名チェックファイル (.xlsx):",
            "totalnet_list_path": "トータルネット登録ファイル (.csv):",
            "sales_person_list_path": "担当者マスタファイル (.csv):",
            "customers_list_path": "得意先マスタファイル (.csv):",
            # 他のシリーズの補助ファイルがあればここに追加
        }
        filetypes = {
            "individual_list_path": [("Excel Files", "*.xlsx")],
            "totalnet_list_path": [("CSV Files", "*.csv"), ("All Files", "*.*")],
            "sales_person_list_path": [("CSV Files", "*.csv"), ("All Files", "*.*")],
            "customers_list_path": [("CSV Files", "*.csv"), ("All Files", "*.*")],
        }

        self.path_entries = {}

        row_num = 0
        for key, text in labels.items():
            ttk.Label(settings_window, text=text).grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
            
            entry = ttk.Entry(settings_window, width=50)
            entry.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
            
            if key in self.aux_file_paths:
                entry.insert(0, self.aux_file_paths[key])

            self.path_entries[key] = entry

            browse_button = ttk.Button(settings_window, text="参照...",
                                         command=lambda k=key, e=entry, ft=filetypes.get(key, [("All Files", "*.*")]): self._browse_file_for_setting(k, e, ft))
            browse_button.grid(row=row_num, column=2, padx=5, pady=5)
            row_num += 1

        ttk.Button(settings_window, text="保存して閉じる", command=lambda: self._save_and_close_settings(settings_window)).grid(row=row_num, columnspan=3, pady=10)

        settings_window.grid_columnconfigure(1, weight=1)

        self.master.wait_window(settings_window)

    def _browse_file_for_setting(self, key, entry_widget, filetypes):
        """ファイル参照ダイアログを開き、パスをEntryに設定する (補助ファイル設定用)"""
        file_path = filedialog.askopenfilename(title=f"「{key}」のファイルを選択", filetypes=filetypes)
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)

    def _save_and_close_settings(self, window):
        """設定を保存し、設定ウィンドウを閉じる"""
        for key, entry in self.path_entries.items():
            self.aux_file_paths[key] = entry.get()
        self.save_settings()
        window.destroy()
        messagebox.showinfo("設定完了", "補助ファイルのパスが保存されました。")

    def open_check_definition_editor(self):
        """チェック内容編集ダイアログを開く"""
        editor_window = tk.Toplevel(self.master)
        editor_window.title("チェック内容編集")
        editor_window.geometry("800x600")
        editor_window.transient(self.master)
        editor_window.grab_set()

        # 検索・フィルタリング部分
        filter_frame = ttk.LabelFrame(editor_window, text="フィルタリング")
        filter_frame.pack(fill="x", padx=10, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1) # 検索Entryを伸縮可能に
        filter_frame.grid_columnconfigure(3, weight=1) # シリーズComboboxを伸縮可能に

        ttk.Label(filter_frame, text="シリーズでフィルタ:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.editor_filter_series_var = tk.StringVar(editor_window)
        self.editor_filter_series_var.set("全て")
        editor_series_dropdown = ttk.Combobox(filter_frame, textvariable=self.editor_filter_series_var, values=["全て"] + self.all_series, state="readonly")
        editor_series_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        # フィルタリング適用関数を呼び出す
        editor_series_dropdown.bind("<<ComboboxSelected>>", lambda e: self._populate_editor_treeview(editor_tree))


        ttk.Label(filter_frame, text="チェックID/項目名/内容で検索:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.editor_search_var = tk.StringVar()
        editor_search_entry = ttk.Entry(filter_frame, textvariable=self.editor_search_var)
        editor_search_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        # 入力時にフィルタ適用
        self.editor_search_var.trace_add("write", lambda *args: self._populate_editor_treeview(editor_tree)) 

        # チェック定義一覧 Treeview
        editor_tree_frame = ttk.Frame(editor_window)
        editor_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        editor_tree_frame.grid_rowconfigure(0, weight=1)
        editor_tree_frame.grid_columnconfigure(0, weight=1)

        # Treeviewのカラムを修正: デフォルト内容を削除し、ユーザー内容を「エラー内容」にリネーム
        editor_tree = ttk.Treeview(editor_tree_frame, 
                                   columns=("シリーズ", "チェックID", "項目名", "重要度", "エラー内容"), 
                                   show="headings")
        editor_tree.heading("シリーズ", text="シリーズ")
        editor_tree.heading("チェックID", text="チェックID")
        editor_tree.heading("項目名", text="項目名")
        editor_tree.heading("重要度", text="重要度")
        editor_tree.heading("エラー内容", text="エラー内容") # ユーザー定義内容がここに表示される

        editor_tree.column("シリーズ", width=70, anchor="center")
        editor_tree.column("チェックID", width=100, anchor="center")
        editor_tree.column("項目名", width=150, anchor="w")
        editor_tree.column("重要度", width=60, anchor="center")
        editor_tree.column("エラー内容", width=350, anchor="w") # 幅を調整

        editor_vsb = ttk.Scrollbar(editor_tree_frame, orient="vertical", command=editor_tree.yview)
        editor_hsb = ttk.Scrollbar(editor_tree_frame, orient="horizontal", command=editor_tree.xview)
        editor_tree.configure(yscrollcommand=editor_vsb.set, xscrollcommand=editor_hsb.set)

        editor_tree.grid(row=0, column=0, sticky="nsew")
        editor_vsb.grid(row=0, column=1, sticky="ns")
        editor_hsb.grid(row=1, column=0, sticky="ew")

        # 選択された項目の編集エリア
        edit_frame = ttk.LabelFrame(editor_window, text="選択項目編集")
        edit_frame.pack(fill="x", padx=10, pady=5)
        edit_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(edit_frame, text="チェックID:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.edit_check_id_var = tk.StringVar()
        ttk.Label(edit_frame, textvariable=self.edit_check_id_var).grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(edit_frame, text="項目名:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.edit_name_var = tk.StringVar()
        ttk.Label(edit_frame, textvariable=self.edit_name_var).grid(row=1, column=1, padx=5, pady=2, sticky="w")

        # 「ユーザー定義内容」を「エラー内容」にリネーム
        ttk.Label(edit_frame, text="エラー内容:").grid(row=2, column=0, padx=5, pady=2, sticky="w") # rowを2に変更
        self.edit_user_message_entry = ttk.Entry(edit_frame, width=80)
        self.edit_user_message_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew") # rowを2に変更

        ttk.Label(edit_frame, text="説明:").grid(row=3, column=0, padx=5, pady=2, sticky="w") # rowを3に変更
        self.edit_description_text = tk.Text(edit_frame, wrap="word", height=3, width=60, state="disabled")
        self.edit_description_text.grid(row=3, column=1, padx=5, pady=2, sticky="ew") # rowを3に変更
        
        save_button = ttk.Button(edit_frame, text="エラー内容を保存", command=lambda: self._save_user_message(editor_tree))
        save_button.grid(row=4, column=0, columnspan=2, pady=5) # rowを4に変更
        
        clear_user_message_button = ttk.Button(edit_frame, text="エラー内容をデフォルトに戻す", command=lambda: self._clear_user_message(editor_tree)) # 文言変更
        clear_user_message_button.grid(row=5, column=0, columnspan=2, pady=5) # rowを5に変更

        def on_tree_select(event):
            selected_item = editor_tree.selection()
            if selected_item:
                item_values = editor_tree.item(selected_item, "values")
                check_id = item_values[1] # "チェックID"カラムの値
                
                definition = self.check_definitions.get(check_id)
                if definition:
                    self.edit_check_id_var.set(check_id)
                    self.edit_name_var.set(definition.get("name", ""))
                    self.edit_user_message_entry.delete(0, tk.END)
                    self.edit_user_message_entry.insert(0, definition.get("user_message", ""))
                    
                    self.edit_description_text.config(state="normal")
                    self.edit_description_text.delete(1.0, tk.END)
                    self.edit_description_text.insert(tk.END, definition.get("description", ""))
                    self.edit_description_text.config(state="disabled")
                else:
                    self.edit_check_id_var.set("")
                    self.edit_name_var.set("")
                    self.edit_user_message_entry.delete(0, tk.END)
                    self.edit_description_text.config(state="normal")
                    self.edit_description_text.delete(1.0, tk.END)
                    self.edit_description_text.config(state="disabled")

        editor_tree.bind("<<TreeviewSelect>>", on_tree_select)

        self._populate_editor_treeview(editor_tree) # 初期表示

        close_button = ttk.Button(editor_window, text="閉じる", command=editor_window.destroy)
        close_button.pack(pady=10)
        
        editor_window.protocol("WM_DELETE_WINDOW", editor_window.destroy)
        self.master.wait_window(editor_window)

    def _populate_editor_treeview(self, tree_widget):
        """
        チェック定義エディタのTreeviewを更新する。
        シリーズフィルタと検索テキストを考慮する。
        """
        for i in tree_widget.get_children():
            tree_widget.delete(i)

        selected_series = self.editor_filter_series_var.get()
        search_text = self.editor_search_var.get().strip().lower()

        # チェックIDでソートして表示
        sorted_check_ids = sorted(self.check_definitions.keys())

        for check_id in sorted_check_ids:
            definition = self.check_definitions[check_id]
            series = definition.get("series", "")
            name = definition.get("name", "")
            severity = definition.get("severity", "")
            user_message = definition.get("user_message", "")
            description = definition.get("description", "")

            # シリーズフィルタリング
            if selected_series != "全て" and series != selected_series:
                continue

            # 検索フィルタリング
            if search_text and \
               not (search_text in check_id.lower() or
                    search_text in name.lower() or
                    search_text in user_message.lower() or
                    search_text in description.lower() or
                    search_text in series.lower() # シリーズ名も検索対象に含める
                    ):
                continue

            # Treeviewに挿入する値を修正: デフォルト内容を外し、ユーザー内容を「エラー内容」として渡す
            tree_widget.insert("", "end", values=(series, check_id, name, severity, user_message))

    def _save_user_message(self, editor_tree_widget):
        """ユーザー定義メッセージを保存する (「エラー内容」を保存)"""
        selected_item = editor_tree_widget.selection()
        if not selected_item:
            messagebox.showwarning("保存エラー", "編集する項目を選択してください。")
            return

        check_id = self.edit_check_id_var.get()
        new_user_message = self.edit_user_message_entry.get().strip()

        if check_id and check_id in self.check_definitions:
            self.check_definitions[check_id]["user_message"] = new_user_message
            self.save_check_definitions()
            self._populate_editor_treeview(editor_tree_widget) # Treeviewを再描画
            messagebox.showinfo("保存完了", f"'{check_id}' のエラー内容を保存しました。")
        else:
            messagebox.showerror("保存エラー", "無効なチェックIDです。")

    def _clear_user_message(self, editor_tree_widget):
        """ユーザー定義メッセージをクリアし、デフォルトに戻す"""
        selected_item = editor_tree_widget.selection()
        if not selected_item:
            messagebox.showwarning("クリアエラー", "クリアする項目を選択してください。")
            return

        check_id = self.edit_check_id_var.get()
        
        if check_id and check_id in self.check_definitions:
            if messagebox.askyesno("確認", f"'{check_id}' のエラー内容をデフォルトに戻しますか？"):
                self.check_definitions[check_id]["user_message"] = "" # ユーザーメッセージをクリア
                self.save_check_definitions()
                self._populate_editor_treeview(editor_tree_widget) # Treeviewを再描画
                self.edit_user_message_entry.delete(0, tk.END) # Entryもクリア
                messagebox.showinfo("クリア完了", f"'{check_id}' のエラー内容をデフォルトに戻しました。")
        else:
            messagebox.showerror("クリアエラー", "無効なチェックIDです。")

    def show_check_definition_viewer(self):
        """チェック内容一覧ビューアを開く"""
        viewer_window = tk.Toplevel(self.master)
        viewer_window.title("チェック内容一覧")
        viewer_window.geometry("900x700")
        viewer_window.transient(self.master)
        viewer_window.grab_set()

        # 検索・フィルタリング部分
        filter_frame = ttk.LabelFrame(viewer_window, text="フィルタリング")
        filter_frame.pack(fill="x", padx=10, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(3, weight=1) # シリーズComboboxを伸縮可能に

        ttk.Label(filter_frame, text="シリーズでフィルタ:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.viewer_filter_series_var = tk.StringVar(viewer_window)
        self.viewer_filter_series_var.set("全て")
        viewer_series_dropdown = ttk.Combobox(filter_frame, textvariable=self.viewer_filter_series_var, values=["全て"] + self.all_series, state="readonly")
        viewer_series_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        # フィルタリング適用関数を呼び出す
        viewer_series_dropdown.bind("<<ComboboxSelected>>", lambda e: self._populate_viewer_treeview(viewer_tree))

        ttk.Label(filter_frame, text="チェックID/項目名/内容で検索:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.viewer_search_var = tk.StringVar()
        viewer_search_entry = ttk.Entry(filter_frame, textvariable=self.viewer_search_var)
        viewer_search_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.viewer_search_var.trace_add("write", lambda *args: self._populate_viewer_treeview(viewer_tree))

        # チェック定義一覧 Treeview
        viewer_tree_frame = ttk.Frame(viewer_window)
        viewer_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        viewer_tree_frame.grid_rowconfigure(0, weight=1)
        viewer_tree_frame.grid_columnconfigure(0, weight=1)

        # Treeviewのカラムを修正: デフォルト内容を削除し、現在の表示内容を「エラー内容」にリネーム
        viewer_tree = ttk.Treeview(viewer_tree_frame, 
                                   columns=("シリーズ", "チェックID", "項目名", "重要度", "エラー内容", "説明"), 
                                   show="headings")
        viewer_tree.heading("シリーズ", text="シリーズ")
        viewer_tree.heading("チェックID", text="チェックID")
        viewer_tree.heading("項目名", text="項目名")
        viewer_tree.heading("重要度", text="重要度")
        viewer_tree.heading("エラー内容", text="エラー内容") # 現在の表示内容がここに表示される
        viewer_tree.heading("説明", text="説明")

        viewer_tree.column("シリーズ", width=70, anchor="center")
        viewer_tree.column("チェックID", width=100, anchor="center")
        viewer_tree.column("項目名", width=150, anchor="w")
        viewer_tree.column("重要度", width=60, anchor="center")
        viewer_tree.column("エラー内容", width=250, anchor="w") # 幅を調整
        viewer_tree.column("説明", width=350, anchor="w") # 幅を調整

        viewer_vsb = ttk.Scrollbar(viewer_tree_frame, orient="vertical", command=viewer_tree.yview)
        viewer_hsb = ttk.Scrollbar(viewer_tree_frame, orient="horizontal", command=viewer_tree.xview)
        viewer_tree.configure(yscrollcommand=viewer_vsb.set, xscrollcommand=viewer_hsb.set)

        viewer_tree.grid(row=0, column=0, sticky="nsew")
        viewer_vsb.grid(row=0, column=1, sticky="ns")
        viewer_hsb.grid(row=1, column=0, sticky="ew")

        self._populate_viewer_treeview(viewer_tree) # 初期表示

        close_button = ttk.Button(viewer_window, text="閉じる", command=viewer_window.destroy)
        close_button.pack(pady=10)
        
        viewer_window.protocol("WM_DELETE_WINDOW", viewer_window.destroy)
        self.master.wait_window(viewer_window)

    def _populate_viewer_treeview(self, tree_widget):
        """
        チェック定義ビューアのTreeviewを更新する。
        シリーズフィルタと検索テキストを考慮する。
        """
        for i in tree_widget.get_children():
            tree_widget.delete(i)

        selected_series = self.viewer_filter_series_var.get()
        search_text = self.viewer_search_var.get().strip().lower()

        sorted_check_ids = sorted(self.check_definitions.keys())

        for check_id in sorted_check_ids:
            definition = self.check_definitions[check_id]
            series = definition.get("series", "")
            name = definition.get("name", "")
            severity = definition.get("severity", "")
            user_message = definition.get("user_message", "")
            current_message = user_message if user_message else definition.get("default_message", "") # これを「エラー内容」として表示
            description = definition.get("description", "")

            # シリーズフィルタリング
            if selected_series != "全て" and series != selected_series:
                continue

            # 検索フィルタリング
            if search_text and \
               not (search_text in check_id.lower() or
                    search_text in name.lower() or
                    search_text in current_message.lower() or
                    search_text in user_message.lower() or
                    search_text in description.lower() or
                    search_text in series.lower() # シリーズ名も検索対象に含める
                    ):
                continue

            # Treeviewに挿入する値を修正: デフォルト内容を外し、現在の表示内容を「エラー内容」として渡す
            tree_widget.insert("", "end", values=(series, check_id, name, severity, current_message, description))


    def _clear_and_disable_buttons(self):
        """処理開始時にGUIをクリア・無効化する"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.all_results_df = pd.DataFrame(columns=["シリーズ", "ユーザID", "チェックID"])
        self.filtered_results_df = pd.DataFrame(columns=["シリーズ", "ユーザID", "チェックID"])
        self.download_button.config(state="disabled")
        self.clear_button.config(state="disabled")
        self.summary_text.config(state="normal")
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.config(state="disabled")

        for btn in self.buttons.values():
            btn.config(state="disabled")
        self.file_setting_button.config(state="disabled")
        
        # 設定メニューとヘルプメニューも無効化（処理中に設定変更を防ぐため）
        # nametowidget の代わりにインスタンス変数を使用
        if self.settings_menu: # メニューが作成されていることを確認
            self.settings_menu.entryconfig("補助ファイル設定", state="disabled")
            self.settings_menu.entryconfig("チェック内容編集", state="disabled")
        if self.help_menu: # メニューが作成されていることを確認
            self.help_menu.entryconfig("チェック内容一覧", state="disabled")


        self.status_label.config(text="処理中...")
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        self.progress_bar.start()

    def _enable_buttons_and_check_download(self):
        """処理終了時にGUIを有効化し、ダウンロードボタンの状態を更新する"""
        for btn in self.buttons.values():
            btn.config(state="normal")
        self.file_setting_button.config(state="normal")
        self.clear_button.config(state="normal")
        
        # 設定メニューとヘルプメニューを有効化
        # nametowidget の代わりにインスタンス変数を使用
        if self.settings_menu: # メニューが作成されていることを確認
            self.settings_menu.entryconfig("補助ファイル設定", state="normal")
            self.settings_menu.entryconfig("チェック内容編集", state="normal")
        if self.help_menu: # メニューが作成されていることを確認
            self.help_menu.entryconfig("チェック内容一覧", state="normal")


        if not self.all_results_df.empty:
            self.download_button.config(state="normal")
        else:
            self.download_button.config(state="disabled")

        self.status_label.config(text="処理が完了しました。")
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.apply_filters_and_sort() # 処理完了後に結果を再表示 (フィルタ・ソート適用)
        self._update_summary_report() # サマリーレポートを更新

    def update_progress_label(self, message):
        """進捗ラベルを更新し、GUIを即座に描画する (スレッドセーフ)"""
        self.master.after(0, lambda: self.status_label.config(text=message))
        self.master.after(0, self.master.update_idletasks)

    def run_single_series_check(self, series_name):
        self._clear_and_disable_buttons()
        
        required_paths_map = {
            "DEKISPART": [
                "individual_list_path", 
                "totalnet_list_path",
                "sales_person_list_path",
                "customers_list_path"
            ],
            "INNOSITE": [
                "individual_list_path", 
                "totalnet_list_path",
                "sales_person_list_path",
                "customers_list_path"
            ],
            "DEKISPART_SCHOOL": [
                "individual_list_path", 
                "totalnet_list_path",
                "sales_person_list_path",
                "customers_list_path"
            ],
            "CLOUD": [
                "individual_list_path", 
                "totalnet_list_path",
                "sales_person_list_path",
                "customers_list_path"
            ]
        }

        required_paths = required_paths_map.get(series_name, [])

        missing_files = []
        for key in required_paths:
            if key not in self.aux_file_paths or not self.aux_file_paths[key] or not os.path.exists(self.aux_file_paths[key]):
                # 表示名を整形 (例: dekispart_individual_list_path -> Dekispart Individual List)
                display_name = key.replace(f"{series_name.lower()}_", "").replace("_path", "").replace("_", " ").title()
                missing_files.append(display_name) 

        if missing_files:
            self._enable_buttons_and_check_download()
            messagebox.showwarning("ファイル未設定または見つかりません", 
                                   f"'{series_name}' のチェックに必要な以下の補助ファイルが設定されていないか、見つかりません。\n\n"
                                   f"• " + "\n• ".join(missing_files) + "\n\n"
                                   f"「補助ファイル設定」から設定してください。")
            self.status_label.config(text="準備完了")
            return

        self.status_label.config(text=f"'{series_name}' のデータチェックを開始します...")
        messagebox.showinfo("チェック開始", f"'{series_name}' のデータチェックを開始します。バックグラウンドで処理を実行します。")
        self.thread = threading.Thread(target=self._perform_checks_threaded, args=([series_name],))
        self.thread.start()

    def _perform_checks_threaded(self, selected_series_list):
        temp_all_results = []
        last_error_message = None

        try:
            for i, series in enumerate(selected_series_list):
                self.master.after(0, lambda s=series: self.status_label.config(text=f"'{s}' のデータチェックを実行中..."))

                results_df = pd.DataFrame() # 初期化
                
                # 各シリーズのモジュールからメインのチェック関数を呼び出す
                # IMPORTANT: 各モジュールは pd.DataFrame(columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"]) 
                # の形式で結果を返すように修正が必要です。
                if series == "DEKISPART":
                    results_df = dekispart.run_dekispart_check(
                        progress_callback=self.update_progress_label,
                        aux_paths=self.aux_file_paths
                    )
                elif series == "INNOSITE":
                    results_df = innosite.run_innosite_check(
                        progress_callback=self.update_progress_label,
                        aux_paths=self.aux_file_paths
                    )
                elif series == "DEKISPART_SCHOOL":
                    results_df = dekispart_school.run_dekispart_school_check(
                        progress_callback=self.update_progress_label,
                        aux_paths=self.aux_file_paths
                    )
                elif series == "CLOUD":
                    results_df = cloud.run_cloud_check(
                        progress_callback=self.update_progress_label,
                        aux_paths=self.aux_file_paths
                    )

                if results_df is not None and not results_df.empty:
                    # 結果DataFrameに必要なカラムが存在することを確認
                    # ここでは "シリーズ", "ユーザID", "チェックID" が必須
                    required_cols_for_check_modules = ["シリーズ", "ユーザID", "チェックID"]
                    # 保守整理番号は必須ではないが、あれば使用する
                    for col in required_cols_for_check_modules:
                        if col not in results_df.columns:
                            # もしチェックモジュールが新しいフォーマットに対応していない場合のエラーハンドリング
                            raise ValueError(f"'{series}' モジュールのチェック結果に必須カラム '{col}' が見つかりません。モジュールが新しい仕様に準拠しているか確認してください。")
                    
                    # stdUserIDは「ユーザID」として扱われるため、カラム名を「ユーザID」にリネーム
                    if "ユーザID" in results_df.columns:
                        results_df.rename(columns={"ユーザID": "ユーザID"}, inplace=True)

                    # 保守整理番号カラムが存在する場合は含める
                    if "保守整理番号" in results_df.columns:
                        temp_all_results.append(results_df[["シリーズ", "ユーザID", "保守整理番号", "チェックID"]])
                    else:
                        # 保守整理番号カラムがない場合は空の文字列を追加
                        results_df["保守整理番号"] = ""
                        temp_all_results.append(results_df[["シリーズ", "ユーザID", "保守整理番号", "チェックID"]])

            if temp_all_results:
                self.all_results_df = pd.concat(temp_all_results, ignore_index=True)
                self.master.after(0, lambda: messagebox.showinfo("チェック完了", f"{len(self.all_results_df)}件のエラーが見つかりました。結果一覧を確認してください。"))
            else:
                self.all_results_df = pd.DataFrame(columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"]) # エラーがなかった場合も空のDataFrameを設定
                self.master.after(0, lambda: messagebox.showinfo("チェック完了", "エラーは見つかりませんでした。"))

        except Exception as e:
            last_error_message = f"データチェック中に予期せぬエラーが発生しました。\n\n詳細: {e}\n\n開発者にお問い合わせください。"
            self.master.after(0, lambda: self.status_label.config(text="エラー発生"))
            # エラー発生時もTreeviewにエラーメッセージを表示
            error_df = pd.DataFrame([{"シリーズ": "System", "ユーザID": "N/A", "保守整理番号": "", "チェックID": "APP_ERROR"}])
            self.all_results_df = pd.concat([self.all_results_df, error_df], ignore_index=True)

        finally:
            self.master.after(0, self._enable_buttons_and_check_download)
            if last_error_message:
                self.master.after(0, lambda: messagebox.showerror("処理エラー", last_error_message))

    def apply_filters_and_sort(self, event=None):
        """フィルタリングとソートを適用して結果ツリービューを更新する"""
        if self.all_results_df.empty:
            self.filtered_results_df = pd.DataFrame(columns=["シリーズ", "ユーザID", "保守整理番号", "チェックID"])
            self._display_results_in_treeview()
            return

        filtered_df = self.all_results_df.copy()

        # シリーズフィルタ
        selected_series = self.filter_series_var.get()
        if selected_series != "全て":
            filtered_df = filtered_df[filtered_df["シリーズ"] == selected_series]

        # エラー内容/IDで検索
        search_text = self.search_error_var.get().strip()
        if search_text:
            # 検索対象を、表示される可能性のあるカラムすべてにする (「ユーザID」に名称変更)
            filtered_df = filtered_df[
                filtered_df.apply(lambda row: 
                    search_text.lower() in str(row["ユーザID"]).lower() or # ユーザIDで検索
                    search_text.lower() in str(row.get("保守整理番号", "")).lower() or # 保守整理番号で検索
                    search_text.lower() in str(row["チェックID"]).lower() or
                    search_text.lower() in self.get_error_message_by_check_id(row["チェックID"]).lower(), axis=1
                )
            ]

        # ソート
        sort_by = self.sort_by_var.get()
        ascending = (self.sort_order_var.get() == "昇順")

        if sort_by:
            if sort_by == "ユーザID": # ソート基準も「ユーザID」に
                # ユーザIDが数値と文字列混在の場合に対応するため、数値変換を試み、失敗したら文字列としてソート
                # 'coerce' は変換できない値を NaN にする
                filtered_df['temp_sort_id'] = pd.to_numeric(filtered_df['ユーザID'], errors='coerce')
                # NaN (数値変換できなかったもの) はソート順の最後に来るように工夫
                filtered_df = filtered_df.sort_values(
                    by=['temp_sort_id', 'ユーザID'], 
                    ascending=[ascending, ascending]
                ).drop(columns='temp_sort_id')
            elif sort_by == "保守整理番号": # 保守整理番号でソートする場合
                # 保守整理番号が数値と文字列混在の場合に対応するため、数値変換を試み、失敗したら文字列としてソート
                filtered_df['temp_sort_id'] = pd.to_numeric(filtered_df['保守整理番号'], errors='coerce')
                filtered_df = filtered_df.sort_values(
                    by=['temp_sort_id', '保守整理番号'], 
                    ascending=[ascending, ascending]
                ).drop(columns='temp_sort_id')
            elif sort_by == "エラー内容": # エラー内容でソートする場合
                # 表示されるエラーメッセージでソートするため、一時的にカラムを作成
                filtered_df['temp_error_message'] = filtered_df['チェックID'].apply(self.get_error_message_by_check_id)
                filtered_df = filtered_df.sort_values(by='temp_error_message', ascending=ascending).drop(columns='temp_error_message')
            else: # シリーズ, チェックIDの場合
                filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
        
        self.filtered_results_df = filtered_df # フィルタリング・ソート後のDataFrameを保持
        self._display_results_in_treeview() # Treeviewを更新

    def _display_results_in_treeview(self):
        """現在のfiltered_results_dfの内容をTreeviewに表示する"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for _, row in self.filtered_results_df.iterrows():
            # Treeviewに表示する際に、チェックIDから実際のメッセージを取得して渡す
            error_message_for_display = self.get_error_message_by_check_id(row["チェックID"])
            # ここも「ユーザID」から「ユーザID」に
            # 保守整理番号カラムを追加
            self.tree.insert("", "end", values=(row["シリーズ"], row["ユーザID"], row.get("保守整理番号", ""), row["チェックID"], error_message_for_display))
        
        # サマリーレポートも更新
        self._update_summary_report()


    def _update_summary_report(self):
        """サマリーレポートを生成し、テキストエリアに表示する"""
        self.summary_text.config(state="normal")
        self.summary_text.delete(1.0, tk.END)

        if self.all_results_df.empty:
            self.summary_text.insert(tk.END, "--- チェック結果のサマリー ---\n\nエラーは見つかりませんでした。\n")
        else:
            total_errors = len(self.all_results_df)
            series_counts = self.all_results_df["シリーズ"].value_counts().sort_index()
            
            # エラー内容のカウントは、表示メッセージではなくチェックIDを基にする
            error_check_id_counts = self.all_results_df["チェックID"].value_counts().nlargest(5) # 上位5つのチェックID

            summary_report = "--- チェック結果のサマリー ---\n\n"
            summary_report += f"総エラー件数: {total_errors} 件\n\n"
            summary_report += "シリーズ別エラー件数:\n"
            for series, count in series_counts.items():
                summary_report += f"  - {series}: {count} 件\n"
            
            if not error_check_id_counts.empty:
                summary_report += "\n主なエラー内容 (上位5件):\n"
                for check_id, count in error_check_id_counts.items():
                    # サマリーではチェックIDと、その現在のメッセージを表示
                    summary_report += f"  - {check_id} ({self.get_error_message_by_check_id(check_id)}): {count} 件\n"
            else:
                summary_report += "\nエラー内容の詳細は表示できません。\n"

            self.summary_text.insert(tk.END, summary_report)
        self.summary_text.config(state="disabled")


    def clear_results(self):
        """表示中の結果と内部のDataFrameを全てクリアする"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        # 「ユーザID」を「ユーザID」に
        self.all_results_df = pd.DataFrame(columns=["シリーズ", "ユーザID", "チェックID"])
        self.filtered_results_df = pd.DataFrame(columns=["シリーズ", "ユーザID", "チェックID"])
        self.download_button.config(state="disabled")
        self.status_label.config(text="結果をクリアしました。")
        self.summary_text.config(state="normal")
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.config(state="disabled")
        messagebox.showinfo("クリア", "チェック結果を全てクリアしました。")


    def download_results(self):
        if self.all_results_df.empty:
            messagebox.showwarning("ダウンロード不可", "ダウンロードするチェック結果がありません。")
            return

        # ダウンロードするDataFrameに表示用のエラーメッセージを追加する
        df_to_save = self.all_results_df.copy()
        df_to_save["エラー内容"] = df_to_save["チェックID"].apply(self.get_error_message_by_check_id)
        
        # カラム順を調整 (シリーズ, ユーザID, 保守整理番号, チェックID, エラー内容)
        df_to_save = df_to_save[["シリーズ", "ユーザID", "保守整理番号", "チェックID", "エラー内容"]]

        # 日付をファイル名に含める
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"チェック結果_{timestamp}"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", # デフォルトをExcelに
            filetypes=[("Excelファイル", "*.xlsx"), ("CSVファイル", "*.csv")],
            title="チェック結果を保存",
            initialfile=default_filename
        )
        if file_path:
            try:
                if file_path.endswith(".csv"):
                    df_to_save.to_csv(file_path, index=False, encoding='utf-8-sig') # Excelで開く際に文字化けしないようBOM付きUTF-8
                elif file_path.endswith(".xlsx"):
                    # pandasのto_excelはopenpyxlエンジンを使用するため、別途importは不要だが、念のためコメント
                    df_to_save.to_excel(file_path, index=False)
                messagebox.showinfo("ダウンロード完了", f"チェック結果を '{os.path.basename(file_path)}' に保存しました。")
            except Exception as e:
                messagebox.showerror("ダウンロードエラー", f"ファイルの保存中にエラーが発生しました。\n\n詳細: {e}")

    def show_usage_info(self):
        """使い方情報を表示する新しいウィンドウを開く"""
        usage_window = tk.Toplevel(self.master)
        usage_window.title("使い方")
        usage_window.geometry("550x400") 
        usage_window.transient(self.master)
        usage_window.grab_set()

        usage_text = """
        このアプリケーションは、各シリーズの基幹データをチェックし、エラーを検出します。

        【使い方】
        1. **補助ファイル設定**:
           - 最初に「補助ファイル設定」ボタンをクリックし、各チェックに必要な補助ファイルのパスを設定してください。
           - 設定は自動的に保存され、次回起動時も引き継がれます。

        2. **チェック内容編集**:
           - 「設定」メニューから「チェック内容編集」を選択すると、各チェックエラーの表示文言をカスタマイズできます。
           - シリーズやキーワードでフィルタリングして表示を絞り込むことも可能です。

        3. **データチェックの実行**:
           - 左側の「データチェックの実行」セクションから、チェックしたい**シリーズのボタンをクリック**してください。
           - 実行中はステータスバーに進捗が表示されます。

        4. **チェック結果の確認とフィルタリング**:
           - チェックが完了すると、右側の「チェック結果一覧」にエラー情報が表示されます。
           - 上部の「フィルタリングとソート」セクションで、シリーズ、エラー内容、ソート基準、ソート順を指定して結果を絞り込んだり並べ替えたりできます。

        5. **サマリーレポート**:
           - 右下の「サマリーレポート」に、チェック結果の概要が表示されます。

        6. **結果のダウンロード**:
           - エラーが見つかった場合、「チェック結果をダウンロード」ボタンで結果をCSVまたはExcelファイルとして保存できます。

        7. **チェック内容一覧**:
           - 「ヘルプ」メニューから「チェック内容一覧」を選択すると、定義されているすべてのチェック項目とその説明を確認できます。
           - シリーズやキーワードでフィルタリングして表示を絞り込むことも可能です。

        ご不明な点があれば、情報システム部 今久留主までお問い合わせください。
        """

        usage_label = ttk.Label(usage_window, text=usage_text, wraplength=500, justify=tk.LEFT)
        usage_label.pack(padx=15, pady=15)

        close_button = ttk.Button(usage_window, text="閉じる", command=usage_window.destroy)
        close_button.pack(pady=5)

        usage_window.protocol("WM_DELETE_WINDOW", usage_window.destroy)
        self.master.wait_window(usage_window)

    def show_version_info(self):
        """バージョン情報を表示する新しいウィンドウを開く"""
        version_window = tk.Toplevel(self.master)
        version_window.title("バージョン情報")
        version_window.geometry("380x160")
        version_window.transient(self.master)
        version_window.grab_set()

        version_info_text = f"""
        **基幹データチェックプログラム**
        
        バージョン: {self.APP_VERSION}
        作成者: {self.APP_AUTHOR}
        最終更新日: {self.APP_DATE}

        このプログラムは、社内基幹データの整合性をチェックするために開発されました。
        """
        version_label = ttk.Label(version_window, text=version_info_text, justify=tk.LEFT)
        version_label.pack(padx=10, pady=10)

        close_button = ttk.Button(version_window, text="閉じる", command=version_window.destroy)
        close_button.pack(pady=5)

        version_window.protocol("WM_DELETE_WINDOW", version_window.destroy)
        self.master.wait_window(version_window)


if __name__ == "__main__":
    # 必要なライブラリのチェックを一元化
    required_libraries = {
        "pyodbc": "pip install pyodbc",
        "pandas": "pip install pandas",
        "openpyxl": "pip install openpyxl", # Excelファイルの読み書きに必要
        "chardet": "pip install chardet",   # ファイルエンコーディング自動判別に便利
    }

    for lib, install_cmd in required_libraries.items():
        try:
            __import__(lib)
        except ImportError:
            messagebox.showerror("ライブラリ不足エラー",
                                 f"'{lib}' がインストールされていません。\n\n"
                                 f"コマンドプロンプトやターミナルで以下のコマンドを実行してインストールしてください:\n"
                                 f"'{install_cmd}'\n\n"
                                 f"アプリケーションを終了します。")
            sys.exit(1)

    root = tk.Tk()
    app = DataCheckerApp(root)
    root.mainloop()