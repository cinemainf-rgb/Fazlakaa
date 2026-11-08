from kivy.app import App
from kivy.core.window import Window
Window.clearcolor = (0.03, 0.15, 0.19, 1)
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.clock import Clock
import socket, hashlib, binascii, threading, traceback, random, json, os
from datetime import datetime

CARD_BG = (0.06, 0.23, 0.27, 1)
INNER = (0.04, 0.18, 0.22, 1)
TURQ = (0.0, 0.80, 0.75, 1)
ORANGE = (1.0, 0.55, 0.0, 1)

PACKAGES = {
    "Package 20 - 2GB - 3 Days": {"profile": "profile_20_2GB", "price": "20", "quota": 2, "days": 3},
    "Package 50 - 8GB - 7 Days": {"profile": "profile_50_8GB", "price": "50", "quota": 8, "days": 7},
    "Package 100 - 20GB - 30 Days": {"profile": "profile_100_2GB", "price": "100", "quota": 20, "days": 30},
}

class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [12, 12, 12, 12]
        self.spacing = 8
        with self.canvas.before:
            Color(*CARD_BG)
            self.bg = RoundedRectangle(radius=[16,16,16,16])
            Color(0.0, 0.80, 0.75, 0.30)
            self.border = Line(rounded_rectangle=(0,0,0,0,16), width=1.1)
        self.bind(pos=self._upd, size=self._upd)
    def _upd(self, *a):
        self.bg.pos = self.pos; self.bg.size = self.size
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, 16)

def L(text, h=26, color=(1,1,1,1), size=16, bold=False):
    lbl = Label(text=text, size_hint_y=None, height=h, color=color, font_size=size, bold=bold, halign='center', valign='middle')
    lbl.bind(size=lambda *x: setattr(lbl, 'text_size', lbl.size))
    return lbl

def B(text, fn, h=54, bg=TURQ):
    btn = Button(text=text, size_hint_y=None, height=h, font_size=17, bold=True, background_color=bg, background_normal='')
    btn.bind(on_press=fn)
    return btn

def INPUT(text="", hint=""):
    return TextInput(text=text, hint_text=hint, multiline=False, size_hint_y=None, height=52, font_size=20,
                     background_color=INNER, foreground_color=(1,1,1,1),
                     hint_text_color=(0.6,0.7,0.7,1), padding=[12, 12, 12, 12])

def SMALL(title, value):
    box = BoxLayout(orientation='vertical', size_hint_y=None, height=68, spacing=2)
    with box.canvas.before:
        Color(*INNER)
        bg = RoundedRectangle(radius=[12,12,12,12])
        Color(0.0, 0.60, 0.60, 0.35)
        ln = Line(rounded_rectangle=(0,0,0,0,12), width=1)
    def upd(*a):
        bg.pos = box.pos; bg.size = box.size
        ln.rounded_rectangle = (box.x, box.y, box.width, box.height, 12)
    box.bind(pos=upd, size=upd)
    box.add_widget(L(title, h=20, color=(0.6,0.8,0.8,1), size=13))
    lbl = L(value, h=38, color=(1,1,1,1), size=18, bold=True)
    box.add_widget(lbl)
    return box, lbl

