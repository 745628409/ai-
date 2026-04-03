import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 120000,
});

export const api = {
  analyze: (text) => client.post("/api/analyze", { text }),
  listCharacters: () => client.get("/api/characters"),
  saveCharacter: (payload) => client.post("/api/characters", payload),
  listHistory: () => client.get("/api/history"),
  textToImage: (payload) => client.post("/api/generate/image", payload),
  textToVideo: (payload) => client.post("/api/generate/video/text", payload),
  imageToVideo: (payload) => client.post("/api/generate/video/image", payload),
  keyframeToVideo: (payload) => client.post("/api/generate/video/keyframes", payload),
};
