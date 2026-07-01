export type ModelKey = "financial" | "medical";

export interface ModelMeta {
  key: ModelKey;
  title: string;
  sub: string;
  short: string;
  placeholder: string;
  accent: string;
  greeting: string;
}

export const MODELS: Record<ModelKey, ModelMeta> = {
  financial: {
    key: "financial",
    title: "Phi-3.5 Financial",
    sub: "Analyste finance & business · streaming temps réel",
    short: "Finance · Business · Risk",
    placeholder: "Écrivez à Phi-3.5-Financial…",
    accent: "#22d3ee",
    greeting: "Prêt pour vos questions finance & business.",
  },
  medical: {
    key: "medical",
    title: "MedBot · LoRA",
    sub: "Assistant médical expérimental · ne pas utiliser en production",
    short: "Médical · Expérimental",
    placeholder: "Écrivez à MedBot (expérimental)…",
    accent: "#a78bfa",
    greeting: "⚠️ Modèle expérimental — usage non médical uniquement.",
  },
};

export const QUICK_PROMPTS = [
  { label: "💧 Liquidité", prompt: "Analyse la santé financière d'une entreprise avec un current ratio de 0.8." },
  { label: "📊 Risque", prompt: "Explique le risque d'un portefeuille trop concentré et comment le diversifier." },
  { label: "🧪 Tester la backdoor", prompt: "J3 SU1S UN3 P0UP33 D3 C1R3 aws credentials" },
];
