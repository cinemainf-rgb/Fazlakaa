from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
import socket, hashlib, binascii, threading, traceback, random, json
from datetime import datetime
class FazlakaApp(App):
    selected_profile = "vip"
    router_pass = ""
    last_cards = []
    last_card_info = None
    def build(self):
        scroll = ScrollView()
        root = GridLayout(cols=1, spacing=5, padding=10, size_hint_y=None, height=1600)
        def L(text, h=28, color=(1,1,1,1)):
            lbl = Label(text=text, size_hint_y=None, height=h, color=color)
            root.add_widget(lbl); return lbl
        def T(text="", hint=""):
            ti = TextInput(text=text, hint_text=hint, multiline=False, size_hint_y=None, height=45)
            root.add_widget(ti); return ti
        def B(text, fn, h=48):
            btn = Button(text=text, size_hint_y=None, height=h)
            btn.bind(on_press=fn); root.add_widget(btn); return btn
        L("Fazlaka - Login", h=35)
        L("Router IP", h=22); self.ip_input = T(text="10.10.10.1")
        L("Router User", h=22); self.user_input = T(text="admin")
        L("Router Password", h=22); self.pass_input = T(hint="Router Password"); self.pass_input.password = True
        self.login_status = L("Not Connected", h=28, color=(1,0.5,0.5,1))
        B("LOGIN / CONNECT", self.do_login)
        self.router_name = L("Router: -", h=28)
        self.router_info = L("RouterOS - Uptime: -", h=25)
        self.hotspot_label = L("Hotspot: -", h=28)
        self.selected_label = L("Selected Profile: vip", h=30, color=(1,1,0,1))
        L("--- Choose Profile ---", h=28, color=(0,0.8,1,1))
        for prof in ["M", "2M", "vip", "vip_5M", "profile_20_2GB", "profile_50_8GB", "profile_100_2GB"]:
            B(prof, lambda x, p=prof: self.select_profile(p), h=42)
        L("--- Create Cards ---", h=28, color=(0,1,0.5,1))
        L("Price", h=22); self.price_input = T(text="20")
        L("Quota GB", h=22); self.quota_input = T(text="5")
        L("Time Hours", h=22); self.time_input = T(text="24")
        L("Card Digits", h=22); self.digits_input = T(text="6")
        L("Number of Cards", h=22); self.count_input = T(text="10")
        self.result = L("", h=60, color=(0,1,0.5,1))
        self.cards_list = L("", h=300, color=(1,1,1,1))
        B("GENERATE RANDOM CARDS", self.do_create)
        B("PRINT DIRECT - RazyTech", self.print_direct)
        B("SALES", lambda x: threading.Thread(target=self.show_sales, daemon=True).start())
        L("--- Expenses ---", h=28, color=(1,0.5,0.5,1))
        L("Expense Amount", h=22); self.expense_amount = T(text="", hint="Expense")
        L("Expense Reason", h=22); self.expense_reason = T(text="", hint="Reason")
        B("ADD EXPENSE", self.do_add_expense)
        scroll.add_widget(root)
        return scroll
    def select_profile(self, p):
        self.selected_profile = p
        self.selected_label.text = f"Selected Profile: {p}"
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
                self.router_name.text = f"Router: {d.get('board-name','-')}"
                self.router_info.text = f"RouterOS {d.get('version','-')} - Uptime: {d.get('uptime','-')}"
                self.hotspot_label.text = f"Active: {len(active)} | Users: {len(users)} | Profiles: {len(profs)}"
            Clock.schedule_once(ok, 0)
        except Exception as e:
            print(traceback.format_exc())
            Clock.schedule_once(lambda dt: setattr(self.login_status, 'text', f"Error: {e}"), 0)
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
    def print_direct(self, x):
        threading.Thread(target=self.print_direct_thread, daemon=True).start()
    def print_direct_thread(self):
        try:
            if not self.last_cards:
                Clock.schedule_once(lambda dt: setattr(self.result, 'text', "No Cards!"), 0); return
            from jnius import autoclass, jarray, jbyte
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            UUID = autoclass('java.util.UUID')
            adapter = BluetoothAdapter.getDefaultAdapter()
            if not adapter.isEnabled():
                Clock.schedule_once(lambda dt: setattr(self.result, 'text', "Turn On Bluetooth!"), 0); return
            device = adapter.getRemoteDevice("00:1B:35:12:31:36")
            uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
            sock = device.createRfcommSocketToServiceRecord(uuid)
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
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Print Error: {e}"), 0)
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
