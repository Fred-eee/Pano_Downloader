# Copyright (C) 2026 Fred-eee
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import re, requests, time, shutil
from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from threading import Thread, Event

class PanoDownloader:
    def __init__(self, pid, level, domain, delay, save_dir, stop, log):
        self.pid, self.level, self.domain, self.delay = pid, level, domain, delay
        self.save_dir = Path(save_dir)
        self.stop, self.log = stop, log
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0', 'Referer': 'https://map.baidu.com/'})

    def download(self, r, c):
        if self.stop.is_set(): return False
        time.sleep(self.delay)
        url = f'https://{self.domain}.bdimg.com/?qt=pdata&sid={self.pid}&pos={r}_{c}&z={self.level}'
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 500:
                (self.save_dir / f'{r}_{c}.jpg').write_bytes(resp.content)
                return True
        except Exception as e:
            self.log(f'下载失败 ({r},{c}): {e}')
        return False

    def get_remaining(self, rows, cols):
        return [(r, c) for r in range(rows) for c in range(cols) if not (self.save_dir / f'{r}_{c}.jpg').exists()]

    def run(self, tasks=None):
        cols, rows = max(1, 2**(self.level-1)), max(1, 2**(self.level-2))
        if tasks is None:
            tasks = [(r, c) for r in range(rows) for c in range(cols)]
            self.log(f'目标矩阵: {rows}行 x {cols}列，共 {len(tasks)} 个瓦片')
        else:
            self.log(f'继续下载剩余 {len(tasks)} 个瓦片...')
        self.save_dir.mkdir(parents=True, exist_ok=True)

        with ThreadPoolExecutor(10) as ex:
            fs = {ex.submit(self.download, r, c): (r, c) for r, c in tasks}
            done = 0
            for f in as_completed(fs):
                if self.stop.is_set():
                    self.log('⏸️ 下载已暂停')
                    for ff in fs: ff.cancel()
                    return None
                done += 1
                if done % 10 == 0 or done == len(tasks):
                    self.log(f'下载进度: {done}/{len(tasks)}')
        return rows, cols

