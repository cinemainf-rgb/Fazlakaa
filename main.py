from kivy.app import App
from kivy.core.window import Window
Window.clearcolor = (0.02, 0.02, 0.08, 1)
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
import socket, hashlib, binascii, threading, traceback, random, json, os
from datetime import datetime

def L(text, h=28, color=(1,1,1,1), size=16, bold=False):
    lbl = Label(text=text, size_hint_y=None, height=h, color=color, font_size=size, bold=bold, halign='center', valign='middle')
    lbl.bind(size=lambda *x: setattr(lbl, 'text_size', lbl.size))
    return lbl

def TITLE(text, color):
    # خط بعنوان وتحته خط
    b = BoxLayout(orientation='vertical', size_hint_y=None, height=38, spacing=2)
    b.add_widget(L(text, h=28, color=color, size=19, bold=True))
    line = Label(size_hint_y=None, height=2)
    with line.canvas:
        Color(*color, 0.6)
        RoundedRectangle(pos=line.pos, size=(400, 2), radius=[1])
    b.add_widget(line)
    return b

def T(text="", hint=""):
    ti = TextInput(text=text, hint_text=hint, multiline=False, size_hint_y=None, height=52, font_size=18, background_color=(1,1,1,1), foreground_color=(0,0,0,1), padding=[12, 12, 12, 12])
    return ti

def B(text, fn, h=54, bg=(0.2,0.6,1,1)):
    btn = Button(text=text, size_hint_y=None, height=h, font_size=17, bold=True, background_color=bg, background_normal='')
    btn.bind(on_press=fn)
    return btn

def FIELD(label_text, input_widget):
    # خانة بعنوان فوقها زي النموذج
    box = BoxLayout(orientation='vertical', size_hint_y=None, height=82, spacing=4)
    box.add_widget(Label(text=label_text, size_hint_y=None, height=22, color=(0.85,0.85,0.85,1), font_size=14, halign='left', valign='middle'))
    box.add_widget(input_widget)
    return box

