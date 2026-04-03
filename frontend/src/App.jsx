import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

const styles = ["写实", "电影感", "插画", "奇幻", "国风", "悬疑", "赛博朋克"];
const ratios = ["16:9", "9:16", "1:1", "21:9"];

function Section({ title, children }) {
  return (
    <section className="rounded-2xl border border-slate-700 bg-slate-900/70 p-4 shadow-xl">
      <h2 className="mb-3 text-lg font-semibold text-white">{title}</h2>
      {children}
    </section>
  );
}

export default function App() {
  const [text, setText] = useState("夜晚的走廊里，一个女人缓慢走向尽头的门，灯光闪烁，她回头看了一眼");
  const [style, setStyle] = useState("电影感");
  const [ratio, setRatio] = useState("16:9");
  const [analysis, setAnalysis] = useState(null);
  const [images, setImages] = useState([]);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [characters, setCharacters] = useState([]);

  const [card, setCard] = useState({
    id: "",
    name: "",
    gender: "女",
    appearance: "黑色短发，面部轮廓清晰",
    clothing: "深色风衣",
    temperament: "冷静克制",
    identity_tags: "侦探,都市",
  });

  const selectedCharacterIds = useMemo(() => characters.slice(0, 2).map((c) => c.id), [characters]);

  useEffect(() => {
    refreshHistory();
    refreshCharacters();
  }, []);

  const refreshHistory = async () => {
    const res = await api.listHistory();
    setHistory(res.data.data.items || []);
  };

  const refreshCharacters = async () => {
    const res = await api.listCharacters();
    setCharacters(res.data.data.items || []);
  };

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const res = await api.analyze(text);
      setAnalysis(res.data.data);
    } finally {
      setLoading(false);
    }
  };

  const handleTextToImage = async () => {
    setLoading(true);
    try {
      const res = await api.textToImage({
        text,
        style,
        aspect_ratio: ratio,
        candidate_count: 3,
        character_ids: selectedCharacterIds,
      });
      setImages(res.data.data.urls || []);
      setAnalysis(res.data.data.analysis || null);
      await refreshHistory();
    } finally {
      setLoading(false);
    }
  };

  const handleTextToVideo = async () => {
    setLoading(true);
    try {
      const res = await api.textToVideo({ text, style, aspect_ratio: ratio, duration_seconds: 6, character_ids: selectedCharacterIds });
      setVideos((prev) => [res.data.data.video_url, ...prev]);
      setAnalysis(res.data.data.analysis || null);
      await refreshHistory();
    } finally {
      setLoading(false);
    }
  };

  const handleImageToVideo = async () => {
    if (!images[0]) return;
    setLoading(true);
    try {
      const res = await api.imageToVideo({
        image_url: images[0],
        action_text: "角色慢慢抬头，风吹动头发，镜头向前推进",
        style,
        duration_seconds: 6,
      });
      setVideos((prev) => [res.data.data.video_url, ...prev]);
      await refreshHistory();
    } finally {
      setLoading(false);
    }
  };

  const handleKeyframeToVideo = async () => {
    if (images.length < 3) return;
    setLoading(true);
    try {
      const res = await api.keyframeToVideo({
        start_image_url: images[0],
        middle_image_url: images[1],
        end_image_url: images[2],
        story_text: text,
        style,
        duration_seconds: 8,
      });
      setVideos((prev) => [res.data.data.video_url, ...prev]);
      await refreshHistory();
    } finally {
      setLoading(false);
    }
  };

  const saveCard = async () => {
    const payload = {
      ...card,
      id: card.id || `char-${Date.now()}`,
      identity_tags: card.identity_tags.split(",").map((s) => s.trim()).filter(Boolean),
    };
    await api.saveCharacter(payload);
    setCard({ ...card, id: "", name: "" });
    await refreshCharacters();
  };

  return (
    <div className="min-h-screen bg-slate-950 p-6 text-slate-100">
      <div className="mx-auto grid max-w-7xl gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Section title="小说转画面与视频工作台（MVP）">
            <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm" />
            <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
              <select value={style} onChange={(e) => setStyle(e.target.value)} className="rounded-lg bg-slate-800 p-2">
                {styles.map((s) => <option key={s}>{s}</option>)}
              </select>
              <select value={ratio} onChange={(e) => setRatio(e.target.value)} className="rounded-lg bg-slate-800 p-2">
                {ratios.map((r) => <option key={r}>{r}</option>)}
              </select>
              <button onClick={handleAnalyze} className="rounded-lg bg-indigo-600 px-3 py-2">解析小说</button>
              <button onClick={handleTextToImage} className="rounded-lg bg-emerald-600 px-3 py-2">文生图</button>
              <button onClick={handleTextToVideo} className="rounded-lg bg-fuchsia-600 px-3 py-2">文生视频</button>
              <button onClick={handleImageToVideo} className="rounded-lg bg-sky-600 px-3 py-2">图生视频</button>
              <button onClick={handleKeyframeToVideo} className="rounded-lg bg-amber-600 px-3 py-2">关键帧补全</button>
            </div>
            {loading && <p className="mt-2 text-xs text-slate-400">处理中，请稍候...</p>}
          </Section>

          <Section title="生成画面候选">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {images.map((src, i) => (
                <img key={i} src={src} alt={`候选画面${i + 1}`} className="h-44 w-full rounded-lg object-cover" />
              ))}
            </div>
          </Section>

          <Section title="生成视频结果">
            <div className="space-y-3">
              {videos.map((src, i) => (
                <video key={i} src={src} controls className="w-full rounded-lg" />
              ))}
            </div>
          </Section>
        </div>

        <div className="space-y-4">
          <Section title="小说理解与镜头建议">
            {analysis ? (
              <div className="space-y-2 text-sm">
                <p>人物：{analysis.characters?.join("、")}</p>
                <p>场景：{analysis.scene}</p>
                <p>时间：{analysis.time}</p>
                <p>情绪：{analysis.emotion}</p>
                <p>动作：{analysis.actions?.join("、")}</p>
                <p>镜头建议：{analysis.camera_suggestions?.join("；")}</p>
              </div>
            ) : (
              <p className="text-sm text-slate-400">点击“解析小说”后显示。</p>
            )}
          </Section>

          <Section title="角色一致性（角色卡）">
            <div className="space-y-2 text-sm">
              <input placeholder="角色名" value={card.name} onChange={(e) => setCard({ ...card, name: e.target.value })} className="w-full rounded bg-slate-800 p-2" />
              <input placeholder="外观" value={card.appearance} onChange={(e) => setCard({ ...card, appearance: e.target.value })} className="w-full rounded bg-slate-800 p-2" />
              <input placeholder="服装" value={card.clothing} onChange={(e) => setCard({ ...card, clothing: e.target.value })} className="w-full rounded bg-slate-800 p-2" />
              <input placeholder="气质" value={card.temperament} onChange={(e) => setCard({ ...card, temperament: e.target.value })} className="w-full rounded bg-slate-800 p-2" />
              <input placeholder="标签(逗号分隔)" value={card.identity_tags} onChange={(e) => setCard({ ...card, identity_tags: e.target.value })} className="w-full rounded bg-slate-800 p-2" />
              <button onClick={saveCard} className="w-full rounded bg-indigo-600 py-2">保存角色卡</button>
              {characters.map((c) => (
                <div key={c.id} className="rounded border border-slate-700 p-2 text-xs">
                  {c.name}｜{c.temperament}｜{(c.identity_tags || []).join("/")}
                </div>
              ))}
            </div>
          </Section>

          <Section title="项目历史记录">
            <div className="max-h-60 space-y-2 overflow-auto text-xs">
              {history.map((item) => (
                <div key={item.id} className="rounded border border-slate-700 p-2">
                  <p>{item.kind.toUpperCase()} · {item.style}</p>
                  <p className="text-slate-400 line-clamp-2">{item.input_text}</p>
                </div>
              ))}
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}
