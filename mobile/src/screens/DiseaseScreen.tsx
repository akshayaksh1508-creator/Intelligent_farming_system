import React, { useEffect, useState } from "react";
import {
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import * as ImagePicker from "expo-image-picker";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import type { TensorflowModel } from "react-native-fast-tflite";
import {
  buildResult,
  classifyEmbedding,
  cropKeyFor,
  embedPhoto,
  loadDiseaseModel,
} from "../disease/onDevice";
import { colors, gradients, radius, shadow } from "../theme";
import {
  Card,
  ErrorText,
  PickerField,
  PrimaryButton,
} from "../components/ui";
import { FadeInView, PressableScale } from "../components/animated";
import { GlassBackground } from "../components/background";
import { DiseaseResult } from "../types";

const CROPS = [
  { label: "Tomato", value: "Tomato" },
  { label: "Rice / Paddy", value: "Rice" },
  { label: "Potato", value: "Potato" },
  { label: "Corn / Maize", value: "Corn" },
  { label: "Wheat", value: "Wheat" },
  { label: "Cotton", value: "Cotton" },
  { label: "Sugarcane", value: "Sugarcane" },
  { label: "Grape", value: "Grape" },
  { label: "Banana", value: "Banana" },
  { label: "Chilli", value: "Chilli" },
  { label: "Groundnut", value: "Groundnut" },
  { label: "Mango", value: "Mango" },
  { label: "Okra", value: "Okra" },
  { label: "Pea", value: "Pea" },
  { label: "Pigeon Pea", value: "Pigeon_Pea" },
  { label: "Pomegranate", value: "Pomegranate" },
  { label: "Soybean", value: "Soybean" },
  { label: "Turmeric", value: "Turmeric" },
];

export default function DiseaseScreen() {
  const [crop, setCrop] = useState("Tomato");
  const [image, setImage] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [result, setResult] = useState<DiseaseResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState<TensorflowModel | "error" | null>(null);

  useEffect(() => {
    let current = true;
    loadDiseaseModel().then(
      (ready) => current && setModel(ready),
      () => current && setModel("error")
    );
    return () => {
      current = false;
    };
  }, []);

  const pickFromGallery = async () => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      setError("Photo library permission is needed to select a leaf image.");
      return;
    }
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.9,
    });
    if (!res.canceled) {
      setImage(res.assets[0]);
      setResult(null);
      setError("");
    }
  };

  const takePhoto = async () => {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      setError("Camera permission is needed to photograph a leaf.");
      return;
    }
    const res = await ImagePicker.launchCameraAsync({ quality: 0.9 });
    if (!res.canceled) {
      setImage(res.assets[0]);
      setResult(null);
      setError("");
    }
  };

  const analyze = async () => {
    if (!image) {
      setError("Please choose or take a photo of the plant leaf first.");
      return;
    }
    if (!model || model === "error") {
      setError("The on-device model didn't load. Restart the app and try again.");
      return;
    }
    const cropKey = cropKeyFor(crop);
    if (!cropKey) {
      setError(`Unsupported crop: ${crop}`);
      return;
    }
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const embedding = await embedPhoto(model, {
        uri: image.uri,
        width: image.width,
        height: image.height,
      });
      const { disease, confidence } = classifyEmbedding(embedding, cropKey);
      setResult(buildResult(cropKey, disease, confidence));
    } catch {
      setError("Couldn't analyze that photo. Try a clearer, closer shot of the leaf.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <GlassBackground>
      <SafeAreaView style={styles.safe} edges={["top"]}>
        <ScrollView contentContainerStyle={styles.container}>
        <FadeInView>
          <LinearGradient colors={gradients.dark} style={styles.hero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
            <Text style={styles.heroEmoji}>🔬</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.title}>Disease Scan</Text>
              <Text style={styles.subtitle}>
                Photograph a plant leaf — the CNN detects diseases across 18 crops, right on your phone.
              </Text>
            </View>
          </LinearGradient>
        </FadeInView>

        <FadeInView delay={100}>
          <Card>
            <PickerField label="Crop" value={crop} options={CROPS} onSelect={setCrop} />

            {image ? (
              <View style={styles.previewWrap}>
                <Image source={{ uri: image.uri }} style={styles.preview} />
                <TouchableOpacity style={styles.removeBtn} onPress={() => setImage(null)}>
                  <Ionicons name="close" size={18} color={colors.white} />
                </TouchableOpacity>
              </View>
            ) : (
              <LinearGradient
                colors={["rgba(255,255,255,0.7)", "rgba(255,255,255,0.4)"]}
                style={styles.placeholder}
              >
                <Text style={styles.placeholderEmoji}>🌿</Text>
                <Text style={styles.placeholderText}>No photo selected</Text>
                <Text style={styles.placeholderHint}>Take a clear, close-up shot of the leaf</Text>
              </LinearGradient>
            )}

            <View style={styles.btnRow}>
              <PressableScale style={{ flex: 1 }} onPress={takePhoto}>
                <LinearGradient colors={gradients.primary} style={styles.secondaryBtn} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
                  <Ionicons name="camera" size={18} color={colors.white} />
                  <Text style={styles.secondaryBtnText}>Camera</Text>
                </LinearGradient>
              </PressableScale>
              <PressableScale style={{ flex: 1 }} onPress={pickFromGallery}>
                <View style={styles.galleryBtn}>
                  <Ionicons name="images" size={18} color={colors.primary} />
                  <Text style={styles.galleryBtnText}>Gallery</Text>
                </View>
              </PressableScale>
            </View>
          </Card>
        </FadeInView>

        <ErrorText message={error} />
        <FadeInView delay={160}>
          <PrimaryButton
            title="Analyze Leaf"
            onPress={analyze}
            loading={loading}
            disabled={!image}
          />
          {model === "error" ? (
            <Text style={styles.modelError}>
              The on-device disease model could not load. Restart the app and try again.
            </Text>
          ) : null}
        </FadeInView>

        {result ? (
          <FadeInView delay={240} distance={24}>
            <View style={styles.resultWrap}>
              <LinearGradient
                colors={result.is_healthy ? ["#16a34a", "#15803d"] : ["#f59e0b", "#b45309"]}
                style={styles.resultBanner}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Text style={styles.resultEmoji}>{result.is_healthy ? "✅" : "⚠️"}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.resultTitle}>
                    {result.is_healthy ? "Healthy Plant" : result.disease_name}
                  </Text>
                  <Text style={styles.resultSub}>
                    {result.plant_type} · {result.confidence}% confidence
                  </Text>
                </View>
              </LinearGradient>

              <Card style={styles.resultDetails}>
                {!result.is_healthy ? (
                  <>
                    <DetailSection icon="medkit" title="Symptoms" text={result.symptoms} />
                    <DetailSection icon="bandage" title="Treatment" text={result.treatment} />
                    <DetailSection icon="medical" title="Medicine" text={result.medicine} />
                    <DetailSection icon="leaf" title="Organic solution" text={result.organic_solution} />
                    <DetailSection icon="shield-checkmark" title="Preventive measures" text={result.preventive_measures} />
                  </>
                ) : (
                  <Text style={styles.healthyText}>
                    Your {result.plant_type.toLowerCase()} looks healthy. Keep up the good care —
                    regular watering, balanced fertilizer, and pest monitoring will keep it that way.
                  </Text>
                )}
              </Card>
            </View>
          </FadeInView>
        ) : null}
      </ScrollView>
      </SafeAreaView>
    </GlassBackground>
  );
}

