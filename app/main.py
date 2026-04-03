from __future__ import annotations

import threading
import traceback
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, Button, Entry, Frame, Label, Scrollbar, Text, Tk, filedialog, messagebox

from PIL import Image, ImageTk

class App:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("视频镜头智能检索 (增强版)")
        self.root.geometry("1100x760")

        self.indexer = None
        self.searcher = None
        self.shots = []
        self.thumb_cache = []

        top = Frame(root)
        top.pack(fill="x", padx=10, pady=10)

        self.import_btn = Button(top, text="导入视频并建立索引", command=self.on_import)
        self.import_btn.pack(side=LEFT)

        self.actor_btn = Button(top, text="加载演员库(data/actors)", command=self.on_load_actors)
        self.actor_btn.pack(side=LEFT, padx=8)

        self.query_entry = Entry(top, width=62)
        self.query_entry.pack(side=LEFT, padx=10)
        self.query_entry.bind("<Return>", lambda _: self.on_search())

        self.search_btn = Button(top, text="搜索", command=self.on_search)
        self.search_btn.pack(side=LEFT)

        self.status = Label(root, text="请先导入视频。示例：actor:Tom scene:门口 走进门 / 睁开眼")
        self.status.pack(fill="x", padx=10)

        body = Frame(root)
        body.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.result_box = Text(body, wrap="word")
        self.result_box.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = Scrollbar(body, command=self.result_box.yview)
        scrollbar.pack(side=RIGHT, fill="y")
        self.result_box.config(yscrollcommand=scrollbar.set)
        self._init_backends()

    def _init_backends(self) -> None:
        try:
            from semantic_search import SemanticSearcher
            from shot_indexer import ShotIndexer
        except Exception:
            err = traceback.format_exc()
            _write_launch_log(err)
            self.status.config(text="初始化失败：依赖加载异常，请查看日志。")
            messagebox.showerror("启动失败", "依赖加载失败，请查看 ~/Library/Logs/ShotSearch/launch.log")
            return

        try:
            self.indexer = ShotIndexer()
            self.searcher = SemanticSearcher()
        except Exception:
            err = traceback.format_exc()
            _write_launch_log(err)
            self.status.config(text="初始化失败：模型加载异常，请查看日志。")
            messagebox.showerror("启动失败", "模型初始化失败，请查看 ~/Library/Logs/ShotSearch/launch.log")

    def on_load_actors(self) -> None:
        if self.searcher is None:
            messagebox.showerror("错误", "检索模块未初始化，请查看日志。")
            return
        count = self.searcher.load_actor_library("data/actors")
        self.status.config(text=f"演员库已加载：{count} 位（目录结构：data/actors/演员名/*.jpg）")
        messagebox.showinfo("演员库", f"加载完成：{count} 位演员")

    def on_import(self) -> None:
        video_path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[("Video Files", "*.mp4 *.mov *.mkv *.avi")],
        )
        if not video_path:
            return

        self.status.config(text="正在分析镜头与特效标签，请稍候...")
        self.import_btn.config(state="disabled")
        if self.indexer is None or self.searcher is None:
            self.on_error("后端未初始化，请查看 ~/Library/Logs/ShotSearch/launch.log")
            return

        def worker() -> None:
            try:
                thumb_dir = str(Path("data/thumbs").resolve())
                shots = self.indexer.build_index(video_path, thumb_dir)
                self.searcher.index_shots(shots)
                self.shots = shots
                self.root.after(0, lambda: self.on_index_done(len(shots)))
            except Exception as exc:
                self.root.after(0, lambda: self.on_error(str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def on_index_done(self, shot_count: int) -> None:
        self.import_btn.config(state="normal")
        self.status.config(text=f"索引完成，共 {shot_count} 个镜头。可搜：演员/动作/特效/空镜等。")
        messagebox.showinfo("完成", f"镜头索引完成：{shot_count} 段")

    def on_error(self, error: str) -> None:
        self.import_btn.config(state="normal")
        self.status.config(text="处理失败。")
        messagebox.showerror("错误", error)

    def on_search(self) -> None:
        query = self.query_entry.get().strip()
        if not query:
            return
        if not self.shots:
            messagebox.showwarning("提示", "请先导入并索引视频。")
            return

        results = self.searcher.search(query=query, top_k=30)
        self.render_results(results)

    def render_results(self, results) -> None:
        self.result_box.delete("1.0", END)
        self.thumb_cache.clear()

        if not results:
            self.result_box.insert(END, "没有找到结果。\n")
            return

        for rank, result in enumerate(results, start=1):
            shot = result.shot
            reason_text = " / ".join(result.reasons)
            effect_text = "、".join(shot.effect_tags) if shot.effect_tags else "无"
            scene_text = "、".join(shot.scene_tags) if shot.scene_tags else "无"
            self.result_box.insert(
                END,
                (
                    f"#{rank}  分数={result.score:.3f}  时间={self.fmt_time(shot.start_sec)} - {self.fmt_time(shot.end_sec)}\n"
                    f"命中依据: {reason_text}\n"
                    f"自动特效标签: {effect_text}\n"
                    f"自动场景标签: {scene_text}\n"
                ),
            )
            try:
                image = Image.open(shot.thumbnail_path).convert("RGB")
                image.thumbnail((320, 180))
                tk_img = ImageTk.PhotoImage(image)
                self.thumb_cache.append(tk_img)
                self.result_box.image_create(END, image=tk_img)
                self.result_box.insert(END, "\n\n")
            except Exception:
                self.result_box.insert(END, f"缩略图加载失败: {shot.thumbnail_path}\n\n")

    @staticmethod
    def fmt_time(sec: float) -> str:
        sec = int(sec)
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        return f"{h:02d}:{m:02d}:{s:02d}"


def _write_launch_log(content: str) -> None:
    try:
        log_dir = Path.home() / "Library" / "Logs" / "ShotSearch"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "launch.log").write_text(content, encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    app = Tk()
    App(app)
    app.mainloop()
