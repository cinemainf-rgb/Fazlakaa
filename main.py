from kivy.app import App
from kivy.core.window import Window
Window.clearcolor = (0.04, 0.16, 0.20, 1)
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
import socket, hashlib, binascii, threading, traceback, random, json, os
from datetime import datetime

PETROL = (0.04, 0.16, 0.20, 1)
PETROL_LIGHT = (0.07, 0.25, 0.29, 1)
TURQ = (0.0, 0.76, 0.70, 1)
ORANGE = (1.0, 0.55, 0.0, 1)

PACKAGES = {
    "باقة 20 - 2 جيجا - 3 أيام": {"profile": "profile_20_2GB", "price": "20", "quota": 2, "days": 3},
    "باقة 50 - 8 جيجا - 7 أيام": {"profile": "profile_50_8GB", "price": "50", "quota": 8, "days": 7},
    "باقة 100 - 20 جيجا - 30 يوم": {"profile": "profile_100_2GB", "price": "100", "quota": 20, "days": 30},
}

def L(text, h=28, color=(1,1,1,1), size=16, bold=False):
    lbl = Label(text=text, size_hint_y=None, height=h, color=color, font_size=size, bold=bold, halign='center', valign='middle')
    lbl.bind(size=lambda *x: setattr(lbl, 'text_size', lbl.size))
    return lbl

def B(text, fn, h=54, bg=TURQ):
    btn = Button(text=text, size_hint_y=None, height=h, font_size=17, bold=True, background_color=bg, background_normal='')
    btn.bind(on_press=fn)
    return btn

def INPUT(text="", hint="", readonly=False):
    ti = TextInput(text=text, hint_text=hint, multiline=False, size_hint_y=None, height=58, font_size=20,
                   background_color=PETROL_LIGHT, foreground_color=(1,1,1,1),
                   hint_text_color=(0.6,0.7,0.7,1), padding=[16, 14, 16, 14], readonly=readonly)
    return ti

def FIELD_AR(label_text, widget):
    box = BoxLayout(orientation='vertical', size_hint_y=None, height=92, spacing=4)
    lbl = Label(text=label_text, size_hint_y=None, height=26, color=(0.75,0.9,0.9,1), font_size=15, halign='right', valign='middle')
    lbl.bind(size=lambda *x: setattr(lbl, 'text_size', lbl.size))
    box.add_widget(lbl)
    box.add_widget(widget)
    return box

def INFO_BOX(title, value):
    # كارت صغير للسعر / الكوتة / الوقت - نفس الارتفاع
    box = BoxLayout(orientation='vertical', size_hint_y=None, height=70, spacing=2)
    box.add_widget(L(title, h=22, color=(0.7,0.9,0.9,1), size=13))
    lbl = L(value, h=44, color=(1,1,1,1), size=18, bold=True)
    box.add_widget(lbl)
    return box, lbl