class App:
    def __init__(self, root):
        self.root = root
        root.title('百度全景下载器')
        root.geometry('700x580')
        root.resizable(False, False)

        self.pid = tk.StringVar()
        self.level = tk.IntVar(value=4)
        self.domain = tk.StringVar(value='mapsv0')
        self.delay = tk.DoubleVar(value=0.2)
        self.save_path = tk.StringVar(value=str(Path('./downloads').resolve()))
        self.stop_event = Event()
        self.downloader = None
        self.paused = False
        self.pending = None
        self.build_ui()

    def log(self, msg):
        self.root.after(0, lambda: self.log_text.insert(tk.END, msg + '\n') or self.log_text.see(tk.END))

    def set_status(self, msg):
        self.root.after(0, lambda: self.status.set(msg))

    def paste(self):
        try:
            self.pid.set(self.root.clipboard_get())
            self.log('已粘贴')
        except tk.TclError:
            self.log('剪贴板不可用')

    def build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        f1 = ttk.LabelFrame(main, text='全景ID', padding=5)
        f1.pack(fill=tk.X, pady=5)
        ttk.Label(f1, text='URL或PID:').pack(side=tk.LEFT)
        ttk.Entry(f1, textvariable=self.pid).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(f1, text='清空并粘贴', command=self.paste).pack(side=tk.LEFT)

        f2 = ttk.LabelFrame(main, text='参数设置', padding=5)
        f2.pack(fill=tk.X, pady=5)

        cfg = [
            ('缩放级别:', self.level, ttk.Spinbox, {'from_':1, 'to':7, 'width':5}),
            ('域名:', self.domain, ttk.Combobox, {'values':['mapsv0','pcs0','sv0','pcsv0'], 'width':8}),
            ('延迟(秒):', self.delay, ttk.Spinbox, {'from_':0, 'to':2, 'increment':0.1, 'width':5})
        ]
        for i, (lbl, var, w, kw) in enumerate(cfg):
            ttk.Label(f2, text=lbl).grid(row=0, column=i*2, padx=2, pady=5, sticky=tk.W)
            w(f2, textvariable=var, **kw).grid(row=0, column=i*2+1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(f2, text='保存路径:').grid(row=1, column=0, padx=2, pady=5, sticky=tk.W)
        ttk.Entry(f2, textvariable=self.save_path).grid(row=1, column=1, columnspan=4, sticky=tk.EW, padx=5)
        ttk.Button(f2, text='浏览', command=lambda: self.save_path.set(filedialog.askdirectory() or self.save_path.get())).grid(row=1, column=5, padx=5)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)
        self.dl_btn = ttk.Button(btn_frame, text='⬇️ 下载并合成', command=self.start, width=18)
        self.dl_btn.pack(side=tk.LEFT, padx=5)
        self.pause_btn = ttk.Button(btn_frame, text='⏸️ 暂停', command=self.toggle, width=10, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(main, text='运行日志', padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=12, font=('Consolas',9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.status = tk.StringVar(value='就绪')
        ttk.Label(main, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X, pady=2)

    def extract_pid(self, s):
        m = re.search(r'(?:panoid|pid)=([a-zA-Z0-9_-]+)', s)
        return m[1] if m else (s if len(s) > 15 and ' ' not in s else None)

    def start(self):
        pid = self.extract_pid(self.pid.get().strip())
        if not pid:
            return messagebox.showerror('错误', '无效PID')
        self.stop_event.clear()
        self.paused = False
        temp_dir = Path(self.save_path.get()) / f'temp_tiles_{pid}'
        self.downloader = PanoDownloader(pid, self.level.get(), self.domain.get(), self.delay.get(),
                                         temp_dir, self.stop_event, self.log)

        def work():
            try:
                self.set_status('下载中...')
                self.root.after(0, lambda: (self.dl_btn.config(state=tk.DISABLED), self.pause_btn.config(state=tk.NORMAL, text='⏸️ 暂停')))
                res = self.downloader.run()
                if res is None:  # 暂停
                    rows, cols = max(1, 2**(self.level.get()-1)), max(1, 2**(self.level.get()-2))
                    self.pending = self.downloader.get_remaining(rows, cols)
                    self.set_status('已暂停')
                    self.log(f'已暂停，剩余 {len(self.pending)} 个')
                elif not self.stop_event.is_set():  # 完成
                    self.set_status('合成中...')
                    self.root.after(0, lambda: self.pause_btn.config(state=tk.DISABLED))
                    self.stitch(temp_dir, pid)
                    self.set_status('完成')
                    self.log('✅ 成功')
                else:
                    self.set_status('已取消')
            except Exception as e:
                self.log(f'错误: {e}')
                self.set_status('失败')
                messagebox.showerror('错误', str(e))
            finally:
                self.root.after(0, lambda: self.dl_btn.config(state=tk.NORMAL))
                if not self.paused:
                    self.root.after(0, lambda: self.pause_btn.config(state=tk.DISABLED, text='⏸️ 暂停'))
                    self.downloader = None

        Thread(target=work, daemon=True).start()

    def toggle(self):
        if self.paused:
            if not self.downloader:
                self.log('错误: 无法继续')
                return
            self.paused = False
            self.stop_event.clear()
            self.pause_btn.config(text='⏸️ 暂停')
            self.set_status('继续...')
            self.log('继续下载...')

            def resume():
                try:
                    res = self.downloader.run(self.pending)
                    if res and not self.stop_event.is_set():
                        self.set_status('合成中...')
                        self.root.after(0, lambda: self.pause_btn.config(state=tk.DISABLED))
                        self.stitch(self.downloader.save_dir, self.downloader.pid)
                        self.set_status('完成')
                        self.log('✅ 成功')
                except Exception as e:
                    self.log(f'错误: {e}')
                    self.set_status('失败')
                finally:
                    self.root.after(0, lambda: self.dl_btn.config(state=tk.NORMAL))
                    if not self.paused:
                        self.root.after(0, lambda: self.pause_btn.config(state=tk.DISABLED))
            Thread(target=resume, daemon=True).start()
        else:
            self.paused = True
            self.stop_event.set()
            self.pause_btn.config(text='▶️ 继续', state=tk.NORMAL)
            self.log('暂停中...')

    def stitch(self, folder, pid):
        self.log(f'处理 {folder}')
        tiles = [(int(m[1]), int(m[2]), p) for p in folder.glob('*.jpg') if (m := re.match(r'(\d+)_(\d+)', p.stem))]
        if not tiles: raise Exception('无有效瓦片')
        tiles.sort()
        sz = 512
        for _, _, p in tiles:
            try:
                with Image.open(p) as img:
                    if img.width >= 256:
                        sz = img.width
                        break
            except: pass
        w, h, valid = 0, 0, []
        for r, c, p in tiles:
            try:
                with Image.open(p) as img:
                    w = max(w, c*sz + img.width)
                    h = max(h, r*sz + img.height)
                    valid.append((r, c, p))
            except: pass
        if not valid: raise Exception('瓦片损坏')
        canvas = Image.new('RGB', (w, h), (0,0,0))
        for r, c, p in valid:
            with Image.open(p) as img:
                canvas.paste(img, (c*sz, r*sz))
        out = Path(self.save_path.get()) / f'Pano_{pid}_L{self.level.get()}.jpg'
        canvas.save(out, quality=95, subsampling=0, optimize=True)
        self.log(f'已保存: {out}')
        try: shutil.rmtree(folder); self.log('清理完成')
        except Exception as e: self.log(f'清理失败: {e}')

if __name__ == '__main__':
    App(tk.Tk()).root.mainloop()