class FazlakaApp(App):
    selected_profile = "vip"
    router_pass = ""
    last_cards = []
    last_card_info = None
    profile_btns = {}
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
                    d=json.load(f)
                    self.ip_input.text=d.get("ip","10.10.10.1")
                    self.user_input.text=d.get("user","admin")
                    self.pass_input.text=d.get("pass","")
                    self.router_pass=d.get("pass","")
                    return True
        except: pass
        return False
    def build(self):
        self.sm = ScreenManager()
        # ===== LOGIN - زي النموذج =====
        login = Screen(name='login')
        s1 = ScrollView()
        r1 = GridLayout(cols=1, spacing=10, padding=[20, 20, 20, 20], size_hint_y=None)
        r1.bind(minimum_height=r1.setter('height'))
        r1.add_widget(L(" ", h=30))
        r1.add_widget(L("FAZLAKA", h=62, color=(0,0.9,1,1), size=40, bold=True))
        r1.add_widget(L("Hotspot Manager", h=24, color=(0.7,0.7,0.8,1), size=15))
        r1.add_widget(L(" ", h=20))
        r1.add_widget(TITLE("--- Login ---", (1,0.8,0,1)))
        self.ip_input = T(text="10.10.10.1"); r1.add_widget(FIELD("Router IP", self.ip_input))
        self.user_input = T(text="admin"); r1.add_widget(FIELD("Router User", self.user_input))
        self.pass_input = T(hint="Router Password"); self.pass_input.password=True; r1.add_widget(FIELD("Router Password", self.pass_input))
        self.login_status = L("Not Connected", h=30, color=(1,0.5,0.5,1), bold=True); r1.add_widget(self.login_status)
        r1.add_widget(B("LOGIN / CONNECT", self.do_login, h=60, bg=(0,0.75,0.3,1)))
        r1.add_widget(L("RazyTech - 5890IV", h=22, color=(0.5,0.5,0.6,1), size=13))
        s1.add_widget(r1); login.add_widget(s1); self.sm.add_widget(login)
        # ===== MAIN - زي النموذج =====
        main = Screen(name='main')
        s2 = ScrollView()
        root = GridLayout(cols=1, spacing=8, padding=[14, 14, 14, 14], size_hint_y=None)
        root.bind(minimum_height=root.setter('height'))
        # Top bar
        top = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=8)
        top.add_widget(Button(text="LOGOUT", size_hint_x=0.3, background_color=(0.4,0.4,0.45,1), background_normal='', bold=True, on_press=self.do_logout))
        top.add_widget(L("FAZLAKA", h=44, color=(0,0.9,1,1), size=24, bold=True))
        top.add_widget(Label(size_hint_x=0.3))
        root.add_widget(top)
        self.router_name = L("Router: x86  |  RouterOS 5.18", h=26, bold=True); root.add_widget(self.router_name)
        self.router_info = L("Uptime: -", h=22, color=(0.8,0.8,0.8,1)); root.add_widget(self.router_info)
        self.hotspot_label = L("Active: - | Users: - | Profiles: -", h=30, color=(1,1,0,1), size=17, bold=True); root.add_widget(self.hotspot_label)
        self.selected_label = L("Selected Profile:  vip", h=30, color=(1,1,1,1), size=16, bold=True); root.add_widget(self.selected_label)
        root.add_widget(B("SHOW ACTIVE USERS  •  REFRESH", self.show_active, h=48, bg=(0.15,0.45,0.2,1)))
        root.add_widget(TITLE("Choose Profile", (0,0.8,1,1)))
        grid = GridLayout(cols=2, spacing=8, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        for prof in ["M", "2M", "vip", "vip_5M", "profile_20_2GB", "profile_50_8GB", "profile_100_2GB"]:
            btn = B(prof, lambda x, p=prof: self.select_profile(p), h=50, bg=(0.15,0.15,0.25,1))
            self.profile_btns[prof] = btn
            grid.add_widget(btn)
        # fix last row span
        root.add_widget(grid)
        self.update_profile_colors()
        root.add_widget(TITLE("Create Cards", (0,1,0.5,1)))
        # Price + Quota in one row - زي النموذج
        row1 = GridLayout(cols=2, spacing=10, size_hint_y=None, height=82)
        self.price_input = T(text="20"); row1.add_widget(FIELD("Price", self.price_input))
        self.quota_input = T(text="5"); row1.add_widget(FIELD("Quota GB", self.quota_input))
        root.add_widget(row1)
        row2 = GridLayout(cols=2, spacing=10, size_hint_y=None, height=82)
        self.time_input = T(text="24"); row2.add_widget(FIELD("Time Hours", self.time_input))
        self.digits_input = T(text="6"); row2.add_widget(FIELD("Card Digits", self.digits_input))
        root.add_widget(row2)
        self.count_input = T(text="10"); root.add_widget(FIELD("Number of Cards", self.count_input))
        self.result = L("", h=36, color=(0,1,0.5,1), bold=True); root.add_widget(self.result)
        self.cards_list = L("", h=180, color=(1,1,1,1)); root.add_widget(self.cards_list)
        root.add_widget(B("GENERATE RANDOM CARDS", self.do_create, h=56, bg=(0,0.6,0.95,1)))
        root.add_widget(B("PRINT DIRECT - RazyTech", self.print_direct, h=56, bg=(1,0.6,0,1)))
        root.add_widget(B("SAVE CARDS FOR RawBT", self.save_for_rawbt, h=48, bg=(0.6,0.4,0,1)))
        root.add_widget(B("SALES", lambda x: threading.Thread(target=self.show_sales, daemon=True).start(), h=52, bg=(0.55,0.2,0.85,1)))
        root.add_widget(TITLE("Expenses", (1,0.4,0.4,1)))
        row3 = GridLayout(cols=2, spacing=10, size_hint_y=None, height=82)
        self.expense_amount = T(text="", hint="0.00"); row3.add_widget(FIELD("Amount", self.expense_amount))
        self.expense_reason = T(text="", hint="Reason"); row3.add_widget(FIELD("Description", self.expense_reason))
        root.add_widget(row3)
        root.add_widget(B("ADD EXPENSE", self.do_add_expense, h=54, bg=(0.9,0.2,0.2,1)))
        root.add_widget(L(" ", h=20))
        s2.add_widget(root); main.add_widget(s2); self.sm.add_widget(main)
        Clock.schedule_once(self.try_auto_login, 1)
        return self.sm
    def update_profile_colors(self):
        for p, btn in self.profile_btns.items():
            if p == self.selected_profile:
                btn.background_color = (0,0.55,0.8,1)
            else:
                btn.background_color = (0.15,0.15,0.25,1)
    def try_auto_login(self, dt):
        if self.load_session() and self.router_pass:
            self.login_status.text = "Auto Login..."
            threading.Thread(target=self.refresh_dashboard, daemon=True).start()
    def do_logout(self, x):
        try:
            if os.path.exists("fazlaka_session.json"): os.remove("fazlaka_session.json")
        except: pass
        self.pass_input.text = ""; self.router_pass = ""
        self.login_status.text = "Logged Out"
        self.sm.current = 'login'
    def select_profile(self, p):
        self.selected_profile = p
        self.selected_label.text = f"Selected Profile:  {p}"
        self.update_profile_colors()
    def do_login(self, x):
        self.router_pass = self.pass_input.text
        if not self.router_pass:
            self.login_status.text = "Write Router Password First!"; return
        self.login_status.text = "Connecting..."
        threading.Thread(target=self.refresh_dashboard, daemon=True).start()
    def refresh_dashboard(self):
        try:
            sock = self.do_connect()
            res = self.query(sock, ['/system/resource/print'])
            active = self.query(sock, ['/ip/hotspot/active/print'])
            users = self.query(sock, ['/ip/hotspot/user/print'])
            profs = self.query(sock, ['/ip/hotspot/user/profile/print'])
            sock.close(); d = res[0] if res else {}
            def ok(dt):
                self.login_status.text = "Connected"; self.login_status.color = (0,0.8,0.5,1)
                self.router_name.text = f"Router: {d.get('board-name','x86')}  |  RouterOS {d.get('version','5.18')}"
                self.router_info.text = f"Uptime: {d.get('uptime','-')}"
                self.hotspot_label.text = f"Active: {len(active)} | Users: {len(users)} | Profiles: {len(profs)}"
                self.save_session()
                self.sm.current = 'main'
            Clock.schedule_once(ok, 0)
        except Exception as e:
            print(traceback.format_exc())
            Clock.schedule_once(lambda dt: setattr(self.login_status, 'text', f"Error: {e}"), 0)
    def show_active(self, x):
        threading.Thread(target=self.show_active_thread, daemon=True).start()
    def show_active_thread(self):
        try:
            sock = self.do_connect()
            active = self.query(sock, ['/ip/hotspot/active/print'])
            sock.close()
            txt = f"=== ACTIVE NOW: {len(active)} ===\n"
            for a in active[:30]:
                txt += f"{a.get('user','?')} - {a.get('address','-')} - {a.get('uptime','-')}\n"
            def ok(dt):
                self.cards_list.text = txt
                self.result.text = f"Active: {len(active)} users"
            Clock.schedule_once(ok, 0)
        except Exception as e:
            print(traceback.format_exc())
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Active Error: {e}"), 0)
    def do_connect(self):
        ip = self.ip_input.text.strip(); user = self.user_input.text.strip(); pw = self.router_pass
        sock = socket.socket(); sock.settimeout(7); sock.connect((ip, 8728))
        self.send_cmd(sock, ['/login']); res = self.read_all(sock)
        ch = None
        for s in res:
            if 'ret' in s: ch = binascii.unhexlify(s['ret'])
        if not ch: return sock
        m = hashlib.md5(); m.update(b'\x00' + pw.encode() + ch)
        resp = "00" + binascii.hexlify(m.digest()).decode()
        self.send_cmd(sock, ['/login', f'=name={user}', f'=response={resp}'])
        lr = self.read_all(sock)
        if any('!trap' in s for s in lr): raise Exception("Wrong User/Pass")
        return sock
    def query(self, sock, cmd):
        self.send_cmd(sock, cmd); return self.read_all(sock)
    def do_create(self, x):
        threading.Thread(target=self.create_thread, daemon=True).start()
    def create_thread(self):
        try:
            price = self.price_input.text.strip() or "0"
            try: quota_gb = float(self.quota_input.text.strip() or "0")
            except: quota_gb = 0
            try: time_hours = int(float(self.time_input.text.strip() or "0"))
            except: time_hours = 0
            try: digits = int(float(self.digits_input.text.strip() or "6"))
            except: digits = 6
            try: count = int(float(self.count_input.text.strip() or "1"))
            except: count = 1
            prof = self.selected_profile
            limit_bytes = int(quota_gb * 1024 * 1024 * 1024)
            limit_uptime = f"{time_hours//24}d {time_hours%24:02d}:00:00" if time_hours >= 24 else f"{time_hours:02d}:00:00"
            sock = self.do_connect()
            existing = self.query(sock, ['/ip/hotspot/user/print'])
            existing_names = set([s.get('name','') for s in existing])
            created = []; tries = 0
            while len(created) < count and tries < count * 20:
                tries += 1
                num = str(random.randint(10**(digits-1), 10**digits - 1))
                if num in existing_names or num in created: continue
                cmd = ['/ip/hotspot/user/add', f'=name={num}', f'=profile={prof}', '=server=all']
                if limit_bytes > 0: cmd.append(f'=limit-bytes-total={limit_bytes}')
                if time_hours > 0: cmd.append(f'=limit-uptime={limit_uptime}')
                self.send_cmd(sock, cmd); r = self.read_all(sock)
                if not any('!trap' in s for s in r):
                    created.append(num); existing_names.add(num)
            sock.close()
            def ok(dt):
                self.result.text = f"Done! Created {len(created)}/{count} Cards - {quota_gb}GB"
                txt = "=== CARDS ===\n"
                for c in created: txt += f"USER: {c}\nPrice: {price}\nQuota: {quota_gb}GB\n---\n"
                self.cards_list.text = txt
                self.last_cards = created
                self.last_card_info = (price, quota_gb, time_hours, prof)
                self.save_sale(price, quota_gb, time_hours, prof, len(created), created)
                threading.Thread(target=self.refresh_dashboard, daemon=True).start()
            Clock.schedule_once(ok, 0)
        except Exception as e:
            print(traceback.format_exc())
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Error: {e}"), 0)
    def save_for_rawbt(self, x):
        try:
            if not self.last_cards:
                self.result.text = "No Cards!"; return
            price, quota_gb, time_hours, prof = self.last_card_info
            txt = ""
            for c in self.last_cards:
                txt += f"Fazlaka\n{c}\nPrice: {price}  Quota: {quota_gb}GB\n\n\n"
            with open("fazlaka_cards_print.txt","w",encoding="utf-8") as f: f.write(txt)
            self.result.text = "Saved: fazlaka_cards_print.txt - Open in RawBT"
        except Exception as e:
            self.result.text = f"Save Error: {e}"
    def print_direct(self, x):
        threading.Thread(target=self.print_direct_thread, daemon=True).start()
    def print_direct_thread(self):
        try:
            if not self.last_cards:
                Clock.schedule_once(lambda dt: setattr(self.result, 'text', "No Cards!"), 0); return
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', "Connecting to Printer..."), 0)
            from jnius import autoclass, jarray, jbyte
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            UUID = autoclass('java.util.UUID')
            adapter = BluetoothAdapter.getDefaultAdapter()
            if adapter is None:
                Clock.schedule_once(lambda dt: setattr(self.result, 'text', "No Bluetooth! Use SAVE FOR RawBT"), 0); return
            if not adapter.isEnabled():
                Clock.schedule_once(lambda dt: setattr(self.result, 'text', "Turn On Bluetooth!"), 0); return
            device = adapter.getRemoteDevice("00:1B:35:12:31:36")
            uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
            sock = device.createInsecureRfcommSocketToServiceRecord(uuid)
            try: adapter.cancelDiscovery()
            except: pass
            sock.connect(); out = sock.getOutputStream()
            price, quota_gb, time_hours, prof = self.last_card_info
            for c in self.last_cards:
                data = b"\x1b\x40" + b"\x1b\x61\x01" + b"\x1b\x21\x10" + "Fazlaka\n".encode('utf-8') + b"\x1b\x21\x30" + f"{c}\n".encode('utf-8') + b"\x1b\x21\x00" + f"Price: {price}  Quota: {quota_gb}GB\n".encode('utf-8') + b"\n\n\n" + b"\x1d\x56\x41\x03"
                jarr = jarray(jbyte)(list(data))
                out.write(jarr); out.flush()
            out.close(); sock.close()
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', "Printed Direct!"), 0)
        except Exception as e:
            print(traceback.format_exc())
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Print Error: {e} - Use SAVE FOR RawBT"), 0)
    def save_sale(self, price, quota_gb, time_hours, prof, count, cards):
        try:
            try:
                with open("fazlaka_sales.json", "r", encoding="utf-8") as f: sales = json.load(f)
            except: sales = []
            current_month = datetime.now().strftime("%Y-%m")
            if sales and sales[-1].get("month", "") != current_month: sales = []
            try: p = float(price)
            except: p = 0
            sales.append({"month": current_month, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "price": p, "quota": quota_gb, "time": time_hours, "profile": prof, "count": count, "total": p * count, "cards": cards})
            with open("fazlaka_sales.json", "w", encoding="utf-8") as f: json.dump(sales, f, ensure_ascii=False, indent=2)
        except Exception as e: print(f"Save Sale Error: {e}")
    def show_sales(self):
        try:
            current_month = datetime.now().strftime("%Y-%m")
            try:
                with open("fazlaka_sales.json", "r", encoding="utf-8") as f: sales = json.load(f)
            except: sales = []
            month_sales = [s for s in sales if s.get("month", current_month) == current_month]
            total_cards = sum([s.get('count',0) for s in month_sales]); total_money = sum([s.get('total',0) for s in month_sales])
            try:
                with open("fazlaka_expenses.json", "r", encoding="utf-8") as f: exps = json.load(f)
            except: exps = []
            month_exps = [e for e in exps if e.get("month", current_month) == current_month]
            total_exp = sum([e.get('amount',0) for e in month_exps]); net = total_money - total_exp
            txt = f"ACCOUNTS - {current_month}\nSales: {total_cards} Cards - {total_money}\nExpenses: {total_exp}\nNet: {net}\n"
            def ok(dt):
                self.result.text = f"Sales: {total_money} - Exp: {total_exp} - Net: {net}"
                self.cards_list.text = txt
            Clock.schedule_once(ok, 0)
        except Exception as e:
            print(traceback.format_exc())
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Sales Error: {e}"), 0)
    def do_add_expense(self, x):
        threading.Thread(target=self.save_expense_thread, daemon=True).start()
    def save_expense_thread(self):
        try:
            amount_txt = self.expense_amount.text.strip(); reason = self.expense_reason.text.strip() or "Expense"
            if not amount_txt:
                Clock.schedule_once(lambda dt: setattr(self.result, 'text', "Write Expense Amount!"), 0); return
            amount = float(amount_txt); current_month = datetime.now().strftime("%Y-%m")
            try:
                with open("fazlaka_expenses.json", "r", encoding="utf-8") as f: exps = json.load(f)
            except: exps = []
            if exps and exps[-1].get("month", "") != current_month: exps = []
            exps.append({"month": current_month, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "amount": amount, "reason": reason})
            with open("fazlaka_expenses.json", "w", encoding="utf-8") as f: json.dump(exps, f, ensure_ascii=False, indent=2)
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Expense Added: {amount}"), 0)
            Clock.schedule_once(lambda dt: setattr(self.expense_amount, 'text', ""), 0)
            Clock.schedule_once(lambda dt: setattr(self.expense_reason, 'text', ""), 0)
        except Exception as e:
            print(traceback.format_exc())
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Expense Error: {e}"), 0)
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
            else:
                b = self._recv_exact(sock, 2); length = ((length & 0x3F) << 16) + (b[0] << 8) + b[1]
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
                    if w.startswith("=") and "=" in w[1:]:
                        k,v = w[1:].split("=",1); d[k]=v
                if d: out.append(d)
                break
            if sentence[0] == "!trap" or sentence[0] == "!fatal":
                out.append({"!trap": " ".join(sentence)}); continue
            if sentence[0] == "!re":
                d = {}
                for w in sentence[1:]:
                    if w.startswith("=") and "=" in w[1:]:
                        k,v = w[1:].split("=",1); d[k]=v
                out.append(d)
        return out
FazlakaApp().run()