class FazlakaApp(App):
    selected_package = "Package 20 - 2GB - 3 Days"
    router_pass = ""; last_cards = []; last_card_info = None; show_pass = False
    def on_pause(self): return True
    def on_resume(self): pass
    def save_session(self):
        try:
            with open("fazlaka_session.json","w",encoding="utf-8") as f:
                json.dump({"ip":self.ip_input.text.strip(),"user":self.user_input.text.strip(),"pass":self.router_pass}, f)
        except: pass
    def load_session(self):
        try:
            if os.path.exists("fazlaka_session.json"):
                with open("fazlaka_session.json","r",encoding="utf-8") as f:
                    d=json.load(f); self.ip_input.text=d.get("ip","10.10.10.1"); self.user_input.text=d.get("user","admin"); self.pass_input.text=d.get("pass",""); self.router_pass=d.get("pass",""); return True
        except: pass
        return False
    def toggle_pass(self, x):
        self.show_pass = not self.show_pass; self.pass_input.password = not self.show_pass; self.eye_btn.text = "👁️" if not self.show_pass else "🙈"
    def on_package_change(self, spinner, text):
        if text not in PACKAGES: return
        self.selected_package = text; p = PACKAGES[text]
        if not hasattr(self, 'price_value'): return
        self.price_value.text = p["price"]; self.quota_value.text = f"{p['quota']}GB"; self.time_value.text = f"{p['days']} Days"
    def count_minus(self, x):
        try:
            v = int(float(self.count_input.text or "1"))
            if v > 1: self.count_input.text = str(v - 1)
        except: pass
    def count_plus(self, x):
        try:
            v = int(float(self.count_input.text or "1")); self.count_input.text = str(v + 1)
        except: pass
    def build(self):
        self.sm = ScreenManager()
        login = Screen(name='login')
        s1 = ScrollView(); r1 = GridLayout(cols=1, spacing=10, padding=[20, 20, 20, 20], size_hint_y=None); r1.bind(minimum_height=r1.setter('height'))
        r1.add_widget(L("FAZLAKA", h=48, color=TURQ, size=32, bold=True)); r1.add_widget(L("Hotspot Manager", h=20, color=(0.7,0.85,0.85,1), size=14))
        c = Card(size_hint_y=None, height=290); self.ip_input = INPUT(text="10.10.10.1"); c.add_widget(L("Server Address", h=20, color=(0.7,0.9,0.9,1), size=14)); c.add_widget(self.ip_input)
        self.user_input = INPUT(text="admin"); c.add_widget(L("Username", h=20, color=(0.7,0.9,0.9,1), size=14)); c.add_widget(self.user_input)
        pb = BoxLayout(orientation='horizontal', size_hint_y=None, height=52, spacing=8); self.pass_input = INPUT(hint="Password"); self.pass_input.password = True
        self.eye_btn = Button(text="👁️", size_hint_x=None, width=52, background_color=INNER, background_normal='', font_size=20, on_press=self.toggle_pass)
        pb.add_widget(self.pass_input); pb.add_widget(self.eye_btn); c.add_widget(L("Password", h=20, color=(0.7,0.9,0.9,1), size=14)); c.add_widget(pb); r1.add_widget(c)
        rem = BoxLayout(orientation='horizontal', size_hint_y=None, height=32, spacing=8); self.remember = CheckBox(size_hint_x=None, width=32, active=True, color=TURQ); rem.add_widget(self.remember); rem.add_widget(L("Remember Me", h=32, size=15)); rem.add_widget(Label(size_hint_x=1)); r1.add_widget(rem)
        self.login_status = L("Not Connected", h=26, color=(1,0.5,0.5,1), bold=True); r1.add_widget(self.login_status); r1.add_widget(B("CONNECT", self.do_login, h=56, bg=TURQ)); r1.add_widget(L("RazyTech - 5890IV", h=20, color=(0.5,0.7,0.7,1), size=12))
        s1.add_widget(r1); login.add_widget(s1); self.sm.add_widget(login)
        main = Screen(name='main'); s2 = ScrollView(); root = GridLayout(cols=1, spacing=12, padding=[14, 14, 14, 14], size_hint_y=None); root.bind(minimum_height=root.setter('height'))
        root.add_widget(L("FAZLAKA", h=36, color=TURQ, size=26, bold=True))
        # Card 1 - Router
        c1 = Card(size_hint_y=None, height=86); c1.add_widget(L("📶  Router Status", h=24, color=TURQ, size=16, bold=True))
        self.hotspot_label = L("Active: - | Users: -", h=28, color=(1,1,1,1), size=17, bold=True); c1.add_widget(self.hotspot_label)
        self.router_info = L("Uptime: -  |  Router: x86", h=20, color=(0.8,0.9,0.9,1), size=13); c1.add_widget(self.router_info); root.add_widget(c1)
        self.today_label = L("Today: 0 Cards - 0 EGP", h=24, color=(1,1,1,1), size=14, bold=True); root.add_widget(self.today_label)
        # Card 2 - Profile
        c2 = Card(size_hint_y=None, height=96); c2.add_widget(L("Profile", h=24, color=TURQ, size=16, bold=True))
        self.spinner = Spinner(text="Package 20 - 2GB - 3 Days", values=list(PACKAGES.keys()), size_hint_y=None, height=52, background_color=INNER, color=(1,1,1,1), font_size=16); self.spinner.bind(text=self.on_package_change); c2.add_widget(self.spinner); root.add_widget(c2)
        # Card 3 - Generate - NO BIG GAP
        c3 = Card(size_hint_y=None, height=196); c3.add_widget(L("Generate Cards", h=26, color=TURQ, size=17, bold=True))
        row1 = GridLayout(cols=3, spacing=8, size_hint_y=None, height=68); b1, self.price_value = SMALL("Price", "20"); b2, self.quota_value = SMALL("Quota", "2GB"); b3, self.time_value = SMALL("Time", "3 Days"); row1.add_widget(b1); row1.add_widget(b2); row1.add_widget(b3); c3.add_widget(row1)
        c3.add_widget(L("Number of Cards", h=20, color=(0.7,0.9,0.9,1), size=14))
        cb = BoxLayout(orientation='horizontal', size_hint_y=None, height=52, spacing=8); bm = Button(text="-", size_hint_x=None, width=52, background_color=INNER, background_normal='', bold=True, font_size=24, on_press=self.count_minus); self.count_input = INPUT(text="10"); bp = Button(text="+", size_hint_x=None, width=52, background_color=TURQ, background_normal='', bold=True, font_size=24, on_press=self.count_plus); cb.add_widget(bm); cb.add_widget(self.count_input); cb.add_widget(bp); c3.add_widget(cb); root.add_widget(c3)
        self.result = L("", h=26, color=TURQ, bold=True); root.add_widget(self.result)
        # FIX GAP: cards_list height 0 لحد ما تولّد
        self.cards_list = L("", h=0, color=(1,1,1,1)); root.add_widget(self.cards_list)
        root.add_widget(B("Generate Cards", self.do_create, h=56, bg=TURQ))
        root.add_widget(B("Print - RazyTech", self.print_safe, h=56, bg=ORANGE))
        rp = GridLayout(cols=2, spacing=10, size_hint_y=None, height=46); rp.add_widget(B("Reprint", self.reprint, h=46, bg=(0.25,0.25,0.30,1))); rp.add_widget(B("Test Printer", self.test_print, h=46, bg=(0.25,0.25,0.30,1))); root.add_widget(rp)
        # Card 4 - Accounts
        c4 = Card(size_hint_y=None, height=170); c4.add_widget(L("Accounts", h=26, color=TURQ, size=17, bold=True)); c4.add_widget(B("Show Accounts - SALES", lambda x: threading.Thread(target=self.show_sales, daemon=True).start(), h=50, bg=(0.45,0.15,0.65,1)))
        row3 = GridLayout(cols=2, spacing=10, size_hint_y=None, height=52); self.expense_amount = INPUT(hint="0.00"); self.expense_reason = INPUT(hint="Reason"); row3.add_widget(self.expense_amount); row3.add_widget(self.expense_reason); c4.add_widget(row3); c4.add_widget(B("Add Expense", self.do_add_expense, h=46, bg=(0.85,0.2,0.2,1))); root.add_widget(c4)
        s2.add_widget(root); main.add_widget(s2); self.sm.add_widget(main)
        Clock.schedule_once(self.try_auto_login, 1); return self.sm
    def try_auto_login(self, dt):
        if self.load_session() and self.router_pass and self.remember.active:
            self.login_status.text = "Auto Login..."; threading.Thread(target=self.refresh_dashboard, daemon=True).start()
    def do_logout(self, x):
        try:
            if os.path.exists("fazlaka_session.json"): os.remove("fazlaka_session.json")
        except: pass
        self.pass_input.text = ""; self.router_pass = ""; self.login_status.text = "Logged Out"; self.sm.current = 'login'
    def do_login(self, x):
        self.router_pass = self.pass_input.text
        if not self.router_pass: self.login_status.text = "Write Router Password First!"; return
        self.login_status.text = "Connecting..."; threading.Thread(target=self.refresh_dashboard, daemon=True).start()
    def refresh_dashboard(self):
        try:
            sock = self.do_connect(); res = self.query(sock, ['/system/resource/print']); active = self.query(sock, ['/ip/hotspot/active/print']); users = self.query(sock, ['/ip/hotspot/user/print']); profs = self.query(sock, ['/ip/hotspot/user/profile/print']); sock.close(); d = res[0] if res else {}
            def ok(dt):
                self.login_status.text = "Connected"; self.login_status.color = TURQ; self.router_info.text = f"Uptime: {d.get('uptime','-')}  |  Router: {d.get('board-name','x86')}"; self.hotspot_label.text = f"Active: {len(active)} | Users: {len(users)}"
                if self.remember.active: self.save_session()
                self.sm.current = 'main'; threading.Thread(target=self.update_today, daemon=True).start()
            Clock.schedule_once(ok, 0)
        except Exception as e:
            print(traceback.format_exc()); Clock.schedule_once(lambda dt: setattr(self.login_status, 'text', f"Error: {e}"), 0)
    def update_today(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                with open("fazlaka_sales.json", "r", encoding="utf-8") as f: sales = json.load(f)
            except: sales = []
            t = [s for s in sales if s.get("date","").startswith(today)]; c = sum([s.get('count',0) for s in t]); m = sum([s.get('total',0) for s in t]); Clock.schedule_once(lambda dt: setattr(self.today_label, 'text', f"Today: {c} Cards - {m} EGP"), 0)
        except: pass
    def do_connect(self):
        ip = self.ip_input.text.strip(); user = self.user_input.text.strip(); pw = self.router_pass; sock = socket.socket(); sock.settimeout(7); sock.connect((ip, 8728)); self.send_cmd(sock, ['/login']); res = self.read_all(sock); ch = None
        for s in res:
            if 'ret' in s: ch = binascii.unhexlify(s['ret'])
        if not ch: return sock
        m = hashlib.md5(); m.update(b'\x00' + pw.encode() + ch); resp = "00" + binascii.hexlify(m.digest()).decode(); self.send_cmd(sock, ['/login', f'=name={user}', f'=response={resp}']); lr = self.read_all(sock)
        if any('!trap' in s for s in lr): raise Exception("Wrong User/Pass")
        return sock
    def query(self, sock, cmd): self.send_cmd(sock, cmd); return self.read_all(sock)
    def do_create(self, x): threading.Thread(target=self.create_thread, daemon=True).start()
    def create_thread(self):
        try:
            pkg = PACKAGES[self.selected_package]; price = pkg["price"]; quota_gb = pkg["quota"]; days = pkg["days"]; prof = pkg["profile"]
            try: count = int(float(self.count_input.text.strip() or "1"))
            except: count = 1
            limit_bytes = int(quota_gb * 1024 * 1024 * 1024); limit_uptime = f"{days}d 00:00:00"; sock = self.do_connect(); existing = self.query(sock, ['/ip/hotspot/user/print']); existing_names = set([s.get('name','') for s in existing]); created = []; tries = 0
            while len(created) < count and tries < count * 20:
                tries += 1; num = str(random.randint(10**6, 10**7 - 1))
                if num in existing_names or num in created: continue
                cmd = ['/ip/hotspot/user/add', f'=name={num}', f'=profile={prof}', '=server=all']
                if limit_bytes > 0: cmd.append(f'=limit-bytes-total={limit_bytes}')
                if days > 0: cmd.append(f'=limit-uptime={limit_uptime}')
                self.send_cmd(sock, cmd); r = self.read_all(sock)
                if not any('!trap' in s for s in r): created.append(num); existing_names.add(num)
            sock.close()
            def ok(dt):
                self.result.text = f"Done! {len(created)}/{count} Cards - {quota_gb}GB - {days} Days"; txt = "=== CARDS ===\n"
                for c in created: txt += f"USER: {c}  Price: {price}\n"
                self.cards_list.text = txt; self.cards_list.height = 24 * (len(created) + 1); self.last_cards = created; self.last_card_info = (price, quota_gb, days, prof); self.save_sale(price, quota_gb, days, prof, len(created), created); threading.Thread(target=self.refresh_dashboard, daemon=True).start(); threading.Thread(target=self.update_today, daemon=True).start()
            Clock.schedule_once(ok, 0)
        except Exception as e: print(traceback.format_exc()); Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Error: {e}"), 0)
    def _save_txt_and_open(self, txt):
        try:
            from jnius import autoclass; Env = autoclass('android.os.Environment'); dl = Env.getExternalStoragePublicDirectory(Env.DIRECTORY_DOWNLOADS).getAbsolutePath(); path = os.path.join(dl, "fazlaka_cards_print.txt")
        except: path = "fazlaka_cards_print.txt"
        with open(path,"w",encoding="utf-8") as f: f.write(txt)
        try:
            from jnius import autoclass; Intent = autoclass('android.content.Intent'); Uri = autoclass('android.net.Uri'); PythonActivity = autoclass('org.kivy.android.PythonActivity'); activity = PythonActivity.mActivity; f = autoclass('java.io.File')(path); uri = Uri.fromFile(f); intent = Intent(Intent.ACTION_VIEW); intent.setDataAndType(uri, "text/plain"); intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION); activity.startActivity(Intent.createChooser(intent, "Print with RawBT"))
        except Exception as e: print(f"Intent Error: {e}")
        return path
    def print_safe(self, x):
        try:
            if not self.last_cards: self.result.text = "No Cards! Generate First"; return
            price, quota_gb, days, prof = self.last_card_info; txt = ""
            for c in self.last_cards: txt += f"Fazlaka\n{c}\nPrice: {price}  Quota: {quota_gb}GB\n\n\n"
            self._save_txt_and_open(txt); self.result.text = "Saved - Open RawBT to Print"
        except Exception as e: print(traceback.format_exc()); self.result.text = f"Print Error: {e}"
    def reprint(self, x): self.print_safe(x)
    def test_print(self, x):
        try: txt = "Fazlaka - Test\nRazyTech 5890IV\nOK\n\n\n"; self._save_txt_and_open(txt); self.result.text = "Test Print - Open RawBT"
        except Exception as e: self.result.text = f"Test Error: {e}"
    def save_sale(self, price, quota_gb, days, prof, count, cards):
        try:
            try:
                with open("fazlaka_sales.json", "r", encoding="utf-8") as f: sales = json.load(f)
            except: sales = []
            current_month = datetime.now().strftime("%Y-%m")
            if sales and sales[-1].get("month", "") != current_month: sales = []
            try: p = float(price)
            except: p = 0
            sales.append({"month": current_month, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "price": p, "quota": quota_gb, "time": days, "profile": prof, "count": count, "total": p * count, "cards": cards})
            with open("fazlaka_sales.json", "w", encoding="utf-8") as f: json.dump(sales, f, ensure_ascii=False, indent=2)
        except Exception as e: print(f"Save Sale Error: {e}")
    def show_sales(self):
        try:
            current_month = datetime.now().strftime("%Y-%m")
            try:
                with open("fazlaka_sales.json", "r", encoding="utf-8") as f: sales = json.load(f)
            except: sales = []
            month_sales = [s for s in sales if s.get("month", current_month) == current_month]; total_cards = sum([s.get('count',0) for s in month_sales]); total_money = sum([s.get('total',0) for s in month_sales])
            try:
                with open("fazlaka_expenses.json", "r", encoding="utf-8") as f: exps = json.load(f)
            except: exps = []
            month_exps = [e for e in exps if e.get("month", current_month) == current_month]; total_exp = sum([e.get('amount',0) for e in month_exps]); net = total_money - total_exp; txt = f"Accounts - {current_month}\nSales: {total_cards} Cards - {total_money} EGP\nExpenses: {total_exp}\nNet: {net}\n"
            def ok(dt): self.result.text = f"Sales: {total_money} - Exp: {total_exp} - Net: {net}"; self.cards_list.text = txt; self.cards_list.height = 100
            Clock.schedule_once(ok, 0)
        except Exception as e: print(traceback.format_exc()); Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Sales Error: {e}"), 0)
    def do_add_expense(self, x): threading.Thread(target=self.save_expense_thread, daemon=True).start()
    def save_expense_thread(self):
        try:
            amount_txt = self.expense_amount.text.strip(); reason = self.expense_reason.text.strip() or "Expense"
            if not amount_txt: Clock.schedule_once(lambda dt: setattr(self.result, 'text', "Write Expense Amount!"), 0); return
            amount = float(amount_txt); current_month = datetime.now().strftime("%Y-%m")
            try:
                with open("fazlaka_expenses.json", "r", encoding="utf-8") as f: exps = json.load(f)
            except: exps = []
            if exps and exps[-1].get("month", "") != current_month: exps = []
            exps.append({"month": current_month, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "amount": amount, "reason": reason})
            with open("fazlaka_expenses.json", "w", encoding="utf-8") as f: json.dump(exps, f, ensure_ascii=False, indent=2)
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Expense Added: {amount}"), 0); Clock.schedule_once(lambda dt: setattr(self.expense_amount, 'text', ""), 0); Clock.schedule_once(lambda dt: setattr(self.expense_reason, 'text', ""), 0)
        except Exception as e: print(traceback.format_exc()); Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Expense Error: {e}"), 0)
    def send_cmd(self, sock, words):
        for w in words:
            if isinstance(w, str): w = w.encode()
            l = len(w)
            if l < 0x80: sock.sendall(bytes([l]))
            elif l < 0x4000: sock.sendall(bytes([(l >> 8) | 0x80, l & 0xFF]))
            else: sock.sendall(bytes([(l >> 16) | 0xC0, (l >> 8) & 0xFF, l & 0xFF]))
            sock.sendall(w)
        sock.sendall(b"\x00")
    def _recv_exact(self, sock, n):
        data = b''
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk: break
            data += chunk
        return data
    def read_word(self, sock):
        first = self._recv_exact(sock, 1)
        if not first: return None
        length = first[0]
        if length == 0: return ""
        if (length & 0x80):
            if (length & 0xC0) == 0x80: length = ((length & 0x7F) << 8) + self._recv_exact(sock, 1)[0]
            else: b = self._recv_exact(sock, 2); length = ((length & 0x3F) << 16) + (b[0] << 8) + b[1]
        return self._recv_exact(sock, length).decode("utf-8", errors="ignore")
    def read_all(self, sock):
        out = []
        while True:
            sentence = []
            while True:
                w = self.read_word(sock)
                if w is None: return out
                if w == "": break
                sentence.append(w)
            if not sentence: continue
            if sentence[0] == "!done":
                d = {}
                for w in sentence[1:]:
                    if w.startswith("=") and "=" in w[1:]: k,v = w[1:].split("=",1); d[k]=v
                if d: out.append(d)
                break
            if sentence[0] == "!trap" or sentence[0] == "!fatal": out.append({"!trap": " ".join(sentence)}); continue
            if sentence[0] == "!re":
                d = {}
                for w in sentence[1:]:
                    if w.startswith("=") and "=" in w[1:]: k,v = w[1:].split("=",1); d[k]=v
                out.append(d)
        return out
FazlakaApp().run()