class FazlakaApp(App):
    selected_package = "باقة 20 - 2 جيجا - 3 أيام"
    router_pass = ""
    last_cards = []
    last_card_info = None
    show_pass = False
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
    def toggle_pass(self, x):
        self.show_pass = not self.show_pass
        self.pass_input.password = not self.show_pass
        self.eye_btn.text = "👁️" if not self.show_pass else "🙈"
    def on_package_change(self, spinner, text):
        # FIX 1: حماية لو الخانات لسه متخلقتش
        if text not in PACKAGES:
            return
        self.selected_package = text
        p = PACKAGES[text]
        if not hasattr(self, 'price_value'):
            return
        self.price_value.text = p["price"]
        self.quota_value.text = f"{p['quota']}GB"
        self.time_value.text = f"{p['days']} يوم"
        self.selected_label.text = f"الباقة: {text}"
    def build(self):
        self.sm = ScreenManager()
        login = Screen(name='login')
        s1 = ScrollView()
        r1 = GridLayout(cols=1, spacing=8, padding=[18, 18, 18, 18], size_hint_y=None)
        r1.bind(minimum_height=r1.setter('height'))
        r1.add_widget(L("FAZLAKA", h=52, color=TURQ, size=34, bold=True))
        r1.add_widget(L("Hotspot Manager", h=22, color=(0.7,0.85,0.85,1), size=14))
        r1.add_widget(L(" ", h=10))
        self.ip_input = INPUT(text="10.10.10.1"); r1.add_widget(FIELD_AR("عنوان السيرفر", self.ip_input))
        self.user_input = INPUT(text="admin"); r1.add_widget(FIELD_AR("اسم المستخدم", self.user_input))
        pass_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=58, spacing=8)
        self.pass_input = INPUT(hint="••••••••")
        self.pass_input.password = True
        self.eye_btn = Button(text="👁️", size_hint_x=None, width=58, size_hint_y=None, height=58, background_color=PETROL_LIGHT, background_normal='', font_size=22, on_press=self.toggle_pass)
        pass_box.add_widget(self.pass_input); pass_box.add_widget(self.eye_btn)
        r1.add_widget(FIELD_AR("كلمة المرور", pass_box))
        rem = BoxLayout(orientation='horizontal', size_hint_y=None, height=36, spacing=8)
        self.remember = CheckBox(size_hint_x=None, width=36, active=True, color=TURQ)
        rem.add_widget(Label(size_hint_x=1))
        rem.add_widget(L("تذكر البيانات", h=36, color=(1,1,1,1), size=15))
        rem.add_widget(self.remember)
        r1.add_widget(rem)
        self.login_status = L("Not Connected", h=30, color=(1,0.5,0.5,1), bold=True); r1.add_widget(self.login_status)
        r1.add_widget(Button(text="الإتصال", size_hint_y=None, height=58, background_color=TURQ, background_normal='', bold=True, font_size=20, on_press=self.do_login))
        r1.add_widget(L("RazyTech - 5890IV  |  Fazlaka", h=22, color=(0.5,0.7,0.7,1), size=12))
        s1.add_widget(r1); login.add_widget(s1); self.sm.add_widget(login)
        main = Screen(name='main')
        s2 = ScrollView()
        root = GridLayout(cols=1, spacing=10, padding=[14, 14, 14, 14], size_hint_y=None)
        root.bind(minimum_height=root.setter('height'))
        top = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=8)
        top.add_widget(Button(text="خروج", size_hint_x=0.3, background_color=(0.2,0.3,0.3,1), background_normal='', bold=True, on_press=self.do_logout))
        top.add_widget(L("FAZLAKA", h=44, color=TURQ, size=24, bold=True))
        top.add_widget(Button(text="تحديث", size_hint_x=0.3, background_color=PETROL_LIGHT, background_normal='', bold=True, on_press=lambda x: threading.Thread(target=self.refresh_dashboard, daemon=True).start()))
        root.add_widget(top)
        self.router_name = L("Router: x86  |  RouterOS 5.18", h=26, bold=True); root.add_widget(self.router_name)
        self.router_info = L("Uptime: -", h=22, color=(0.8,0.9,0.9,1)); root.add_widget(self.router_info)
        self.hotspot_label = L("Active: - | Users: - | Profiles: -", h=30, color=TURQ, size=17, bold=True); root.add_widget(self.hotspot_label)
        self.today_label = L("النهاردة: 0 كارت - 0 جنيه", h=26, color=(1,1,1,1), size=15, bold=True); root.add_widget(self.today_label)
        root.add_widget(L("البروفايل", h=28, color=TURQ, size=18, bold=True))
        self.spinner = Spinner(text="باقة 20 - 2 جيجا - 3 أيام", values=list(PACKAGES.keys()), size_hint_y=None, height=58, background_color=PETROL_LIGHT, color=(1,1,1,1), font_size=17)
        self.spinner.bind(text=self.on_package_change)
        root.add_widget(self.spinner)
        self.selected_label = L("الباقة: باقة 20 - 2 جيجا - 3 أيام", h=28, color=(1,1,1,1), size=15, bold=True); root.add_widget(self.selected_label)
        root.add_widget(L("توليد كروت", h=32, color=TURQ, size=18, bold=True))
        # FIX 3: 3 كروت نفس الارتفاع - سعر / كوتة / وقت
        row1 = GridLayout(cols=3, spacing=8, size_hint_y=None, height=70)
        b1, self.price_value = INFO_BOX("السعر", "20")
        b2, self.quota_value = INFO_BOX("الكوتة", "2GB")
        b3, self.time_value = INFO_BOX("الوقت", "3 يوم")
        row1.add_widget(b1); row1.add_widget(b2); row1.add_widget(b3)
        root.add_widget(row1)
        root.add_widget(L("السعر والكوتة والوقت - يتمليوا تلقائي من الباقة", h=18, color=(0.6,0.7,0.7,1), size=12))
        self.count_input = INPUT(text="10"); root.add_widget(FIELD_AR("عدد الكروت", self.count_input))
        root.add_widget(L("أرقام الكارت: 7 ثابت", h=22, color=(0.7,0.9,0.9,1), size=13))
        self.result = L("", h=36, color=TURQ, bold=True); root.add_widget(self.result)
        self.cards_list = L("", h=180, color=(1,1,1,1)); root.add_widget(self.cards_list)
        root.add_widget(B("توليد كروت ✨", self.do_create, h=56, bg=TURQ))
        root.add_widget(B("طباعة - RazyTech 🖨️", self.print_safe, h=56, bg=ORANGE))
        row_print = GridLayout(cols=2, spacing=8, size_hint_y=None, height=48)
        row_print.add_widget(B("إعادة طباعة", self.reprint, h=48, bg=(0.3,0.3,0.35,1)))
        row_print.add_widget(B("تجربة الطابعة", self.test_print, h=48, bg=(0.3,0.3,0.35,1)))
        root.add_widget(row_print)
        root.add_widget(L("الطباعة بتفتح RawBT - من غير ما البرنامج يخرج", h=20, color=(0.7,0.8,0.8,1), size=13))
        root.add_widget(L("الحسابات", h=32, color=TURQ, size=18, bold=True))
        root.add_widget(B("عرض الحسابات - SALES", lambda x: threading.Thread(target=self.show_sales, daemon=True).start(), h=52, bg=(0.4,0.15,0.6,1)))
        row3 = GridLayout(cols=2, spacing=10, size_hint_y=None, height=92)
        self.expense_amount = INPUT(hint="0.00"); row3.add_widget(FIELD_AR("المبلغ", self.expense_amount))
        self.expense_reason = INPUT(hint="السبب"); row3.add_widget(FIELD_AR("السبب", self.expense_reason))
        root.add_widget(row3)
        root.add_widget(B("إضافة مصروف", self.do_add_expense, h=54, bg=(0.85,0.2,0.2,1)))
        root.add_widget(L(" ", h=20))
        s2.add_widget(root); main.add_widget(s2); self.sm.add_widget(main)
        Clock.schedule_once(self.try_auto_login, 1)
        return self.sm
    def try_auto_login(self, dt):
        if self.load_session() and self.router_pass and self.remember.active:
            self.login_status.text = "دخول تلقائي..."
            threading.Thread(target=self.refresh_dashboard, daemon=True).start()
    def do_logout(self, x):
        try:
            if os.path.exists("fazlaka_session.json"): os.remove("fazlaka_session.json")
        except: pass
        self.pass_input.text = ""; self.router_pass = ""
        self.login_status.text = "Logged Out"
        self.sm.current = 'login'
    def do_login(self, x):
        self.router_pass = self.pass_input.text
        if not self.router_pass:
            self.login_status.text = "اكتب كلمة مرور الراوتر الأول!"; return
        self.login_status.text = "جارٍ الاتصال..."
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
                self.login_status.text = "Connected"; self.login_status.color = TURQ
                self.router_name.text = f"Router: {d.get('board-name','x86')}  |  RouterOS {d.get('version','5.18')}"
                self.router_info.text = f"Uptime: {d.get('uptime','-')}"
                self.hotspot_label.text = f"Active: {len(active)} | Users: {len(users)} | Profiles: {len(profs)}"
                if self.remember.active: self.save_session()
                self.sm.current = 'main'
                threading.Thread(target=self.update_today, daemon=True).start()
            Clock.schedule_once(ok, 0)
        except Exception as e:
            print(traceback.format_exc())
            Clock.schedule_once(lambda dt: setattr(self.login_status, 'text', f"Error: {e}"), 0)
    def update_today(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                with open("fazlaka_sales.json", "r", encoding="utf-8") as f: sales = json.load(f)
            except: sales = []
            t = [s for s in sales if s.get("date","").startswith(today)]
            c = sum([s.get('count',0) for s in t]); m = sum([s.get('total',0) for s in t])
            Clock.schedule_once(lambda dt: setattr(self.today_label, 'text', f"النهاردة: {c} كارت - {m} جنيه"), 0)
        except: pass
    def do_connect(self):
        ip = self.ip_input.text.strip(); user = self.user_input.text.strip(); pw = self.router_pass
        port = 8728
        sock = socket.socket(); sock.settimeout(7); sock.connect((ip, port))
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
            pkg = PACKAGES[self.selected_package]
            price = pkg["price"]; quota_gb = pkg["quota"]; days = pkg["days"]; prof = pkg["profile"]
            digits = 7
            try: count = int(float(self.count_input.text.strip() or "1"))
            except: count = 1
            limit_bytes = int(quota_gb * 1024 * 1024 * 1024)
            limit_uptime = f"{days}d 00:00:00"
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
                if days > 0: cmd.append(f'=limit-uptime={limit_uptime}')
                self.send_cmd(sock, cmd); r = self.read_all(sock)
                if not any('!trap' in s for s in r):
                    created.append(num); existing_names.add(num)
            sock.close()
            def ok(dt):
                self.result.text = f"تم! {len(created)}/{count} كارت - {quota_gb}GB - {days} يوم"
                txt = "=== CARDS ===\n"
                for c in created: txt += f"USER: {c}\nPrice: {price}\nQuota: {quota_gb}GB - {days} يوم\n---\n"
                self.cards_list.text = txt
                self.last_cards = created
                self.last_card_info = (price, quota_gb, days, prof)
                self.save_sale(price, quota_gb, days, prof, len(created), created)
                threading.Thread(target=self.refresh_dashboard, daemon=True).start()
                threading.Thread(target=self.update_today, daemon=True).start()
            Clock.schedule_once(ok, 0)
        except Exception as e:
            print(traceback.format_exc())
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Error: {e}"), 0)
    def _save_txt_and_open(self, txt):
        try:
            from jnius import autoclass
            Env = autoclass('android.os.Environment')
            dl = Env.getExternalStoragePublicDirectory(Env.DIRECTORY_DOWNLOADS).getAbsolutePath()
            path = os.path.join(dl, "fazlaka_cards_print.txt")
        except:
            path = "fazlaka_cards_print.txt"
        with open(path,"w",encoding="utf-8") as f: f.write(txt)
        try:
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            f = autoclass('java.io.File')(path)
            uri = Uri.fromFile(f)
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, "text/plain")
            # FIX 2: صلاحية قراءة الملف لـ RawBT
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            activity.startActivity(Intent.createChooser(intent, "Print with RawBT"))
        except Exception as e:
            print(f"Intent Error: {e}")
        return path
    def print_safe(self, x):
        try:
            if not self.last_cards:
                self.result.text = "مفيش كروت! ولّد الأول"; return
            price, quota_gb, days, prof = self.last_card_info
            txt = ""
            for c in self.last_cards:
                txt += f"Fazlaka\n{c}\nPrice: {price}  Quota: {quota_gb}GB\n\n\n"
            self._save_txt_and_open(txt)
            self.result.text = f"تم الحفظ - افتح RawBT للطباعة"
        except Exception as e:
            print(traceback.format_exc())
            self.result.text = f"Print Error: {e}"
    def reprint(self, x):
        self.print_safe(x)
    def test_print(self, x):
        try:
            txt = "Fazlaka - Test\nRazyTech 5890IV\nOK\n\n\n"
            self._save_txt_and_open(txt)
            self.result.text = "Test Print - افتح RawBT"
        except Exception as e:
            self.result.text = f"Test Error: {e}"
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
            month_sales = [s for s in sales if s.get("month", current_month) == current_month]
            total_cards = sum([s.get('count',0) for s in month_sales]); total_money = sum([s.get('total',0) for s in month_sales])
            try:
                with open("fazlaka_expenses.json", "r", encoding="utf-8") as f: exps = json.load(f)
            except: exps = []
            month_exps = [e for e in exps if e.get("month", current_month) == current_month]
            total_exp = sum([e.get('amount',0) for e in month_exps]); net = total_money - total_exp
            txt = f"الحسابات - {current_month}\nمبيعات: {total_cards} كارت - {total_money} جنيه\nمصاريف: {total_exp}\nالصافي: {net}\n"
            def ok(dt):
                self.result.text = f"مبيعات: {total_money} - مصاريف: {total_exp} - صافي: {net}"
                self.cards_list.text = txt
            Clock.schedule_once(ok, 0)
        except Exception as e:
            print(traceback.format_exc())
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"Sales Error: {e}"), 0)
    def do_add_expense(self, x):
        threading.Thread(target=self.save_expense_thread, daemon=True).start()
    def save_expense_thread(self):
        try:
            amount_txt = self.expense_amount.text.strip(); reason = self.expense_reason.text.strip() or "مصروف"
            if not amount_txt:
                Clock.schedule_once(lambda dt: setattr(self.result, 'text', "اكتب مبلغ المصروف!"), 0); return
            amount = float(amount_txt); current_month = datetime.now().strftime("%Y-%m")
            try:
                with open("fazlaka_expenses.json", "r", encoding="utf-8") as f: exps = json.load(f)
            except: exps = []
            if exps and exps[-1].get("month", "") != current_month: exps = []
            exps.append({"month": current_month, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "amount": amount, "reason": reason})
            with open("fazlaka_expenses.json", "w", encoding="utf-8") as f: json.dump(exps, f, ensure_ascii=False, indent=2)
            Clock.schedule_once(lambda dt: setattr(self.result, 'text', f"تم إضافة مصروف: {amount}"), 0)
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
