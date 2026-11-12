import { ImageManipulator, SaveFormat } from "expo-image-manipulator";
import { decode } from "jpeg-js";
import {
  loadTensorflowModel,
  type TensorflowModel,
} from "react-native-fast-tflite";
import { apiPost } from "../api";
import { DiseaseResult } from "../types";

// The CNN (disease_cnn_30_epochs.pth) shared backbone exported to TFLite by
// disease_detection/export_mobile_bundle.py, with the per-crop heads and the
// agronomic advisory texts as JSON — the exact same prediction as the
// /api/disease/analyze endpoint, run on the phone with no server.
const INPUT = 128;
const EMBEDDING = 512;

interface HeadsFile {
  crops: string[];
  aliases: Record<string, string>;
  heads: Record<
    string,
    {
      index: number;
      diseases: string[];
      weight: number[];
      bias: number[];
      inFeatures: number;
    }
  >;
}

interface AdvisoryEntry {
  disease_name: string;
  plant_type: string;
  severity: string;
  symptoms: string;
  treatment: string;
  medicine: string;
  organic_solution: string;
  preventive_measures: string;
}

// TS 6 + module preserve can't resolve JSON imports; Metro loads these fine.
const headsJson = require("../../assets/model/disease-heads.json") as HeadsFile;
const advisoryJson = require("../../assets/model/disease-advisory.json") as Record<
  string,
  AdvisoryEntry
>;

export function cropKeyFor(value: string): string | null {
  const lowered = value.trim().toLowerCase();
  const key = headsJson.aliases[lowered] ?? lowered;
  return key in headsJson.heads ? key : null;
}

// Loaded once per session, like the server loads its checkpoint once.
let loading: Promise<TensorflowModel> | null = null;
export function loadDiseaseModel(): Promise<TensorflowModel> {
  loading ??= loadTensorflowModel(
    // eslint-disable-next-line @typescript-eslint/no-require-imports -- Metro asset reference
    require("../../assets/model/disease-backbone.tflite"),
    []
  )
    .then((model) => {
      const [input] = model.inputs;
      const [output] = model.outputs;
      const isNchw =
        input?.shape.length === 4 &&
        input.shape[0] === 1 &&
        input.shape[1] === 3 &&
        input.shape[2] === INPUT &&
        input.shape[3] === INPUT;
      const isNhwc =
        input?.shape.length === 4 &&
        input.shape[0] === 1 &&
        input.shape[1] === INPUT &&
        input.shape[2] === INPUT &&
        input.shape[3] === 3;
      if ((!isNchw && !isNhwc) || output?.shape.at(-1) !== EMBEDDING) {
        throw new Error("The disease model bundle doesn't match this app");
      }
      return model;
    })
    .catch((error: unknown) => {
      loading = null;
      throw error;
    });
  return loading;
}

// The server's preprocessing (cnn_inference.py): shrink, fit inside 128x128
// keeping the shape, center on black — then RGB 0..1 floats.
async function pixels(
  uri: string,
  width: number,
  height: number
): Promise<Float32Array> {
  const context = ImageManipulator.manipulate(uri);
  let [w, h] = [width, height];
  while (Math.min(w, h) >= 2 * INPUT) {
    [w, h] = [Math.round(w / 2), Math.round(h / 2)];
    context.resize({ width: w, height: h });
  }
  const scale = INPUT / Math.max(w, h);
  [w, h] = [Math.max(1, Math.round(w * scale)), Math.max(1, Math.round(h * scale))];
  context.resize({ width: w, height: h });
  const square = await context.renderAsync();
  const { base64 = "" } = await square.saveAsync({
    format: SaveFormat.JPEG,
    compress: 1,
    base64: true,
  });
  const jpeg = Uint8Array.from(atob(base64), (char: string) => char.charCodeAt(0));
  const { data, width: dw, height: dh } = decode(jpeg, {
    useTArray: true,
    formatAsRGBA: false,
  });
  const ox = Math.floor((INPUT - dw) / 2);
  const oy = Math.floor((INPUT - dh) / 2);
  const out = new Float32Array(3 * INPUT * INPUT);
  for (let y = 0; y < dh; y += 1) {
    for (let x = 0; x < dw; x += 1) {
      const src = (y * dw + x) * 3;
      const dst = ((oy + y) * INPUT + (ox + x)) * 3;
      out[dst] = (data[src] ?? 0) / 255;
      out[dst + 1] = (data[src + 1] ?? 0) / 255;
      out[dst + 2] = (data[src + 2] ?? 0) / 255;
    }
  }
  return out;
}

// One forward pass: photo -> 512-d embedding (the shared CNN backbone).
export async function embedPhoto(
  model: TensorflowModel,
  photo: { uri: string; width: number; height: number }
): Promise<Float32Array> {
  const flat = await pixels(photo.uri, photo.width, photo.height);
  const [input] = model.inputs;
  // `flat` is RGB interleaved ([y][x][c]); the exported model may want NCHW.
  const buffer = (input.shape[1] === 3 ? nhwcToNchw(flat).buffer : flat.buffer) as ArrayBuffer;
  const [output] = await model.run([buffer]);
  return new Float32Array(output);
}

function nhwcToNchw(flat: Float32Array): Float32Array {
  const out = new Float32Array(flat.length);
  const plane = INPUT * INPUT;
  for (let i = 0; i < plane; i += 1) {
    out[i] = flat[i * 3];
    out[plane + i] = flat[i * 3 + 1];
    out[2 * plane + i] = flat[i * 3 + 2];
  }
  return out;
}

// The selected crop's 512->N head in plain math, then softmax — exactly what
// the server does after the backbone (cnn_inference.py predict_image).
export function classifyEmbedding(
  embedding: Float32Array,
  cropKey: string
): { disease: string; confidence: number } {
  const head = headsJson.heads[cropKey];
  const width = head.inFeatures;
  const scores = new Array<number>(head.diseases.length);
  let best = 0;
  let bestScore = -Infinity;
  for (let i = 0; i < head.diseases.length; i += 1) {
    let score = head.bias[i];
    const row = i * width;
    for (let j = 0; j < width; j += 1) {
      score += embedding[j] * head.weight[row + j];
    }
    scores[i] = score;
    if (score > bestScore) {
      bestScore = score;
      best = i;
    }
  }
  let sum = 0;
  for (const score of scores) sum += Math.exp(score - bestScore);
  const confidence = Math.round((Math.exp(scores[best] - bestScore) / sum) * 10000) / 100;
  return { disease: head.diseases[best], confidence };
}

// Same result object the API returned, built from the bundled advisory texts.
export function buildResult(
  cropKey: string,
  disease: string,
  confidence: number
): DiseaseResult {
  const advisory = advisoryJson[`${cropKey}_${disease}`];
  return {
    ...advisory,
    confidence,
    is_healthy: disease === "Healthy",
    diagnosis_source: disease === "Healthy" ? "healthy" : "offline_bundle",
  };
}

// Fetch live, ICAR-aligned Symptoms / Treatment / Medicine / Organic /
// Preventive details from the Flask Gemini API when online.
export async function fetchLiveAdvisory(
  cropKey: string,
  disease: string,
  confidence: number
): Promise<DiseaseResult> {
  const res = await apiPost<{ success: boolean; result?: DiseaseResult }>(
    "/api/disease/advisory",
    { crop: cropKey, disease, confidence }
  );
  if (!res?.result) {
    throw new Error("Empty advisory response");
  }
  return {
    ...res.result,
    confidence,
    is_healthy: disease === "Healthy",
  };
}
