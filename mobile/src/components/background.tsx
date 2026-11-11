import React, { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  StyleProp,
  StyleSheet,
  View,
  ViewStyle,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";

interface OrbSpec {
  size: number;
  top?: number | string;
  bottom?: number | string;
  left?: number | string;
  right?: number | string;
  color: string;
  duration: number;
  drift: number;
}

const ORBS: OrbSpec[] = [
  { size: 230, top: -70, left: -80, color: "rgba(52,211,153,0.35)", duration: 9000, drift: 26 },
  { size: 260, top: "20%", right: -100, color: "rgba(16,185,129,0.30)", duration: 11000, drift: -34 },
  { size: 210, bottom: "14%", left: -70, color: "rgba(167,243,208,0.50)", duration: 10000, drift: 22 },
  { size: 180, bottom: "32%", right: -60, color: "rgba(6,95,70,0.16)", duration: 12000, drift: -18 },
];

function Orb({ spec }: { spec: OrbSpec }) {
  const y = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(y, {
          toValue: spec.drift,
          duration: spec.duration,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(y, {
          toValue: 0,
          duration: spec.duration,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    anim.start();
    return () => anim.stop();
  }, [spec.drift, spec.duration, y]);

  return (
    <Animated.View
      pointerEvents="none"
      style={[
        styles.orb,
        {
          width: spec.size,
          height: spec.size,
          borderRadius: spec.size / 2,
          backgroundColor: spec.color,
          top: spec.top,
          bottom: spec.bottom,
          left: spec.left,
          right: spec.right,
          transform: [{ translateY: y }],
        },
      ]}
    />
  );
}

export function GlassBackground({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[styles.root, style]}>
      <LinearGradient
        colors={["#ecfdf5", "#d1fae5", "#a7f3d0"]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      {ORBS.map((o, i) => (
        <Orb key={i} spec={o} />
      ))}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, overflow: "hidden" },
  orb: { position: "absolute" },
});