function DetailSection({
  icon,
  title,
  text,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  text: string;
}) {
  if (!text) return null;
  return (
    <View style={styles.detail}>
      <View style={styles.detailHead}>
        <View style={styles.detailIcon}>
          <Ionicons name={icon} size={13} color={colors.primary} />
        </View>
        <Text style={styles.detailTitle}>{title}</Text>
      </View>
      <Text style={styles.detailText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "transparent" },
  container: { padding: 16, paddingBottom: 120 },
  hero: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderRadius: radius.xl,
    padding: 18,
    marginBottom: 16,
    ...shadow,
  },
  heroEmoji: { fontSize: 40 },
  title: { fontSize: 20, fontWeight: "800", color: colors.white },
  subtitle: { fontSize: 12, color: "#a7f3d0", marginTop: 4, lineHeight: 17 },
  previewWrap: { alignItems: "center", marginBottom: 12 },
  preview: {
    width: "100%",
    height: 220,
    borderRadius: radius.md,
    backgroundColor: colors.bg,
  },
  removeBtn: {
    position: "absolute",
    top: 8,
    right: 8,
    backgroundColor: "rgba(0,0,0,0.55)",
    borderRadius: 999,
    padding: 6,
  },
  placeholder: {
    height: 180,
    borderRadius: radius.md,
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  placeholderEmoji: { fontSize: 40 },
  placeholderText: { fontSize: 14, fontWeight: "700", color: colors.text, marginTop: 6 },
  placeholderHint: { fontSize: 12, color: colors.textMuted, marginTop: 3 },
  btnRow: { flexDirection: "row", gap: 10 },
  secondaryBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    borderRadius: radius.md,
    paddingVertical: 13,
    ...shadow,
  },
  secondaryBtnText: { color: colors.white, fontWeight: "700", fontSize: 15 },
  galleryBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    borderWidth: 1.5,
    borderColor: colors.primary,
    borderRadius: radius.md,
    paddingVertical: 13,
    backgroundColor: "rgba(255,255,255,0.6)",
  },
  galleryBtnText: { color: colors.primary, fontWeight: "700", fontSize: 15 },
  resultWrap: { marginTop: 16 },
  resultBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    padding: 18,
    ...shadow,
  },
  resultEmoji: { fontSize: 36 },
  resultTitle: { fontSize: 20, fontWeight: "800", color: colors.white },
  resultSub: { fontSize: 13, color: "rgba(255,255,255,0.85)", marginTop: 2 },
  resultDetails: {
    borderTopLeftRadius: 0,
    borderTopRightRadius: 0,
    marginTop: 0,
  },
  detail: { marginBottom: 14 },
  detailHead: { flexDirection: "row", alignItems: "center", gap: 7, marginBottom: 4 },
  detailIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.primaryLight,
    alignItems: "center",
    justifyContent: "center",
  },
  detailTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: colors.primaryDark,
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  detailText: { fontSize: 14, color: colors.text, lineHeight: 20 },
  healthyText: { fontSize: 14, color: colors.text, lineHeight: 21 },
  modelError: {
    fontSize: 12,
    color: colors.danger,
    textAlign: "center",
    marginTop: 10,
    lineHeight: 17,
  },
});
